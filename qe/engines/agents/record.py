"""Records the context agents' results for replay, calling the model only where a recording is
missing or was made from a different input.

    python -m qe.engines.agents.record             runs inside the qe-api container, with the key set

Every result passes the same checks as in the app before it is written. A result that fails a
check is not saved, and the script says why.
"""

import json
import sys
from pathlib import Path

from pydantic import BaseModel

from qe.engines.agents.gateway import (
    AgentRequest,
    AgentResult,
    ClaudeGateway,
    LiveAgentError,
    ReplayGateway,
    ReplayMiss,
    StaleReplay,
)
from qe.engines.analysis import RECORDINGS, CheckFailed, Sources, analyse, checked

QE_ROOT = Path(__file__).resolve().parents[2]
HISTORY_REPO = QE_ROOT / "history" / "repo"
MODEL = "claude-opus-5-5"
GATE_PERCENT = 80


class RecordingGateway:
    def __init__(self, src: Sources) -> None:
        self._src = src
        self._replay = ReplayGateway(RECORDINGS)
        self._live = ClaudeGateway(MODEL)
        self.failures: list[str] = []

    def run(self, request: AgentRequest, schema: type[BaseModel] | None = None) -> AgentResult:
        label = f"{request.agent} on {request.subject}"
        try:
            return self._replay.run(request, schema)
        except (ReplayMiss, StaleReplay):
            pass
        print(f"...  {label}", flush=True)
        try:
            result = self._live.run(request, schema)
            checked(self._src, request, result.output)
        except (LiveAgentError, CheckFailed) as error:
            self.failures.append(f"{label}: {error}")
            print(f"FAIL {label}: {error}", flush=True)
            raise ReplayMiss(label) from error
        path = self._replay.path_for(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "input_hash": request.input_hash,
            "source": result.source,
            "model": result.model,
            "duration_ms": result.duration_ms,
            "output": result.output,
        }
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        print(
            f"OK   {label}: {(result.duration_ms or 0) / 1000:.0f} s, "
            f"{result.input_tokens} in, {result.output_tokens} out",
            flush=True,
        )
        return result


def main() -> None:
    src = Sources.at(QE_ROOT, HISTORY_REPO, GATE_PERCENT)
    gateway = RecordingGateway(src)
    analyse(src, gateway)
    print(f"{len(gateway.failures)} failed" if gateway.failures else "All recordings are current")
    sys.exit(1 if gateway.failures else 0)


if __name__ == "__main__":
    main()
