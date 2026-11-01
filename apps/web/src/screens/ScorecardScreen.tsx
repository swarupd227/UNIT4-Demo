import { useQuery } from "@tanstack/react-query";
import { Check, CircleDashed, X } from "lucide-react";
import { usePersona } from "../lib/persona";
import { OUTCOMES, type Outcome } from "../lib/terms";
import { workbench } from "../lib/workbench";
import { CountUp, Panel, Screen } from "../ui/layout";
import { CodeBadge, Skeleton } from "../ui/primitives";

function minutes(seconds: number): string {
  if (seconds === 0) return "None logged";
  return seconds < 60 ? `${seconds} sec` : `${(seconds / 60).toFixed(1)} min`;
}

function outcomeLabel(outcome: string): string {
  return OUTCOMES[outcome as Outcome]?.label ?? outcome;
}

function Hero({ value, of, label, note }: { value: number; of?: number; label: string; note: string }) {
  return (
    <Panel>
      <div className="tnum text-[36px] leading-none font-semibold">
        <CountUp value={value} />
        {of !== undefined && <span className="text-[22px] font-medium text-ink-3"> of {of}</span>}
      </div>
      <div className="mt-2 text-[17px] font-medium">{label}</div>
      <div className="text-[15px] text-ink-3">{note}</div>
    </Panel>
  );
}

export function ScorecardScreen() {
  const { role } = usePersona();
  const { data } = useQuery({ queryKey: ["scorecard"], queryFn: () => workbench.scorecard(role) });
  if (!data) return <Skeleton className="m-5 h-96" />;
  const authored = data.artefacts.find((row) => row.source === "hand_authored");
  const max = Math.max(...data.stages.map((stage) => stage.seconds), 1);

  const measures: [string, string, string][] = [
    ["Assessment time", "From J2X", "Not measured here"],
    [
      "Reconciliation accuracy",
      data.reconciliation.run ? `${data.reconciliation.passed} of ${data.reconciliation.total} checks pass` : "Not run",
      "All known differences found",
    ],
    ["Validation run time", data.reconciliation.seconds ? `${data.reconciliation.seconds.toFixed(1)} sec` : "Not run", "Measured"],
    ["Defects", data.defects.tested ? `${data.defects.failed} of ${data.defects.tested} rebuilds failed first run` : "Not tested", "Measured"],
    [
      "Agent run time",
      authored ? "Not measured" : "Recorded run",
      authored ? `${authored.count} prepared analyses` : "From the recorded run",
    ],
    ["Full customer journey", "Pilot measure", "Not measured here"],
    ["Saving against baseline", "Not calculated", "No baseline available"],
  ];

  return (
    <Screen
      title="Results"
      lead="Measured on the sandbox dataset against expected results. Not a forecast for customer migrations."
      aside={<CodeBadge title="Computed from the database and the expected results" />}
    >
      <div className="grid grid-cols-3 gap-4">
        <Hero value={data.found} of={data.planted} label="Known issues found" note="Target: all 10" />
        <Hero value={data.false_items.count} label="False items raised" note={`Limit ${data.false_items.limit}: ${data.false_items.items.join(", ") || "none"}`} />
        <Hero value={data.decision_quality.matched} of={data.decision_quality.total} label="Decisions match expected results" note={`Missed: ${data.decision_quality.wrong.join(", ") || "none"}`} />
      </div>
      <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-4">
        <div className="space-y-4">
          <Panel title="Time logged by the workbench">
            <ul className="space-y-3">
              {data.stages.map((stage) => (
                <li key={stage.stage}>
                  <div className="flex justify-between text-[16px]">
                    <span>{stage.stage}</span>
                    <span className="tnum text-ink-2">{minutes(stage.seconds)}</span>
                  </div>
                  <div className="mt-1 h-2.5 rounded-sm bg-canvas">
                    <div
                      className="h-full rounded-sm bg-accent"
                      style={{ width: `${(stage.seconds / max) * 100}%` }}
                      title={`Consultant: ${minutes(stage.consultant_seconds)}`}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Consultant effort by case">
            <table className="w-full text-[16px]">
              <tbody className="divide-y divide-line">
                {data.cases.map((entry) => (
                  <tr key={entry.case}>
                    <th scope="row" className="py-2 text-left font-normal">{entry.case}</th>
                    <td className="tnum py-2 text-right text-ink-2">{minutes(entry.consultant_seconds)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
          <Panel title="Measures">
            <table className="w-full text-[16px]">
              <tbody className="divide-y divide-line">
                {measures.map(([label, value, note]) => (
                  <tr key={label}>
                    <th scope="row" className="py-2 pr-3 text-left font-normal">{label}</th>
                    <td className="tnum py-2 pr-3 font-medium">{value}</td>
                    <td className="py-2 text-right text-[14px] text-ink-3">{note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
          <Panel title="Customer sign-off">
            <ul className="space-y-1.5 text-[16px]">
              {[...data.signoff.conditions.map((c) => ({ label: c.label, passed: c.passed })),
                { label: "Pack generated", passed: data.signoff.generated },
                { label: "Signed by the customer", passed: data.signoff.signed }].map((condition) => (
                <li key={condition.label} className="flex items-center gap-2">
                  {condition.passed ? <Check size={18} className="text-ok" aria-hidden /> : <CircleDashed size={18} className="text-ink-3" aria-hidden />}
                  {condition.label}
                </li>
              ))}
            </ul>
          </Panel>
        </div>
        <Panel title="Known issues">
          <ol className="divide-y divide-line">
            {data.issues.map((issue) => (
              <li key={issue.issue_id} className="flex items-start gap-3 py-2 text-[16px]">
                {issue.found ? (
                  <Check size={20} className="mt-0.5 shrink-0 text-ok" aria-label="Found" />
                ) : (
                  <X size={20} className="mt-0.5 shrink-0 text-bad" aria-label="Not found yet" />
                )}
                <span className="tnum w-9 shrink-0 font-semibold">{issue.issue_id}</span>
                <span className="leading-6">{issue.planted}</span>
              </li>
            ))}
          </ol>
        </Panel>
      </div>
      <Panel
        title="Mapping memory"
        aside={
          <span className="tnum text-[15px] text-ink-2">
            {data.memory.precedents} precedents, {data.memory.approved} approved and {data.memory.rejected} rejected
            here
          </span>
        }
      >
        {data.memory.entries.length === 0 ? (
          <p className="text-[16px] text-ink-2">No decisions stored in this session yet.</p>
        ) : (
          <table className="w-full text-[15px]">
            <thead>
              <tr className="border-b border-line-strong text-left text-[13px] tracking-wide text-ink-3 uppercase">
                <th className="py-1.5 font-semibold">Item</th>
                <th className="py-1.5 font-semibold">Decision</th>
                <th className="py-1.5 font-semibold">Review</th>
                <th className="py-1.5 font-semibold">By</th>
                <th className="py-1.5 font-semibold">Next similar item starts at</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.memory.entries.map((entry) => (
                <tr key={entry.memory_id}>
                  <td className="tnum py-1.5 pr-3">{entry.item_id}</td>
                  <td className="py-1.5 pr-3">{outcomeLabel(entry.outcome)}</td>
                  <td className="py-1.5 pr-3 capitalize">{entry.review_status}</td>
                  <td className="py-1.5 pr-3">{entry.decided_by}</td>
                  <td className="tnum py-1.5">
                    {entry.next_outcome
                      ? `${outcomeLabel(entry.next_outcome)}, ${entry.next_confidence}% confidence`
                      : "No proposal yet"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </Screen>
  );
}
