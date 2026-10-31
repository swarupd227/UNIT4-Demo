"""Who may do what. This is the rule that nothing moves without a person."""

from dataclasses import dataclass

from engines.decision.rules import EXTENSION, GAP, RETIRE

CONSULTANT = "consultant"
CUSTOMER = "customer"
UNIT4_TECHNICAL = "unit4_technical"
UNIT4_PRODUCT = "unit4_product"

# Fictional demo personas. Agents have no role, so they cannot accept anything.
PERSONAS = {
    CONSULTANT: "Robin Hale",
    CUSTOMER: "Jordan Ashby",
    UNIT4_TECHNICAL: "Casey Lund",
    UNIT4_PRODUCT: "Taylor Voss",
}

ROLE_NAMES = {
    CONSULTANT: "the consultant",
    CUSTOMER: "the customer",
    UNIT4_TECHNICAL: "the Unit4 technical lead",
    UNIT4_PRODUCT: "the Unit4 product team",
}

OUTCOMES = {"retire", "replace_standard", "rebuild_extension", "keep_repoint", "product_gap"}


def required_roles(item_type: str, outcome: str | None) -> list[str]:
    if outcome is None:
        return []
    if outcome == RETIRE or item_type == "WF":
        return [CONSULTANT, CUSTOMER]
    if outcome == EXTENSION:
        return [CONSULTANT, UNIT4_TECHNICAL]
    if outcome == GAP:
        return [CONSULTANT, UNIT4_PRODUCT]
    return [CONSULTANT]


def status_for(required: list[str], approved: list[str], question_open: bool, conflict_open: bool) -> str:
    if question_open:
        return "question"
    if conflict_open:
        return "conflict"
    if required and set(required) <= set(approved):
        return "agreed"
    return "awaiting" if approved else "review"


@dataclass(frozen=True)
class Allowed:
    accept: bool
    edit: bool
    ask: bool
    answer: bool
    reason: str | None


def allowed_actions(
    role: str, outcome: str | None, required: list[str], approved: list[str], status: str
) -> Allowed:
    question_open = status == "question"
    answer = role == CUSTOMER and question_open
    if status == "agreed":
        return Allowed(False, False, False, False, "This decision is agreed.")

    consultant = role == CONSULTANT
    edit = consultant
    ask = consultant and not question_open

    if question_open:
        reason = None if answer else "Waiting for the customer's answer."
        return Allowed(False, edit, False, answer, reason)
    if status == "conflict":
        return Allowed(False, edit, ask, False, "Resolve the conflict first.")
    if outcome is None:
        return Allowed(
            False, edit, ask, False, "Choose an outcome first." if consultant else "No outcome yet."
        )

    missing = [r for r in required if r not in approved]
    next_role = missing[0]
    if role == next_role:
        return Allowed(True, edit, ask, False, None)
    return Allowed(False, edit, ask, False, f"Waiting for {ROLE_NAMES[next_role]}.")
