import { useQuery } from "@tanstack/react-query";
import { Check, Minus, X } from "lucide-react";
import { useState } from "react";
import { api, type AgentRun, type RuleCoverage } from "../lib/api";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { AiBadge, CodeBadge, SectionLabel, Skeleton } from "../ui/primitives";

function GateBar({ percent, gate }: { percent: number; gate: number }) {
  return (
    <div className="relative h-3 rounded-full bg-line" aria-hidden>
      <div className="h-3 rounded-full bg-accent" style={{ width: `${percent}%` }} />
      <div className="absolute -top-1.5 h-6 w-0.5 bg-ink" style={{ left: `${gate}%` }} />
    </div>
  );
}

function ScoreBar({ row, gate }: { row: RuleCoverage; gate: number }) {
  if (row.score === null) return <span className="text-ink-3">No seeded faults</span>;
  const tone = row.covered ? "bg-ok" : row.score > 0 ? "bg-warn" : "bg-bad";
  return (
    <div className="flex items-center gap-3">
      <div className="relative h-2 w-28 rounded-full bg-line" aria-hidden>
        <div className={`h-2 rounded-full ${tone}`} style={{ width: `${Math.max(row.score, 3)}%` }} />
        <div className="absolute -top-1 h-4 w-px bg-ink-3" style={{ left: `${gate}%` }} />
      </div>
      <span className="tnum text-[15px]">
        {row.caught} of {row.faults.length}
      </span>
    </div>
  );
}

function Status({ row }: { row: RuleCoverage }) {
  if (row.covered) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-ok-soft px-2 py-0.5 text-[13px] font-semibold text-ok">
        <Check size={14} aria-hidden /> Covered
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-bad-soft px-2 py-0.5 text-[13px] font-semibold text-bad">
      {row.tests.length ? <Minus size={14} aria-hidden /> : <X size={14} aria-hidden />}
      {row.tests.length ? "Weak test" : "No test"}
    </span>
  );
}

function agentBadge(run: AgentRun) {
  return run.status === "ok" ? <AiBadge source={run.source} /> : <span className="text-ink-3">Not analysed</span>;
}

function RuleDetail({ row }: { row: RuleCoverage }) {
  return (
    <div className="space-y-5">
      <div>
        <div className="text-[13px] font-semibold text-ink-3">{row.rule}</div>
        <h3 className="text-[19px] font-semibold">{row.title}</h3>
      </div>
      <div>
        <SectionLabel>Automated tests</SectionLabel>
        {row.tests.length ? (
          <ul className="space-y-2">
            {row.tests.map((test) => (
              <li key={test.title} className="rounded-lg bg-surface-2 p-3">
                <div className="text-[15px]">{test.title}</div>
                <div className="mt-0.5 font-mono text-[13px] text-ink-3">{test.file}</div>
                {test.flaky && (
                  <div className="mt-1 text-[13px] font-semibold text-warn">
                    Flaky: failed {test.flaky.failed} of {test.flaky.runs} runs on the unchanged module
                  </div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-ink-2">No automated test names this rule.</p>
        )}
      </div>
      <div>
        <SectionLabel>Seeded faults</SectionLabel>
        <ul className="space-y-1.5">
          {row.faults.map((fault) => (
            <li key={fault.id} className="flex items-start gap-2 text-[15px]">
              {fault.caught ? (
                <Check size={17} className="mt-0.5 shrink-0 text-ok" aria-label="Caught" />
              ) : (
                <X size={17} className="mt-0.5 shrink-0 text-bad" aria-label="Missed" />
              )}
              <span>
                <span className="font-mono text-[13px] text-ink-3">{fault.id}</span> {fault.description}
              </span>
            </li>
          ))}
        </ul>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <SectionLabel>Manual cases</SectionLabel>
          <p className="tnum text-[15px]">{row.manual_cases.length ? row.manual_cases.join(", ") : "None"}</p>
        </div>
        <div>
          <SectionLabel>Defects</SectionLabel>
          <p className="tnum text-[15px]">{row.defects.length || "None"}</p>
        </div>
      </div>
    </div>
  );
}

export function CoverageScreen() {
  const { data, error } = useQuery({ queryKey: ["coverage"], queryFn: api.coverage });
  const [selected, setSelected] = useState("BR-04");
  const row = data?.rules.find((entry) => entry.rule === selected);
  return (
    <Screen
      title="Coverage"
      lead="Which business rules the existing tests protect, measured by the faults they catch."
      next="context"
    >
      {error && <ErrorNote message={(error as Error).message} />}
      {!data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <Panel>
            <div className="flex items-end justify-between gap-6">
              <div>
                <div className="tnum text-[32px] leading-10 font-semibold">
                  {data.summary.critical_covered} of {data.summary.critical_rules} critical rules covered (
                  {data.summary.percent}%)
                </div>
                <p className="text-[15px] text-ink-2">
                  The gate is {data.gate_percent}%. A rule is covered when its tests catch at least {data.gate_percent}%
                  of its seeded faults, each catch confirmed on five fresh databases.
                </p>
              </div>
              <CodeBadge title="Calculated by plain code from the lab's fault check." />
            </div>
            <div className="mt-4">
              <GateBar percent={data.summary.percent} gate={data.gate_percent} />
            </div>
          </Panel>
          <div className="grid grid-cols-[minmax(0,1fr)_420px] gap-5">
            <Panel title="Business rules">
              <table className="w-full text-left text-[15px]">
                <thead className="text-[13px] text-ink-3">
                  <tr className="border-b border-line">
                    <th className="py-2 font-semibold">Rule</th>
                    <th className="py-2 font-semibold">Tests</th>
                    <th className="py-2 font-semibold">Faults caught</th>
                    <th className="py-2 font-semibold">
                      <span className="inline-flex items-center gap-2">Manual cases {agentBadge(data.case_mapping)}</span>
                    </th>
                    <th className="py-2 font-semibold">
                      <span className="inline-flex items-center gap-2">Defects {agentBadge(data.defect_mapping)}</span>
                    </th>
                    <th className="py-2 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.rules.map((entry) => (
                    <tr
                      key={entry.rule}
                      onClick={() => setSelected(entry.rule)}
                      className={`cursor-pointer border-b border-line last:border-0 ${
                        entry.rule === selected ? "bg-selected" : "hover:bg-surface-2"
                      }`}
                    >
                      <td className="py-2.5 pr-3">
                        <button type="button" className="text-left" onClick={() => setSelected(entry.rule)}>
                          <span className="font-mono text-[13px] text-ink-3">{entry.rule}</span>{" "}
                          <span className={entry.critical ? "font-semibold" : ""}>{entry.title}</span>
                          {entry.critical && <span className="ml-2 text-[12px] font-semibold text-accent">Critical</span>}
                        </button>
                      </td>
                      <td className="tnum py-2.5">
                        {entry.tests.length}
                        {entry.tests.some((test) => test.flaky) && (
                          <span className="ml-2 text-[12px] font-semibold text-warn">Flaky</span>
                        )}
                      </td>
                      <td className="py-2.5">
                        <ScoreBar row={entry} gate={data.gate_percent} />
                      </td>
                      <td className="tnum py-2.5">{entry.manual_cases.length}</td>
                      <td className="tnum py-2.5">{entry.defects.length}</td>
                      <td className="py-2.5">
                        <Status row={entry} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
            <Panel>{row && <RuleDetail row={row} />}</Panel>
          </div>
        </>
      )}
    </Screen>
  );
}
