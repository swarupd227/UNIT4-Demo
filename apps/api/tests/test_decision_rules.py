from datetime import date

import pytest

from engines.decision.policy import allowed_actions, required_roles, status_for
from engines.decision.rules import EXTENSION, GAP, RETIRE, ItemFacts, propose


def facts(**overrides) -> ItemFacts:
    values = {
        "item_id": "RP-001",
        "item_type": "RP",
        "name": "Debtors by region",
        "owner": "Finance systems",
        "documented": True,
        "usage_12m": 12,
        "last_used": date(2026, 10, 1),
        "definition": {},
        "source_text": None,
        "signal": {"purpose_known": True},
    }
    return ItemFacts(**(values | overrides))


def test_unused_item_is_a_retire_proposal() -> None:
    assert propose(facts(usage_12m=0, last_used=date(2021, 1, 1))).outcome == RETIRE


@pytest.mark.parametrize("name", ["Year-end audit pack", "Statutory accounts", "Old tax code listing"])
def test_protected_words_are_never_retired(name: str) -> None:
    proposal = propose(facts(name=name, usage_12m=1))
    assert (proposal.outcome, proposal.state) == (None, "held")
    assert proposal.candidate_outcome == RETIRE


def test_protected_word_in_definition_counts() -> None:
    assert propose(facts(usage_12m=0, definition={"schedule": "After the year-end close"})).state == "held"


def test_well_used_item_with_protected_word_is_not_held() -> None:
    assert propose(facts(name="VAT and tax summary", usage_12m=12)).state == "proposed"


def test_dormant_entity_only_use_proposes_retirement() -> None:
    proposal = propose(
        facts(
            item_type="WF",
            usage_12m=40,
            usage_entities=["NL02"],
            dormant_entities={"NL02": "June 2023"},
        )
    )
    assert proposal.outcome == RETIRE
    assert "dormant_use" in proposal.flags


def test_unknown_purpose_gets_no_outcome() -> None:
    proposal = propose(facts(item_type="CC", signal={"purpose_known": False}))
    assert (proposal.outcome, proposal.state) == (None, "held")


def test_writer_becomes_extension_or_product_gap() -> None:
    writer = {"item_type": "CC", "definition": {"tables_written": ["billing_line"]}}
    assert propose(facts(**writer)).outcome == EXTENSION
    assert propose(facts(**writer, precedents=6)).outcome == GAP


def test_evidence_citation_must_exist_in_source() -> None:
    signal = {"purpose_known": True, "evidence": [{"kind": "code", "label": "x", "find": "absent"}]}
    with pytest.raises(ValueError):
        propose(facts(source_text="line one", signal=signal))


def test_retire_needs_the_customer() -> None:
    assert required_roles("RP", RETIRE) == ["consultant", "customer"]


def test_status_requires_every_role() -> None:
    required = ["consultant", "customer"]
    assert status_for(required, ["consultant"], False, False) == "awaiting"
    assert status_for(required, required, False, False) == "agreed"
    assert status_for(required, required, True, False) == "question"


def test_customer_cannot_accept_before_the_consultant() -> None:
    required = ["consultant", "customer"]
    assert not allowed_actions("customer", RETIRE, required, [], "review").accept
    assert allowed_actions("customer", RETIRE, required, ["consultant"], "awaiting").accept
