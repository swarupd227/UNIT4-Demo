"""The shape every agent result must take, whether a model or a person produced it."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Citation(Strict):
    text: str
    find: str = Field(
        description="Exact text in the source. Resolved to a line number, or the result is rejected."
    )


class CodeExplanation(Strict):
    plain_english: str
    purpose_known: bool
    steps: list[Citation]
    hidden_rules: list[Citation]
    cloud_blockers: list[Citation]


class RuleCard(Strict):
    rule_id: str
    statement: str
    threshold_pct: int
    applies_to: str
    approver: str
    stored_in: str
    sources: list[Citation]
    policy_reference: str
    policy_threshold_pct: int


class ApiCall(Strict):
    purpose: str
    call: str


class ExtensionSpec(Strict):
    title: str
    summary: str
    standard_coverage: list[str]
    extension_name: str
    trigger: str
    behaviour: list[str]
    data: list[str]
    api_calls: list[ApiCall]
    dependencies: list[str]
    open_points: list[str]
    caveat: str


class RuleTestCase(Strict):
    id: str
    description: str
    adjust_type: Literal["write_down", "write_up"]
    billable_minor: int
    adjust_minor: int
    prior_approval: bool
    expected_at_10: Literal["apply", "hold"]
    expected_at_15: Literal["apply", "hold"]


class TestCases(Strict):
    rule_id: str
    cases: list[RuleTestCase] = Field(min_length=1)


class ReportRebuild(Strict):
    report_id: str
    summary: str
    rebuilt_as: str
    changes: list[str]
    flagged: list[str]
    parity_plan: list[str]


class ProposedWorkflow(Strict):
    keeps: str
    name: str
    rule: str
    absorbs: list[str]
    erpx_configuration: list[str]


class WorkflowTest(Strict):
    id: str
    description: str
    expected: str


class WorkflowPack(Strict):
    headline: str
    from_count: int
    to_count: int
    proposed: list[ProposedWorkflow]
    retire: list[str]
    control_impact: list[str]
    tests: list[WorkflowTest]
    decision_needed: str
