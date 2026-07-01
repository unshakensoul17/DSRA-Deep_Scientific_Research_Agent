"""
DSRA V2 — LLM Gateway
======================
Handles communication with LLM providers with automatic retries,
model fallbacks, structured JSON enforcement, and token counting telemetry.
"""

from typing import Any, Optional, Type
import json
import time

from openai import AsyncOpenAI, RateLimitError, APIError
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.exceptions.base import LLMGatewayError, LLMRateLimitError, LLMInvalidResponseError

log = get_logger(__name__)
settings = get_settings()


class LLMGateway:
    """
    Central gateway for all LLM interactions.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_request_timeout,
        )
        self.default_model = settings.openai_default_model
        self.fallback_model = settings.openai_fallback_model
        self.max_retries = settings.openai_max_retries

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError)),
        before_sleep=before_sleep_log(log, "warning"),
    )
    async def _execute_with_retry(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        response_format: Optional[dict[str, Any]],
    ) -> Any:
        """Call the OpenAI client with tenacity retry rules."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                temperature=temperature,
                response_format=response_format,  # type: ignore
            )
            return response
        except RateLimitError as e:
            log.warning("openai_rate_limit", model=model, error=str(e))
            raise e
        except APIError as e:
            log.error("openai_api_error", model=model, error=str(e))
            raise e

    async def get_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_schema: Optional[Type[BaseModel]] = None,
    ) -> str:
        """
        Request a completion from the LLM, automatically handling fallback routing.
        """
        response_format = None
        if response_schema:
            # Force structured JSON mode
            response_format = {"type": "json_object"}
            # Append JSON formatting instructions to system prompt
            schema_inst = (
                f"\nYou must return a JSON object that strictly complies with this schema:\n"
                f"{json.dumps(response_schema.model_json_schema())}"
            )
            # Find the system message to append the schema instructions
            for msg in messages:
                if msg["role"] == "system":
                    msg["content"] += schema_inst
                    break

        model = self.default_model
        start_time = time.perf_counter()

        try:
            log.debug("llm_completion_started", model=model)
            response = await self._execute_with_retry(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
            )
        except Exception as primary_error:
            log.warning(
                "llm_primary_model_failed_attempting_fallback",
                model=model,
                fallback=self.fallback_model,
                error=str(primary_error),
            )
            # Route to fallback model on failure
            try:
                response = await self._execute_with_retry(
                    model=self.fallback_model,
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format,
                )
                model = self.fallback_model
            except Exception as fallback_error:
                log.error("llm_both_models_failed", error=str(fallback_error))
                raise LLMGatewayError(
                    message=f"LLM gateway failed on primary and fallback models: {str(fallback_error)}"
                ) from fallback_error

        duration = time.perf_counter() - start_time
        content = response.choices[0].message.content or ""
        
        # Telemetry metrics
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        log.info(
            "llm_completion_finished",
            model=model,
            duration_ms=int(duration * 1000),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

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
            log.error("llm_invalid_json_format", content=content, error=str(e))
            raise LLMInvalidResponseError(
                message=f"LLM failed to return valid JSON: {str(e)}",
                details={"raw_content": content},
            ) from e
        except Exception as e:
            log.error("pydantic_validation_failed", content=content, error=str(e))
            raise LLMInvalidResponseError(
                message=f"LLM output failed Pydantic validation: {str(e)}",
                details={"raw_content": content},
            ) from e


# Singleton instance
llm_gateway = LLMGateway()
