import { useQuery } from "@tanstack/react-query";
import { Check, X } from "lucide-react";
import { useState } from "react";
import { testsApi, type Attempt, type GeneratedTest, type IntakeEntry } from "../lib/api";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { AiBadge, CodeBadge, SectionLabel, Skeleton, SourceBadge } from "../ui/primitives";

const OUTCOME: Record<IntakeEntry["outcome"], { label: string; tone: string }> = {
  ready: { label: "Ready to automate", tone: "text-ok" },
  merged: { label: "Merged", tone: "text-ink-2" },
  already_automated: { label: "Already automated", tone: "text-ink-2" },
  to_person: { label: "Sent to a person", tone: "text-bad" },
  needs_expected_result: { label: "Expected result needed", tone: "text-warn" },
  review: { label: "Not reviewed yet", tone: "text-ink-3" },
};

function IntakeRow({ entry }: { entry: IntakeEntry }) {
  const outcome = OUTCOME[entry.outcome];
  const problem = entry.review?.steps.find((s) => s.verdict !== "agrees");
  return (
    <li className="rounded-lg px-2 py-2 hover:bg-surface-2">
      <div className="flex items-start justify-between gap-3">
        <span className="text-[15px]">
          <span className="font-mono text-[13px] text-ink-3">{entry.case}</span> {entry.title}
        </span>
        <span className={`shrink-0 text-[13px] font-semibold ${outcome.tone}`}>{outcome.label}</span>
      </div>
      {entry.outcome === "merged" && (
        <p className="text-[14px] text-ink-2">Same steps and results as case {entry.into}. One test serves both.</p>
      )}
      {entry.outcome === "already_automated" && (
        <p className="text-[14px] text-ink-2">
          {entry.by} already checks this with the same data. Cases {entry.duplicates.join(" and ")} can be retired.
        </p>
      )}
      {problem && (
        <p className="text-[14px] text-ink-2">
          Step {problem.step}: {problem.expected}
        </p>
      )}
    </li>
  );
}

function statusOf(test: GeneratedTest): { label: string; tone: string } {
  if (test.accepted) return { label: "Passed all four checks", tone: "text-ok" };
  const last = test.attempts[test.attempts.length - 1];
  if (!last.checks.faults.ran && last.ready_for_lab) return { label: "Waiting for the lab", tone: "text-ink-3" };
  return { label: "Rejected", tone: "text-bad" };
}

function Validation({ attempt }: { attempt: Attempt }) {
  return (
    <table className="w-full text-left text-[14px]">
      <thead className="text-[13px] text-ink-3">
        <tr className="border-b border-line">
          <th className="py-1.5 font-semibold">Check</th>
          <th className="py-1.5 font-semibold">The test expects</th>
          <th className="py-1.5 font-semibold">The documents give</th>
          <th className="py-1.5" />
        </tr>
      </thead>
      <tbody>
        {attempt.validation.map((v) => (
          <tr key={v.check} className="border-b border-line align-top last:border-0">
            <td className="py-1.5 pr-3">{v.check}</td>
            <td className="py-1.5 pr-3 font-mono text-[13px]">{v.asserted}</td>
            <td className="py-1.5 pr-3">
              <span className="font-mono text-[13px]">{v.expected}</span>
              {v.basis[0] && <div className="text-[12px] text-ink-3">{v.basis.map((b) => b.document).join(", ")}</div>}
            </td>
            <td className="py-1.5">
              {v.agrees ? (
                <Check size={17} className="text-ok" aria-label="Agrees" />
              ) : (
                <X size={17} className="text-bad" aria-label="Disagrees" />
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TestDetail({ test }: { test: GeneratedTest }) {
  const attempt = test.attempts[test.attempts.length - 1];
  return (
    <div className="space-y-5">
      <div>
        <div className="text-[13px] font-semibold text-ink-3">
          {test.kind} {test.ref} · {test.rule} · attempt {attempt.attempt}
        </div>
        <h3 className="text-[19px] font-semibold">{test.title}</h3>
        <div className="mt-1 font-mono text-[13px] text-ink-3">{attempt.generated.path}</div>
      </div>
      <div>
        <SectionLabel aside={<AiBadge source={attempt.agents.generator.source} />}>Test data</SectionLabel>
        <p className="text-[15px]">
          <span className="font-mono text-[13px]">
            {attempt.generated.data.group}.{attempt.generated.data.key}
          </span>{" "}
          = {attempt.generated.data.value}. {attempt.generated.data_choice}
        </p>
      </div>
      <div>
        <SectionLabel>Code</SectionLabel>
        <pre className="scroll-quiet max-h-[420px] overflow-auto rounded-lg bg-spine p-4 font-mono text-[13px] leading-5 text-on-spine">
          {attempt.generated.code}
        </pre>
      </div>
      <div>
        <SectionLabel aside={<AiBadge source={attempt.agents.validator.source} />}>
          Expected results worked out without the test
        </SectionLabel>
        <Validation attempt={attempt} />
      </div>
    </div>
  );
}

export function GeneratedTestsScreen() {
  const { data, error } = useQuery({ queryKey: ["tests"], queryFn: testsApi.tests });
  const [selected, setSelected] = useState<string | null>(null);
  const test = data?.tests.find((t) => t.id === selected) ?? data?.tests[0];
  return (
    <Screen
      title="Generated tests"
      lead="Manual cases, defects and approved context turned into tests in the suite's own conventions."
      next="proof"
    >
      {error && <ErrorNote message={(error as Error).message} />}
      {!data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <div className="grid grid-cols-[460px_minmax(0,1fr)] items-start gap-5">
          <div className="space-y-5">
            <Panel
              title="Manual case intake"
              aside={<SourceBadge>Batch chosen by {data.batch.chosen_by}</SourceBadge>}
            >
              <ul className="space-y-0.5">
                {data.intake.map((entry) => (
                  <IntakeRow key={entry.case} entry={entry} />
                ))}
              </ul>
              <div className="mt-3 flex gap-2">
                <CodeBadge title="Duplicates and existing automation are found by plain code." />
                <AiBadge source={data.intake.find((e) => e.agent)?.agent?.source} />
              </div>
            </Panel>
            <Panel title="Tests">
              <ul className="space-y-0.5">
                {data.tests.map((t) => {
                  const status = statusOf(t);
                  return (
                    <li key={t.id}>
                      <button
                        type="button"
                        onClick={() => setSelected(t.id)}
                        className={`w-full rounded-lg px-2 py-2 text-left ${t.id === test?.id ? "bg-selected" : "hover:bg-surface-2"}`}
                      >
                        <div className="text-[15px]">{t.title.replace(" @critical", "")}</div>
                        <div className="flex justify-between gap-3 text-[13px]">
                          <span className="text-ink-3">
                            {t.kind} {t.ref}
                            {t.attempts.length > 1 && `, ${t.attempts.length} attempts`}
                          </span>
                          <span className={`font-semibold ${status.tone}`}>{status.label}</span>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </Panel>
          </div>
          <Panel>{test ? <TestDetail test={test} /> : <p>No tests have been generated yet.</p>}</Panel>
        </div>
      )}
    </Screen>
  );
}
