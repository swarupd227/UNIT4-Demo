"""The live agent path, with a stand-in for the model so that tests need no key or network."""

import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import app
from engines.agents.gateway import AgentRequest, AgentResult, ClaudeGateway, LiveAgentError
from engines.agents.pipeline import CACHE_DIR
from engines.agents.schemas import CodeExplanation

CONSULTANT = {"X-Studio-Persona": "consultant"}
CUSTOMER = {"X-Studio-Persona": "customer"}
RUN_URL = "/api/agents/code_explainer/CC-014/run"


def cached_output() -> dict[str, Any]:
    record = json.loads((CACHE_DIR / "code_explainer" / "CC-014.json").read_text(encoding="utf-8"))
    return record["output"]


class FakeGateway:
    def __init__(self, output: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self._output = output
        self._error = error

    def run(self, request: AgentRequest, schema: type[BaseModel] | None = None) -> AgentResult:
        if self._error:
            raise self._error
        return AgentResult(self._output or {}, "live_model", "test-model", 1500, 100, 50)


def use_gateway(monkeypatch: pytest.MonkeyPatch, gateway: FakeGateway) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr("app.validation._live_gateway", lambda: gateway)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        test_client.post("/api/workspace/reset")
        yield test_client
        test_client.post("/api/workspace/reset")


def explanation(client: TestClient) -> dict[str, Any]:
    rows = client.get("/api/artefacts/CC-014").json()
    return next(row for row in rows if row["kind"] == "code_explanation")


def test_a_live_result_replaces_the_cached_one_and_a_reset_restores_it(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = {**cached_output(), "plain_english": "Written by the model."}
    use_gateway(monkeypatch, FakeGateway(output))
    response = client.post(RUN_URL, headers=CONSULTANT)
    assert response.status_code == 200, response.text
    stored = explanation(client)
    assert (stored["source"], stored["model"], stored["duration_ms"]) == ("live_model", "test-model", 1500)
    assert stored["content"]["plain_english"] == "Written by the model."
    client.post("/api/workspace/reset")
    assert explanation(client)["source"] == "hand_authored"


def test_a_citation_the_source_does_not_contain_is_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = cached_output()
    output["steps"] = [{"text": "Invented", "find": "this line is not in the code"}]
    use_gateway(monkeypatch, FakeGateway(output))
    response = client.post(RUN_URL, headers=CONSULTANT)
    assert response.status_code == 502
    assert "rejected" in response.json()["detail"]
    assert explanation(client)["source"] == "hand_authored"


def test_a_model_failure_keeps_the_cached_result(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    use_gateway(monkeypatch, FakeGateway(error=LiveAgentError("The model could not be reached in time.")))
    response = client.post(RUN_URL, headers=CONSULTANT)
    assert response.status_code == 502
    assert "still in place" in response.json()["detail"]
    assert explanation(client)["source"] == "hand_authored"


def test_only_the_consultant_runs_agents(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    use_gateway(monkeypatch, FakeGateway(cached_output()))
    assert client.post(RUN_URL, headers=CUSTOMER).status_code == 403


def test_an_unknown_agent_or_item_is_refused(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    use_gateway(monkeypatch, FakeGateway(cached_output()))
    assert client.post("/api/agents/code_explainer/RP-001/run", headers=CONSULTANT).status_code == 404


def test_without_a_key_the_status_is_off_and_a_run_is_refused(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert client.get("/api/agents/status").json()["live"] is False
    assert client.post(RUN_URL, headers=CONSULTANT).status_code == 409


def test_a_live_run_is_on_the_audit_trail(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    use_gateway(monkeypatch, FakeGateway(cached_output()))
    client.post(RUN_URL, headers=CONSULTANT)
    audit = client.get("/api/decisions/CC-014").json()["audit"]
    assert audit[0]["action"] == "ran_agent"
    assert client.get("/api/audit/verify").json()["intact"] is True


def parsed(**overrides: Any) -> SimpleNamespace:
    fields = {
        "stop_reason": "end_turn",
        "parsed_output": CodeExplanation.model_validate(cached_output()),
        "model": "claude-test",
        "usage": SimpleNamespace(input_tokens=10, output_tokens=20),
    }
    return SimpleNamespace(**{**fields, **overrides})


def gateway_returning(response: SimpleNamespace) -> ClaudeGateway:
    parse = lambda **_: response  # noqa: E731
    return ClaudeGateway(
        "claude-test", SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=parse)))
    )


REQUEST = AgentRequest("code_explainer", "CC-014", "1", {"item_id": "CC-014"})


def test_the_gateway_reports_tokens_and_marks_the_source() -> None:
    result = gateway_returning(parsed()).run(REQUEST, CodeExplanation)
    assert (result.source, result.model) == ("live_model", "claude-test")
    assert (result.input_tokens, result.output_tokens) == (10, 20)


@pytest.mark.parametrize("response", [parsed(stop_reason="refusal"), parsed(stop_reason="max_tokens")])
def test_an_incomplete_response_never_counts_as_a_result(response: SimpleNamespace) -> None:
    with pytest.raises(LiveAgentError):
        gateway_returning(response).run(REQUEST, CodeExplanation)
