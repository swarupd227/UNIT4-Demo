"""Estate analysis that needs no language model: plain code over report and workflow definitions.

Its results fill the same `signal` fields a model would, so the decision rules do not care where
they came from. A pilot would add semantic matching for names this cannot normalise.
"""

import re

from engines.decision.rules import LOW_USE_MAX_EVENTS, ItemFacts

NOISE_WORDS = {
    "by", "client", "office", "partner", "uk", "only", "monthly", "v1", "v2", "old", "copy", "of",
    "custom", "view", "layout", "test", "2016",
}  # fmt: skip
MIN_COLUMN_OVERLAP = 0.5
EXACT_MATCH_CONFIDENCE = 92


def name_key(name: str) -> tuple[str, ...]:
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    return tuple(token for token in tokens if token not in NOISE_WORDS)


def column_overlap(first: list[str], second: list[str]) -> float:
    a, b = set(first), set(second)
    return len(a & b) / len(a | b) if a | b else 0.0


def analyse_reports(facts: list[ItemFacts], catalogue: list[str]) -> None:
    standard = {name_key(name): name for name in catalogue}
    groups: dict[tuple[str, ...], list[ItemFacts]] = {}
    for item in facts:
        if item.item_type != "RP" or item.usage_12m <= LOW_USE_MAX_EVENTS:
            continue
        key = name_key(item.name)
        if key in standard:
            item.signal["standard_feature"] = f"{standard[key]} (ERPx standard report)"
            item.signal["standard_confidence"] = EXACT_MATCH_CONFIDENCE
        else:
            groups.setdefault(key, []).append(item)

    for members in groups.values():
        # The most used report leads its group, which is the one people would miss.
        lead = max(members, key=lambda item: (item.usage_12m, item.item_id))
        similar = [
            item
            for item in members
            if item is lead
            or column_overlap(item.definition["columns"], lead.definition["columns"]) >= MIN_COLUMN_OVERLAP
        ]
        if len(similar) > 1:
            for item in similar:
                item.signal["merge_target"] = lead.item_id


def analyse_workflows(facts: list[ItemFacts]) -> None:
    """Variants that enforce the same rule are one workflow. Dormant-only use never leads a group."""
    groups: dict[str, list[ItemFacts]] = {}
    for item in facts:
        if item.item_type == "WF" and not set(item.usage_entities) <= set(item.dormant_entities):
            groups.setdefault(item.definition["enforced_rule"], []).append(item)
    for members in groups.values():
        lead = max(members, key=lambda item: (item.usage_12m, item.item_id))
        lead.signal["standard_feature"] = "ERPx standard approval workflow"
        lead.signal["standard_confidence"] = EXACT_MATCH_CONFIDENCE
        for item in members:
            if item is not lead:
                item.signal["merge_target"] = lead.item_id


def find_stale_partner_lists(facts: list[ItemFacts], active_partners: set[str]) -> None:
    for item in facts:
        listed = item.definition.get("hard_coded_partners")
        if listed:
            item.signal["stale_logic"] = {
                "omitted": sorted(active_partners - set(listed)),
                "departed": sorted(set(listed) - active_partners),
            }
