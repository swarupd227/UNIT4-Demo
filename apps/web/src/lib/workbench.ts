import { api, request, post, type CaseSummary } from "./api";
import type { Role } from "./terms";

export type EstateData = {
  types: { item_type: string; count: number; j2x_explained: number; direct_db_writes: number }[];
  integrations: { item_id: string; name: string; direction: string; system: string }[];
  volumes: Record<string, number>;
  j2x: { assessment_date: string; readiness: string; scope_note: string; simulated: boolean };
};

export type ReportRow = {
  item_id: string;
  name: string;
  usage_12m: number;
  frequency: string | null;
  outcome: string | null;
};

export type ReportsOverview = {
  total: number;
  retire: number;
  merged: number;
  merged_into: number;
  standard: number;
  rebuild: number;
  held: ReportRow[];
  groups: { lead: ReportRow; members: ReportRow[] }[];
  rebuild_items: ReportRow[];
};

export type Parity = {
  report: string;
  name: string;
  status: string;
  cr_total: number;
  faithful_rebuild_total?: number;
  fixed_rebuild_total?: number;
  rebuilt_total?: number;
  reconciling_item?: { label: string; partners: string[]; amount: number };
};

export type WorkflowVariant = {
  item_id: string;
  name: string;
  subtype: string;
  usage_12m: number;
  definition: { approval_steps: string[]; enforced_rule: string };
  outcome: string | null;
  action: string | null;
  status: string;
  reason: string;
  flags: string[];
  entities: string[];
};

export type WorkflowPack = {
  headline: string;
  from_count: number;
  to_count: number;
  proposed: { keeps: string; name: string; rule: string; absorbs: string[]; erpx_configuration: string[] }[];
  retire: string[];
  control_impact: string[];
  tests: { id: string; description: string; expected: string }[];
  decision_needed: string;
};

export type CheckResult = {
  check_id: string;
  name: string;
  compares: string;
  tolerance: string;
  status: "pass" | "fail" | "waiting";
  unit: "money" | "count";
  source_value: number | null;
  target_value: number | null;
  difference_count: number;
  summary: Record<string, unknown>;
};

export type ReconException = {
  exception_id: string;
  check_id: string;
  code: string;
  title: string;
  cause: string;
  proposed_action: string;
  approver_role: Role;
  amount_minor: number | null;
  detail: Record<string, unknown>;
};

export type ReconRun = {
  run_id: number;
  input_hash: string;
  result_hash: string;
  definitions_hash: string;
  started_at: string;
  finished_at: string;
  checks: CheckResult[];
  exceptions: ReconException[];
};

export type Difference = {
  row_number: number;
  row_key: string;
  source_value: number | null;
  target_value: number | null;
  difference: number | null;
  detail: Record<string, unknown>;
};

export type Artefact = {
  kind: string;
  content: Record<string, never>;
  source: string;
  model: string | null;
  duration_ms: number | null;
};

export type Condition = { key: string; label: string; passed: boolean; detail: string };

export type SignoffState = {
  scope: string;
  conditions: Condition[];
  ready_to_generate: boolean;
  pack_current: boolean;
  pack: {
    pack_id: number;
    generated_at: string;
    generated_by: string;
    manifest_hash: string;
    audit_head: string;
    summary: Record<string, number>;
    signed_by: string | null;
    signed_at: string | null;
  } | null;
  open_questions: { question_id: number; item_id: string; name: string; question: string; options: string[] }[];
};

export type Scorecard = {
  issues: { issue_id: string; issue_type: string; planted: string; scene: number; found: boolean }[];
  found: number;
  planted: number;
  false_items: { count: number; limit: number; items: string[] };
  decision_quality: { matched: number; total: number; wrong: string[] };
  passed: boolean;
  stages: { stage: string; seconds: number; consultant_seconds: number }[];
  reconciliation: { run: boolean; seconds: number | null; passed: number; total: number };
  defects: { tested: number; failed: number };
  artefacts: { source: string; count: number; ms: number | null }[];
  signoff: { generated: boolean; signed: boolean; conditions: Condition[] };
};

export const workbench = {
  case: (role: Role): Promise<CaseSummary> => api.case(role),
  estate: (role: Role) => request<EstateData>("/api/estate", role),
  reports: (role: Role) => request<ReportsOverview>("/api/reports/overview", role),
  parity: (id: string, role: Role) => post<Parity>(`/api/reports/${id}/parity`, role),
  workflows: (role: Role) =>
    request<{ variants: WorkflowVariant[]; pack: WorkflowPack; pack_source: string }>("/api/workflows", role),
  artefacts: (id: string, role: Role) => request<Artefact[]>(`/api/artefacts/${id}`, role),
  latestRun: (role: Role) => request<ReconRun | null>("/api/reconciliation/latest", role),
  runChecks: (role: Role) => post<ReconRun>("/api/reconciliation/run", role),
  differences: (id: string, role: Role) => request<Difference[]>(`/api/reconciliation/${id}/differences`, role),
  signoff: (role: Role) => request<SignoffState>("/api/signoff", role),
  generatePack: (role: Role) => post<SignoffState>("/api/signoff/generate", role),
  signPack: (role: Role) => post<SignoffState>("/api/signoff/sign", role),
  scorecard: (role: Role) => request<Scorecard>("/api/scorecard", role),
  timing: (stage: string, seconds: number, role: Role) => post("/api/timing", role, { stage, seconds }),
};
