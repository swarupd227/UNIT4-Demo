"""What each agent returns. Plain code checks every result against the material it was given."""

from typing import Literal

from pydantic import BaseModel, Field


class CaseRule(BaseModel):
    case_id: str
    rule: str | None = Field(description="The rule ID, such as BR-04, or null if no rule fits")
    reason: str = Field(description="One short sentence")


class CaseMapping(BaseModel):
    cases: list[CaseRule]


class DefectRule(BaseModel):
    defect_id: str
    rule: str | None = Field(description="The rule ID the defect broke, or null if it broke none")


class DefectMapping(BaseModel):
    defects: list[DefectRule]


class Citation(BaseModel):
    file: str = Field(description="The code file path exactly as given")
    find: str = Field(description="An exact substring of one line of that file")


class HiddenRule(BaseModel):
    title: str = Field(description="At most eight words")
    statement: str = Field(description="The rule as the code enforces it, in one or two sentences")
    related_rule: str | None = Field(description="The register rule it belongs to, or null")
    citations: list[Citation]
    why_hidden: str = Field(description="What the register, help pages, cases and tests say instead")
    search_phrases: list[str] = Field(
        description="Two to four phrases of two or more words that would appear wherever it is documented"
    )
    proposed_test: str = Field(description="One sentence")
    ontology_concepts: list[str]


class HiddenRules(BaseModel):
    rules: list[HiddenRule]


class RiskPoint(BaseModel):
    point: str = Field(description="One sentence")
    defects: list[str]


class ProposedTest(BaseModel):
    title: str
    scenario: str = Field(description="Data and expected result, in one or two sentences")
    defects: list[str]


class RiskCard(BaseModel):
    headline: str = Field(description="At most twelve words")
    what_keeps_breaking: list[RiskPoint]
    why_it_escapes: str = Field(description="One or two sentences")
    proposed_tests: list[ProposedTest]
    ontology_concepts: list[str]


class Basis(BaseModel):
    document: str = Field(description="The document's name exactly as given in `documents`")
    find: str = Field(description="An exact substring of one line of that document")


class StepReview(BaseModel):
    step: int
    verdict: Literal["agrees", "disagrees", "not_checkable"]
    expected: str = Field(
        description="What the documents say the application shows at this step, or what the case must state"
    )
    basis: list[Basis]


class CaseReview(BaseModel):
    steps: list[StepReview]
    summary: str = Field(description="One sentence")


class DataKey(BaseModel):
    group: Literal["projects", "invoices", "customers"]
    key: str = Field(description="A camelCase name for the testData entry")
    value: str = Field(
        description="The value exactly as the application lists it, such as 'P-1020 Norrsken grid analytics'"
    )


class AssertedValue(BaseModel):
    check: str = Field(description="A short name for what is checked, such as 'Line 1 amount'")
    value: str = Field(description="The text the test expects, exactly as it appears in the code")


class GeneratedTest(BaseModel):
    path: str = Field(description="specs/<area>/<name>.spec.ts")
    title: str
    data: DataKey
    data_choice: str = Field(description="One or two sentences: why this data shows the behaviour")
    scenario: list[str] = Field(description="The inputs and actions, in order, with no expected results")
    checks: list[AssertedValue]
    code: str


class ExpectedValue(BaseModel):
    check: str
    expected: str = Field(
        description="The text the page should show, or 'Not settled' followed by what is missing"
    )
    basis: list[Basis]


class TestValidation(BaseModel):
    checks: list[ExpectedValue]


class FileChange(BaseModel):
    path: str = Field(description="Path under tests/e2e, such as specs/pricing/discount.spec.ts")
    content: str = Field(description="The whole new content of the file")


class FlakyDiagnosis(BaseModel):
    cause: Literal["fixed_wait", "shared_data", "timing", "environment", "other"]
    explanation: str = Field(description="Two or three sentences")
    evidence: list[str] = Field(description="Facts from the material that show the cause, one per entry")
    fix_summary: str = Field(description="One sentence")
    files: list[FileChange]


class SelectorRepair(BaseModel):
    cause: str = Field(description="One sentence")
    fix_summary: str = Field(description="One sentence")
    files: list[FileChange]
