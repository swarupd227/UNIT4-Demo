import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, FileCode2, X } from "lucide-react";
import { useState } from "react";
import { api, type ContextEntry, type RiskFacts } from "../lib/api";
import { formatDate } from "../lib/format";
import { usePersona } from "../lib/persona";
import { ROLES } from "../lib/terms";
import { useToast } from "../lib/toast";
import { ErrorNote, Panel, Screen } from "../ui/layout";
import { Modal } from "../ui/overlays";
import { AiBadge, Button, CodeBadge, SectionLabel, Skeleton, SourceBadge } from "../ui/primitives";

const REVIEWERS = new Set(["engineer", "qe_lead"]);
const KIND_LABEL = { risk_card: "Risk card", hidden_rule: "Hidden rule", dead_code: "Dead code" };
const TAB_LABEL = { risk_card: "Risk cards", hidden_rule: "Hidden rules", dead_code: "Dead code" };
type Kind = keyof typeof KIND_LABEL;
const KINDS = Object.keys(KIND_LABEL) as Kind[];
const TEST_LABEL = { automated: "Automated test", manual: "Manual case only", none: "No test" };

function DefectChips({ ids }: { ids: string[] }) {
  return (
    <span className="inline-flex flex-wrap gap-1">
      {ids.map((id) => (
        <span key={id} className="rounded bg-line px-1.5 font-mono text-[12px] text-ink-2">
          {id}
        </span>
      ))}
    </span>
  );
}

function RiskRanking({ ranking }: { ranking: RiskFacts[] }) {
  const shown = ranking.filter((entry) => entry.defects.length);
  return (
    <Panel title="Risk by rule" aside={<CodeBadge title="Ranked by plain code: uncovered critical rules first, then defects without an automated test." />}>
      <ol className="space-y-1">
        {shown.map((entry) => (
          <li key={entry.rule} className="rounded-lg px-2 py-1.5 hover:bg-surface-2">
            <div className="text-[15px]">
              <span className="font-mono text-[13px] text-ink-3">{entry.rule}</span> {entry.title}
              {entry.critical && !entry.covered && (
                <span className="ml-2 text-[12px] font-semibold text-bad">Not covered</span>
              )}
            </div>
            <div className="tnum text-[14px] text-ink-2">
              {entry.defects.length} defects, {entry.untested} without an automated test
              {entry.no_test > 0 && `, ${entry.no_test} with no test at all`}
            </div>
          </li>
        ))}
      </ol>
    </Panel>
  );
}

function RiskCardBody({ entry }: { entry: Extract<ContextEntry, { kind: "risk_card" }> }) {
  const { card, facts } = entry.content;
  const byTest = (kind: keyof typeof TEST_LABEL) => facts.defects.filter((d) => d.test === kind).length;
  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-surface-2 p-4">
        <div className="mb-2 flex items-center justify-between">
          <SectionLabel>From the defect history</SectionLabel>
          <CodeBadge title="Counted by plain code from the defect export and the fix commits." />
        </div>
        <div className="grid grid-cols-3 gap-3 text-[15px]">
          <div>
            <div className="tnum text-[24px] font-semibold">{facts.defects.length}</div>
            defects in three years
          </div>
          <div>
            <div className="tnum text-[24px] font-semibold">{facts.no_test}</div>
            fixed with no test at all
          </div>
          <div>
            <div className="tnum text-[24px] font-semibold">{byTest("automated")}</div>
            fixed with an automated test
          </div>
        </div>
        <div className="mt-3 space-y-1">
          {facts.files.map(([file, count]) => (
            <div key={file} className="flex items-center gap-2 font-mono text-[13px] text-ink-2">
              <FileCode2 size={14} aria-hidden /> {file} <span className="font-sans">({count} fixes)</span>
            </div>
          ))}
        </div>
        <ul className="mt-3 space-y-1 text-[14px]">
          {facts.defects.map((d) => (
            <li key={d.id} className="flex gap-2">
              <span className="font-mono text-[12px] text-ink-3">{d.id}</span>
              <span className="min-w-0 flex-1">{d.title}</span>
              <span className={d.test === "none" ? "font-semibold text-bad" : "text-ink-3"}>{TEST_LABEL[d.test]}</span>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <SectionLabel>What keeps breaking</SectionLabel>
        <ul className="space-y-2">
          {card.what_keeps_breaking.map((point) => (
            <li key={point.point} className="text-[15px]">
              {point.point} <DefectChips ids={point.defects} />
            </li>
          ))}
        </ul>
      </div>
      <div>
        <SectionLabel>Why these escaped</SectionLabel>
        <p className="text-[15px]">{card.why_it_escapes}</p>
      </div>
      <div>
        <SectionLabel>Proposed tests</SectionLabel>
        <ul className="space-y-2">
          {card.proposed_tests.map((test) => (
            <li key={test.title} className="rounded-lg border border-line p-3">
              <div className="font-semibold">{test.title}</div>
              <div className="mt-0.5 text-[15px] text-ink-2">{test.scenario}</div>
              <div className="mt-1.5">
                <DefectChips ids={test.defects} />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function HiddenRuleBody({ entry }: { entry: Extract<ContextEntry, { kind: "hidden_rule" }> }) {
  const rule = entry.content;
  return (
    <div className="space-y-4">
      <p className="text-[17px]">{rule.statement}</p>
      <div>
        <SectionLabel>Where the code enforces it</SectionLabel>
        <ul className="space-y-1.5">
          {[...new Set(rule.citations.map((c) => c.file))].map((file) => (
            <li key={file} className="rounded-lg bg-surface-2 p-2.5">
              <div className="mb-1 font-mono text-[13px] text-ink-3">{file}</div>
              {rule.citations
                .filter((c) => c.file === file)
                .map((c) => (
                  <div key={c.line} className="flex gap-3 font-mono text-[13px]">
                    <span className="tnum w-8 shrink-0 text-right text-ink-3">{c.line}</span>
                    <code>{c.text}</code>
                  </div>
                ))}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <SectionLabel>What the documents say</SectionLabel>
        <p className="text-[15px]">{rule.why_hidden}</p>
      </div>
      <div className="rounded-lg bg-surface-2 p-4">
        <div className="mb-2 flex items-center justify-between">
          <SectionLabel>Searched the register, help pages, manual cases and tests</SectionLabel>
          <CodeBadge title="Plain text search of every document for each phrase." />
        </div>
        <ul className="space-y-1 text-[15px]">
          {rule.document_search.map((hit) => (
            <li key={hit.phrase} className="flex items-start gap-2">
              {hit.found_in.length ? (
                <Check size={17} className="mt-0.5 shrink-0 text-warn" aria-hidden />
              ) : (
                <X size={17} className="mt-0.5 shrink-0 text-ink-3" aria-hidden />
              )}
              <span>
                “{hit.phrase}”:{" "}
                {hit.found_in.length ? `found in ${hit.found_in.join(", ")}` : "found nowhere"}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[15px] font-semibold">
          {rule.documented ? "Partly documented. Check the matches above." : "Found in code only."}
        </p>
      </div>
      <div>
        <SectionLabel>Proposed test</SectionLabel>
        <p className="text-[15px]">{rule.proposed_test}</p>
      </div>
    </div>
  );
}

function DeadCodeBody({ entry }: { entry: Extract<ContextEntry, { kind: "dead_code" }> }) {
  const item = entry.content;
  return (
    <div className="space-y-2 text-[15px]">
      <div className="font-mono text-[13px] text-ink-3">
        {item.file}:{item.line}
      </div>
      <p>{item.reason}</p>
      {item.called_from.length > 0 && <p className="text-ink-2">Called from {item.called_from.join(", ")}.</p>}
      <p className="text-ink-2">No test is proposed for code no user can reach.</p>
    </div>
  );
}

function ReviewState({ entry }: { entry: ContextEntry }) {
  if (entry.status === "proposed") return <SourceBadge>Awaiting review</SourceBadge>;
  const approved = entry.status === "approved";
  return (
    <span className={`text-[14px] font-semibold ${approved ? "text-ok" : "text-bad"}`}>
      {approved ? "Approved" : "Rejected"} by {entry.reviewed_by}, {formatDate(entry.reviewed_at)}
    </span>
  );
}

function EntryCard({ entry, onReject }: { entry: ContextEntry; onReject: (entry: ContextEntry) => void }) {
  const { role } = usePersona();
  const notify = useToast();
  const client = useQueryClient();
  const approve = useMutation({
    mutationFn: () => api.review(entry.entry_id, role, "approved", ""),
    onSuccess: () => {
      notify(`${entry.entry_id} approved`);
      void client.invalidateQueries({ queryKey: ["context"] });
    },
    onError: (error) => notify((error as Error).message, "bad"),
  });
  return (
    <Panel>
      <div className="mb-3 flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[13px] font-semibold text-ink-3">
            {KIND_LABEL[entry.kind]}
            {entry.rule && <span className="font-mono">{entry.rule}</span>}
            <span className="font-mono">{entry.entry_id}</span>
          </div>
          <h3 className="text-[19px] font-semibold">{entry.title}</h3>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {entry.provenance === "ai_analysis" ? <AiBadge source={entry.source} /> : <CodeBadge />}
        </div>
      </div>
      {entry.kind === "risk_card" && <RiskCardBody entry={entry} />}
      {entry.kind === "hidden_rule" && <HiddenRuleBody entry={entry} />}
      {entry.kind === "dead_code" && <DeadCodeBody entry={entry} />}
      <div className="mt-4 flex items-center justify-between gap-3 border-t border-line pt-3">
        <div>
          <ReviewState entry={entry} />
          {entry.review_note && <p className="text-[14px] text-ink-2">{entry.review_note}</p>}
        </div>
        {entry.status === "proposed" && REVIEWERS.has(role) && (
          <div className="flex gap-2">
            <Button onClick={() => onReject(entry)}>Reject</Button>
            <Button variant="primary" disabled={approve.isPending} onClick={() => approve.mutate()}>
              Approve
            </Button>
          </div>
        )}
      </div>
    </Panel>
  );
}

function RejectDialog({ entry, onClose }: { entry: ContextEntry | null; onClose: () => void }) {
  const { role } = usePersona();
  const notify = useToast();
  const client = useQueryClient();
  const [note, setNote] = useState("");
  const reject = useMutation({
    mutationFn: () => api.review(entry!.entry_id, role, "rejected", note),
    onSuccess: () => {
      notify(`${entry!.entry_id} rejected`);
      setNote("");
      onClose();
      void client.invalidateQueries({ queryKey: ["context"] });
    },
    onError: (error) => notify((error as Error).message, "bad"),
  });
  return (
    <Modal open={entry !== null} onClose={onClose} title={`Reject ${entry?.entry_id ?? ""}`} description="Say why, so the next run can be corrected.">
      <label className="block text-[15px] font-medium" htmlFor="reject-note">
        Reason
      </label>
      <textarea
        id="reject-note"
        value={note}
        onChange={(event) => setNote(event.target.value)}
        rows={3}
        className="mt-1 w-full rounded-lg border border-line-strong bg-surface p-3 text-[15px]"
      />
      <div className="mt-4 flex justify-end gap-2">
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="primary" disabled={!note.trim() || reject.isPending} onClick={() => reject.mutate()}>
          Reject
        </Button>
      </div>
    </Modal>
  );
}

async function download() {
  const body = await api.exportContext();
  const url = URL.createObjectURL(new Blob([JSON.stringify(body, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "project-billing-context.json";
  link.click();
  URL.revokeObjectURL(url);
}

export function ContextScreen() {
  const { data, error } = useQuery({ queryKey: ["context"], queryFn: api.context });
  const { role } = usePersona();
  const notify = useToast();
  const [rejecting, setRejecting] = useState<ContextEntry | null>(null);
  const [kind, setKind] = useState<Kind>("risk_card");
  const approved = data?.entries.filter((entry) => entry.status === "approved").length ?? 0;
  const shown = data?.entries.filter((entry) => entry.kind === kind) ?? [];
  return (
    <Screen
      title="Context"
      lead="What the defect history and the code say about this area, reviewed before anyone relies on it."
      next="tests"
      aside={
        <Button
          disabled={!approved}
          onClick={() => download().catch((reason: Error) => notify(reason.message, "bad"))}
        >
          <Download size={17} aria-hidden /> Export {approved} approved
        </Button>
      }
    >
      {error && <ErrorNote message={(error as Error).message} />}
      {!data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <div className="grid grid-cols-[440px_minmax(0,1fr)] items-start gap-5">
          <div className="space-y-5">
            <RiskRanking ranking={data.risk_ranking} />
            <Panel title="Defects by code touched" aside={<CodeBadge title="Grouped by plain code from the fix commits." />}>
              <ul className="space-y-1">
                {data.clusters.slice(0, 8).map((cluster) => (
                  <li key={cluster.file} className="flex items-center justify-between gap-3 text-[14px]">
                    <span className="min-w-0 truncate font-mono text-[13px]">{cluster.file.replace("src/Billing.Web/", "")}</span>
                    <span className="tnum shrink-0 text-ink-2">
                      {cluster.defects} fixes, {cluster.no_test} with no test
                    </span>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>
          <div className="space-y-5">
            {!REVIEWERS.has(role) && (
              <p className="rounded-lg bg-surface p-3 text-[15px] text-ink-2">
                Context is reviewed by an engineer. You are viewing as {ROLES[role].label}.
              </p>
            )}
            <div role="tablist" aria-label="Kind of context" className="flex gap-1">
              {KINDS.map((key) => {
                const count = data.entries.filter((entry) => entry.kind === key).length;
                const waiting = data.entries.filter((e) => e.kind === key && e.status === "proposed").length;
                return (
                  <button
                    key={key}
                    type="button"
                    role="tab"
                    aria-selected={kind === key}
                    onClick={() => setKind(key)}
                    className={`h-10 rounded-lg px-3.5 text-[15px] font-medium transition-colors ${
                      kind === key ? "bg-ink text-canvas" : "text-ink-2 hover:bg-line/50"
                    }`}
                  >
                    {TAB_LABEL[key]} ({count}){waiting > 0 && `, ${waiting} to review`}
                  </button>
                );
              })}
            </div>
            {shown.length === 0 && <Panel>No context of this kind has been analysed yet.</Panel>}
            {shown.map((entry) => (
              <EntryCard key={entry.entry_id} entry={entry} onReject={setRejecting} />
            ))}
          </div>
        </div>
      )}
      <RejectDialog entry={rejecting} onClose={() => setRejecting(null)} />
    </Screen>
  );
}
