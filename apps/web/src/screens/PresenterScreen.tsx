import { useMutation } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Clapperboard, Pause, Play, RotateCcw, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { usePersona } from "../lib/persona";
import { usePresenterChannel } from "../lib/presenter";
import { formatClock, recordingPath, sceneForPath, SCENES, TOTAL_MINUTES } from "../lib/scenes";
import { Button, Kbd } from "../ui/primitives";

const RUNS_KEY = "studio.rehearsals";

type Rehearsal = { at: string; totalMs: number; scenes: number[] };

function loadRuns(): Rehearsal[] {
  try {
    return JSON.parse(localStorage.getItem(RUNS_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveRuns(runs: Rehearsal[]): void {
  try {
    localStorage.setItem(RUNS_KEY, JSON.stringify(runs));
  } catch {
    // The readout is a rehearsal aid only.
  }
}

// The presenter's own screen. Open it on the laptop and show the audience window on the projector.
export function PresenterScreen() {
  const { role } = usePersona();
  const [index, setIndex] = useState(0);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState<number[]>(() => SCENES.map(() => 0));
  const [recording, setRecording] = useState(false);
  const [recordings, setRecordings] = useState<boolean[]>(() => SCENES.map(() => false));
  const [runs, setRuns] = useState(loadRuns);
  const indexRef = useRef(index);
  indexRef.current = index;

  const send = usePresenterChannel((message) => {
    if (message.type === "at") {
      const scene = sceneForPath(message.pathname);
      if (scene >= 0) setIndex(scene);
    }
  });

  useEffect(() => {
    if (!running) return;
    let last = Date.now();
    const timer = window.setInterval(() => {
      const now = Date.now();
      const step = now - last;
      last = now;
      setElapsed((current) => current.map((value, i) => (i === indexRef.current ? value + step : value)));
    }, 250);
    return () => window.clearInterval(timer);
  }, [running]);

  useEffect(() => {
    Promise.all(
      SCENES.map((scene) =>
        fetch(recordingPath(scene.number), { method: "HEAD" })
          .then((response) => response.ok && (response.headers.get("content-type") ?? "").includes("webm"))
          .catch(() => false),
      ),
    ).then(setRecordings);
  }, []);

  const go = (next: number) => {
    const target = Math.min(Math.max(next, 0), SCENES.length - 1);
    setIndex(target);
    setRecording(false);
    send({ type: "go", path: SCENES[target].path });
  };

  const prepare = useMutation({
    mutationFn: () => api.prepare(index, role),
    onSuccess: () => send({ type: "refresh" }),
  });
  const answerOpen = useMutation({
    mutationFn: () => api.answerOpen(role),
    onSuccess: () => send({ type: "refresh" }),
  });
  const reset = useMutation({
    mutationFn: () => api.reset(role),
    onSuccess: () => {
      send({ type: "reset" });
      setRunning(false);
      setRecording(false);
      setIndex(0);
      setElapsed(SCENES.map(() => 0));
    },
  });

  const toggleRecording = () => {
    send({ type: "fallback", scene: recording ? null : index });
    setRecording(!recording);
  };

  const finish = () => {
    setRunning(false);
    const run = { at: new Date().toISOString(), totalMs: elapsed.reduce((a, b) => a + b, 0), scenes: elapsed };
    const next = [run, ...runs].slice(0, 6);
    setRuns(next);
    saveRuns(next);
  };

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "ArrowRight") go(index + 1);
      if (event.key === "ArrowLeft") go(index - 1);
      if (event.key === " ") {
        event.preventDefault();
        setRunning((value) => !value);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const scene = SCENES[index];
  const sceneBudget = scene.minutes * 60_000;
  const over = elapsed[index] > sceneBudget;
  const total = elapsed.reduce((sum, value) => sum + value, 0);

  return (
    <main className="grid h-full grid-cols-[minmax(0,1fr)_420px] gap-4 bg-spine p-4 text-on-spine">
      <section className="flex min-h-0 flex-col gap-4">
        <header className="flex items-baseline justify-between">
          <h1 className="text-[34px] font-semibold">
            <span className="tnum mr-3 text-on-spine-2">{scene.number}</span>
            {scene.title}
            {scene.protected && <span className="ml-3 text-[16px] font-medium text-on-spine-2">Never cut</span>}
          </h1>
          <p className={`tnum text-[44px] font-semibold ${over ? "text-[#f08379]" : ""}`} aria-live="off">
            {formatClock(elapsed[index])}
            <span className="text-[24px] font-normal text-on-spine-2"> / {scene.minutes}:00</span>
          </p>
        </header>
        <ul className="min-h-0 flex-1 space-y-4 overflow-y-auto text-[24px] leading-9">
          {scene.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
        <footer className="flex flex-wrap items-center gap-2">
          <Button onClick={() => go(index - 1)} disabled={index === 0}>
            <ChevronLeft size={18} aria-hidden /> Back
          </Button>
          <Button variant="primary" className="!bg-canvas !text-ink" onClick={() => go(index + 1)} disabled={index === 8}>
            Next: {SCENES[index + 1]?.title ?? "End"} <ChevronRight size={18} aria-hidden />
          </Button>
          <Button onClick={() => setRunning(!running)}>
            {running ? <Pause size={18} aria-hidden /> : <Play size={18} aria-hidden />}
            {running ? "Pause" : "Start"} <Kbd>Space</Kbd>
          </Button>
          <Button onClick={finish} disabled={total === 0}>
            <Square size={16} aria-hidden /> Log this run
          </Button>
          <Button onClick={toggleRecording} disabled={!recordings[index]}>
            <Clapperboard size={18} aria-hidden />
            {recording ? "Back to live" : recordings[index] ? "Play recording" : "No recording"}
          </Button>
          <Button onClick={() => prepare.mutate()} disabled={prepare.isPending}>
            {prepare.isPending ? "Preparing…" : `Prepare scene ${index}`}
          </Button>
          <Button onClick={() => answerOpen.mutate()} disabled={answerOpen.isPending}>
            Answer customer questions
          </Button>
          <Button onClick={() => reset.mutate()} disabled={reset.isPending}>
            <RotateCcw size={16} aria-hidden /> Reset
          </Button>
        </footer>
      </section>

      <aside className="flex min-h-0 flex-col gap-4 overflow-y-auto rounded-xl bg-spine-2 p-4">
        <div>
          <h2 className="text-[15px] font-semibold text-on-spine-2">Total</h2>
          <p className="tnum text-[32px] font-semibold">
            {formatClock(total)}
            <span className="text-[18px] font-normal text-on-spine-2"> / {TOTAL_MINUTES}:00</span>
          </p>
        </div>
        <ol className="tnum space-y-1 text-[16px]">
          {SCENES.map((entry, i) => (
            <li key={entry.number}>
              <button
                type="button"
                aria-current={i === index ? "step" : undefined}
                onClick={() => go(i)}
                className={`flex w-full justify-between rounded-md px-2 py-1 text-left ${
                  i === index ? "bg-canvas text-ink" : "hover:bg-spine"
                }`}
              >
                <span>
                  {entry.number} {entry.title}
                </span>
                <span>
                  {formatClock(elapsed[i])} / {entry.minutes}:00
                </span>
              </button>
            </li>
          ))}
        </ol>
        <div>
          <h2 className="mb-1 text-[15px] font-semibold text-on-spine-2">Rehearsals</h2>
          {runs.length === 0 ? (
            <p className="text-[15px] text-on-spine-2">None logged yet.</p>
          ) : (
            <ul className="tnum space-y-0.5 text-[15px]">
              {runs.map((run) => (
                <li key={run.at} className="flex justify-between">
                  <span>{new Date(run.at).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short" })}</span>
                  <span className={run.totalMs > TOTAL_MINUTES * 60_000 ? "text-[#f08379]" : ""}>
                    {formatClock(run.totalMs)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </main>
  );
}
