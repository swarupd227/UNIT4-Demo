import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Check, Minus, X } from "lucide-react";
import { testsApi, type Attempt } from "../lib/api";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { CodeBadge, Skeleton } from "../ui/primitives";

function Mark({ passed, ran = true }: { passed: boolean; ran?: boolean }) {
  if (!ran) return <Minus size={18} className="text-ink-3" aria-label="Not run" />;
  return passed ? (
    <Check size={18} className="text-ok" aria-label="Passed" />
  ) : (
    <X size={18} className="text-bad" aria-label="Failed" />
  );
}

function Cells({ attempt }: { attempt: Attempt }) {
  const { conventions, expected_results: expected, faults, stability } = attempt.checks;
  return (
    <>
      <td className="py-2">
        <Mark passed={conventions.passed} />
      </td>
      <td className="py-2">
        <Mark passed={expected.passed} />
      </td>
      <td className="py-2">
        <span className="inline-flex items-center gap-2">
          <Mark passed={faults.passed} ran={faults.ran} />
          {faults.ran && (
            <span className="tnum text-[14px] text-ink-2">
              {faults.caught?.length ?? 0} of {faults.rule_faults?.length ?? 0}
            </span>
          )}
        </span>
      </td>
      <td className="py-2">
        <span className="inline-flex items-center gap-2">
          <Mark passed={stability.passed} ran={stability.ran} />
          {stability.ran && (
            <span className="tnum text-[14px] text-ink-2">
              {stability.passed_runs} of {stability.runs}
            </span>
          )}
        </span>
      </td>
    </>
  );
}

export function ProofScreen() {
  const { data, error } = useQuery({ queryKey: ["tests"], queryFn: testsApi.tests });
  const rows = data?.tests.flatMap((t) => t.attempts.map((a) => ({ test: t, attempt: a }))) ?? [];
  const rejected = rows.filter((r) => !r.attempt.accepted);
  return (
    <Screen
      title="Proof"
      lead="Every test is proved four ways before an engineer sees it."
      next="flaky"
      aside={<CodeBadge title="Every check is plain code over lab runs and the validator's results." />}
    >
      {error && <ErrorNote message={(error as Error).message} />}
      {!data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <Panel>
            <div className="flex items-center gap-6">
              <div className="tnum text-[28px] font-semibold">
                {data.coverage_before.critical_covered} of {data.coverage_before.critical_rules} (
                {data.coverage_before.percent}%)
              </div>
              <ArrowRight size={24} className="text-ink-3" aria-hidden />
              <div className="tnum text-[28px] font-semibold text-accent">
                {data.coverage_after.critical_covered} of {data.coverage_after.critical_rules} (
                {data.coverage_after.percent}%)
              </div>
              <p className="text-[15px] text-ink-2">
                critical rules covered with the accepted tests
                {data.coverage_after.newly_covered.length > 0 &&
                  `: ${data.coverage_after.newly_covered.join(" and ")} are now covered`}
                .
              </p>
            </div>
          </Panel>
          <Panel title="Checks">
            <table className="w-full text-left text-[15px]">
              <thead className="text-[13px] text-ink-3">
                <tr className="border-b border-line">
                  <th className="py-2 font-semibold">Test</th>
                  <th className="py-2 font-semibold">Attempt</th>
                  <th className="py-2 font-semibold">Conventions</th>
                  <th className="py-2 font-semibold">Independent expected results</th>
                  <th className="py-2 font-semibold">Seeded faults caught</th>
                  <th className="py-2 font-semibold">Stable over 20 runs</th>
                  <th className="py-2 font-semibold">Result</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ test, attempt }) => (
                  <tr key={`${test.id}-${attempt.attempt}`} className="border-b border-line last:border-0">
                    <td className="py-2 pr-3">
                      <div>{attempt.generated.title.replace(" @critical", "")}</div>
                      <div className="text-[13px] text-ink-3">
                        {test.kind} {test.ref}
                      </div>
                    </td>
                    <td className="tnum py-2">{attempt.attempt}</td>
                    <Cells attempt={attempt} />
                    <td className="py-2">
                      {attempt.accepted ? (
                        <span className="text-[14px] font-semibold text-ok">Accepted</span>
                      ) : (
                        <span className="text-[14px] font-semibold text-bad">Rejected</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
          {rejected.length > 0 && (
            <Panel title="Why tests were rejected">
              <ul className="space-y-3">
                {rejected.map(({ test, attempt }) => (
                  <li key={`${test.id}-${attempt.attempt}`}>
                    <div className="font-semibold">
                      {attempt.generated.title.replace(" @critical", "")}, attempt {attempt.attempt}
                    </div>
                    <ul className="list-disc pl-5 text-[15px] text-ink-2">
                      {attempt.problems.map((problem) => (
                        <li key={problem}>{problem}</li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </>
      )}
    </Screen>
  );
}
