import { expect, it } from "vitest";
import {
  completedVisits,
  durationChart,
  slices,
  timeline,
} from "./analytics-data";
import type { Schema } from "../api/types";
const history = [
  ["2026-09-01", "a"],
  ["2026-09-05", "b"],
  ["2026-09-10", "a"],
].map(([occurred_at, code], i) => ({
  id: String(i),
  occurred_at: occurred_at + "T00:00:00Z",
  to_stage: { code, name: code },
  from_stage: i ? { code: "a", name: "a" } : null,
})) as Schema["TransitionOut"][];
it("длительность считается по завершённым посещениям, не по текущему количеству", () => {
  expect(
    completedVisits([{ history: [...history].reverse() }]).map((v) => v.days),
  ).toEqual([4, 5]);
  expect(
    durationChart([{ history }], [{ name: "a" }, { name: "b" }, { name: "c" }])
      .values,
  ).toEqual([4, 5]);
});
it("динамика считает переходы по датам, исключая создание и будущие события", () => {
  const data = timeline(
    [{ history }],
    30,
    "transitions",
    "",
    new Date("2026-09-08"),
  );
  expect(data.values.reduce<number>((a, v) => a + (v || 0), 0)).toBe(1);
});
it("динамика длительности сохраняет пробелы без наблюдений и фильтрует этап", () => {
  const data = timeline(
    [{ history }],
    30,
    "duration",
    "a",
    new Date("2026-09-12"),
  );
  expect(data.values.filter((v) => v !== null)).toEqual([4]);
  expect(data.samples.reduce((a, b) => a + b, 0)).toBe(1);
});
it("нулевые доли не рисуются, индексы фильтра остаются исходными", () => {
  expect(
    slices({
      title: "",
      labels: ["a", "b", "c"],
      values: [0, 3, 1],
      option: {},
    }),
  ).toMatchObject([
    { index: 1, share: 0.75, offset: 0 },
    { index: 2, share: 0.25, offset: 0.75 },
  ]);
  expect(slices({ title: "", labels: ["a"], values: [0], option: {} })).toEqual(
    [],
  );
});
