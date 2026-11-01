import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Hourglass, Play, RotateCw, ShieldCheck, XCircle } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { usePersona } from "../lib/persona";
import { ROLES } from "../lib/terms";
import { useToast } from "../lib/toast";
import { workbench, type CheckResult, type ReconException, type ReconRun } from "../lib/workbench";
import { SideDrawer } from "../ui/overlays";
import { money, Panel, Screen, useDecision } from "../ui/layout";
import { Button, CodeBadge, Skeleton } from "../ui/primitives";

const RULE_ITEM = "CC-014";

const STATUS = {
  pass: { icon: CheckCircle2, label: "Pass", text: "text-ok", ring: "border-line" },
  fail: { icon: XCircle, label: "Difference", text: "text-bad", ring: "border-bad/40" },
  waiting: { icon: Hourglass, label: "Waiting", text: "text-warn", ring: "border-warn/40" },
};

function headline(check: CheckResult, exceptions: ReconException[]): string {
  const summary = check.summary as { waiting_for?: string; threshold?: number; results?: unknown[] };
  if (check.status === "waiting") return summary.waiting_for ?? "Waiting";
  if (check.check_id === "R8") return `${summary.results?.length} tests pass at ${summary.threshold}%`;
  if (check.status === "fail") return exceptions.map((exception) => exception.title).join(" · ");
  if (check.unit === "money") return money(check.target_value);
  return `${(check.target_value ?? 0).toLocaleString("en-GB")} matched`;
}

function ThresholdCard({ onAnswered }: { onAnswered: () => void }) {
  const { role } = usePersona();
  const toast = useToast();
  const client = useQueryClient();
  const { data: item } = useDecision(RULE_ITEM);
  const open = item?.questions.find((question) => question.status === "open");
  const mutate = useMutation({
    mutationFn: async (action: { answer?: string }) => {
      if (action.answer) await api.answer(RULE_ITEM, role, action.answer);
      else await api.ask(RULE_ITEM, role, item!.conflict!.question, item!.conflict!.options);
    },
    onSuccess: (_, action) => {
      client.invalidateQueries();
      if (action.answer) onAnswered();
    },
    onError: (error: Error) => toast(error.message, "bad"),
  });
  if (!item?.conflict) return null;
  return (
    <div className="rounded-xl border border-warn/40 bg-warn-soft p-4">
      <h3 className="text-[17px] font-semibold">R8 needs one decision</h3>
      <p className="mt-1 text-[16px] leading-6">{item.conflict.question}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {open && item.allowed.answer &&
          open.options.map((option) => (
            <Button key={option} onClick={() => mutate.mutate({ answer: option })}>
              {option}
            </Button>
          ))}
        {open && !item.allowed.answer && (
          <span className="text-[15px] text-ink-2">Waiting for Jordan Ashby. Switch persona to answer.</span>
        )}
        {!open && item.allowed.ask && <Button onClick={() => mutate.mutate({})}>Ask the customer</Button>}
      </div>
    </div>
  );
}

function CheckDrawer({ check, run, onClose }: { check: CheckResult; run: ReconRun; onClose: () => void }) {
  const { role } = usePersona();
  const { data: rows } = useQuery({
    queryKey: ["differences", run.run_id, check.check_id],
    queryFn: () => workbench.differences(check.check_id, role),
  });
  const exceptions = run.exceptions.filter((exception) => exception.check_id === check.check_id);
  return (
    <SideDrawer open onClose={onClose} title={`${check.check_id} ${check.name}`} description={check.compares}>
      <div className="space-y-4 p-6">
        <div className="flex items-center gap-3">
          <CodeBadge />
          <span className="text-[14px] text-ink-3">Tolerance: {check.tolerance}</span>
        </div>
        {exceptions.map((exception) => (
          <section key={exception.exception_id} className="rounded-lg border border-line bg-surface-2 p-4">
            <h3 className="text-[17px] font-semibold">{exception.title}</h3>
            <p className="mt-1 text-[15px] leading-6">{exception.cause}</p>
            <p className="mt-2 text-[15px]">
              <strong>Proposed:</strong> {exception.proposed_action}
            </p>
            <p className="mt-1 text-[14px] text-ink-3">
              {exception.exception_id} · Approver: {ROLES[exception.approver_role].label}
            </p>
          </section>
        ))}
        {check.difference_count > 0 && (
          <table className="w-full text-[15px]">
            <caption className="mb-2 text-left text-[14px] text-ink-3">
              {check.difference_count.toLocaleString("en-GB")} rows behind this result
              {check.difference_count > 200 && ", largest 200 shown"}
            </caption>
            <thead>
              <tr className="border-b border-line-strong text-left text-[13px] tracking-wide text-ink-3 uppercase">
                <th className="py-1.5 font-semibold">Row</th>
                {check.check_id !== "R6" && (
                  <>
                    <th className="py-1.5 text-right font-semibold">CR</th>
                    <th className="py-1.5 text-right font-semibold">ERPx</th>
                    <th className="py-1.5 text-right font-semibold">Difference</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="tnum divide-y divide-line">
              {rows?.map((row) => (
                <tr key={row.row_number}>
                  <td className="py-1.5 pr-3 whitespace-pre-wrap">{row.row_key}</td>
                  {check.check_id !== "R6" && (
                    <>
                      <td className="py-1.5 text-right">{money(row.source_value)}</td>
                      <td className="py-1.5 text-right">{money(row.target_value) || "Not loaded"}</td>
                      <td className="py-1.5 text-right font-medium">{money(row.difference)}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {check.status === "pass" && check.check_id !== "R7" && (
          <p className="text-[16px] text-ok">No differences.</p>
        )}
        {check.check_id === "R7" && <ParitySummary check={check} />}
      </div>
    </SideDrawer>
  );
}

function ParitySummary({ check }: { check: CheckResult }) {
  const reports = (check.summary as { reports: { name: string; cr_total: number; fixed_rebuild_total?: number; reconciling_item?: { amount: number; partners: string[] } }[] }).reports;
  const report = reports[0];
  return (
    <div className="text-[16px] leading-7">
      <p>{report.name}: the faithful rebuild matches CR exactly at {money(report.cr_total)}.</p>
      <p>
        The fixed report adds {money(report.reconciling_item?.amount)}, which is exactly the WIP of{" "}
        {report.reconciling_item?.partners.join(", ")}.
      </p>
    </div>
  );
}

export function ReconcileScreen() {
  const { role } = usePersona();
  const toast = useToast();
  const client = useQueryClient();
  const { data: latest, isPending } = useQuery({
    queryKey: ["reconciliation"],
    queryFn: () => workbench.latestRun(role),
  });
  const [selected, setSelected] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(99);
  const [comparison, setComparison] = useState<{ same: boolean; hash: string } | null>(null);
  const [needsRerun, setNeedsRerun] = useState(false);
  const previous = useRef<ReconRun | null>(null);

  const run = useMutation({
    mutationFn: () => workbench.runChecks(role),
    onMutate: () => {
      previous.current = latest ?? null;
      setComparison(null);
    },
    onSuccess: (result) => {
      if (previous.current) {
        const before = previous.current;
        const sameInput = before.input_hash === result.input_hash;
        if (sameInput) setComparison({ same: before.result_hash === result.result_hash, hash: result.result_hash });
      }
      setRevealed(0);
      setNeedsRerun(false);
      client.setQueryData(["reconciliation"], result);
      client.invalidateQueries({ predicate: (query) => query.queryKey[0] !== "reconciliation" });
    },
    onError: (error: Error) => toast(error.message, "bad"),
  });

  useEffect(() => {
    if (!latest || revealed >= latest.checks.length) return;
    const timer = setTimeout(() => setRevealed((count) => count + 1), 320);
    return () => clearTimeout(timer);
  }, [revealed, latest]);

  const check = latest?.checks.find((entry) => entry.check_id === selected);
  const finished = latest ? revealed >= latest.checks.length : false;
  const waiting = latest?.checks.find((entry) => entry.check_id === "R8")?.status === "waiting";
  const passed = latest?.checks.filter((entry) => entry.status === "pass").length ?? 0;

  return (
    <Screen
      title="Reconciliation"
      lead="Plain code, not a language model. The same data always gives the same result."
      next="signoff"
      aside={
        <Button variant={latest ? "secondary" : "primary"} disabled={run.isPending} onClick={() => run.mutate()}>
          {latest ? <RotateCw size={17} aria-hidden /> : <Play size={17} aria-hidden />}
          {latest ? "Run again" : "Run the checks"}
        </Button>
      }
    >
      {isPending && <Skeleton className="h-96" />}
      {!isPending && !latest && !run.isPending && (
        <Panel>
          <p className="py-16 text-center text-[18px] text-ink-2">
            Eight checks on the trial migration of the UK entity into the simulated ERPx target.
          </p>
        </Panel>
      )}
      {latest && (
        <>
          <div className="grid grid-cols-4 gap-3">
            {latest.checks.map((entry, index) => {
              const shown = index < revealed;
              const status = STATUS[entry.status];
              const Icon = status.icon;
              const exceptions = latest.exceptions.filter((exception) => exception.check_id === entry.check_id);
              return (
                <motion.button
                  key={`${latest.run_id}-${entry.check_id}`}
                  type="button"
                  disabled={!shown}
                  onClick={() => setSelected(entry.check_id)}
                  animate={{ opacity: shown ? 1 : 0.45 }}
                  className={`h-[150px] rounded-xl border bg-surface p-4 text-left shadow-panel transition-colors hover:border-ink-3 ${
                    shown ? status.ring : "border-line"
                  }`}
                >
                  <span className="flex items-center justify-between">
                    <span className="tnum text-[15px] font-semibold text-ink-3">{entry.check_id}</span>
                    {shown ? (
                      <span className={`inline-flex items-center gap-1.5 text-[15px] font-semibold ${status.text}`}>
                        <Icon size={18} aria-hidden />
                        {status.label}
                      </span>
                    ) : (
                      <span className="text-[15px] text-ink-3">Checking…</span>
                    )}
                  </span>
                  <span className="mt-1 block text-[18px] font-semibold">{entry.name}</span>
                  {shown && (
                    <span className="tnum mt-1 line-clamp-2 block text-[15px] leading-6 text-ink-2">
                      {headline(entry, exceptions)}
                    </span>
                  )}
                </motion.button>
              );
            })}
          </div>

          {finished && (
            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <Panel className="flex items-center justify-between gap-6">
                <p className="text-[17px]">
                  <strong className="tnum">{passed} of {latest.checks.length}</strong> checks pass.{" "}
                  <strong className="tnum">{latest.exceptions.length}</strong> exceptions listed for people to resolve.
                </p>
                <p className="tnum flex items-center gap-2 text-[15px] text-ink-2">
                  <ShieldCheck size={18} className="text-accent" aria-hidden />
                  {comparison
                    ? comparison.same
                      ? `Run again, identical result: ${comparison.hash.slice(0, 12)}`
                      : `Result changed: ${comparison.hash.slice(0, 12)}`
                    : `Result hash ${latest.result_hash.slice(0, 12)}`}
                </p>
              </Panel>
              {waiting && !needsRerun && <ThresholdCard onAnswered={() => setNeedsRerun(true)} />}
              {needsRerun && (
                <div className="flex items-center justify-between rounded-xl border border-ok/30 bg-ok-soft p-4">
                  <p className="text-[17px] font-medium">Threshold chosen. Run the checks again to test the rule.</p>
                  <Button variant="primary" onClick={() => run.mutate()}>
                    Run again
                  </Button>
                </div>
              )}
            </motion.div>
          )}
        </>
      )}
      {check && latest && <CheckDrawer check={check} run={latest} onClose={() => setSelected(null)} />}
    </Screen>
  );
}
