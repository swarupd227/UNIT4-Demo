import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, Hammer, Wrench } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { usePersona } from "../lib/persona";
import { useToast } from "../lib/toast";
import { workbench, type Parity } from "../lib/workbench";
import { CountUp, money, Panel, Screen } from "../ui/layout";
import { Button, CodeBadge, Skeleton } from "../ui/primitives";

const REBUILDS = [
  { id: "RP-077", name: "WIP ageing by partner" },
  { id: "RP-084", name: "Utilisation by grade" },
];

function Reduction({ segments, total }: { segments: { label: string; count: number; className: string }[]; total: number }) {
  return (
    <div>
      <div className="flex h-11 gap-0.5" role="img" aria-label={segments.map((s) => `${s.label}: ${s.count}`).join(", ")}>
        {segments.map((segment, index) => (
          <motion.div
            key={segment.label}
            initial={{ flexGrow: total / segments.length }}
            animate={{ flexGrow: segment.count }}
            transition={{ duration: 0.8, delay: 0.25 + index * 0.05, ease: "easeInOut" }}
            style={{ flexBasis: 0 }}
            title={`${segment.label}: ${segment.count}`}
            className={`first:rounded-l-md last:rounded-r-md ${segment.className}`}
          />
        ))}
      </div>
      <dl className="mt-3 flex flex-wrap gap-x-9 gap-y-2">
        {segments.map((segment) => (
          <div key={segment.label} className="flex items-center gap-2">
            <i className={`size-3.5 rounded-sm ${segment.className}`} aria-hidden />
            <dd className="tnum text-[24px] font-semibold">{segment.count}</dd>
            <dt className="text-[15px] text-ink-2">{segment.label}</dt>
          </div>
        ))}
      </dl>
    </div>
  );
}

function Total({ label, value, tone = "" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="flex-1 rounded-lg bg-surface-2 p-4">
      <div className="text-[14px] text-ink-3">{label}</div>
      <div className={`tnum text-[28px] leading-9 font-semibold ${tone}`}>
        <CountUp value={value} format={(n) => money(Math.round(n))} />
      </div>
    </div>
  );
}

function ParityView({ parity, fixed, onFix }: { parity: Parity; fixed: boolean; onFix: () => void }) {
  const item = parity.reconciling_item;
  if (!item) {
    const match = parity.cr_total === parity.rebuilt_total;
    return (
      <div className="space-y-3">
        <div className="flex gap-3">
          <div className="flex-1 rounded-lg bg-surface-2 p-4">
            <div className="text-[14px] text-ink-3">CR billable hours</div>
            <div className="tnum text-[28px] font-semibold">{parity.cr_total.toLocaleString("en-GB")}</div>
          </div>
          <div className="flex-1 rounded-lg bg-surface-2 p-4">
            <div className="text-[14px] text-ink-3">Rebuilt report</div>
            <div className="tnum text-[28px] font-semibold">{parity.rebuilt_total?.toLocaleString("en-GB")}</div>
          </div>
        </div>
        <p className="flex items-center gap-2 text-[16px] font-medium text-ok">
          <Check size={19} aria-hidden /> {match ? "Totals match by period and grade" : "Totals differ"}
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      <section>
        <h3 className="mb-2 text-[15px] font-semibold">Step 1: rebuild it faithfully, old partner list included</h3>
        <div className="flex gap-3">
          <Total label="CR report" value={parity.cr_total} />
          <Total label="Rebuilt report" value={parity.faithful_rebuild_total ?? 0} />
        </div>
        <p className="mt-2 flex items-center gap-2 text-[16px] font-medium text-ok">
          <Check size={19} aria-hidden /> Totals match to the penny, so the logic is proven
        </p>
      </section>
      {!fixed ? (
        <div className="rounded-lg bg-warn-soft p-4">
          <p className="text-[16px] leading-6">
            The report only includes partners typed into it in 2022. {item.partners.length} current partners are missing.
          </p>
          <Button variant="primary" className="mt-3" onClick={onFix}>
            <Wrench size={17} aria-hidden />
            Fix the partner list
          </Button>
        </div>
      ) : (
        <motion.section initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
          <h3 className="mb-2 text-[15px] font-semibold">Step 2: use current partners from the reference data</h3>
          <div className="flex gap-3">
            <Total label="Fixed report" value={parity.fixed_rebuild_total ?? 0} />
            <Total label="Difference" value={(parity.fixed_rebuild_total ?? 0) - parity.cr_total} tone="text-warn" />
            <Total label="Missing partners' WIP" value={item.amount} tone="text-warn" />
          </div>
          <p className="mt-2 flex items-center gap-2 text-[16px] font-medium text-ok">
            <Check size={19} aria-hidden /> The difference is exactly the WIP of {item.partners.join(", ")}
          </p>
        </motion.section>
      )}
    </div>
  );
}

export function ReportsScreen() {
  const { role } = usePersona();
  const toast = useToast();
  const { data } = useQuery({ queryKey: ["reports"], queryFn: () => workbench.reports(role) });
  const [report, setReport] = useState(REBUILDS[0].id);
  const [results, setResults] = useState<Record<string, Parity>>({});
  const [fixed, setFixed] = useState(false);
  const rebuild = useMutation({
    mutationFn: (id: string) => workbench.parity(id, role),
    onSuccess: (parity, id) => setResults((current) => ({ ...current, [id]: parity })),
    onError: (error: Error) => toast(error.message, "bad"),
  });

  if (!data) return <Skeleton className="m-5 h-96" />;
  const after = data.merged_into + data.rebuild;
  const parity = results[report];

  return (
    <Screen
      title={`${data.total} custom reports`}
      lead={`${after} custom reports remain, and the ones that stay are proven.`}
      next="workflows"
    >
      <Panel>
        <Reduction
          total={data.total}
          segments={[
            { label: "retire", count: data.retire, className: "bg-neutral-mark" },
            { label: `merge into ${data.merged_into}`, count: data.merged, className: "bg-accent" },
            { label: "replace with standard", count: data.standard, className: "bg-ai" },
            { label: "rebuild", count: data.rebuild, className: "bg-ink" },
            { label: "held for the customer", count: data.held.length, className: "bg-warn" },
          ]}
        />
      </Panel>
      <div className="grid grid-cols-[minmax(0,5fr)_minmax(0,7fr)] gap-4">
        <div className="space-y-4">
          <Panel title={`${data.merged} near-duplicates become ${data.merged_into}`}>
            <ul tabIndex={0} aria-label="Merge groups" className="scroll-quiet max-h-[340px] divide-y divide-line overflow-y-auto">
              {data.groups.map((group) => (
                <li key={group.lead.item_id} className="py-2">
                  <div className="flex justify-between gap-3 text-[16px]">
                    <span className="font-medium">{group.lead.name}</span>
                    <span className="tnum shrink-0 text-ink-3">{group.members.length + 1} reports</span>
                  </div>
                  <p className="truncate text-[14px] text-ink-3">
                    Absorbs {group.members.map((member) => member.name).join(", ")}
                  </p>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Held, not retired">
            <ul className="space-y-1.5">
              {data.held.map((row) => (
                <li key={row.item_id}>
                  <Link to={`/decisions/${row.item_id}`} className="flex justify-between text-[16px] hover:underline">
                    <span>{row.name}</span>
                    <span className="tnum text-ink-3">{row.item_id}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
        <Panel
          title="Prove the rebuild"
          aside={
            <div className="flex items-center gap-3">
              {parity && <CodeBadge />}
              <div className="flex rounded-lg border border-line-strong p-0.5">
                {REBUILDS.map((entry) => (
                  <button
                    key={entry.id}
                    type="button"
                    aria-pressed={report === entry.id}
                    onClick={() => setReport(entry.id)}
                    className={`rounded-md px-3 py-1 text-[14px] font-medium ${
                      report === entry.id ? "bg-ink text-canvas" : "text-ink-2"
                    }`}
                  >
                    {entry.name}
                  </button>
                ))}
              </div>
            </div>
          }
        >
          {parity ? (
            <ParityView parity={parity} fixed={fixed} onFix={() => setFixed(true)} />
          ) : (
            <div className="grid h-72 place-items-center">
              <Button variant="primary" disabled={rebuild.isPending} onClick={() => rebuild.mutate(report)}>
                <Hammer size={18} aria-hidden />
                Rebuild and run parity
              </Button>
            </div>
          )}
        </Panel>
      </div>
    </Screen>
  );
}
