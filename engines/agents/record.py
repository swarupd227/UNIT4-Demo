"""Runs every agent against the model and reports the checks, time and tokens.

Writes to data/generated/agent_runs, so nothing the app replays changes. With --save, results go
to the replay cache instead, and a changed input then means re-running this, never stamping.
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.config import get_settings
from app.db import get_engine
from data.generator.common import GENERATED
from engines.agents.gateway import AgentRequest, ClaudeGateway, LiveAgentError
from engines.agents.pipeline import CACHE_DIR, AgentSpec, build_requests, checked_content

PARALLEL_CALLS = 4
INPUT_USD_PER_MILLION = 4.0
OUTPUT_USD_PER_MILLION = 20.0


def _run(gateway: ClaudeGateway, spec: AgentSpec, request: AgentRequest, out: Path) -> tuple[int, int] | None:
    label = f"{request.agent} on {request.subject}"
    try:
        result = gateway.run(request, spec.schema)
        checked_content(spec, request, result)
    except (LiveAgentError, ValueError) as error:
        print(f"FAIL {label}: {error}")
        return None
    path = out / request.agent / f"{request.subject}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "input_hash": request.input_hash,
        "source": result.source,
        "model": result.model,
        "duration_ms": result.duration_ms,
        "output": result.output,
    }
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(
        f"OK   {label}: {result.duration_ms / 1000:.1f} sec, "
        f"{result.input_tokens} in, {result.output_tokens} out, {result.model}"
    )
    return result.input_tokens or 0, result.output_tokens or 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", action="store_true", help="Write to the replay cache")
    parser.add_argument("--agent", help="Run only this agent")
    arguments = parser.parse_args()
    out = CACHE_DIR if arguments.save else GENERATED / "agent_runs"
    with get_engine().connect() as db:
        requests = [
            entry
            for entry in build_requests(db)
            if arguments.agent is None or entry[1].agent == arguments.agent
        ]
    gateway = ClaudeGateway(get_settings().llm_model)
    with ThreadPoolExecutor(PARALLEL_CALLS) as pool:
        results = list(pool.map(lambda entry: _run(gateway, entry[0], entry[1], out), requests))
    passed = [result for result in results if result]
    tokens_in = sum(result[0] for result in passed)
    tokens_out = sum(result[1] for result in passed)
    cost = tokens_in * INPUT_USD_PER_MILLION / 1e6 + tokens_out * OUTPUT_USD_PER_MILLION / 1e6
    print(f"{len(passed)} of {len(results)} passed. {tokens_in} in, {tokens_out} out, about ${cost:.2f}.")


if __name__ == "__main__":
    main()
