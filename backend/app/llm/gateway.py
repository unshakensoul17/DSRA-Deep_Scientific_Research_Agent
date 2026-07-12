"""
DSRA V2 — LLM Gateway
======================
Handles communication with Google Gemini with automatic retries,
model fallbacks, structured JSON enforcement, and token counting telemetry.
"""

import asyncio
from typing import Any, Optional, Type
import json
import time

from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.exceptions.base import LLMGatewayError, LLMRateLimitError, LLMInvalidResponseError

try:
    import google.generativeai as genai
    from google.api_core.exceptions import GoogleAPIError, ResourceExhausted
except ModuleNotFoundError:
    genai = None  # type: ignore[assignment]

    class ResourceExhausted(Exception):
        """Placeholder used when google-generativeai is not installed."""

    class GoogleAPIError(Exception):
        """Placeholder used when google-api-core is not installed."""


log = get_logger(__name__)
settings = get_settings()
STRUCTURED_MAX_OUTPUT_TOKENS = 4096


def _build_gemini_contents(messages: list[dict[str, str]]) -> tuple[str, list[dict]]:
    """
    Convert the standard messages list (role/content dicts) into Gemini's
    system_instruction + contents format.

    - The first 'system' message becomes the Gemini system_instruction.
    - Remaining messages are mapped: 'user' → 'user', 'assistant' → 'model'.
    """
    system_instruction = ""
    contents: list[dict] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system" and not system_instruction:
            system_instruction = content
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        else:
            contents.append({"role": "user", "parts": [{"text": content}]})

    return system_instruction, contents


def _extract_json_candidate(content: str) -> str:
    """
    Pull the likeliest JSON payload out of model output.
    Handles code fences and surrounding commentary.
    """
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].lstrip()

    first_brace = candidate.find("{")
    last_brace = candidate.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return candidate[first_brace:last_brace + 1]

    return candidate


class LLMGateway:
    """
    Central gateway for all LLM interactions.
    Wraps Google Gemini with retry logic, fallback routing, and telemetry.
    """

    def __init__(self) -> None:
        if genai is not None:
            genai.configure(api_key=settings.gemini_api_key)
        self.default_model = settings.gemini_default_model
        self.fallback_model = settings.gemini_fallback_model
        self.max_retries = settings.gemini_max_retries
        self.request_timeout = settings.gemini_request_timeout

    def _get_model(
        self,
        model_name: str,
        system_instruction: str,
        generation_config: dict,
    ) -> Any:
        if genai is None:
            raise LLMGatewayError(
                message="google-generativeai is not installed. Install backend requirements before using LLM calls."
            )
        return genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction or None,
            generation_config=generation_config,
        )

    async def _request_completion(
        self,
        messages: list[dict[str, str]],
        generation_config: dict[str, Any],
    ) -> tuple[str, Any, str]:
        """
        Execute a completion with fallback routing and return raw text plus telemetry.
        """
        system_instruction, contents = _build_gemini_contents(messages)
        model_name = self.default_model
        start_time = time.perf_counter()

        try:
            log.debug("llm_completion_started", model=model_name)
            response = await self._execute_with_retry(
                model_name=model_name,
                system_instruction=system_instruction,
                contents=contents,
                generation_config=generation_config,
            )
        except Exception as primary_error:
            log.warning(
                "llm_primary_model_failed_attempting_fallback",
                model=model_name,
                fallback=self.fallback_model,
                error=str(primary_error),
            )
            try:
                response = await self._execute_with_retry(
                    model_name=self.fallback_model,
                    system_instruction=system_instruction,
                    contents=contents,
                    generation_config=generation_config,
                )
                model_name = self.fallback_model
            except Exception as fallback_error:
                log.error("llm_both_models_failed", error=str(fallback_error))
                raise LLMGatewayError(
                    message=f"LLM gateway failed on primary and fallback models: {str(fallback_error)}"
                ) from fallback_error

        duration = time.perf_counter() - start_time
        content = response.text or ""

        try:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
        except Exception:
            input_tokens = 0
            output_tokens = 0

        log.info(
            "llm_completion_finished",
            model=model_name,
            duration_ms=int(duration * 1000),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return content, response, model_name

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ResourceExhausted, GoogleAPIError)),
    )
    async def _execute_with_retry(
        self,
        model_name: str,
        system_instruction: str,
        contents: list[dict],
        generation_config: dict,
    ) -> Any:
        """Call the Gemini model with tenacity retry rules."""
        try:
            model = self._get_model(model_name, system_instruction, generation_config)
            response = await asyncio.wait_for(
                model.generate_content_async(contents),
                timeout=self.request_timeout,
            )
            return response
        except asyncio.TimeoutError as e:
            log.warning(
                "gemini_request_timeout",
                model=model_name,
                timeout_seconds=self.request_timeout,
            )
            raise e
        except ResourceExhausted as e:
            log.warning("gemini_rate_limit", model=model_name, error=str(e))
            raise e
        except GoogleAPIError as e:
            log.error("gemini_api_error", model=model_name, error=str(e))
            raise e

    async def get_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_schema: Optional[Type[BaseModel]] = None,
    ) -> str:
        """
        Request a completion from Gemini, automatically handling fallback routing.
        """
        generation_config: dict[str, Any] = {
            "temperature": temperature,
        }

        if response_schema:
            # Append JSON schema instruction to system message
            schema_inst = (
                f"\nYou must return only a JSON object that strictly complies with this schema:\n"
                f"{json.dumps(response_schema.model_json_schema())}"
            )
            messages = [dict(msg) for msg in messages]
            for idx, msg in enumerate(messages):
                if msg["role"] == "system":
                    msg["content"] = msg["content"] + schema_inst
                    messages[idx] = msg
                    break
            else:
                messages.insert(0, {"role": "system", "content": schema_inst.strip()})
            generation_config["response_mime_type"] = "application/json"
            generation_config["max_output_tokens"] = STRUCTURED_MAX_OUTPUT_TOKENS

        content, _, _ = await self._request_completion(messages, generation_config)
        return content

    async def get_structured_completion(
        self,
        messages: list[dict[str, str]],
        response_schema: Type[BaseModel],
        temperature: float = 0.2,
    ) -> Any:
        """
        Request a completion and parse it directly into a Pydantic model.
        Guarantees that the return value matches the expected schema.
        """
        content = await self.get_chat_completion(
            messages=messages,
            temperature=temperature,
            response_schema=response_schema,
        )

        try:
            data = json.loads(content)
            return response_schema.model_validate(data)
        except json.JSONDecodeError as e:
            candidate = _extract_json_candidate(content)
            try:
                data = json.loads(candidate)
                return response_schema.model_validate(data)
            except json.JSONDecodeError:
                log.warning("llm_invalid_json_format_attempting_repair", error=str(e), content_length=len(content))
                repair_schema = json.dumps(response_schema.model_json_schema())
                repair_messages = [
                    {
                        "role": "system",
                        "content": (
                            "You repair malformed JSON produced by another model. "
                            "Return only valid JSON and nothing else."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Fix the following malformed response so it strictly matches this schema.\n"
                            f"SCHEMA:\n{repair_schema}\n\n"
                            f"RESPONSE:\n{content}"
                        ),
                    },
                ]

                repair_generation_config: dict[str, Any] = {
                    "temperature": 0.0,
                    "response_mime_type": "application/json",
                    "max_output_tokens": STRUCTURED_MAX_OUTPUT_TOKENS,
                }
                repair_content, _, _ = await self._request_completion(repair_messages, repair_generation_config)

                try:
                    repair_data = json.loads(_extract_json_candidate(repair_content))
                    return response_schema.model_validate(repair_data)
                except Exception as repair_error:
                    log.error(
                        "llm_json_repair_failed",
                        content_length=len(content),
                        repair_length=len(repair_content),
                        error=str(repair_error),
                    )
                    raise LLMInvalidResponseError(
                        message=f"LLM failed to return valid JSON: {str(e)}",
                        details={"raw_content": content, "repair_content": repair_content},
                    ) from repair_error
        except ValidationError as e:
            log.error("pydantic_validation_failed", content_length=len(content), error=str(e))
            raise LLMInvalidResponseError(
                message=f"LLM output failed Pydantic validation: {str(e)}",
                details={"raw_content": content},
            ) from e


# Singleton instance
llm_gateway = LLMGateway()
