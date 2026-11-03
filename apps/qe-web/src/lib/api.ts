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
