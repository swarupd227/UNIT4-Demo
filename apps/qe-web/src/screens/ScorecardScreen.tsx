import { useQuery } from "@tanstack/react-query";
import { Check, X } from "lucide-react";
import type { ReactNode } from "react";
import { evidenceApi } from "../lib/api";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { CodeBadge, Skeleton, SourceBadge } from "../ui/primitives";

function Measure({
  name,
  before,
  after,
  note,
}: {
  name: string;
  before: ReactNode;
  after: ReactNode;
  note: ReactNode;
}) {
  return (
    <tr className="border-b border-line align-top last:border-0">
      <td className="py-3 pr-4 font-semibold">{name}</td>
      <td className="tnum py-3 pr-4">{before}</td>
      <td className="tnum py-3 pr-4 font-semibold text-accent">{after}</td>
      <td className="py-3 text-[14px] text-ink-2">{note}</td>
    </tr>
  );
}

export function ScorecardScreen() {
  const { data, error } = useQuery({
    queryKey: ["scorecard"],
    queryFn: evidenceApi.scorecard,
  });
  return (
    <Screen
      title="Scorecard"
      lead="The RFP's measures for this area, before and after, measured on this module."
      aside={
        <CodeBadge title="Every figure is calculated by plain code from lab runs, checks and recorded decisions." />
      }
    >
      {error && <ErrorNote message={(error as Error).message} />}
      {!data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <Panel title="Measures">
            <table className="w-full text-left text-[15px]">
              <thead className="text-[13px] text-ink-3">
                <tr className="border-b border-line">
                  <th className="py-2 font-semibold">Measure</th>
                  <th className="py-2 font-semibold">Before</th>
                  <th className="py-2 font-semibold">After</th>
                  <th className="py-2 font-semibold">How it is measured</th>
                </tr>
              </thead>
              <tbody>
                <Measure
                  name="Meaningful coverage"
                  before={`${data.coverage.before.critical_covered} of ${data.coverage.before.critical_rules} (${data.coverage.before.percent}%)`}
                  after={`${data.coverage.after.critical_covered} of ${data.coverage.after.critical_rules} (${data.coverage.after.percent}%)`}
                  note={`Critical rules whose tests catch at least ${data.coverage.gate_percent}% of their seeded faults. ${data.coverage.newly_covered.join(" and ")} are now covered; the gate is ${data.coverage.gate_percent}%.`}
                />
                <Measure
                  name="Defects detected"
                  before={`${data.defects_detected.caught_before} of ${data.defects_detected.faults}`}
                  after={`${data.defects_detected.caught_after} of ${data.defects_detected.faults}`}
                  note={`Seeded faults the suite catches, each confirmed on five fresh databases.${data.defects_detected.t1_t2_caught ? " Every rounding and write-down approval fault is caught." : ""}`}
                />
                <Measure
                  name="Test reliability"
                  before={data.reliability.before
                    .map((t) => `${t.test.slice(0, 5)} failed ${t.failed} of ${t.runs}`)
                    .join(", ")}
                  after={`${data.reliability.after_failures} failures in ${data.reliability.after_runs} runs of ${data.reliability.after_tests} tests`}
                  note="Repeat runs of the unchanged module. Every failure there is flakiness."
                />
                <Measure
                  name="Manual regression effort"
                  before={`${data.manual_regression.total_minutes} min for ${data.manual_regression.cases} cases`}
                  after={`${data.manual_regression.total_minutes - data.manual_regression.automated_minutes} min by hand, plus a ${Math.round(data.manual_regression.suite_run_seconds ?? 0)} s automated run`}
                  note={`${data.manual_regression.automated_cases.length} cases are now automated or retired as duplicates. ${data.manual_regression.assumption} Automated time is measured.`}
                />
                <Measure
                  name="Maintenance cost"
                  before={`${data.maintenance.broken_tests} tests broken by a screen label change`}
                  after={`${Math.round(data.maintenance.machine_seconds ?? 0)} s to find, repair and prove`}
                  note={
                    data.maintenance.approved
                      ? `Repair approved by ${data.maintenance.approved.reviewed_by}.`
                      : "Lab run, repair and proving run, measured. The engineer's review is extra."
                  }
                />
                <Measure
                  name="Escaped defects"
                  before="Not measured"
                  after="Not measured"
                  note={data.escaped_defects.note}
                />
              </tbody>
            </table>
          </Panel>
          <div className="grid grid-cols-[minmax(0,1fr)_420px] items-start gap-5">
            <Panel title="Planted issues" aside={<SourceBadge>Answer key written before any agent ran</SourceBadge>}>
              <ul className="space-y-2">
                {data.planted.map((p) => (
                  <li key={p.id} className="flex items-start gap-3">
                    {p.handled ? (
                      <Check size={18} className="mt-0.5 shrink-0 text-ok" aria-label="Handled as expected" />
                    ) : (
                      <X size={18} className="mt-0.5 shrink-0 text-bad" aria-label="Not handled" />
                    )}
                    <span className="text-[15px]">
                      <span className="font-mono text-[13px] text-ink-3">{p.id}</span> {p.what}.{" "}
                      <span className="text-ink-2">{p.how}.</span>
                    </span>
                  </li>
                ))}
              </ul>
            </Panel>
            <Panel title="Engineer review">
              <p className="text-[15px]">
                {data.engineer.accepted} of {data.engineer.items} items approved, {data.engineer.rejected} rejected.
              </p>
              <p className="mt-2 text-[15px] text-ink-2">
                {data.engineer.merged
                  ? `Merged by ${data.engineer.merged.merged_by} as ${data.engineer.merged.merge_commit.slice(0, 7)}.`
                  : "Not merged yet."}
              </p>
              <p className="mt-2 text-[14px] text-ink-2">
                No productivity multiple is claimed: it would depend on an assumed baseline.
              </p>
            </Panel>
          </div>
        </>
      )}
    </Screen>
  );
}
