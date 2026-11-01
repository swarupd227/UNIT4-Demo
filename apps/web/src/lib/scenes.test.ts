import { expect, test } from "vitest";
import { formatClock, sceneForPath, SCENES, TOTAL_MINUTES } from "./scenes";

test("the script runs for the 22 minutes in the specification", () => {
  expect(SCENES).toHaveLength(9);
  expect(TOTAL_MINUTES).toBe(22);
});

test("the three protected scenes are decisions, code and reconcile", () => {
  expect(SCENES.filter((scene) => scene.protected).map((scene) => scene.number)).toEqual([2, 3, 6]);
});

test("a deep link still belongs to its scene", () => {
  expect(sceneForPath("/decisions/RP-112")).toBe(2);
  expect(sceneForPath("/code/CC-041")).toBe(3);
  expect(sceneForPath("/scorecard")).toBe(8);
});

test("the clock shows minutes and seconds", () => {
  expect(formatClock(65_000)).toBe("1:05");
  expect(formatClock(-1)).toBe("0:00");
});
