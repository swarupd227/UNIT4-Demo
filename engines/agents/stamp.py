"""Records which input each hand-authored result was written against.

Run after reviewing an authored file against a changed input. Results recorded from a live model
are never stamped: they are re-run.
"""

import json

from app.db import get_engine
from engines.agents.gateway import ReplayGateway
from engines.agents.pipeline import CACHE_DIR, build_requests


def main() -> None:
    gateway = ReplayGateway(CACHE_DIR)
    with get_engine().connect() as db:
        for _, request in build_requests(db):
            path = gateway.path_for(request)
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["source"] != "hand_authored":
                continue
            record["input_hash"] = request.input_hash
            path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
            )
            print(f"Stamped {request.agent} on {request.subject}")


if __name__ == "__main__":
    main()
