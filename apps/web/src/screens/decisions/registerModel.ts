import type { DecisionRow } from "../../lib/api";
import { STATUS_KEYS, type Outcome, type Role, type Status } from "../../lib/terms";

export type Filters = {
  outcome: Outcome | "held" | null;
  status: Status | null;
  type: string | null;
  needsMe: boolean;
  search: string;
};

export const NO_FILTERS: Filters = { outcome: null, status: null, type: null, needsMe: false, search: "" };

export function refusedRetire(row: DecisionRow): boolean {
  return row.flags.includes("refused_retire") && row.outcome === null;
}

function matchesOutcome(row: DecisionRow, outcome: Filters["outcome"]): boolean {
  if (outcome === null) return true;
  if (outcome === "held") return row.outcome === null;
  // Retire also lists what the system refused to retire: that is the point of the filter.
  if (outcome === "retire") return row.outcome === "retire" || refusedRetire(row);
  return row.outcome === outcome;
}

export function nextRole(row: DecisionRow): Role | null {
  return row.required_roles.find((role) => !row.approved_roles.includes(role)) ?? null;
}

export function needsRole(row: DecisionRow, role: Role): boolean {
  if (row.status === "agreed") return false;
  if (row.status === "question") return role === "customer";
  if (row.status === "conflict" || row.outcome === null) return role === "consultant";
  return nextRole(row) === role;
}

export function applyFilters(rows: DecisionRow[], filters: Filters, role: Role): DecisionRow[] {
  const search = filters.search.trim().toLowerCase();
  return rows.filter(
    (row) =>
      matchesOutcome(row, filters.outcome) &&
      (!filters.status || row.status === filters.status) &&
      (!filters.type || row.item_type === filters.type) &&
      (!filters.needsMe || needsRole(row, role)) &&
      (!search || `${row.item_id} ${row.name}`.toLowerCase().includes(search)),
  );
}

function attention(row: DecisionRow): number {
  if (refusedRetire(row)) return 0;
  if (row.status === "conflict") return 1;
  if (row.flags.includes("conflict")) return 2;
  if (row.status === "question") return 3;
  if (row.flags.includes("hidden_dependency")) return 4;
  return 5 + STATUS_KEYS.indexOf(row.status);
}

// What needs a person comes first. Within a group, the lowest confidence comes first.
export function byAttention(rows: DecisionRow[]): DecisionRow[] {
  return [...rows].sort(
    (a, b) =>
      attention(a) - attention(b) ||
      (a.confidence ?? 0) - (b.confidence ?? 0) ||
      a.item_id.localeCompare(b.item_id),
  );
}

export function countByOutcome(rows: DecisionRow[], outcome: Filters["outcome"]): number {
  return rows.filter((row) => matchesOutcome(row, outcome)).length;
}

export function countByStatus(rows: DecisionRow[]): Record<Status, number> {
  const counts = Object.fromEntries(STATUS_KEYS.map((key) => [key, 0])) as Record<Status, number>;
  for (const row of rows) counts[row.status] += 1;
  return counts;
}
