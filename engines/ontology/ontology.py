"""The migration ontology: what the agents are grounded in and what the decision rules protect."""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ONTOLOGY_PATH = Path(__file__).parent / "migration_ontology.yaml"


@lru_cache
def _document() -> dict[str, Any]:
    return yaml.safe_load(ONTOLOGY_PATH.read_text(encoding="utf-8"))


def version() -> str:
    return _document()["version"]


def concepts() -> dict[str, dict[str, Any]]:
    return {concept["id"]: concept for concept in _document()["concepts"]}


def protected_patterns() -> list[str]:
    return [c["protected_pattern"] for c in _document()["concepts"] if c.get("protected_pattern")]


def _mentioned(concept: dict[str, Any], text: str) -> bool:
    return any(
        re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", text, re.IGNORECASE)
        for term in concept["synonyms"]
    )


def grounding_for(text: str) -> list[dict[str, Any]]:
    """The concepts this material mentions, plus the ones they relate to, in ontology order."""
    known = concepts()
    found = {concept_id for concept_id, concept in known.items() if _mentioned(concept, text)}
    related = {r["target"] for concept_id in found for r in known[concept_id].get("relations", [])}
    return [
        {
            "id": concept_id,
            "label": concept["label"],
            "meaning": concept["meaning"],
            "relations": concept.get("relations", []),
        }
        for concept_id, concept in known.items()
        if concept_id in found | related
    ]
