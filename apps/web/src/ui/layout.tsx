import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { animate } from "motion";
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { api, type DecisionDetail } from "../lib/api";
import { usePersona } from "../lib/persona";
import { STAGES } from "../lib/terms";

export function Screen({ title, lead, next, aside, children }: {
  title: string;
  lead: string;
  next?: string;
  aside?: ReactNode;
  children: ReactNode;
}) {
  const stage = STAGES.find((entry) => entry.key === next);
  return (
    <div className="scroll-quiet min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto max-w-[1760px] space-y-5 p-5">
        <header className="flex items-end justify-between gap-6">
          <div>
            <h1 className="text-[28px] leading-9 font-semibold">{title}</h1>
            <p className="mt-0.5 text-[17px] text-ink-2">{lead}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {aside}
            {stage && (
              <Link
                to={`/${stage.key}`}
                className="inline-flex h-11 items-center gap-2 rounded-lg border border-line-strong bg-surface px-4 text-[15px] font-medium transition-colors hover:bg-surface-2"
              >
                {stage.label}
                <ArrowRight size={17} aria-hidden />
              </Link>
            )}
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}

export function Panel({ title, aside, className = "", children }: {
  title?: string;
  aside?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section className={`rounded-xl bg-surface p-5 shadow-panel ${className}`}>
      {title && (
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-[18px] font-semibold">{title}</h2>
          {aside}
        </div>
      )}
      {children}
    </section>
  );
}

export function money(minor: number | null | undefined): string {
  if (minor === null || minor === undefined) return "";
  return (minor / 100).toLocaleString("en-GB", { style: "currency", currency: "GBP" });
}

export function CountUp({ value, format = (n) => Math.round(n).toLocaleString("en-GB") }: {
  value: number;
  format?: (value: number) => string;
}) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(value);
      return;
    }
    const controls = animate(0, value, { duration: 0.7, ease: "easeOut", onUpdate: setShown });
    return () => controls.stop();
  }, [value]);
  return <>{format(shown)}</>;
}

export function ErrorNote({ message }: { message: string }) {
  return <p className="rounded-lg bg-bad-soft p-4 text-bad">{message}</p>;
}

export function useDecision(itemId: string) {
  const { role } = usePersona();
  return useQuery<DecisionDetail>({
    queryKey: ["decision", itemId, role],
    queryFn: () => api.decision(itemId, role),
  });
}
