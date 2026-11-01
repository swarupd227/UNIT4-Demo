"""File storage behind an interface: a local folder here, Blob Storage on Azure."""

from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from app.config import get_settings


class Storage(Protocol):
    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes: ...


def _validated(key: str) -> PurePosixPath:
    relative = PurePosixPath(key)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Invalid storage key: {key}")
    return relative


class LocalStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root)

    def _path(self, key: str) -> Path:
        return self._root / _validated(key)

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()


class BlobStorage:
    def __init__(self, container: Any) -> None:
        self._container = container

    def put(self, key: str, data: bytes) -> None:
        self._container.upload_blob(str(_validated(key)), data, overwrite=True)

    def get(self, key: str) -> bytes:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            return self._container.download_blob(str(_validated(key))).readall()
        except ResourceNotFoundError as error:
            raise FileNotFoundError(key) from error


@lru_cache
def get_storage() -> Storage:
    settings = get_settings()
    if settings.blob_connection_string:
        from azure.storage.blob import ContainerClient

        container = ContainerClient.from_connection_string(
            settings.blob_connection_string, settings.blob_container
        )
        if not container.exists():
            container.create_container()
        return BlobStorage(container)
    if settings.blob_account_url:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        service = BlobServiceClient(settings.blob_account_url, credential=DefaultAzureCredential())
        return BlobStorage(service.get_container_client(settings.blob_container))
    return LocalStorage(settings.storage_root)
