"""The decision tree. Plain code: the same facts always give the same proposal.

The agents' part is limited to the inputs in `signal`. Whether an item may be retired is decided
here, so a model can never retire a year-end report.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

ENGINE_VERSION = "decision-rules-1"
REPORTING_DATE = date(2026, 10, 31)
LOW_USE_MAX_EVENTS = 2
PRODUCT_GAP_MIN_PRECEDENTS = 5
PROTECTED_WORDS = re.compile(r"year-end|\baudit|statutory|\btax\b", re.IGNORECASE)

RETIRE = "retire"
STANDARD = "replace_standard"
EXTENSION = "rebuild_extension"
KEEP = "keep_repoint"
GAP = "product_gap"


@dataclass
class ItemFacts:
    item_id: str
    item_type: str
    name: str
    owner: str | None
    documented: bool
    usage_12m: int
    last_used: date | None
    definition: dict[str, Any]
    source_text: str | None
    signal: dict[str, Any]
    usage_entities: list[str] = field(default_factory=list)
    dormant_entities: dict[str, str] = field(default_factory=dict)
    dependencies: list[dict[str, str]] = field(default_factory=list)
    precedents: int = 0
    j2x_summary: str | None = None


@dataclass
class Proposal:
    outcome: str | None
    action: str | None
    state: str
    reason: str
    confidence: int | None
    rule: str
    flags: list[str]
    evidence: list[dict[str, Any]]
    candidate_outcome: str | None = None


def _months_since(day: date) -> int:
    return (REPORTING_DATE.year - day.year) * 12 + REPORTING_DATE.month - day.month


def _usage_evidence(facts: ItemFacts) -> dict[str, Any]:
    if facts.last_used is None:
        detail = "No recorded run"
    else:
        detail = f"Last used {facts.last_used.strftime('%d %b %Y').lstrip('0')}"
    runs = f"{facts.usage_12m:,} use{'' if facts.usage_12m == 1 else 's'} in 12 months"
    return {"kind": "usage", "label": runs, "detail": detail}


def _protected_match(facts: ItemFacts) -> str | None:
    text = " ".join([facts.name, json.dumps(facts.definition), facts.source_text or ""])
    match = PROTECTED_WORDS.search(text)
    return match.group(0).lower() if match else None


def _resolve_evidence(facts: ItemFacts) -> list[dict[str, Any]]:
    """Turns an agent's `find` text into a line number, so a citation can only point at real code."""
    lines = (facts.source_text or "").splitlines()
    resolved = []
    for entry in facts.signal.get("evidence") or []:
        item = dict(entry)
        if needle := item.pop("find", None):
            matches = [number for number, line in enumerate(lines, start=1) if needle in line]
            if not matches:
                raise ValueError(f"{facts.item_id}: evidence not found in source: {needle}")
            item["line"] = matches[0]
        resolved.append(item)
    return resolved


def propose(facts: ItemFacts) -> Proposal:
    signal = facts.signal
    evidence = _resolve_evidence(facts)
    flags: list[str] = []
    if facts.item_type != "CF":
        evidence.insert(0, _usage_evidence(facts))
    if facts.owner:
        evidence.append({"kind": "owner", "label": f"Owner: {facts.owner}"})
    else:
        evidence.append({"kind": "owner", "label": "No owner on record"})
        flags.append("no_owner")
    if facts.item_type == "CC" and not facts.documented:
        evidence.append({"kind": "owner", "label": "No documentation"})
        flags.append("undocumented")
    if facts.j2x_summary:
        evidence.append({"kind": "j2x", "label": "Explained by J2X", "detail": facts.j2x_summary})
    for dependency in facts.dependencies:
        evidence.append(
            {
                "kind": "dependency",
                "label": f"{dependency['depends_on']} also writes {dependency['table_name']}",
                "detail": f"{dependency['name']} feeds a table this item reads. "
                "Resolve this before the item is retired or rebuilt.",
                "item": dependency["depends_on"],
            }
        )
        flags.append("hidden_dependency")
    if signal.get("conflict"):
        flags.append("conflict")
    if stale := signal.get("stale_logic"):
        evidence.append(
            {
                "kind": "stale",
                "label": f"{len(stale['omitted'])} current partners missing from the list",
                "detail": f"Missing: {', '.join(stale['omitted'])}. No longer partners: "
                f"{', '.join(stale['departed'])}. Rebuild from the resource reference data.",
            }
        )
        flags.append("stale_logic")

    if not signal["purpose_known"]:
        return Proposal(
            None,
            None,
            "held",
            "Purpose cannot be established from the code, and nobody owns it. "
            "Needs a customer interview before any decision.",
            None,
            "purpose_unknown",
            [*flags, "needs_interview"],
            evidence,
        )

    usage_applies = facts.item_type in ("CC", "RP", "WF")
    entities = set(facts.usage_entities)
    if usage_applies and entities and entities <= set(facts.dormant_entities):
        entity = sorted(entities)[0]
        evidence.append(
            {
                "kind": "entity",
                "label": f"Used only by dormant entity {entity}",
                "detail": f"{entity} has been dormant since {facts.dormant_entities[entity]}.",
            }
        )
        return Proposal(
            RETIRE,
            None,
            "proposed",
            "Used only by a dormant legal entity.",
            90,
            "dormant_entity_only",
            [*flags, "dormant_use"],
            evidence,
        )

    if usage_applies and facts.usage_12m <= LOW_USE_MAX_EVENTS:
        if word := _protected_match(facts):
            evidence.append(
                {
                    "kind": "keyword",
                    "label": f'Protected word "{word}" found',
                    "detail": "Items with a legal, audit, tax or year-end purpose are never retired "
                    "automatically.",
                }
            )
            return Proposal(
                None,
                None,
                "held",
                f'Looks unused, but "{word}" suggests a legal or audit purpose. '
                "Sent to the customer rather than retired.",
                None,
                "protected_word",
                [*flags, "refused_retire"],
                evidence,
                candidate_outcome=RETIRE,
            )
        if facts.usage_12m == 0:
            stale = facts.last_used is not None and _months_since(facts.last_used) >= 36
            return Proposal(
                RETIRE,
                None,
                "proposed",
                "Not used in the last 12 months, with no legal, audit or year-end purpose found.",
                96 if stale else 91,
                "unused",
                flags,
                evidence,
            )
        return Proposal(
            RETIRE,
            None,
            "proposed",
            "Used at most twice in 12 months, with no legal, audit or year-end purpose found.",
            76,
            "low_use",
            [*flags, "low_use"],
            evidence,
        )

    if facts.item_type in ("RP", "WF") and signal.get("merge_target"):
        target = signal["merge_target"]
        if facts.item_type == "WF":
            evidence.append({"kind": "standard", "label": f"Enforces the same rule as {target}"})
            return Proposal(
                STANDARD,
                f"merge_into:{target}",
                "proposed",
                f"Enforces the same approval rule as {target}.",
                88,
                "workflow_merge",
                flags,
                evidence,
            )
        survivor = target == facts.item_id
        evidence.append({"kind": "standard", "label": f"Near-duplicate group led by {target}"})
        return Proposal(
            KEEP,
            "merge_survivor" if survivor else "merge_into",
            "proposed",
            "Kept as the report for its near-duplicate group."
            if survivor
            else f"Near-duplicate of {target}, so it merges into that report.",
            88,
            "report_merge",
            flags,
            evidence,
        )

    if signal.get("standard_feature"):
        evidence.append(
            {
                "kind": "standard",
                "label": signal["standard_feature"],
                "detail": "Illustrative mapping, to be confirmed against Unit4's standard content.",
            }
        )
        return Proposal(
            STANDARD,
            None,
            "proposed",
            f"{signal['standard_feature']} gives the same business result.",
            signal["standard_confidence"],
            "standard_match",
            flags,
            evidence,
        )

    writes = facts.definition.get("tables_written") or []
    if facts.item_type == "CC" and writes:
        if facts.precedents >= PRODUCT_GAP_MIN_PRECEDENTS:
            evidence.append(
                {
                    "kind": "precedent",
                    "label": f"{facts.precedents} similar items in mapping memory",
                    "detail": "Synthetic precedents from other fictional customers.",
                }
            )
            return Proposal(
                GAP,
                None,
                "proposed",
                f"The same rebuild appears across {facts.precedents} other customers.",
                82,
                "product_gap",
                flags,
                evidence,
            )
        reason = signal.get("proposal_note") or "Needed, not covered by standard, and writes data."
        return Proposal(
            EXTENSION,
            signal.get("action_note"),
            "proposed",
            reason,
            86,
            "writes_data",
            flags,
            evidence,
        )

    if facts.item_type == "RP":
        return Proposal(
            KEEP,
            "rebuild",
            "proposed",
            "Needed read-only report with no standard equivalent.",
            80,
            "read_only_report",
            flags,
            evidence,
        )
    return Proposal(
        KEEP,
        None,
        "proposed",
        "Needed read-only query with no standard equivalent.",
        80,
        "read_only_query",
        flags,
        evidence,
    )
