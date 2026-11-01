"""Provider-neutral LLM gateway.

Replay is the default: results come from a recorded file per agent and subject, so the demo runs
with no key and no network. A recorded result carries the hash of the input it was made from, so
a changed input fails loudly instead of replaying an out-of-date answer.

A live provider implements the same `run`. Claude is the one wired in here, and another approved
model only needs its own gateway class.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import anthropic
from pydantic import BaseModel

from engines.agents.prompts import SYSTEM_PROMPT, TASKS

LIVE_SOURCE = "live_model"
MAX_OUTPUT_TOKENS = 16000
TIMEOUT_SECONDS = 110
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class ReplayMiss(LookupError):
    pass


class StaleReplay(LookupError):
    pass


class LiveAgentError(RuntimeError):
    """A plain message for the person who pressed the button. The cached result stays in place."""


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
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMGateway(Protocol):
    def run(self, request: AgentRequest, schema: type[BaseModel] | None = None) -> AgentResult: ...


class ReplayGateway:
    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir

    def path_for(self, request: AgentRequest) -> Path:
        return self._cache_dir / request.agent / f"{request.subject}.json"

    def run(self, request: AgentRequest, schema: type[BaseModel] | None = None) -> AgentResult:
        path = self.path_for(request)
        if not path.exists():
            raise ReplayMiss(f"No recorded result for {request.agent} on {request.subject}")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["input_hash"] != request.input_hash:
            raise StaleReplay(f"{request.agent} on {request.subject} was recorded from a different input")
        return AgentResult(record["output"], record["source"], record["model"], record["duration_ms"])


class ClaudeGateway:
    def __init__(self, model: str, client: Any = None) -> None:
        self._model = model
        self._client = client or anthropic.Anthropic(timeout=TIMEOUT_SECONDS, max_retries=1)

    def _call(self, request: AgentRequest, schema: type[BaseModel]) -> Any:
        material = json.dumps(request.payload, indent=2, sort_keys=True, default=str)
        try:
            return self._client.beta.messages.parse(
                model=self._model,
                max_tokens=MAX_OUTPUT_TOKENS,
                betas=[FALLBACK_BETA],
                extra_body={"fallbacks": "default"},
                output_config={"effort": "medium"},
                output_format=schema,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"{TASKS[request.agent]}\n\n<material>\n{material}\n</material>",
                    }
                ],
            )
        except anthropic.AuthenticationError as error:
            raise LiveAgentError("The API key was not accepted.") from error
        except anthropic.PermissionDeniedError as error:
            raise LiveAgentError("This API key may not use the model.") from error
        except anthropic.RateLimitError as error:
            raise LiveAgentError("The model is rate limited. Try again in a minute.") from error
        except anthropic.APIConnectionError as error:
            raise LiveAgentError("The model could not be reached in time.") from error
        except anthropic.APIStatusError as error:
            raise LiveAgentError(f"The model returned an error ({error.status_code}).") from error

    def run(self, request: AgentRequest, schema: type[BaseModel] | None = None) -> AgentResult:
        if schema is None:
            raise ValueError("A live agent needs an output schema.")
        started = time.monotonic()
        response = self._call(request, schema)
        if response.stop_reason == "refusal":
            raise LiveAgentError("The model declined this request.")
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            raise LiveAgentError("The model did not return a complete result.")
        return AgentResult(
            response.parsed_output.model_dump(),
            LIVE_SOURCE,
            response.model,
            round((time.monotonic() - started) * 1000),
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
