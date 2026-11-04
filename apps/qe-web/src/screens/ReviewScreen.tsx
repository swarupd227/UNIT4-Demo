import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, GitMerge, ShieldCheck, X } from "lucide-react";
import { useState } from "react";
import { evidenceApi, type PrItem, type PullRequest } from "../lib/api";
import { formatTime } from "../lib/format";
import { usePersona } from "../lib/persona";
import { useToast } from "../lib/toast";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { AiBadge, Button, CodeBadge, SectionLabel, Skeleton } from "../ui/primitives";

const SOURCE = {
  manual_case: "Manual case",
  defect: "Defect",
  hidden_rule: "Hidden rule",
  flaky: "Flaky test",
} as Record<string, string>;

function RunStrip({ runs }: { runs: PrItem["runs"] }) {
  const passed = runs.filter((r) => r.status === "passed").length;
  return (
    <div>
      <div className="flex gap-0.5" aria-label={`${passed} of ${runs.length} runs passed`}>
        {runs.map((r, i) => (
          <span
            key={i}
            title={`Run ${i + 1}: ${r.status}, ${(r.ms / 1000).toFixed(1)} s`}
            className={`h-5 w-3 rounded-sm ${r.status === "passed" ? "bg-ok" : "bg-bad"}`}
          />
        ))}
      </div>
      <p className="mt-1 text-[14px] text-ink-2">
        Passed {passed} of {runs.length} runs of the whole suite, each on a fresh database
      </p>
    </div>
  );
}

function Evidence({ item, pr }: { item: PrItem; pr: PullRequest }) {
  const files = pr.files.filter((f) => item.files.includes(f.path));
  return (
    <div className="space-y-5">
      <div>
        <div className="text-[13px] font-semibold text-ink-3">
          {SOURCE[item.source.kind] ?? item.source.kind} {item.source.ref} · {item.rule}
          {item.attempts && item.attempts > 1 && ` · accepted on attempt ${item.attempts}`}
        </div>
        <h3 className="text-[19px] font-semibold">{item.title.replace(" @critical", "")}</h3>
      </div>
      {item.kind === "test" && item.validation && item.faults && (
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg bg-surface-2 p-3">
            <SectionLabel>Expected results</SectionLabel>
            <p className="text-[15px]">
              {item.validation.filter((v) => v.agrees).length} of {item.validation.length} values agree with the
              validator, which never saw the test
            </p>
          </div>
          <div className="rounded-lg bg-surface-2 p-3">
            <SectionLabel>Seeded faults</SectionLabel>
            <p className="text-[15px]">
              Catches {item.faults.caught?.join(", ")} of {item.rule}'s {item.faults.rule_faults?.length} faults
              {item.faults.required?.length
                ? `, including ${item.faults.required.join(", ")}, which puts the defect back`
                : ""}
            </p>
          </div>
          <div className="rounded-lg bg-surface-2 p-3">
            <SectionLabel>Conventions</SectionLabel>
            <p className="text-[15px]">Follows the suite's fixtures, page objects, naming and data ownership</p>
          </div>
        </div>
      )}
      {item.kind === "flaky_fix" && item.before && (
        <div className="rounded-lg bg-surface-2 p-3 text-[15px]">
          <SectionLabel>Flaky before the fix</SectionLabel>
          Failed {item.before.failed} of {item.before.runs} runs of the unchanged module. {item.fix_summary}
        </div>
      )}
      <div>
        <SectionLabel aside={<CodeBadge title="Lab runs after the change, each on a fresh database." />}>
          Run record
        </SectionLabel>
        <RunStrip runs={item.runs} />
      </div>
      {files.map((f) => (
        <div key={f.path}>
          <SectionLabel>
            {f.status === "added" ? "Added" : "Changed"} {f.path}
          </SectionLabel>
          <pre
            tabIndex={0}
            aria-label={`Contents of ${f.path}`}
            className="scroll-quiet max-h-[340px] overflow-auto rounded-lg bg-spine p-4 font-mono text-[13px] leading-5 text-on-spine"
          >
            {f.content}
          </pre>
        </div>
      ))}
    </div>
  );
}

function Decide({ item, merged }: { item: PrItem; merged: boolean }) {
  const { role } = usePersona();
  const notify = useToast();
  const client = useQueryClient();
  const [note, setNote] = useState("");
  const [rejecting, setRejecting] = useState(false);
  const decide = useMutation({
    mutationFn: (decision: "approved" | "rejected") => evidenceApi.decide(item.item_id, role, decision, note),
    onSuccess: (_, decision) => {
      notify(`${item.item_id} ${decision}`);
      setRejecting(false);
      setNote("");
      void client.invalidateQueries({ queryKey: ["review"] });
    },
    onError: (error) => notify((error as Error).message, "bad"),
  });
  if (item.decision) {
    const ok = item.decision.decision === "approved";
    return (
      <span className={`text-[14px] font-semibold ${ok ? "text-ok" : "text-bad"}`}>
        {ok ? "Approved" : "Rejected"} by {item.decision.reviewed_by}, {formatTime(item.decision.reviewed_at)}
      </span>
    );
  }
  if (merged) return null;
  if (role !== "engineer") return <span className="text-[14px] text-ink-2">An engineer decides on each test</span>;
  if (rejecting) {
    return (
      <div className="flex items-center gap-2">
        <label className="sr-only" htmlFor="reject-reason">
          Reason
        </label>
        <input
          id="reject-reason"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Why it is rejected"
          className="h-11 w-72 rounded-lg border border-line-strong bg-surface px-3 text-[15px]"
        />
        <Button onClick={() => setRejecting(false)}>Cancel</Button>
        <Button variant="primary" disabled={!note.trim() || decide.isPending} onClick={() => decide.mutate("rejected")}>
          Reject
        </Button>
      </div>
    );
  }
  return (
    <div className="flex gap-2">
      <Button onClick={() => setRejecting(true)}>Reject</Button>
      <Button variant="primary" disabled={decide.isPending} onClick={() => decide.mutate("approved")}>
        Approve
      </Button>
    </div>
  );
}

function Merge({ pr }: { pr: PullRequest }) {
  const { role } = usePersona();
  const notify = useToast();
  const client = useQueryClient();
  const merge = useMutation({
    mutationFn: () => evidenceApi.merge(role),
    onSuccess: (result) => {
      notify(`Merged as ${result.merge_commit.slice(0, 7)}`);
      void client.invalidateQueries();
    },
    onError: (error) => notify((error as Error).message, "bad"),
  });
  if (pr.merged) {
    return (
      <div className="flex items-center gap-2 text-[15px] font-semibold text-ok">
        <GitMerge size={18} aria-hidden /> Merged by {pr.merged.merged_by}, {formatTime(pr.merged.merged_at)}, as{" "}
        <span className="font-mono">{pr.merged.merge_commit.slice(0, 7)}</span>
      </div>
    );
  }
  const undecided = pr.items.filter((i) => !i.decision).length;
  return (
    <Button
      variant="primary"
      disabled={role !== "engineer" || undecided > 0 || merge.isPending}
      onClick={() => merge.mutate()}
      title={undecided ? `Decide on ${undecided} more first` : undefined}
    >
      <GitMerge size={17} aria-hidden /> {undecided ? `Merge (${undecided} to decide)` : "Merge approved items"}
    </Button>
  );
}

export function ReviewScreen() {
  const { data, error } = useQuery({
    queryKey: ["review"],
    queryFn: evidenceApi.review,
  });
  const [selected, setSelected] = useState<string | null>(null);
  const item = data?.items.find((i) => i.item_id === selected) ?? data?.items[0];
  return (
    <Screen
      title="Pull request"
      lead="An engineer accepts each test with all its evidence. Release controls do not change."
      next="gaps"
      aside={data && <Merge pr={data} />}
    >
      {error && <ErrorNote message={(error as Error).message} />}
      {!data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <Panel>
            <div className="flex items-start justify-between gap-6">
              <div>
                <div className="font-mono text-[13px] text-ink-3">
                  {data.id} · {data.branch} → main
                </div>
                <h2 className="text-[20px] font-semibold">{data.title}</h2>
                <p className="text-[15px] text-ink-2">
                  Opened by {data.author}. {data.items.filter((i) => i.kind === "test").length} new tests and{" "}
                  {data.items.filter((i) => i.kind === "flaky_fix").length} flaky-test fixes
                  {data.merged ? "" : `, ${data.files.length} files`}.
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2 rounded-lg bg-accent-soft px-3 py-2 text-[14px] font-semibold text-accent">
                <ShieldCheck size={17} aria-hidden />
                {data.release_controls_unchanged
                  ? `Release controls unchanged: only tests/e2e changes, ${data.pipeline_file} is untouched`
                  : "This change touches more than the tests"}
              </div>
            </div>
          </Panel>
          <div className="grid grid-cols-[400px_minmax(0,1fr)] items-start gap-5">
            <Panel title="Items">
              <ul className="space-y-0.5">
                {data.items.map((i) => (
                  <li key={i.item_id}>
                    <button
                      type="button"
                      onClick={() => setSelected(i.item_id)}
                      className={`flex w-full items-start gap-2 rounded-lg px-2 py-2 text-left ${
                        i.item_id === item?.item_id ? "bg-selected" : "hover:bg-surface-2"
                      }`}
                    >
                      <span className="mt-0.5 shrink-0">
                        {i.decision?.decision === "approved" ? (
                          <Check size={17} className="text-ok" aria-label="Approved" />
                        ) : i.decision?.decision === "rejected" ? (
                          <X size={17} className="text-bad" aria-label="Rejected" />
                        ) : (
                          <span
                            className="block h-[17px] w-[17px] rounded-full border-2 border-line-strong"
                            aria-label="Not decided"
                          />
                        )}
                      </span>
                      <span>
                        <span className="block text-[15px]">{i.title.replace(" @critical", "")}</span>
                        <span className="text-[13px] text-ink-3">
                          {SOURCE[i.source.kind] ?? i.source.kind} {i.source.ref}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </Panel>
            <Panel>
              {item && (
                <>
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <AiBadge source="live_model" />
                    <Decide item={item} merged={Boolean(data.merged)} />
                  </div>
                  <Evidence item={item} pr={data} />
                </>
              )}
            </Panel>
          </div>
        </>
      )}
    </Screen>
  );
}
