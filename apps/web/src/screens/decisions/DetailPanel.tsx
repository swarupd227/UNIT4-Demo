import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BookOpenText,
  Building2,
  Check,
  ChevronDown,
  Code2,
  FileText,
  GitBranch,
  History,
  KeyRound,
  Layers,
  Link2,
  ShieldAlert,
  User,
  type LucideIcon,
} from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { api, type Conflict, type DecisionDetail, type Evidence, type Question } from "../../lib/api";
import { confidenceWord, formatTime } from "../../lib/format";
import { usePersona } from "../../lib/persona";
import {
  acceptLabel,
  ACTIONS,
  AUDIT_ACTIONS,
  HELD_LABEL,
  ITEM_TYPES,
  OUTCOMES,
  ROLES,
  SUBTYPES,
} from "../../lib/terms";
import { AiBadge, Button, CodeBadge, SectionLabel, Skeleton, StatusLabel } from "../../ui/primitives";
import { refusedRetire } from "./registerModel";

const EVIDENCE_ICONS: Record<string, LucideIcon> = {
  usage: Activity,
  code: Code2,
  policy: BookOpenText,
  owner: User,
  j2x: Layers,
  dependency: Link2,
  keyword: KeyRound,
  entity: Building2,
  standard: GitBranch,
  precedent: History,
  definition: FileText,
};

function ConflictCard({ conflict, resolvedBy }: { conflict: Conflict; resolvedBy?: Question }) {
  return (
    <section
      className={`rounded-lg border p-4 ${resolvedBy ? "border-ok/30 bg-ok-soft" : "border-bad/30 bg-bad-soft"}`}
    >
      <h3 className={`text-[15px] font-semibold ${resolvedBy ? "text-ok" : "text-bad"}`}>
        {resolvedBy ? "Resolved" : "Conflict"}: {conflict.topic.toLowerCase()}
      </h3>
      <div className="mt-3 grid grid-cols-2 gap-3">
        {[
          [conflict.left_label, conflict.left_value],
          [conflict.right_label, conflict.right_value],
        ].map(([label, value]) => (
          <div key={label} className="rounded-md bg-surface px-3 py-2">
            <div className="tnum text-[28px] leading-9 font-semibold">{value}</div>
            <div className="text-[14px] text-ink-2">{label}</div>
          </div>
        ))}
      </div>
      {resolvedBy && (
        <p className="mt-3 text-[15px] leading-6">
          <span className="font-semibold">{resolvedBy.answer}</span>
          <span className="block text-[14px] text-ink-2">
            Decided by {resolvedBy.answered_by}, {formatTime(resolvedBy.answered_at!)}
          </span>
        </p>
      )}
    </section>
  );
}

function QuestionCard({ question, canAnswer, onAnswer }: {
  question: Question;
  canAnswer: boolean;
  onAnswer: (answer: string) => void;
}) {
  const [text, setText] = useState("");
  const open = question.status === "open";
  return (
    <section className={`rounded-lg p-4 ${open ? "bg-warn-soft" : "bg-surface-2"}`}>
      <h3 className={`text-[14px] font-semibold ${open ? "text-warn" : "text-ink-2"}`}>
        {open ? "Waiting for the customer" : "Customer answered"}
      </h3>
      <p className="mt-1 text-[15px] leading-6">{question.question}</p>
      {question.answer && (
        <p className="mt-2 text-[15px] leading-6 font-medium">
          {question.answer}
          <span className="block text-[13px] font-normal text-ink-3">
            {question.answered_by}, {formatTime(question.answered_at!)}
          </span>
        </p>
      )}
      {open && canAnswer && (
        <div className="mt-3 space-y-2">
          {question.options.map((option) => (
            <Button key={option} className="w-full justify-start" onClick={() => onAnswer(option)}>
              {option}
            </Button>
          ))}
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (text.trim()) onAnswer(text.trim());
            }}
          >
            <input
              aria-label="Your answer"
              placeholder={question.options.length ? "Or write an answer" : "Your answer"}
              value={text}
              onChange={(event) => setText(event.target.value)}
              className="h-11 min-w-0 flex-1 rounded-lg border border-line-strong bg-surface px-3 text-[15px]"
            />
            <Button type="submit" variant="primary" disabled={!text.trim()}>
              Send
            </Button>
          </form>
        </div>
      )}
    </section>
  );
}

function Approvals({ item }: { item: DecisionDetail }) {
  if (item.required_roles.length === 0) return null;
  return (
    <section>
      <SectionLabel>Who confirms</SectionLabel>
      {item.audit.some((event) => event.action === "accepted_seeded") && (
        <p className="mb-2 text-[14px] text-ink-3">Accepted in an earlier session.</p>
      )}
      <ol className="space-y-1.5">
        {item.required_roles.map((role) => {
          const approval = item.approvals.find((a) => a.role === role);
          return (
            <li key={role} className="flex items-center gap-2.5 text-[15px]">
              <span
                className={`grid size-6 place-items-center rounded-full ${
                  approval ? "bg-ok text-white" : "border border-line-strong"
                }`}
              >
                {approval && <Check size={14} strokeWidth={3} aria-hidden />}
              </span>
              <span className={approval ? "" : "text-ink-2"}>{ROLES[role].label}</span>
              <span className="tnum ml-auto text-[14px] text-ink-3">
                {approval ? `${approval.person}, ${formatTime(approval.decided_at)}` : "Not yet"}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function AuditTrail({ item }: { item: DecisionDetail }) {
  const { role } = usePersona();
  const [open, setOpen] = useState(false);
  const { data } = useQuery({
    queryKey: ["audit-intact", item.audit.length],
    queryFn: () => api.auditIntact(role),
    enabled: open,
  });
  return (
    <section>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-[13px] font-semibold tracking-wide text-ink-3 uppercase hover:text-ink"
      >
        Audit trail ({item.audit.length})
        <ChevronDown size={16} className={`transition-transform ${open ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {open && (
        <div className="mt-2">
          {data && (
            <p className="mb-2 flex items-center gap-2 text-[14px] text-ink-2">
              <CodeBadge title="Each event hashes the one before it" />
              {data.intact ? "Hash chain intact" : "Hash chain broken"}
            </p>
          )}
          <ol className="space-y-2 text-[14px]">
            {item.audit.map((event) => (
              <li key={event.seq} className="flex justify-between gap-3">
                <span>
                  {AUDIT_ACTIONS[event.action] ?? event.action}
                  <span className="text-ink-3"> by {event.actor}</span>
                </span>
                <span className="tnum shrink-0 text-ink-3" title={event.hash}>
                  {formatTime(event.at)} · {event.hash.slice(0, 8)}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}

type Props = {
  itemId: string | null;
  onEvidence: (item: DecisionDetail, evidence: Evidence) => void;
  onEdit: (item: DecisionDetail) => void;
  onAsk: (item: DecisionDetail) => void;
  onAccept: () => void;
  onAnswer: (answer: string) => void;
};

export function DetailPanel({ itemId, onEvidence, onEdit, onAsk, onAccept, onAnswer }: Props) {
  const { role } = usePersona();
  const { data: item, isPending } = useQuery({
    queryKey: ["decision", itemId, role],
    queryFn: () => api.decision(itemId!, role),
    enabled: itemId !== null,
  });

  if (itemId === null) {
    return <p className="p-8 text-ink-2">Choose an item to see what it does and why.</p>;
  }
  if (isPending || !item) {
    return (
      <div className="space-y-4 p-6">
        <Skeleton className="h-7 w-2/3" />
        <Skeleton className="h-24" />
        <Skeleton className="h-32" />
      </div>
    );
  }

  const outcomeLabel = item.outcome ? OUTCOMES[item.outcome].label : HELD_LABEL;
  const action = item.action && ACTIONS[item.action.split(":")[0]];
  const edited = item.outcome !== item.proposed_outcome;
  const openQuestions = item.questions.filter((question) => question.status === "open");
  const answered = item.questions.filter((question) => question.status === "answered");
  const conflictAnswer = item.conflict ? answered.at(-1) : undefined;
  const questionCard = (question: Question) => (
    <QuestionCard
      key={question.question_id}
      question={question}
      canAnswer={item.allowed.answer}
      onAnswer={onAnswer}
    />
  );

  return (
    <motion.div
      key={item.item_id}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.12 }}
      className="flex h-full min-h-0 flex-col"
    >
      <header className="border-b border-line px-6 pt-5 pb-4">
        <div className="flex items-center justify-between gap-3">
          <span className="tnum text-[14px] text-ink-3">
            {item.item_id} · {ITEM_TYPES[item.item_type].label}
            {SUBTYPES[item.subtype] && SUBTYPES[item.subtype] !== ITEM_TYPES[item.item_type].label
              ? ` · ${SUBTYPES[item.subtype]}`
              : ""}
          </span>
          <StatusLabel status={item.status} />
        </div>
        <h2 className="mt-1 text-[22px] leading-7 font-semibold">{item.name}</h2>
      </header>

      <div className="scroll-quiet min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5">
        <section>
          <SectionLabel aside={<AiBadge />}>What it does</SectionLabel>
          <p className="text-[16px] leading-7">{item.summary}</p>
        </section>

        {item.conflict && <ConflictCard conflict={item.conflict} resolvedBy={conflictAnswer} />}
        {openQuestions.map(questionCard)}

        <section className="rounded-lg border border-line bg-surface-2 p-4">
          <SectionLabel aside={<CodeBadge title="Chosen by the decision rules, from the evidence below" />}>
            {edited ? "Consultant's decision" : item.state === "held" ? "Decision held" : "Proposed decision"}
          </SectionLabel>
          <p className="text-[18px] font-semibold">
            {outcomeLabel}
            {action && <span className="font-normal text-ink-2"> · {action}</span>}
          </p>
          {refusedRetire(item) && (
            <p className="mt-1 inline-flex items-center gap-1.5 text-[15px] font-semibold text-warn">
              <ShieldAlert size={16} aria-hidden />
              Retirement blocked
            </p>
          )}
          <p className="mt-1 text-[15px] leading-6 text-ink-2">{item.reason}</p>
          {edited && item.proposed_outcome && (
            <p className="mt-2 text-[14px] text-ink-3">
              Originally proposed: {OUTCOMES[item.proposed_outcome].label}. Changed because: {item.edit_reason}
            </p>
          )}
          {item.confidence !== null && (
            <p className="tnum mt-2 text-[14px] text-ink-3">
              Confidence: {confidenceWord(item.confidence)} ({item.confidence})
            </p>
          )}
        </section>

        {answered.filter((question) => question !== conflictAnswer).map(questionCard)}

        <section>
          <SectionLabel>Evidence</SectionLabel>
          <ul className="flex flex-wrap gap-2">
            {item.evidence.map((evidence, index) => {
              const Icon = EVIDENCE_ICONS[evidence.kind] ?? FileText;
              return (
                <li key={index}>
                  <button
                    type="button"
                    onClick={() => onEvidence(item, evidence)}
                    className="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-line-strong bg-surface px-2.5 py-1 text-left text-[14px] transition-colors hover:border-accent hover:bg-selected"
                  >
                    <Icon size={15} className="shrink-0 text-ink-3" aria-hidden />
                    {evidence.label}
                  </button>
                </li>
              );
            })}
          </ul>
        </section>

        <Approvals item={item} />
        <AuditTrail item={item} />
      </div>

      <footer className="border-t border-line px-6 py-4">
        {item.allowed.reason && <p className="mb-2 text-[14px] text-ink-3">{item.allowed.reason}</p>}
        <div className="flex gap-2">
          <Button variant="primary" hint="A" className="flex-1" disabled={!item.allowed.accept} onClick={onAccept}>
            {item.status === "agreed" ? "Agreed" : acceptLabel(role, item.outcome)}
          </Button>
          <Button hint="E" disabled={!item.allowed.edit} onClick={() => onEdit(item)}>
            Edit
          </Button>
          <Button hint="Q" disabled={!item.allowed.ask} onClick={() => onAsk(item)}>
            Ask customer
          </Button>
        </div>
      </footer>
    </motion.div>
  );
}
