import {
  CheckCircle2,
  CircleDashed,
  Hourglass,
  MessageCircleQuestion,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { STATUSES, type Status } from "../lib/terms";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  hint?: string;
};

const BUTTON_STYLES = {
  primary: "bg-ink text-canvas hover:bg-spine-2 disabled:bg-line disabled:text-ink-3",
  secondary:
    "border border-line-strong bg-surface text-ink hover:bg-surface-2 disabled:text-ink-3 disabled:border-line",
  ghost: "text-ink-2 hover:bg-line/50",
};

export function Button({ variant = "secondary", hint, className = "", children, ...props }: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex h-11 items-center justify-center gap-2 rounded-lg px-4 text-[15px] font-medium transition-colors disabled:cursor-not-allowed ${BUTTON_STYLES[variant]} ${className}`}
      {...props}
    >
      {children}
      {hint && <Kbd inverse={variant === "primary"}>{hint}</Kbd>}
    </button>
  );
}

export function Kbd({ children, inverse = false }: { children: ReactNode; inverse?: boolean }) {
  return (
    <kbd
      className={`rounded border px-1.5 font-sans text-[12px] leading-[18px] font-medium ${
        inverse ? "border-white/25 text-current/80" : "border-line-strong text-ink-3"
      }`}
    >
      {children}
    </kbd>
  );
}

export function SectionLabel({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="mb-2 flex items-center justify-between gap-3">
      <h3 className="text-[13px] font-semibold tracking-wide text-ink-3 uppercase">{children}</h3>
      {aside}
    </div>
  );
}

export const STATUS_ICONS: Record<Status, LucideIcon> = {
  conflict: TriangleAlert,
  question: MessageCircleQuestion,
  review: CircleDashed,
  awaiting: Hourglass,
  agreed: CheckCircle2,
};

export const TONE_TEXT = {
  bad: "text-bad",
  warn: "text-warn",
  neutral: "text-ink-2",
  accent: "text-accent",
  ok: "text-ok",
};

export const TONE_MARK = {
  bad: "bg-bad",
  warn: "bg-warn",
  neutral: "bg-neutral-mark",
  accent: "bg-accent",
  ok: "bg-ok",
};

export function StatusLabel({ status }: { status: Status }) {
  const { label, tone } = STATUSES[status];
  const Icon = STATUS_ICONS[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-[15px] font-medium whitespace-nowrap ${TONE_TEXT[tone]}`}>
      <Icon size={16} strokeWidth={2.2} aria-hidden />
      {label}
    </span>
  );
}

// Every agent result is hand-authored until a model runs, and the badge says so.
export function AiBadge({ source = "hand_authored" }: { source?: string }) {
  const authored = source === "hand_authored";
  return (
    <span
      title={
        authored
          ? "Written by hand in the agent format for this demo. No model produced it."
          : "Written by an AI analysis agent. A person reviews it."
      }
      className="inline-flex items-center gap-1 rounded-md bg-ai-soft px-1.5 py-0.5 text-[12px] font-semibold text-ai"
    >
      <Sparkles size={12} aria-hidden />
      {authored ? "Authored stand-in" : "AI analysis"}
    </span>
  );
}

export function CodeBadge({ title }: { title?: string }) {
  return (
    <span
      title={title ?? "Calculated by plain code. The same input always gives the same result."}
      className="inline-flex items-center gap-1 rounded-md bg-accent-soft px-1.5 py-0.5 text-[12px] font-semibold text-accent"
    >
      <ShieldCheck size={12} aria-hidden />
      Verified by code
    </span>
  );
}

export function SourceBadge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md bg-line px-1.5 py-0.5 text-[12px] font-semibold text-ink-2">
      {children}
    </span>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden />;
}
