// Every role and screen name shown in the app lives here, so the wording can change in one place.

export const ROLES = {
  qe_lead: { label: "Quality engineering lead", person: "Maria Lindgren", org: "Unit4" },
  engineer: { label: "Engineer", person: "Ravi Menon", org: "Unit4" },
  full_circuit_owner: { label: "Full Circuit owner", person: "Hanna Koskela", org: "Unit4" },
} as const;

export type Role = keyof typeof ROLES;
export const ROLE_KEYS = Object.keys(ROLES) as Role[];

export const STAGES = [
  { key: "area", label: "Area" },
  { key: "coverage", label: "Coverage" },
  { key: "context", label: "Context" },
  { key: "tests", label: "Generated tests" },
  { key: "proof", label: "Proof" },
  { key: "flaky", label: "Flaky tests" },
  { key: "review", label: "Pull request" },
  { key: "gaps", label: "Gaps" },
  { key: "scorecard", label: "Scorecard" },
] as const;

export type StageKey = (typeof STAGES)[number]["key"];
