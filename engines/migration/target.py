"""The only route into the target. A real ERPx test tenant would implement the same interface
through supported configuration and APIs; nothing writes to a target database directly.
"""

from collections.abc import Sequence
from typing import Any, Protocol


class ErpxTarget(Protocol):
    def load(self, object_name: str, columns: Sequence[str], rows: Sequence[tuple[Any, ...]]) -> None: ...


class SimulatedErpxTarget:
    """Holds loaded objects in memory for the caller to persist. Stated openly in the demo."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[list[str], list[tuple[Any, ...]]]] = {}

    def load(self, object_name: str, columns: Sequence[str], rows: Sequence[tuple[Any, ...]]) -> None:
        self.objects[object_name] = (list(columns), list(rows))
