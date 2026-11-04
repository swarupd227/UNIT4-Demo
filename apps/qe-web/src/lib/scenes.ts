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
    path: "/area",
    minutes: 1,
    protected: false,
    notes: [
      "One legacy area, project billing, from not ready for MOSAIC toward the coverage gate.",
      "Say plainly that the module, its tests and its history are synthetic, built to behave like long-lived ERP code.",
      "Name Full Circuit and the Context Engine: this adds capacity and independent checks to them.",
    ],
  },
  {
    number: 1,
    title: "Coverage map",
    path: "/coverage",
    minutes: 3,
    protected: true,
    notes: [
      "7 of 12 critical rules are covered. A rule counts only when its tests catch its seeded faults.",
      "Open BR-04, multi-currency rounding: no automated test, 4 seeded faults, none caught.",
      "BR-11 has a test, but it catches 1 of 3 faults. A test that passes is not the same as a test that protects.",
    ],
  },
  {
    number: 2,
    title: "Context",
    path: "/context",
    minutes: 3,
    protected: false,
    notes: [
      "Open the BR-04 risk card: 7 defects, all in RoundingHelper.cs, 2 fixed with no test at all.",
      "Open Hidden rules: write-downs over 10% need approval. It is in the code and nowhere else.",
      "Switch to Ravi Menon and approve the entries. Only approved context is exported.",
    ],
  },
  {
    number: 3,
    title: "Generate",
    path: "/tests",
    minutes: 3,
    protected: false,
    notes: [
      "Intake first: one case conflicts with the help pages, one is too vague, two are duplicates.",
      "Ten tests from five manual cases, four defects and the hidden rule.",
      "Open a test: our suite's fixtures, page objects and naming, standing in for Full Circuit's.",
    ],
  },
  {
    number: 4,
    title: "Prove tests",
    path: "/proof",
    minutes: 4,
    protected: true,
    notes: [
      "Four checks: conventions, the validator that never sees the code, seeded faults and 20 runs.",
      "Point at case 48224: it passed everything but still passed with the minimum set to 5 EUR. Rejected, regenerated.",
      "Run one check now: put the rounding bug back and watch its test fail.",
      "Coverage moves from 7 to 9 of 12. Still below the gate, and the gap list says why.",
    ],
  },
  {
    number: 5,
    title: "Flaky tests",
    path: "/flaky",
    minutes: 2,
    protected: false,
    notes: [
      "Twenty runs each. BR-09 waits a fixed two seconds; BR-01 shares a customer with the discount test.",
      "Show the fixes and the new rate: no failures in 20 runs of the whole suite.",
      "Next release relabels a field: five tests break, one line in a page object repairs them.",
    ],
  },
  {
    number: 6,
    title: "Engineer review",
    path: "/review",
    minutes: 2,
    protected: true,
    notes: [
      "Switch to Ravi Menon. Each test carries its source, the validator's result, its faults and its runs.",
      "Approve each item, then merge. It is a real Git commit in the module's repository.",
      "Release controls unchanged: only tests change, the pipeline does not.",
    ],
  },
  {
    number: 7,
    title: "Gaps and pack",
    path: "/gaps",
    minutes: 1,
    protected: false,
    notes: [
      "BR-11, BR-15 and BR-19 are still below the gate, ranked by risk.",
      "Dead code needs no test. Download the evidence pack.",
    ],
  },
  {
    number: 8,
    title: "Results",
    path: "/scorecard",
    minutes: 1,
    protected: false,
    notes: [
      "Coverage, faults caught, reliability, maintenance and manual effort: all measured, before and after.",
      "Escaped defects need a pilot. No productivity multiple is claimed.",
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
