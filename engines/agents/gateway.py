"""Provider-neutral LLM gateway.

Replay is the default: results come from a recorded file per agent and subject, so the demo runs
with no key and no network. A recorded result carries the hash of the input it was made from, so
a changed input fails loudly instead of replaying an out-of-date answer.

A live provider implements the same `run`. None is wired in yet, because no key is available.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class ReplayMiss(LookupError):
    pass


class StaleReplay(LookupError):
    pass


@dataclass(frozen=True)
class AgentRequest:
    agent: str
    subject: str
    prompt_version: str
    payload: dict[str, Any]

    @property
    def input_hash(self) -> str:
        body = json.dumps(
            {"agent": self.agent, "prompt_version": self.prompt_version, "payload": self.payload},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(body.encode()).hexdigest()


@dataclass(frozen=True)
class AgentResult:
    output: dict[str, Any]
    source: str
    model: str | None
    duration_ms: int | None


class LLMGateway(Protocol):
    def run(self, request: AgentRequest) -> AgentResult: ...


class ReplayGateway:
    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir

    def path_for(self, request: AgentRequest) -> Path:
        return self._cache_dir / request.agent / f"{request.subject}.json"

    def run(self, request: AgentRequest) -> AgentResult:
        path = self.path_for(request)
        if not path.exists():
            raise ReplayMiss(f"No recorded result for {request.agent} on {request.subject}")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["input_hash"] != request.input_hash:
            raise StaleReplay(f"{request.agent} on {request.subject} was recorded from a different input")
        return AgentResult(record["output"], record["source"], record["model"], record["duration_ms"])
