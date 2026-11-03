"""What each agent returns. Plain code checks every result against the material it was given."""

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
