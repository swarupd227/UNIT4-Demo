import { expect, test } from "vitest";
import type { DecisionRow } from "../../lib/api";
import { applyFilters, byAttention, countByStatus, needsRole, NO_FILTERS } from "./registerModel";

function row(overrides: Partial<DecisionRow>): DecisionRow {
  return {
    item_id: "RP-001",
    name: "Report",
    item_type: "RP",
    outcome: "retire",
    status: "review",
    flags: [],
    confidence: 90,
    required_roles: ["consultant", "customer"],
    approved_roles: [],
    ...overrides,
  } as DecisionRow;
}

const refused = row({ item_id: "RP-112", outcome: null, status: "question", flags: ["refused_retire"] });

test("the Retire filter includes what the system refused to retire", () => {
  const rows = [row({}), refused, row({ item_id: "RP-002", outcome: "keep_repoint" })];
  const result = applyFilters(rows, { ...NO_FILTERS, outcome: "retire" }, "consultant");
  expect(result.map((r) => r.item_id)).toEqual(["RP-001", "RP-112"]);
});

test("refused items sort to the top", () => {
  expect(byAttention([row({}), refused])[0].item_id).toBe("RP-112");
});

test("lowest confidence comes first within a group", () => {
  const rows = byAttention([row({ item_id: "A", confidence: 96 }), row({ item_id: "B", confidence: 76 })]);
  expect(rows[0].item_id).toBe("B");
});

test("needs me follows who is next to act", () => {
  expect(needsRole(row({}), "consultant")).toBe(true);
  expect(needsRole(row({ approved_roles: ["consultant"], status: "awaiting" }), "customer")).toBe(true);
  expect(needsRole(row({ status: "question" }), "customer")).toBe(true);
  expect(needsRole(row({ status: "agreed" }), "consultant")).toBe(false);
});

test("search matches ID and name", () => {
  const rows = [row({ item_id: "CC-014", name: "Billing adjust writer" }), row({ name: "Other" })];
  expect(applyFilters(rows, { ...NO_FILTERS, search: "billing" }, "consultant")).toHaveLength(1);
  expect(applyFilters(rows, { ...NO_FILTERS, search: "cc-014" }, "consultant")).toHaveLength(1);
});

test("countByStatus covers every status", () => {
  expect(countByStatus([row({}), refused])).toEqual({ conflict: 0, question: 1, review: 1, awaiting: 0, agreed: 0 });
});
