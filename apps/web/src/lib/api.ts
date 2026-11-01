import type { Outcome, Role, Status } from "./terms";

export type EstateCount = { item_type: string; count: number; j2x_explained: number };

export type CaseSummary = {
  case_id: string;
  label: string;
  status: string;
  customer_name: string;
  entity_label: string;
  sector: string;
  staff_count: number;
  erp_since: number;
  cr_since: number;
  modules_in_scope: string;
  out_of_scope: string;
  goal: string;
  synthetic: boolean;
  entities: { entity_code: string; name: string; status: string; in_migration_scope: boolean }[];
  estate: EstateCount[];
  progress: { total: number; agreed: number; open_questions: number };
  reconciliation: { passed: number; total: number; exceptions: number } | null;
};

export type DecisionRow = {
  item_id: string;
  item_type: string;
  name: string;
  subtype: string;
  module: string | null;
  frequency: string | null;
  usage_12m: number;
  last_used: string | null;
  owner: string | null;
  j2x_explained: boolean;
  outcome: Outcome | null;
  action: string | null;
  status: Status;
  conflict_open: boolean;
  edit_reason: string | null;
  proposed_outcome: Outcome | null;
  candidate_outcome: Outcome | null;
  state: "proposed" | "held";
  reason: string;
  confidence: number | null;
  flags: string[];
  approved_roles: Role[];
  required_roles: Role[];
};

export type Evidence = {
  kind: string;
  label: string;
  detail?: string;
  line?: number;
  item?: string;
};

export type Conflict = {
  topic: string;
  left_label: string;
  left_value: string;
  right_label: string;
  right_value: string;
  blocks_acceptance: boolean;
  question: string;
  options: string[];
};

export type Question = {
  question_id: number;
  question: string;
  options: string[];
  status: "open" | "answered";
  asked_by: string;
  asked_at: string;
  answer: string | null;
  answered_by: string | null;
  answered_at: string | null;
};

export type AuditEvent = {
  seq: number;
  at: string;
  actor: string;
  role: string;
  action: string;
  detail: Record<string, unknown>;
  hash: string;
};

export type DecisionDetail = DecisionRow & {
  source_text: string | null;
  summary: string;
  conflict: Conflict | null;
  evidence: Evidence[];
  rule: string;
  engine_version: string;
  j2x_summary: string | null;
  usage_by_month: { month: string; count: number }[];
  approvals: { role: Role; person: string; decided_at: string }[];
  questions: Question[];
  audit: AuditEvent[];
  allowed: { accept: boolean; edit: boolean; ask: boolean; answer: boolean; reason: string | null };
};

export async function request<T>(path: string, role: Role, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Studio-Persona": role },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "Something went wrong. Please try again.";
    throw new Error(detail);
  }
  return response.json();
}

export const post = <T = unknown>(path: string, role: Role, body?: unknown) =>
  request<T>(path, role, { method: "POST", body: body ? JSON.stringify(body) : undefined });

export const api = {
  case: (role: Role) => request<CaseSummary>("/api/case", role),
  decisions: (role: Role) => request<DecisionRow[]>("/api/decisions", role),
  decision: (id: string, role: Role) => request<DecisionDetail>(`/api/decisions/${id}`, role),
  accept: (id: string, role: Role) => post(`/api/decisions/${id}/accept`, role),
  bulkAccept: (ids: string[], role: Role) =>
    post<{ accepted: number; skipped: number }>("/api/decisions/bulk-accept", role, { item_ids: ids }),
  edit: (id: string, role: Role, outcome: Outcome, reason: string) =>
    post(`/api/decisions/${id}/edit`, role, { outcome, reason }),
  ask: (id: string, role: Role, question: string, options: string[]) =>
    post(`/api/decisions/${id}/ask`, role, { question, options }),
  answer: (id: string, role: Role, answer: string) => post(`/api/decisions/${id}/answer`, role, { answer }),
  reset: (role: Role) => post("/api/workspace/reset", role),
  answerOpen: (role: Role) => post<{ answered: number }>("/api/workspace/answer-open", role),
  prepare: (scene: number, role: Role) => post(`/api/workspace/prepare/${scene}`, role),
  auditIntact: (role: Role) => request<{ intact: boolean }>("/api/audit/verify", role),
};
