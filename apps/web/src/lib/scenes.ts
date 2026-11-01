// The nine scenes of the demo script, in order. Timings are from the demo specification.
export type Scene = {
  number: number;
  title: string;
  path: string;
  minutes: number;
  protected: boolean;
  notes: string[];
};

export const SCENES: Scene[] = [
  {
    number: 0,
    title: "Set the scene",
    path: "/customer",
    minutes: 1,
    protected: false,
    notes: [
      "Introduce Ardleigh and its goal: reach ERPx with fewer customisations.",
      "Say plainly that everything is synthetic, with no payroll or HR data.",
      "Say that the ERPx target is simulated and the agent results are authored.",
    ],
  },
  {
    number: 1,
    title: "Load the estate",
    path: "/estate",
    minutes: 2,
    protected: false,
    notes: [
      "Press Load the estate. J2X output arrives first, because this builds on it.",
      "Point at the estate map: J2X explains, and this work starts after that.",
      "Time by stage is to be baselined. We assume no baseline.",
    ],
  },
  {
    number: 2,
    title: "Decisions",
    path: "/decisions?outcome=retire",
    minutes: 4,
    protected: true,
    notes: [
      "Routine items are seeded as earlier work, and the app says so.",
      "On the Retire filter, open RP-112, the Year-end audit pack.",
      "It looks unused, and the system refused to retire it. Show the evidence.",
      "Press A on a retirement: it waits for the customer. Nothing moves alone.",
    ],
  },
  {
    number: 3,
    title: "Custom code",
    path: "/code/CC-014",
    minutes: 4,
    protected: true,
    notes: [
      "Read the plain English first, then select a hidden rule to find its line.",
      "Show the conflict: 10% in code, 15% in policy. The customer decides.",
      "Show the INT-09 dependency, then the extension spec and tests.",
      "Direct database writes cannot move to Unit4 cloud.",
    ],
  },
  {
    number: 4,
    title: "Reports",
    path: "/reports",
    minutes: 3,
    protected: false,
    notes: [
      "148 custom reports reduce to 26, with two held for the customer.",
      "Rebuild WIP ageing by partner. Step 1 matches to the penny.",
      "Fix the list. The difference is exactly the omitted partners' WIP.",
    ],
  },
  {
    number: 5,
    title: "Workflows",
    path: "/workflows",
    minutes: 2,
    protected: false,
    notes: [
      "Two variants handle most approvals. Show the proposal: 9 to 3.",
      "WF-006 is used only by a dormant entity.",
      "Controls are the customer's call, so send the pack.",
    ],
  },
  {
    number: 6,
    title: "Reconcile",
    path: "/reconcile",
    minutes: 4,
    protected: true,
    notes: [
      "Run the checks. Plain code, no language model.",
      "Open R2: £1,240.50, traced to rate precision, and not line rounding.",
      "R4: 14 closed projects hold WIP. R6: the VAT conflict and duplicate value.",
      "Ask the customer, switch to Jordan, choose the threshold, switch back, run again.",
      "Run once more to show the identical result.",
    ],
  },
  {
    number: 7,
    title: "Sign-off pack",
    path: "/signoff",
    minutes: 1,
    protected: false,
    notes: [
      "This accepts a trial migration with listed exceptions. It is not cutover.",
      "Say that undecided items remain, and name the seeded history.",
      "Generate the pack, switch to Jordan, sign.",
    ],
  },
  {
    number: 8,
    title: "Results",
    path: "/scorecard",
    minutes: 1,
    protected: false,
    notes: [
      "Ten of ten planted issues, on synthetic data, against an answer key.",
      "We quote no percentage saving, because there is no baseline.",
      "Open for questions: 10 minutes.",
    ],
  },
];

export const TOTAL_MINUTES = SCENES.reduce((sum, scene) => sum + scene.minutes, 0);

export function sceneForPath(pathname: string): number {
  const stage = pathname.split("/")[1];
  return SCENES.findIndex((scene) => scene.path.split(/[/?]/)[1] === stage);
}

export function formatClock(milliseconds: number): string {
  const seconds = Math.max(0, Math.floor(milliseconds / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export function recordingPath(scene: number): string {
  return `/fallback/scene-${scene}.webm`;
}
