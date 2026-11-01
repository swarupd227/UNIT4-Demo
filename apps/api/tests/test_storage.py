from pathlib import Path
from typing import Any

import pytest
from azure.core.exceptions import ResourceNotFoundError

from app.config import Settings
from app.storage import BlobStorage, LocalStorage, get_storage


class FakeDownload:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def readall(self) -> bytes:
        return self._data


class FakeContainer:
    def __init__(self) -> None:
        self.blobs: dict[str, bytes] = {}

    def upload_blob(self, name: str, data: bytes, overwrite: bool = False) -> None:
        assert overwrite, "A regenerated pack must replace the old file."
        self.blobs[name] = data

    def download_blob(self, name: str) -> FakeDownload:
        if name not in self.blobs:
            raise ResourceNotFoundError("missing")
        return FakeDownload(self.blobs[name])


def test_round_trip(tmp_path: Path) -> None:
    storage = LocalStorage(str(tmp_path))
    storage.put("packs/one.txt", b"evidence")
    assert storage.get("packs/one.txt") == b"evidence"


@pytest.mark.parametrize("key", ["../outside.txt", "/etc/passwd", "a/../../b"])
def test_rejects_escaping_keys(tmp_path: Path, key: str) -> None:
    with pytest.raises(ValueError):
        LocalStorage(str(tmp_path)).put(key, b"x")


def test_blob_round_trip_replaces_the_old_file() -> None:
    storage = BlobStorage(FakeContainer())
    storage.put("packs/1/signoff_pack.pdf", b"first")
    storage.put("packs/1/signoff_pack.pdf", b"second")
    assert storage.get("packs/1/signoff_pack.pdf") == b"second"


def test_blob_missing_file_looks_like_a_missing_local_file() -> None:
    with pytest.raises(FileNotFoundError):
        BlobStorage(FakeContainer()).get("packs/9/signoff_pack.pdf")


@pytest.mark.parametrize("key", ["../outside.txt", "/etc/passwd"])
def test_blob_rejects_escaping_keys(key: str) -> None:
    with pytest.raises(ValueError):
        BlobStorage(FakeContainer()).put(key, b"x")


def test_local_storage_is_the_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings: Any = Settings(storage_root=str(tmp_path))
    monkeypatch.setattr("app.storage.get_settings", lambda: settings)
    get_storage.cache_clear()
    try:
        assert isinstance(get_storage(), LocalStorage)
    finally:
        get_storage.cache_clear()
