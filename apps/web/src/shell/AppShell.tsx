import * as Dropdown from "@radix-ui/react-dropdown-menu";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronDown } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { usePersona } from "../lib/persona";
import { useAudienceLink } from "../lib/presenter";
import { recordingPath, sceneForPath, SCENES } from "../lib/scenes";
import { ROLE_KEYS, ROLES, STAGES } from "../lib/terms";
import { workbench } from "../lib/workbench";
import { Kbd, Skeleton } from "../ui/primitives";
import { CommandPalette } from "./CommandPalette";

const TIMING_INTERVAL_SECONDS = 15;

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div className="leading-tight">
      <div className="tnum text-[17px] font-semibold text-on-spine">{value}</div>
      <div className="text-[13px] text-on-spine-2">{label}</div>
    </div>
  );
}

function PersonaMenu() {
  const { role, setRole } = usePersona();
  const person = ROLES[role];
  const initials = person.person
    .split(" ")
    .map((part) => part[0])
    .join("");

  return (
    <Dropdown.Root>
      <Dropdown.Trigger className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-spine-2">
        <span className="grid size-9 place-items-center rounded-full bg-accent text-[14px] font-semibold text-white">
          {initials}
        </span>
        <span className="leading-tight">
          <span className="block text-[15px] font-medium text-on-spine">{person.person}</span>
          <span className="block text-[13px] text-on-spine-2">{person.label}</span>
        </span>
        <ChevronDown size={16} className="text-on-spine-2" aria-hidden />
      </Dropdown.Trigger>
      <Dropdown.Portal>
        <Dropdown.Content
          align="end"
          sideOffset={6}
          className="z-30 w-72 rounded-xl bg-surface p-1.5 shadow-float"
        >
          <Dropdown.Label className="px-2.5 py-1.5 text-[13px] font-semibold tracking-wide text-ink-3 uppercase">
            View as
          </Dropdown.Label>
          {ROLE_KEYS.map((key) => (
            <Dropdown.Item
              key={key}
              onSelect={() => setRole(key)}
              className="flex cursor-pointer items-center justify-between rounded-lg px-2.5 py-2 outline-none data-[highlighted]:bg-selected"
            >
              <span className="leading-tight">
                <span className="block text-[15px] font-medium">{ROLES[key].person}</span>
                <span className="block text-[14px] text-ink-3">{ROLES[key].label}</span>
              </span>
              {key === role && <Check size={18} className="text-accent" aria-hidden />}
            </Dropdown.Item>
          ))}
        </Dropdown.Content>
      </Dropdown.Portal>
    </Dropdown.Root>
  );
}

function CustomerBar() {
  const { role } = usePersona();
  const { data } = useQuery({ queryKey: ["case", role], queryFn: () => api.case(role) });
  return (
    <header className="flex h-[68px] shrink-0 items-center gap-8 bg-spine px-5">
      <div className="leading-tight">
        <div className="text-[17px] font-semibold text-on-spine">
          {data?.customer_name ?? <Skeleton className="h-5 w-56 opacity-30" />}
        </div>
        <div className="text-[14px] text-on-spine-2">
          CR to ERPx · {data?.entity_label} · {data?.label}
        </div>
      </div>
      {data?.synthetic && (
        <span className="rounded-md border border-on-spine-2/40 px-2 py-0.5 text-[13px] font-medium text-on-spine-2">
          Sandbox
        </span>
      )}
      <div className="ml-auto flex items-center gap-8">
        {data && (
          <>
            <Metric
              value={`${data.progress.agreed} of ${data.progress.total}`}
              label="decisions agreed"
            />
            <Metric value={String(data.progress.open_questions)} label="open questions" />
            <Metric
              value={data.reconciliation ? `${data.reconciliation.passed} of ${data.reconciliation.total}` : "Not run"}
              label={data.reconciliation ? "checks passed" : "reconciliation"}
            />
          </>
        )}
        <PersonaMenu />
      </div>
    </header>
  );
}

function JourneyRail() {
  return (
    <nav aria-label="Migration stages" className="shrink-0 border-b border-line bg-surface px-5">
      <ol className="flex h-[52px] items-center gap-1">
        {STAGES.map((stage) => (
          <li key={stage.key}>
            <NavLink
              to={`/${stage.key}`}
              className={({ isActive }) =>
                `flex h-9 items-center rounded-lg px-3.5 text-[15px] font-medium transition-colors ${
                  isActive ? "bg-ink text-canvas" : "text-ink-2 hover:bg-line/50"
                }`
              }
            >
              {stage.label}
            </NavLink>
          </li>
        ))}
        <li className="ml-auto flex items-center gap-1.5 text-[14px] text-ink-3">
          <Kbd>Ctrl K</Kbd> Search
        </li>
      </ol>
    </nav>
  );
}

// The workbench logs its own time, so effort on the scorecard is measured rather than claimed.
function useStageTiming(stage: string) {
  const { role } = usePersona();
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (!document.hidden) workbench.timing(stage, TIMING_INTERVAL_SECONDS, role).catch(() => undefined);
    }, TIMING_INTERVAL_SECONDS * 1000);
    return () => window.clearInterval(timer);
  }, [stage, role]);
}

export function AppShell() {
  const location = useLocation();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const navigate = useNavigate();
  const { fallback, closeFallback } = useAudienceLink();
  useStageTiming(location.pathname.split("/")[1]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
        return;
      }
      // The presenter console has no menu entry, because it is not part of the product.
      if (event.ctrlKey && event.altKey && event.key.toLowerCase() === "p") {
        event.preventDefault();
        window.open("/presenter", "studio-presenter", "popup,width=1280,height=800");
        return;
      }
      const target = event.target as HTMLElement;
      const busy = /INPUT|TEXTAREA|SELECT/.test(target.tagName) || document.querySelector("[role=dialog]");
      if (busy || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      const next = SCENES[sceneForPath(window.location.pathname) + (event.key === "ArrowRight" ? 1 : -1)];
      if (next) navigate(next.path);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navigate]);

  useEffect(() => setPaletteOpen(false), [location.pathname]);

  return (
    <div className="flex h-full min-w-[1180px] flex-col">
      <CustomerBar />
      <JourneyRail />
      <main className="flex min-h-0 flex-1 flex-col">
        <Outlet />
      </main>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      {fallback !== null && (
        <video
          src={recordingPath(fallback)}
          autoPlay
          muted
          onEnded={closeFallback}
          className="fixed inset-0 z-50 size-full bg-spine object-contain"
        />
      )}    </div>
  );
}
