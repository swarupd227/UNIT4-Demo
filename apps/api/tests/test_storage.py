from pathlib import Path

import pytest

from app.storage import LocalStorage


def test_round_trip(tmp_path: Path) -> None:
    storage = LocalStorage(str(tmp_path))
    storage.put("packs/one.txt", b"evidence")
    assert storage.get("packs/one.txt") == b"evidence"


@pytest.mark.parametrize("key", ["../outside.txt", "/etc/passwd", "a/../../b"])
def test_rejects_escaping_keys(tmp_path: Path, key: str) -> None:
    with pytest.raises(ValueError):
        LocalStorage(str(tmp_path)).put(key, b"x")
