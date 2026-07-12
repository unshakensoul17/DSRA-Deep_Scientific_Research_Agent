import asyncio
from types import SimpleNamespace

import pytest

from app.llm.gateway import LLMGateway
from app.schemas.agents.planner import PlannerLLMPlan


@pytest.mark.asyncio
async def test_get_chat_completion_adds_response_schema_to_system_instruction(monkeypatch) -> None:
    gateway = LLMGateway()
    captured = {}

    async def fake_execute_with_retry(model_name, system_instruction, contents, generation_config):
        captured["system_instruction"] = system_instruction
        captured["contents"] = contents
        captured["generation_config"] = generation_config
        return SimpleNamespace(
            text='{"queries":[]}',
            usage_metadata=SimpleNamespace(prompt_token_count=1, candidates_token_count=1),
        )

    monkeypatch.setattr(gateway, "_execute_with_retry", fake_execute_with_retry)

    await gateway.get_chat_completion(
        messages=[
            {"role": "system", "content": "System contract."},
            {"role": "user", "content": "Plan this topic."},
        ],
        response_schema=PlannerLLMPlan,
    )

    assert "System contract." in captured["system_instruction"]
    assert "strictly complies with this schema" in captured["system_instruction"]
    assert "query_text" in captured["system_instruction"]
    assert captured["generation_config"]["response_mime_type"] == "application/json"
    assert captured["generation_config"]["max_output_tokens"] == 4096


@pytest.mark.asyncio
async def test_get_structured_completion_repairs_malformed_json(monkeypatch) -> None:
    gateway = LLMGateway()
    calls = []

    async def fake_execute_with_retry(model_name, system_instruction, contents, generation_config):
        calls.append(
            {
                "model_name": model_name,
                "system_instruction": system_instruction,
                "generation_config": generation_config,
            }
        )
        if "repair malformed JSON" in system_instruction:
            return SimpleNamespace(
                text=(
                    '{"queries":[{"query_text":"CRISPR sickle cell clinical trial","source_type":"pubmed",'
                    '"priority":0.9,"filters":{}}],"estimated_complexity":0.5,"suggested_depth":2,'
                    '"focus_areas":[],"reasoning":"Valid repaired JSON."}'
                ),
                usage_metadata=SimpleNamespace(prompt_token_count=1, candidates_token_count=1),
            )

        return SimpleNamespace(
            text=(
                '{"queries":[{"query_text":"CRISPR sickle cell clinical trial","source_type":"pubmed",'
                '"priority":0.9,"filters":{}}],"estimated_complexity":0.5,"suggested_depth":2,'
                '"focus_areas":[],"reasoning":"Broken JSON"'
            ),
            usage_metadata=SimpleNamespace(prompt_token_count=1, candidates_token_count=1),
        )

    monkeypatch.setattr(gateway, "_execute_with_retry", fake_execute_with_retry)

    result = await gateway.get_structured_completion(
        messages=[
            {"role": "system", "content": "System contract."},
            {"role": "user", "content": "Plan this topic."},
        ],
        response_schema=PlannerLLMPlan,
    )

    assert isinstance(result, PlannerLLMPlan)
    assert result.queries[0].query_text == "CRISPR sickle cell clinical trial"
    assert len(calls) == 2
    assert "repair malformed JSON" in calls[1]["system_instruction"]


@pytest.mark.asyncio
async def test_execute_with_retry_times_out_when_model_never_returns(monkeypatch) -> None:
    gateway = LLMGateway()
    gateway.request_timeout = 0.05

    class HangingModel:
        async def generate_content_async(self, contents):
            await asyncio.sleep(1)

    monkeypatch.setattr(gateway, "_get_model", lambda *args, **kwargs: HangingModel())

    with pytest.raises(asyncio.TimeoutError):
        await gateway._execute_with_retry(
            model_name="gemini-3.5-flash",
            system_instruction="system",
            contents=[{"role": "user", "parts": [{"text": "hello"}]}],
            generation_config={},
        )
