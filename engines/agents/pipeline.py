"""Runs the agents through the gateway and stores what they produce for people to review."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Connection, text

from data.generator.common import FIXTURES
from engines.agents.gateway import AgentRequest, AgentResult, ReplayGateway
from engines.agents.schemas import (
    CodeExplanation,
    ExtensionSpec,
    ReportRebuild,
    RuleCard,
    TestCases,
    WorkflowPack,
)

CACHE_DIR: Path = FIXTURES / "agent_cache"
PROMPT_VERSION = "1"
WORKFLOW_SUBJECT = "WF-001"


@dataclass(frozen=True)
class AgentSpec:
    agent: str
    kind: str
    schema: type[BaseModel]
    subjects: tuple[str, ...]
    uses_policy: bool = False


AGENTS = [
    AgentSpec("code_explainer", "code_explanation", CodeExplanation, ("CC-014", "CC-037", "CC-041")),
    AgentSpec("rule_extractor", "rule_card", RuleCard, ("CC-014",), uses_policy=True),
    AgentSpec("extension_spec", "extension_spec", ExtensionSpec, ("CC-014",), uses_policy=True),
    AgentSpec("test_generator", "test_cases", TestCases, ("CC-014",), uses_policy=True),
    AgentSpec("report_rebuilder", "report_rebuild", ReportRebuild, ("RP-077", "RP-084")),
    AgentSpec("workflow_pack", "workflow_pack", WorkflowPack, (WORKFLOW_SUBJECT,)),
]


def _payload(db: Connection, spec: AgentSpec, subject: str) -> dict[str, Any]:
    if spec.agent == "workflow_pack":
        rows = db.execute(
            text("""
                SELECT item_id, name, usage_12m, definition FROM studio.estate_item
                WHERE item_type = 'WF' ORDER BY item_id
            """)
        ).mappings()
        return {"workflows": [dict(row) for row in rows]}
    row = (
        db.execute(
            text("SELECT name, definition, source_text FROM studio.estate_item WHERE item_id = :item_id"),
            {"item_id": subject},
        )
        .mappings()
        .one()
    )
    payload = {"item_id": subject, **row}
    if spec.uses_policy:
        payload["billing_policy"] = db.execute(
            text("SELECT content FROM studio.reference_document WHERE document_key = 'billing_policy'")
        ).scalar_one()
    return payload


def build_requests(db: Connection) -> list[tuple[AgentSpec, AgentRequest]]:
    return [
        (spec, AgentRequest(spec.agent, subject, PROMPT_VERSION, _payload(db, spec, subject)))
        for spec in AGENTS
        for subject in spec.subjects
    ]


def _resolve_citations(value: Any, lines: list[str], where: str) -> Any:
    """A citation must point at real text, so a model cannot invent a source line."""
    if isinstance(value, list):
        return [_resolve_citations(entry, lines, where) for entry in value]
    if isinstance(value, dict):
        resolved = {key: _resolve_citations(entry, lines, where) for key, entry in value.items()}
        if "find" in resolved:
            matches = [number for number, line in enumerate(lines, start=1) if resolved["find"] in line]
            if not matches:
                raise ValueError(f"{where}: citation not found in source: {resolved['find']}")
            resolved["line"] = matches[0]
        return resolved
    return value


def store_artefacts(db: Connection, gateway: ReplayGateway | None = None) -> None:
    gateway = gateway or ReplayGateway(CACHE_DIR)
    for spec, request in build_requests(db):
        result: AgentResult = gateway.run(request)
        content = spec.schema.model_validate(result.output).model_dump()
        source_text = request.payload.get("source_text") or ""
        content = _resolve_citations(content, source_text.splitlines(), f"{spec.agent} on {request.subject}")
        db.execute(
            text("""
                INSERT INTO studio.artefact
                    (item_id, kind, content, source, model, duration_ms, prompt_version, input_hash)
                VALUES (:item_id, :kind, CAST(:content AS jsonb), :source, :model, :duration_ms,
                        :prompt_version, :input_hash)
            """),
            {
                "item_id": request.subject,
                "kind": spec.kind,
                "content": json.dumps(content),
                "source": result.source,
                "model": result.model,
                "duration_ms": result.duration_ms,
                "prompt_version": request.prompt_version,
                "input_hash": request.input_hash,
            },
        )
