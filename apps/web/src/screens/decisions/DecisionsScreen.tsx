import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { RowSelectionState } from "@tanstack/react-table";
import { Search, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, type DecisionDetail, type Evidence } from "../../lib/api";
import { usePersona } from "../../lib/persona";
import { ITEM_TYPES, OUTCOME_KEYS, OUTCOMES, ROLES, STATUSES, type Outcome, type Status } from "../../lib/terms";
import { useToast } from "../../lib/toast";
import { Button, Kbd, Skeleton, STATUS_ICONS, TONE_MARK, TONE_TEXT } from "../../ui/primitives";
import { DetailPanel } from "./DetailPanel";
import { AskDialog, EditDialog } from "./DecisionDialogs";
import { EvidenceDrawer } from "./EvidenceDrawer";
import {
  applyFilters,
  byAttention,
  countByOutcome,
  countByStatus,
  needsRole,
  type Filters,
} from "./registerModel";
import { Register } from "./Register";
import { useDecisionActions } from "./useDecisionActions";

function FilterChip({ active, label, count, onClick }: {
  active: boolean;
  label: string;
  count?: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`inline-flex h-9 items-center gap-2 rounded-full border px-3.5 text-[15px] font-medium transition-colors ${
        active ? "border-ink bg-ink text-canvas" : "border-line-strong bg-surface text-ink-2 hover:border-ink-3"
      }`}
    >
      {label}
      {count !== undefined && <span className={`tnum ${active ? "text-canvas/75" : "text-ink-3"}`}>{count}</span>}
    </button>
  );
}

// Status is reserved colour, so every segment also has an icon and label in the legend below it.
function StatusBar({ counts, total, active, onSelect }: {
  counts: Record<Status, number>;
  total: number;
  active: Status | null;
  onSelect: (status: Status | null) => void;
}) {
  const keys = Object.keys(STATUSES) as Status[];
  return (
    <div>
      <div className="flex h-3 gap-0.5" aria-hidden>
        {keys
          .filter((key) => counts[key] > 0)
          .map((key) => (
            <div
              key={key}
              title={`${STATUSES[key].label}: ${counts[key]}`}
              className={`min-w-1.5 first:rounded-l last:rounded-r ${TONE_MARK[STATUSES[key].tone]}`}
              style={{ flexGrow: counts[key], flexBasis: 0, opacity: active && active !== key ? 0.3 : 1 }}
            />
          ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1">
        {keys.map((key) => {
          const Icon = STATUS_ICONS[key];
          return (
            <button
              key={key}
              type="button"
              aria-pressed={active === key}
              onClick={() => onSelect(active === key ? null : key)}
              className={`inline-flex items-center gap-1.5 rounded text-[14px] ${
                active === key ? "font-semibold underline underline-offset-4" : ""
              } ${TONE_TEXT[STATUSES[key].tone]}`}
            >
              <Icon size={15} aria-hidden />
              {STATUSES[key].label}
              <span className="tnum text-ink-2">{counts[key]}</span>
            </button>
          );
        })}
        <span className="tnum ml-auto text-[14px] text-ink-3">
          {Math.round((counts.agreed / Math.max(total, 1)) * 100)}% agreed
        </span>
      </div>
    </div>
  );
}

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement && (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable);

export function DecisionsScreen() {
  const { role } = usePersona();
  const toast = useToast();
  const client = useQueryClient();
  const navigate = useNavigate();
  const { itemId = null } = useParams();
  const [params, setParams] = useSearchParams();
  const [selection, setSelection] = useState<RowSelectionState>({});
  const [evidence, setEvidence] = useState<{ item: DecisionDetail; evidence: Evidence } | null>(null);
  const [dialog, setDialog] = useState<{ kind: "edit" | "ask"; item: DecisionDetail } | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const order = useRef<string[]>([]);
  const onOrder = useCallback((ids: string[]) => {
    order.current = ids;
  }, []);

  const filters: Filters = {
    outcome: params.get("outcome") as Filters["outcome"],
    status: params.get("status") as Status | null,
    type: params.get("type"),
    needsMe: params.get("mine") === "1",
    search: params.get("q") ?? "",
  };

  const setFilter = useCallback(
    (key: string, value: string | null) => {
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          if (value) next.set(key, value);
          else next.delete(key);
          return next;
        },
        { replace: true },
      );
      setSelection({});
    },
    [setParams],
  );

  const { data, isPending, error } = useQuery({
    queryKey: ["decisions"],
    queryFn: () => api.decisions(role),
  });
  const rows = useMemo(() => data ?? [], [data]);
  const shown = useMemo(
    () => byAttention(applyFilters(rows, filters, role)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [rows, params, role],
  );
  const statusCounts = useMemo(() => countByStatus(rows), [rows]);
  const needsMe = useMemo(() => rows.filter((row) => needsRole(row, role)).length, [rows, role]);

  const open = useCallback(
    (id: string) => navigate({ pathname: `/decisions/${id}`, search: params.toString() }),
    [navigate, params],
  );

  useEffect(() => {
    if (!itemId && shown.length > 0) open(shown[0].item_id);
  }, [itemId, shown, open]);

  const actions = useDecisionActions(itemId);

  const bulk = useMutation({
    mutationFn: (ids: string[]) => api.bulkAccept(ids, role),
    onSuccess: ({ accepted, skipped }) => {
      toast(skipped ? `${accepted} accepted, ${skipped} skipped: not yours to accept yet` : `${accepted} accepted`);
      setSelection({});
    },
    onError: (failure: Error) => toast(failure.message, "bad"),
    onSettled: () => client.invalidateQueries(),
  });

  const currentDetail = (): DecisionDetail | undefined =>
    client.getQueryData<DecisionDetail>(["decision", itemId, role]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (isTyping(event.target) || event.ctrlKey || event.metaKey || event.altKey) return;
      if (document.querySelector("[role=dialog]")) return;
      const key = event.key.toLowerCase();
      if (key === "/") {
        event.preventDefault();
        searchRef.current?.focus();
      } else if (key === "j" || key === "k") {
        const index = itemId ? order.current.indexOf(itemId) : -1;
        const next = order.current[index + (key === "j" ? 1 : -1)];
        if (next) open(next);
      } else if (key === "x" && itemId) {
        setSelection((current) => {
          const next = { ...current };
          if (next[itemId]) delete next[itemId];
          else next[itemId] = true;
          return next;
        });
      } else {
        const item = currentDetail();
        if (!item) return;
        if (key === "a" && item.allowed.accept) actions.accept.mutate();
        if (key === "e" && item.allowed.edit) {
          event.preventDefault(); // Otherwise the letter lands in the dialog's autofocused field.
          setDialog({ kind: "edit", item });
        }
        if (key === "q" && item.allowed.ask) {
          event.preventDefault();
          setDialog({ kind: "ask", item });
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const selectedIds = Object.keys(selection);

  if (error) {
    return (
      <div className="m-auto max-w-md text-center">
        <h1 className="text-xl font-semibold">The register could not load</h1>
        <p className="mt-2 text-ink-2">Nothing has been lost. The service may still be starting.</p>
        <Button variant="primary" className="mt-5" onClick={() => client.invalidateQueries()}>
          Try again
        </Button>
      </div>
    );
  }

  const outcomeChips: { key: Outcome | "held"; label: string }[] = [
    ...OUTCOME_KEYS.map((key) => ({ key, label: OUTCOMES[key].short })),
    { key: "held", label: "Held" },
  ];

  return (
    <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_450px] gap-4 p-4 min-[1600px]:grid-cols-[minmax(0,1fr)_540px] min-[1600px]:gap-5 min-[1600px]:p-5">
      <section className="flex min-h-0 flex-col rounded-xl bg-surface shadow-panel">
        <div className="space-y-3.5 border-b border-line p-5">
          <div className="flex items-baseline justify-between gap-6">
            <h1 className="text-2xl font-semibold">Decision register</h1>
            <p className="text-[15px] text-ink-2">Every item gets a decision, a reason and a named person.</p>
          </div>
          {isPending ? (
            <Skeleton className="h-9" />
          ) : (
            <StatusBar
              counts={statusCounts}
              total={rows.length}
              active={filters.status}
              onSelect={(status) => setFilter("status", status)}
            />
          )}
          <div className="flex flex-wrap items-center gap-2">
            <FilterChip
              active={!filters.outcome}
              label="All"
              count={rows.length}
              onClick={() => setFilter("outcome", null)}
            />
            {outcomeChips.map(({ key, label }) => (
              <FilterChip
                key={key}
                active={filters.outcome === key}
                label={label}
                count={countByOutcome(rows, key)}
                onClick={() => setFilter("outcome", filters.outcome === key ? null : key)}
              />
            ))}
          </div>
          <div className="flex items-center gap-3">
            <label className="relative min-w-0 flex-1">
              <span className="sr-only">Search by ID or name</span>
              <Search size={18} className="absolute top-2.5 left-3 text-ink-3" aria-hidden />
              <input
                ref={searchRef}
                value={filters.search}
                onChange={(event) => setFilter("q", event.target.value || null)}
                onKeyDown={(event) => event.key === "Escape" && event.currentTarget.blur()}
                placeholder="Search by ID or name"
                className="h-10 w-full rounded-lg border border-line-strong bg-surface pr-9 pl-10 text-[15px] outline-none focus:border-accent"
              />
              <span className="absolute top-2 right-3">
                <Kbd>/</Kbd>
              </span>
            </label>
            <div className="flex rounded-lg border border-line-strong p-0.5" role="group" aria-label="Item type">
              {[null, ...Object.keys(ITEM_TYPES)].map((type) => (
                <button
                  key={type ?? "all"}
                  type="button"
                  aria-pressed={filters.type === type}
                  onClick={() => setFilter("type", type)}
                  className={`h-8 rounded-md px-3 text-[14px] font-medium transition-colors ${
                    filters.type === type ? "bg-line text-ink" : "text-ink-2 hover:text-ink"
                  }`}
                >
                  {type ? ITEM_TYPES[type].plural : "All types"}
                </button>
              ))}
            </div>
            <FilterChip
              active={filters.needsMe}
              label={`Needs ${ROLES[role].person.split(" ")[0]}`}
              count={needsMe}
              onClick={() => setFilter("mine", filters.needsMe ? null : "1")}
            />
          </div>
        </div>

        {isPending ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 8 }, (_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : (
          <Register
            rows={shown}
            selectedId={itemId}
            onOpen={open}
            selection={selection}
            onSelection={setSelection}
            onOrder={onOrder}
          />
        )}

        {selectedIds.length > 0 && (
          <div className="flex items-center gap-3 rounded-b-xl border-t border-line bg-surface-2 px-5 py-3">
            <span className="tnum text-[15px] font-medium">{selectedIds.length} selected</span>
            <span className="text-[14px] text-ink-3">
              Items that are not yours to accept are skipped. Retirements still go to the customer.
            </span>
            <Button className="ml-auto" onClick={() => setSelection({})}>
              <X size={16} aria-hidden />
              Clear
            </Button>
            <Button variant="primary" disabled={bulk.isPending} onClick={() => bulk.mutate(selectedIds)}>
              Accept selected
            </Button>
          </div>
        )}
      </section>

      <aside className="min-h-0 overflow-hidden rounded-xl bg-surface shadow-panel" aria-label="Item detail">
        <DetailPanel
          itemId={itemId}
          onEvidence={(item, chosen) => setEvidence({ item, evidence: chosen })}
          onEdit={(item) => setDialog({ kind: "edit", item })}
          onAsk={(item) => setDialog({ kind: "ask", item })}
          onAccept={() => actions.accept.mutate()}
          onAnswer={(answer) => actions.answer.mutate(answer)}
        />
      </aside>

      {evidence && (
        <EvidenceDrawer evidence={evidence.evidence} item={evidence.item} onClose={() => setEvidence(null)} />
      )}
      {dialog?.kind === "edit" && (
        <EditDialog
          item={dialog.item}
          onClose={() => setDialog(null)}
          onSave={(outcome, reason) => {
            actions.edit.mutate({ outcome, reason });
            setDialog(null);
          }}
        />
      )}
      {dialog?.kind === "ask" && (
        <AskDialog
          item={dialog.item}
          onClose={() => setDialog(null)}
          onSend={(question, options) => {
            actions.ask.mutate({ question, options });
            setDialog(null);
          }}
        />
      )}
    </div>
  );
}
