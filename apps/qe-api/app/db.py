from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Connection, Engine, create_engine

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def get_connection() -> Iterator[Connection]:
    with get_engine().connect() as connection:
        yield connection


def get_transaction() -> Iterator[Connection]:
    with get_engine().begin() as connection:
        yield connection


Db = Annotated[Connection, Depends(get_connection)]
# Commits before the response is sent, so a client that reads straight after a write sees it.
Tx = Annotated[Connection, Depends(get_transaction, scope="function")]
