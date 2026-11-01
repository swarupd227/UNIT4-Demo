import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BadgeCheck, Check, Circle, Download, FileText, PenLine } from "lucide-react";
import { motion } from "motion/react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { formatTime } from "../lib/format";
import { usePersona } from "../lib/persona";
import { useToast } from "../lib/toast";
import { workbench, type SignoffState } from "../lib/workbench";
import { Panel, Screen } from "../ui/layout";
import { useState } from "react";
import { Button, Skeleton } from "../ui/primitives";

function AnswerControls({ options, disabled, onAnswer }: {
  options: string[];
  disabled: boolean;
  onAnswer: (text: string) => void;
}) {
  const [text, setText] = useState("");
  if (options.length > 0) {
    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {options.map((option) => (
          <Button key={option} disabled={disabled} onClick={() => onAnswer(option)}>
            {option}
          </Button>
        ))}
      </div>
    );
  }
  return (
    <form
      className="mt-2 flex gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        if (text.trim()) onAnswer(text.trim());
      }}
    >
      <input
        aria-label="Your answer"
        placeholder="Your answer"
        value={text}
        onChange={(event) => setText(event.target.value)}
        className="h-11 min-w-0 flex-1 rounded-lg border border-line-strong bg-surface px-3 text-[15px]"
      />
      <Button type="submit" variant="primary" disabled={disabled || !text.trim()}>
        Send
      </Button>
    </form>
  );
}

function QuestionQueue({ state }: { state: SignoffState }) {
  const { role } = usePersona();
  const toast = useToast();
  const client = useQueryClient();
  const answer = useMutation({
    mutationFn: ({ id, text }: { id: string; text: string }) => api.answer(id, role, text),
    onError: (error: Error) => toast(error.message, "bad"),
    onSettled: () => client.invalidateQueries(),
  });
  if (state.open_questions.length === 0) return null;
  const customer = role === "customer";
  return (
    <Panel title={`${state.open_questions.length} customer questions open`}>
      {!customer && <p className="mb-3 text-[15px] text-ink-2">Waiting for Jordan Ashby.</p>}
      <ul className="space-y-3">
        {state.open_questions.map((question) => (
          <li key={question.question_id} className="rounded-lg bg-warn-soft p-3">
            <Link to={`/decisions/${question.item_id}`} className="text-[15px] font-semibold hover:underline">
              {question.item_id} · {question.name}
            </Link>
            <p className="text-[15px] leading-6">{question.question}</p>
            {customer && (
              <AnswerControls
                options={question.options}
                disabled={answer.isPending}
                onAnswer={(text) => answer.mutate({ id: question.item_id, text })}
              />
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}

export function SignoffScreen() {
  const { role } = usePersona();
  const toast = useToast();
  const client = useQueryClient();
  const { data: state } = useQuery({ queryKey: ["signoff"], queryFn: () => workbench.signoff(role) });
  const options = {
    onError: (error: Error) => toast(error.message, "bad"),
    onSettled: () => client.invalidateQueries(),
  };
  const generate = useMutation({ ...options, mutationFn: () => workbench.generatePack(role) });
  const sign = useMutation({ ...options, mutationFn: () => workbench.signPack(role) });

  if (!state) return <Skeleton className="m-5 h-96" />;
  const { pack } = state;
  const signed = Boolean(pack?.signed_at);
  const usable = pack && state.pack_current;

  return (
    <Screen title="Customer sign-off" lead={state.scope} next="scorecard">
      <div className="grid grid-cols-[minmax(0,5fr)_minmax(0,8fr)] gap-4">
        <div className="space-y-4">
          <Panel title="Before signing">
            <ul className="space-y-2.5">
              {state.conditions.map((condition) => (
                <li key={condition.key} className="flex items-start gap-2.5 text-[16px]">
                  <span
                    className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-full ${
                      condition.passed ? "bg-ok text-white" : "text-ink-3"
                    }`}
                  >
                    {condition.passed ? <Check size={15} strokeWidth={3} aria-hidden /> : <Circle size={20} aria-hidden />}
                  </span>
                  <span>
                    {condition.label}
                    <span className="block text-[14px] text-ink-3">{condition.detail}</span>
                  </span>
                </li>
              ))}
            </ul>
            {!signed && role === "consultant" && (
              <Button
                variant="primary"
                className="mt-4 w-full"
                disabled={!state.ready_to_generate || generate.isPending}
                onClick={() => generate.mutate()}
              >
                <FileText size={18} aria-hidden />
                {generate.isPending ? "Generating…" : pack ? "Generate again" : "Generate the pack"}
              </Button>
            )}
          </Panel>
          <QuestionQueue state={state} />
          {pack && (
            <Panel title="Evidence">
              <dl className="tnum grid grid-cols-[1fr_auto] gap-y-1 text-[16px]">
                <dt className="text-ink-2">Decisions agreed</dt>
                <dd>{pack.summary.agreed} of {pack.summary.decisions}</dd>
                <dt className="text-ink-2">Of which accepted in earlier sessions</dt>
                <dd>{pack.summary.seeded_history}</dd>
                <dt className="text-ink-2">Checks passed</dt>
                <dd>{pack.summary.checks_passed} of {pack.summary.checks}</dd>
                <dt className="text-ink-2">Exceptions listed</dt>
                <dd>{pack.summary.exceptions}</dd>
                <dt className="text-ink-2">Customer questions answered</dt>
                <dd>{pack.summary.questions_answered}</dd>
                <dt className="text-ink-2">Audit events</dt>
                <dd>{pack.summary.audit_events}</dd>
              </dl>
              <p className="tnum mt-3 text-[14px] break-all text-ink-3">Manifest {pack.manifest_hash.slice(0, 24)}…</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <a
                  href={`/api/signoff/${pack.pack_id}/signoff_pack.zip`}
                  className="inline-flex h-11 items-center gap-2 rounded-lg border border-line-strong px-4 text-[15px] font-medium hover:bg-surface-2"
                >
                  <Download size={17} aria-hidden />
                  Download the evidence
                </a>
                <a
                  href={`/api/signoff/${pack.pack_id}/signoff_pack.pdf`}
                  target="_blank"
                  rel="noopener"
                  className="inline-flex h-11 items-center gap-2 rounded-lg border border-line-strong px-4 text-[15px] font-medium hover:bg-surface-2"
                >
                  <FileText size={17} aria-hidden />
                  Open PDF
                </a>
              </div>
            </Panel>
          )}
        </div>

        <Panel className="flex min-h-[720px] flex-col !p-0">
          {pack ? (
            <>
              <div className="flex items-center justify-between gap-4 border-b border-line p-4">
                {signed ? (
                  <motion.p
                    initial={{ scale: 0.97, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="flex items-center gap-2 text-[18px] font-semibold text-ok"
                  >
                    <BadgeCheck size={24} aria-hidden />
                    Signed by {pack.signed_by}, {formatTime(pack.signed_at!)}
                  </motion.p>
                ) : usable ? (
                  <p className="text-[16px] text-ink-2">Generated by {pack.generated_by}, {formatTime(pack.generated_at)}</p>
                ) : (
                  <p className="text-[16px] text-warn">Something changed after this pack. Generate it again.</p>
                )}
                {!signed && role === "customer" && (
                  <Button variant="primary" disabled={!usable || sign.isPending} onClick={() => sign.mutate()}>
                    <PenLine size={18} aria-hidden />
                    Sign off the trial migration
                  </Button>
                )}
                {!signed && role !== "customer" && usable && (
                  <span className="text-[15px] text-ink-3">Jordan Ashby signs this.</span>
                )}
              </div>
              <iframe
                title="Sign-off pack"
                sandbox=""
                src={`/api/signoff/${pack.pack_id}/signoff_pack.html`}
                className="min-h-0 w-full flex-1 rounded-b-xl"
              />
            </>
          ) : (
            <p className="m-auto max-w-md text-center text-[18px] leading-7 text-ink-2">
              No pack generated yet. It will hold the decision register, reconciliation report, exception log, test
              evidence and customer questions.
            </p>
          )}
        </Panel>
      </div>
    </Screen>
  );
}
