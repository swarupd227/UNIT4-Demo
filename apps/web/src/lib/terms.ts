// Every CR, ERPx and decision term shown in the app lives here, so the functional specialist
// can correct the language without touching a screen.

export const OUTCOMES = {
  retire: { label: "Retire", short: "Retire" },
  replace_standard: { label: "Replace with standard", short: "Standard" },
  rebuild_extension: { label: "Rebuild as extension", short: "Extension" },
  keep_repoint: { label: "Keep and re-point", short: "Re-point" },
  product_gap: { label: "Flag a product gap", short: "Product gap" },
} as const;

export type Outcome = keyof typeof OUTCOMES;
export const OUTCOME_KEYS = Object.keys(OUTCOMES) as Outcome[];

export const OUTCOME_HINTS: Record<Outcome, string> = {
  retire: "Not used, with no legal, audit or year-end purpose. The customer confirms.",
  replace_standard: "An ERPx standard feature gives the same business result.",
  rebuild_extension: "Needed, not in standard, and writes data. Unit4's technical lead confirms.",
  keep_repoint: "A needed read-only report or query with no standard equivalent.",
  product_gap: "The same rebuild appears across many customers. Unit4's product team confirms.",
};

export const HELD_LABEL = "Held: needs customer";

export const ACTIONS: Record<string, string> = {
  rebuild: "rebuild",
  merge_survivor: "merge lead",
  merge_into: "merge",
  standard_plus_one_extension: "standard + one extension",
};

export const STATUSES = {
  conflict: { label: "Conflict", tone: "bad" },
  question: { label: "Question", tone: "warn" },
  review: { label: "To review", tone: "neutral" },
  awaiting: { label: "With approver", tone: "accent" },
  agreed: { label: "Agreed", tone: "ok" },
} as const;

export type Status = keyof typeof STATUSES;
export const STATUS_KEYS = Object.keys(STATUSES) as Status[];

export const ROLES = {
  consultant: { label: "Migration consultant", person: "Robin Hale", org: "Unit4" },
  customer: { label: "Customer finance lead", person: "Jordan Ashby", org: "Ardleigh" },
  unit4_technical: { label: "Unit4 technical lead", person: "Casey Lund", org: "Unit4" },
  unit4_product: { label: "Unit4 product team", person: "Taylor Voss", org: "Unit4" },
} as const;

export type Role = keyof typeof ROLES;
export const ROLE_KEYS = Object.keys(ROLES) as Role[];

export const ITEM_TYPES: Record<string, { label: string; plural: string; estate: string }> = {
  CC: { label: "Custom code", plural: "Code", estate: "Custom code items" },
  RP: { label: "Report", plural: "Reports", estate: "Custom reports" },
  WF: { label: "Workflow", plural: "Workflows", estate: "Approval workflows" },
  CF: { label: "Configuration", plural: "Config", estate: "Configuration areas" },
};
export const ITEM_TYPE_KEYS = Object.keys(ITEM_TYPES);

export const SUBTYPES: Record<string, string> = {
  server_process: "Server process",
  scripted_rule: "Scripted rule",
  custom_table: "Custom table",
  custom_field: "Custom field",
  enquiry: "Enquiry",
  spreadsheet_addin: "Spreadsheet add-in report",
  report_layout: "Report layout",
  purchase: "Purchase approval",
  expense: "Expense approval",
  configuration: "Configuration",
};

export const AUDIT_ACTIONS: Record<string, string> = {
  proposed: "Proposed",
  accepted: "Accepted",
  accepted_seeded: "Accepted (seeded demo history)",
  edited: "Changed the decision",
  asked_customer: "Asked the customer",
  answered: "Answered",
  generated_pack: "Generated the sign-off pack",
  signed_pack: "Signed the pack",
};

export const STAGES = [
  { key: "customer", label: "Customer" },
  { key: "estate", label: "Estate" },
  { key: "decisions", label: "Decisions" },
  { key: "code", label: "Code" },
  { key: "reports", label: "Reports" },
  { key: "workflows", label: "Workflows" },
  { key: "reconcile", label: "Reconcile" },
  { key: "signoff", label: "Sign-off" },
  { key: "scorecard", label: "Scorecard" },
];

export function acceptLabel(role: Role, outcome: string | null): string {
  if (role === "customer") return outcome === "retire" ? "Confirm retirement" : "Confirm";
  if (role === "unit4_technical") return "Approve approach";
  if (role === "unit4_product") return "Confirm product gap";
  return "Accept";
}
