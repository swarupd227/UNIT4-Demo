import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { evidenceApi } from "../lib/api";
import { useToast } from "../lib/toast";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { Button, CodeBadge, Skeleton } from "../ui/primitives";

const WAITING = {
  to_person: "Conflicts with the documents; a person decides which is right",
  needs_expected_result: "Needs a concrete expected result from its author",
} as Record<string, string>;

async function downloadPack() {
  const body = await evidenceApi.pack();
  const url = URL.createObjectURL(new Blob([JSON.stringify(body, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "project-billing-evidence-pack.json";
  link.click();
  URL.revokeObjectURL(url);
}

export function GapsScreen() {
  const { data, error } = useQuery({
    queryKey: ["gaps"],
    queryFn: evidenceApi.gaps,
  });
  const notify = useToast();
  return (
    <Screen
      title="Gaps"
      lead="What still stands between this area and the coverage gate, ranked by risk."
      next="scorecard"
      aside={
        <Button onClick={() => downloadPack().catch((e: Error) => notify(e.message, "bad"))}>
          <Download size={17} aria-hidden /> Evidence pack
        </Button>
      }
    >
      {error && <ErrorNote message={(error as Error).message} />}
      {!data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <Panel>
            <div className="flex items-center justify-between gap-6">
              <p className="text-[17px]">
                <span className="tnum text-[28px] font-semibold">
                  {data.covered} of {data.critical_rules} ({data.percent}%)
                </span>{" "}
                critical rules are covered. The gate is {data.gate_percent}%, so{" "}
                {Math.ceil((data.gate_percent / 100) * data.critical_rules) - data.covered} more must be covered before
                this area can move.
              </p>
              <CodeBadge title="Ranked by plain code from the coverage map and the defect history." />
            </div>
          </Panel>
          <Panel title="Rules below the gate">
            <table className="w-full text-left text-[15px]">
              <thead className="text-[13px] text-ink-3">
                <tr className="border-b border-line">
                  <th className="py-2 font-semibold">Rule</th>
                  <th className="py-2 font-semibold">Faults caught</th>
                  <th className="py-2 font-semibold">Defects without an automated test</th>
                  <th className="py-2 font-semibold">Not yet caught</th>
                  <th className="py-2 font-semibold">Manual cases to start from</th>
                </tr>
              </thead>
              <tbody>
                {data.below_gate.map((r) => (
                  <tr key={r.rule} className="border-b border-line align-top last:border-0">
                    <td className="py-2 pr-3">
                      <span className="font-mono text-[13px] text-ink-3">{r.rule}</span>{" "}
                      <span className={r.critical ? "font-semibold" : ""}>{r.title}</span>
                      {r.critical && <span className="ml-2 text-[12px] font-semibold text-accent">Critical</span>}
                    </td>
                    <td className="tnum py-2">{r.score ?? 0}%</td>
                    <td className="tnum py-2">{r.untested_defects}</td>
                    <td className="py-2 pr-3 text-[14px]">
                      {r.missed_faults.map((f) => (
                        <div key={f.id}>
                          <span className="font-mono text-[12px] text-ink-3">{f.id}</span> {f.description}
                        </div>
                      ))}
                    </td>
                    <td className="tnum py-2 text-[14px]">{r.manual_cases.join(", ") || "None"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
          <div className="grid grid-cols-2 items-start gap-5">
            <Panel title="Waiting on people">
              <ul className="space-y-2">
                {data.waiting_on_people.map((w) => (
                  <li key={w.case}>
                    <div className="text-[15px]">
                      <span className="font-mono text-[13px] text-ink-3">{w.case}</span> {w.title}
                    </div>
                    <div className="text-[14px] text-ink-2">{WAITING[w.outcome] ?? w.outcome}</div>
                  </li>
                ))}
              </ul>
            </Panel>
            <Panel title="Dead code: no test needed" aside={<CodeBadge />}>
              <ul className="space-y-2">
                {data.dead_code.map((d) => (
                  <li key={d.name}>
                    <div className="font-mono text-[13px]">{d.name}</div>
                    <div className="text-[14px] text-ink-2">{d.reason}</div>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[14px] text-ink-2">Removing it is a code change for the owning team.</p>
            </Panel>
          </div>
        </>
      )}
    </Screen>
  );
}
