import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { maintenanceApi, type FileChange, type Review } from "../lib/api";
import { formatTime } from "../lib/format";
import { usePersona } from "../lib/persona";
import { useToast } from "../lib/toast";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { AiBadge, Button, CodeBadge, SectionLabel, Skeleton } from "../ui/primitives";

const CAUSE = {
  fixed_wait: "Fixed wait",
  shared_data: "Shared test data",
  timing: "Timing",
  environment: "Environment",
  other: "Other",
} as Record<string, string>;
const REVIEWERS = new Set(["engineer", "qe_lead"]);

function Files({ files }: { files: FileChange[] }) {
  const [open, setOpen] = useState(files[0]?.path);
  const file = files.find((f) => f.path === open) ?? files[0];
  if (!file) return null;
  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-1">
        {files.map((f) => (
          <button
            key={f.path}
            type="button"
            onClick={() => setOpen(f.path)}
            className={`rounded-md px-2 py-1 font-mono text-[13px] ${f.path === file.path ? "bg-ink text-canvas" : "bg-line text-ink-2"}`}
          >
            {f.path}
          </button>
        ))}
      </div>
      <pre tabIndex={0} aria-label={`Contents of ${file.path}`} className="scroll-quiet max-h-[320px] overflow-auto rounded-lg bg-spine p-4 font-mono text-[13px] leading-5 text-on-spine">
        {file.content}
      </pre>
    </div>
  );
}

function Approval({ changeId, review }: { changeId: string; review: Review | null | undefined }) {
  const { role } = usePersona();
  const notify = useToast();
  const client = useQueryClient();
  const approve = useMutation({
    mutationFn: () => maintenanceApi.review(changeId, role, "approved"),
    onSuccess: () => {
      notify(`${changeId} approved`);
      void client.invalidateQueries({ queryKey: ["flaky"] });
      void client.invalidateQueries({ queryKey: ["maintenance"] });
    },
    onError: (error) => notify((error as Error).message, "bad"),
  });
  if (review) {
    return (
      <span className={`text-[14px] font-semibold ${review.status === "approved" ? "text-ok" : "text-bad"}`}>
        {review.status === "approved" ? "Approved" : "Rejected"} by {review.reviewed_by}, {formatTime(review.reviewed_at)}
      </span>
    );
  }
  if (!REVIEWERS.has(role)) return <span className="text-[14px] text-ink-2">Waiting for an engineer to approve</span>;
  return (
    <Button variant="primary" disabled={approve.isPending} onClick={() => approve.mutate()}>
      Approve change
    </Button>
  );
}

function FlakySection() {
  const { data, error } = useQuery({ queryKey: ["flaky"], queryFn: maintenanceApi.flaky });
  if (error) return <ErrorNote message={(error as Error).message} />;
  if (!data) return <Skeleton className="h-64 w-full" />;
  return (
    <>
      {data.tests.map(({ test, diagnosis, agent, after, change_id, review }) => (
        <Panel key={change_id}>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <div className="text-[13px] font-semibold text-ink-3">
                {test.file} · {CAUSE[diagnosis.cause] ?? diagnosis.cause}
              </div>
              <h2 className="text-[19px] font-semibold">{test.title.replace(" @critical", "")}</h2>
            </div>
            <AiBadge source={agent.source} />
          </div>
          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-6">
            <div className="space-y-4">
              <div className="rounded-lg bg-surface-2 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <SectionLabel>Measured on the unchanged module</SectionLabel>
                  <CodeBadge title="Counted by plain code from repeat runs, each on a fresh database." />
                </div>
                <div className="flex items-baseline gap-6">
                  <div>
                    <div className="tnum text-[24px] font-semibold text-bad">
                      {test.failed} of {test.runs}
                    </div>
                    runs failed before
                  </div>
                  {after && (
                    <div>
                      <div className={`tnum text-[24px] font-semibold ${after.failed ? "text-bad" : "text-ok"}`}>
                        {after.failed} of {after.runs}
                      </div>
                      runs failed after the fix
                    </div>
                  )}
                </div>
                <ul className="mt-3 space-y-1 text-[14px]">
                  {test.messages.map((m) => (
                    <li key={m.message}>
                      <span className="tnum font-semibold">{m.count}×</span> <span className="font-mono text-[13px]">{m.message}</span>
                    </li>
                  ))}
                </ul>
                {test.running_alongside
                  .filter((o) => test.shared_data.some((s) => s.test === o.test && s.changes.length > 0))
                  .map((o) => (
                    <p key={o.test} className="mt-2 text-[14px] text-ink-2">
                      {o.test.replace(" @critical", "")} changes data this test reads, and was running at the same
                      moment in {o.when_failed} of {o.failed_runs} failing runs but only {o.when_passed} of {o.passed_runs}{" "}
                      passing runs.
                    </p>
                  ))}
              </div>
              <div>
                <SectionLabel>Cause</SectionLabel>
                <p className="text-[15px]">{diagnosis.explanation}</p>
                <ul className="mt-2 list-disc pl-5 text-[14px] text-ink-2">
                  {diagnosis.evidence.map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="space-y-3">
              <SectionLabel>Fix</SectionLabel>
              <p className="text-[15px]">{diagnosis.fix_summary}</p>
              <Files files={diagnosis.files} />
            </div>
          </div>
          <div className="mt-4 flex justify-end border-t border-line pt-3">
            <Approval changeId={change_id} review={review} />
          </div>
        </Panel>
      ))}
      {data.runs_after > 0 && (
        <p className="text-[15px] text-ink-2">
          With the fixes, the whole suite of {data.suite_after} tests ran {data.runs_after} times with{" "}
          {data.failures_after === 0 ? "no failures" : `${data.failures_after} failures`}.
        </p>
      )}
    </>
  );
}

function MaintenanceSection() {
  const { data, error } = useQuery({ queryKey: ["maintenance"], queryFn: maintenanceApi.maintenance });
  if (error) return <ErrorNote message={(error as Error).message} />;
  if (!data) return <Skeleton className="h-64 w-full" />;
  if (!data.repair || !data.timing || !data.release) return <Panel>No release has been checked yet.</Panel>;
  return (
    <Panel title={`Next release: ${data.release.id}`} aside={<AiBadge source={data.agent?.source} />}>
      <p className="text-[15px]">{data.release.description}.</p>
      <div className="mt-3 grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-6">
        <div className="space-y-4">
          <div>
            <SectionLabel>Broken by the change</SectionLabel>
            <ul className="space-y-1 text-[14px]">
              {data.failures?.map((f) => (
                <li key={f.title}>{f.title.replace(" @critical", "")}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg bg-surface-2 p-4">
            <div className="mb-2 flex items-center justify-between">
              <SectionLabel>Time to repair, measured</SectionLabel>
              <CodeBadge title="Lab run times and the agent's own time, as recorded." />
            </div>
            <dl className="grid grid-cols-2 gap-y-1 text-[15px]">
              <dt>Lab run that found the break</dt>
              <dd className="tnum text-right">{data.timing.detect_seconds} s</dd>
              <dt>Repair proposed</dt>
              <dd className="tnum text-right">{data.timing.repair_seconds} s</dd>
              <dt>Lab run that proved the repair</dt>
              <dd className="tnum text-right">{data.timing.verify_seconds} s</dd>
              <dt className="font-semibold">Before the engineer's review</dt>
              <dd className="tnum text-right font-semibold">{Math.round(data.timing.machine_seconds)} s</dd>
            </dl>
            <p className="mt-2 text-[14px] text-ink-2">
              After the repair, {data.after?.tests} tests ran on the new release with{" "}
              {data.after?.failed === 0 ? "no failures" : `${data.after?.failed} failures`}.
            </p>
          </div>
          <p className="text-[15px]">{data.repair.cause}</p>
        </div>
        <div className="space-y-3">
          <SectionLabel>Repair</SectionLabel>
          <p className="text-[15px]">{data.repair.fix_summary}</p>
          <Files files={data.repair.files} />
        </div>
      </div>
      <div className="mt-4 flex justify-end border-t border-line pt-3">
        {data.change_id && <Approval changeId={data.change_id} review={data.review} />}
      </div>
    </Panel>
  );
}

export function FlakyScreen() {
  return (
    <Screen
      title="Flaky tests and maintenance"
      lead="Why tests fail without a code change, and how fast a screen change is repaired."
      next="review"
    >
      <FlakySection />
      <MaintenanceSection />
    </Screen>
  );
}
