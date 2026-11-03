import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { CountUp, ErrorNote, Panel, Screen } from "../ui/layout";
import { CodeBadge, Skeleton } from "../ui/primitives";

function Figure({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-xl bg-surface-2 p-4">
      <div className="tnum text-[32px] leading-10 font-semibold">
        <CountUp value={value} />
      </div>
      <div className="text-[15px] text-ink-2">{label}</div>
    </div>
  );
}

export function AreaScreen() {
  const { data, error } = useQuery({ queryKey: ["area"], queryFn: api.area });
  return (
    <Screen title={data?.area ?? "Project billing"} lead="What exists today in this functional area, before any work." next="coverage">
      {error && <ErrorNote message={(error as Error).message} />}
      <Panel title="Estate" aside={<CodeBadge title="Counted by plain code from the module's repository and exports." />}>
        {data ? (
          <div className="grid grid-cols-3 gap-3 xl:grid-cols-6">
            <Figure value={data.rules} label={`business rules, ${data.critical_rules} critical`} />
            <Figure value={data.manual_cases} label="manual test cases" />
            <Figure value={data.automated_tests} label="automated tests" />
            <Figure value={data.defects} label="defects in three years" />
            <Figure value={data.code_lines} label={`lines of code in ${data.code_files} files`} />
            <Figure value={data.help_pages} label="help pages" />
          </div>
        ) : (
          <Skeleton className="h-24 w-full" />
        )}
      </Panel>
      {data && (
        <Panel title="Coverage gate">
          <p className="text-[17px]">
            A domain moves into MOSAIC when {data.gate_percent}% of its critical rules are covered by tests that
            catch the seeded faults for those rules.
          </p>
        </Panel>
      )}
    </Screen>
  );
}
