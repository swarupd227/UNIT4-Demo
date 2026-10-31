import { useState } from "react";
import type { DecisionDetail } from "../../lib/api";
import { OUTCOME_HINTS, OUTCOME_KEYS, OUTCOMES, type Outcome } from "../../lib/terms";
import { Modal } from "../../ui/overlays";
import { Button } from "../../ui/primitives";

const INPUT =
  "w-full rounded-lg border border-line-strong bg-surface p-3 text-[15px] leading-6 outline-none focus:border-accent";

type EditProps = {
  item: DecisionDetail;
  onClose: () => void;
  onSave: (outcome: Outcome, reason: string) => void;
};

export function EditDialog({ item, onClose, onSave }: EditProps) {
  const [outcome, setOutcome] = useState<Outcome | null>(item.outcome);
  const [reason, setReason] = useState("");
  const ready = outcome !== null && reason.trim().length >= 3;
  return (
    <Modal
      open
      onClose={onClose}
      title={`Change the decision on ${item.item_id}`}
      description="Your reason goes on the audit trail. Any approvals so far are cleared."
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (ready) onSave(outcome, reason.trim());
        }}
      >
        <fieldset className="space-y-1">
          <legend className="sr-only">Outcome</legend>
          {OUTCOME_KEYS.map((key) => (
            <label
              key={key}
              className={`flex cursor-pointer gap-3 rounded-lg border p-2.5 transition-colors ${
                outcome === key ? "border-accent bg-selected" : "border-transparent hover:bg-surface-2"
              }`}
            >
              <input
                type="radio"
                name="outcome"
                className="mt-1 accent-[var(--accent)]"
                checked={outcome === key}
                onChange={() => setOutcome(key)}
              />
              <span>
                <span className="block text-[15px] font-medium">{OUTCOMES[key].label}</span>
                <span className="block text-[14px] text-ink-3">{OUTCOME_HINTS[key]}</span>
              </span>
            </label>
          ))}
        </fieldset>
        <label className="mt-4 block text-[15px] font-medium">
          Reason
          <textarea
            autoFocus
            rows={2}
            className={`${INPUT} mt-1 font-normal`}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
        <div className="mt-5 flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={!ready}>
            Save decision
          </Button>
        </div>
      </form>
    </Modal>
  );
}

type AskProps = {
  item: DecisionDetail;
  onClose: () => void;
  onSend: (question: string, options: string[]) => void;
};

export function AskDialog({ item, onClose, onSend }: AskProps) {
  const [question, setQuestion] = useState(item.conflict?.question ?? "");
  const options = item.conflict?.options ?? [];
  const ready = question.trim().length >= 5;
  return (
    <Modal
      open
      onClose={onClose}
      title={`Ask the customer about ${item.item_id}`}
      description="The item waits until Jordan Ashby at Ardleigh answers."
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (ready) onSend(question.trim(), options);
        }}
      >
        <label className="block text-[15px] font-medium">
          Question
          <textarea
            autoFocus
            rows={4}
            className={`${INPUT} mt-1 font-normal`}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
        </label>
        {options.length > 0 && (
          <p className="mt-2 text-[14px] text-ink-3">Offered choices: {options.join(" or ")}</p>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={!ready}>
            Send to customer
          </Button>
        </div>
      </form>
    </Modal>
  );
}
