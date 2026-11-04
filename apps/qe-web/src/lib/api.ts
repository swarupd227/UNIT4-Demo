export type AreaCard = {
  area: string;
  module: string;
  rules: number;
  critical_rules: number;
  manual_cases: number;
  automated_tests: number;
  defects: number;
  code_files: number;
  code_lines: number;
  help_pages: number;
  gate_percent: number;
};

export type AgentRun = {
  status: "ok" | "not_run" | "stale";
  source?: string;
  model?: string | null;
  duration_ms?: number | null;
};

export type RuleCoverage = {
  rule: string;
  title: string;
  critical: boolean;
  tests: { title: string; file: string; flaky: { failed: number; runs: number } | null }[];
  faults: { id: string; description: string; caught: boolean }[];
  caught: number;
  score: number | null;
  covered: boolean;
  manual_cases: string[];
  defects: string[];
};

export type Coverage = {
  rules: RuleCoverage[];
  summary: { critical_rules: number; critical_covered: number; percent: number; not_covered: string[] };
  gate_percent: number;
  case_mapping: AgentRun;
  defect_mapping: AgentRun;
};

export type DefectBrief = { id: string; title: string; severity: number; test: "automated" | "manual" | "none" };

export type RiskFacts = {
  rule: string;
  title: string;
  critical: boolean;
  covered: boolean;
  score: number | null;
  defects: DefectBrief[];
  untested: number;
  no_test: number;
  files: [string, number][];
};

export type RiskCardContent = {
  headline: string;
  what_keeps_breaking: { point: string; defects: string[] }[];
  why_it_escapes: string;
  proposed_tests: { title: string; scenario: string; defects: string[] }[];
  ontology_concepts: string[];
};

export type HiddenRuleContent = {
  title: string;
  statement: string;
  related_rule: string | null;
  citations: { file: string; find: string; line: number; text: string }[];
  why_hidden: string;
  search_phrases: string[];
  document_search: { phrase: string; found_in: string[] }[];
  documented: boolean;
  proposed_test: string;
  ontology_concepts: string[];
};

export type DeadCodeContent = {
  kind: "class" | "method";
  name: string;
  file: string;
  line: number;
  reason: string;
  called_from: string[];
};

type EntryBase = {
  entry_id: string;
  rule: string | null;
  title: string;
  provenance: "ai_analysis" | "verified_by_code";
  source: string;
  model: string | null;
  status: "proposed" | "approved" | "rejected";
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string | null;
};

export type ContextEntry =
  | (EntryBase & { kind: "risk_card"; content: { card: RiskCardContent; facts: RiskFacts } })
  | (EntryBase & { kind: "hidden_rule"; content: HiddenRuleContent })
  | (EntryBase & { kind: "dead_code"; content: DeadCodeContent });

export type Context = {
  risk_ranking: RiskFacts[];
  clusters: { file: string; defects: number; no_test: number; manual_only: number; automated: number }[];
  entries: ContextEntry[];
  agents: {
    defect_clusterer: AgentRun;
    hidden_rule_finder: AgentRun;
    risk_analyst: Record<string, AgentRun>;
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `The server could not load ${path} (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  area: () => request<AreaCard>("/api/area"),
  coverage: () => request<Coverage>("/api/coverage"),
  context: () => request<Context>("/api/context"),
  review: (entryId: string, personKey: string, decision: "approved" | "rejected", note: string) =>
    request<{ status: string }>(`/api/context/${encodeURIComponent(entryId)}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ person_key: personKey, decision, note }),
    }),
  exportContext: () => request<unknown>("/api/context/export"),
};

export type Basis = { document: string; find: string };

export type IntakeEntry = {
  case: string;
  title: string;
  rule: string | null;
  outcome: "merged" | "already_automated" | "to_person" | "needs_expected_result" | "ready" | "review";
  into?: string;
  by?: string;
  duplicates: string[];
  review?: {
    steps: { step: number; verdict: "agrees" | "disagrees" | "not_checkable"; expected: string; basis: Basis[] }[];
    summary: string;
  };
  agent?: { source: string; model: string | null };
};

export type CheckResult = { passed: boolean; [key: string]: unknown };

export type Attempt = {
  id: string;
  attempt: number;
  title: string;
  ready_for_lab: boolean;
  generated: {
    path: string;
    title: string;
    data: { group: string; key: string; value: string };
    data_choice: string;
    scenario: string[];
    checks: { check: string; value: string }[];
    code: string;
  };
  issues: string[];
  validation: { check: string; asserted: string; expected: string; basis: Basis[]; agrees: boolean }[];
  agents: { generator: { source: string; model: string | null }; validator: { source: string; model: string | null } };
  checks: {
    conventions: CheckResult & { issues: string[] };
    expected_results: CheckResult;
    faults: CheckResult & { ran: boolean; rule_faults?: string[]; caught?: string[]; required?: string[] };
    stability: CheckResult & { ran: boolean; passed_runs?: number; runs?: number; first_failure?: string | null };
  };
  accepted: boolean;
  problems: string[];
};

export type GeneratedTest = {
  id: string;
  kind: string;
  ref: string;
  rule: string;
  title: string;
  accepted: boolean;
  attempts: Attempt[];
};

export type CoverageAfter = {
  rules: {
    rule: string;
    title: string;
    critical: boolean;
    tests: number;
    caught: number;
    faults: number;
    score_before: number | null;
    score: number | null;
    covered_before: boolean;
    covered: boolean;
  }[];
  critical_covered: number;
  critical_rules: number;
  percent: number;
  newly_covered: string[];
};

export type Tests = {
  batch: { chosen_by: string; manual_cases: number[]; defects: string[]; context: string[] };
  intake: IntakeEntry[];
  tests: GeneratedTest[];
  coverage_before: { critical_covered: number; critical_rules: number; percent: number };
  coverage_after: CoverageAfter;
};

export const testsApi = {
  tests: () => request<Tests>("/api/tests"),
};

export type Review = { status: "approved" | "rejected"; reviewed_by: string; reviewed_at: string; note: string | null };
export type FileChange = { path: string; content: string };

export type FlakyEntry = {
  test: {
    title: string;
    rule: string;
    file: string;
    failed: number;
    runs: number;
    messages: { message: string; count: number }[];
    running_alongside: { test: string; when_failed: number; failed_runs: number; when_passed: number; passed_runs: number }[];
    shared_data: { test: string; file: string; customers: string[]; changes: string[] }[];
  };
  diagnosis: { cause: string; explanation: string; evidence: string[]; fix_summary: string; files: FileChange[] };
  agent: { source: string; model: string | null; duration_ms: number | null };
  after: { failed: number; runs: number } | null;
  change_id: string;
  review: Review | null;
};

export type Flaky = {
  runs_before: number;
  runs_after: number;
  suite_after: number;
  failures_after: number;
  tests: FlakyEntry[];
};

export type Maintenance = {
  release?: { id: string; description: string; file: string; find: string; replace: string };
  failures?: { title: string; error: string | null }[];
  repair: { cause: string; fix_summary: string; files: FileChange[] } | null;
  agent?: { source: string; model: string | null; duration_ms: number | null };
  after?: { tests: number; failed: number };
  timing?: { detect_seconds: number; repair_seconds: number; verify_seconds: number; machine_seconds: number };
  change_id?: string;
  review?: Review | null;
};

export const maintenanceApi = {
  flaky: () => request<Flaky>("/api/flaky"),
  maintenance: () => request<Maintenance>("/api/maintenance"),
  review: (changeId: string, personKey: string, decision: "approved" | "rejected", note = "") =>
    request<{ status: string }>(`/api/changes/${encodeURIComponent(changeId)}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ person_key: personKey, decision, note }),
    }),
};

export type RunRecord = { status: string; ms: number; started: string | null };

export type PrItem = {
  item_id: string;
  kind: "test" | "flaky_fix";
  title: string;
  rule: string;
  source: { kind: string; ref: string };
  files: string[];
  attempts?: number;
  validation?: Attempt["validation"];
  faults?: Attempt["checks"]["faults"];
  cause?: string;
  fix_summary?: string;
  before?: { failed: number; runs: number };
  runs: RunRecord[];
  decision: { decision: "approved" | "rejected"; reviewed_by: string; reviewed_at: string; note: string | null } | null;
};

export type PullRequest = {
  id: string;
  branch: string;
  title: string;
  author: string;
  files: { path: string; status: "added" | "modified"; content: string }[];
  release_controls_unchanged: boolean;
  pipeline_file: string;
  items: PrItem[];
  merged: {
    merged_by: string;
    merged_at: string;
    branch: string;
    branch_commit: string;
    merge_commit: string;
    items: string[];
  } | null;
};

export type Gaps = {
  gate_percent: number;
  covered: number;
  critical_rules: number;
  percent: number;
  below_gate: {
    rule: string;
    title: string;
    critical: boolean;
    score: number | null;
    tests: number;
    missed_faults: { id: string; description: string }[];
    defects: number;
    untested_defects: number;
    manual_cases: string[];
  }[];
  waiting_on_people: { case: string; title: string; outcome: string; review: string | null }[];
  dead_code: DeadCodeContent[];
};

export type Scorecard = {
  manual_regression: {
    total_minutes: number;
    cases: number;
    automated_cases: string[];
    automated_minutes: number;
    suite_run_seconds: number | null;
    suite_tests: number;
    assumption: string;
  };
  coverage: {
    before: { critical_covered: number; critical_rules: number; percent: number };
    after: { critical_covered: number; critical_rules: number; percent: number };
    gate_percent: number;
    newly_covered: string[];
  };
  defects_detected: { faults: number; caught_before: number; caught_after: number; t1_t2_caught: boolean };
  escaped_defects: { measured: boolean; note: string };
  reliability: {
    before: { test: string; failed: number; runs: number }[];
    after_runs: number;
    after_tests: number;
    after_failures: number;
  };
  maintenance: { broken_tests: number; machine_seconds: number | null; approved: Review | null };
  engineer: { accepted: number; rejected: number; items: number; merged: PullRequest["merged"] };
  planted: { id: string; what: string; handled: boolean; how: string }[];
};

const post = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const evidenceApi = {
  review: () => request<PullRequest>("/api/review"),
  decide: (itemId: string, personKey: string, decision: "approved" | "rejected", note = "") =>
    request<{ decision: string }>(
      `/api/review/items/${encodeURIComponent(itemId)}`,
      post({ person_key: personKey, decision, note }),
    ),
  merge: (personKey: string) => request<{ merge_commit: string }>("/api/review/merge", post({ person_key: personKey })),
  gaps: () => request<Gaps>("/api/gaps"),
  scorecard: () => request<Scorecard>("/api/scorecard"),
  pack: () => request<unknown>("/api/pack"),
};
