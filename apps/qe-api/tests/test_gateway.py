import json
from pathlib import Path

import pytest

from qe.engines.agents.gateway import AgentRequest, ReplayGateway, ReplayMiss, StaleReplay


def test_replay_returns_the_recorded_result_and_rejects_a_changed_input(tmp_path: Path) -> None:
    request = AgentRequest("validator", "TC-1", "1", {"case": "steps"})
    gateway = ReplayGateway(tmp_path)
    with pytest.raises(ReplayMiss):
        gateway.run(request)

    path = gateway.path_for(request)
    path.parent.mkdir(parents=True)
    record = {
        "input_hash": request.input_hash,
        "output": {"ok": True},
        "source": "live_model",
        "model": "m",
        "duration_ms": 5,
    }
    path.write_text(json.dumps(record), encoding="utf-8")
    assert gateway.run(request).output == {"ok": True}

    with pytest.raises(StaleReplay):
        gateway.run(AgentRequest("validator", "TC-1", "1", {"case": "other steps"}))
