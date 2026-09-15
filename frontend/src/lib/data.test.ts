import { describe, expect, it } from "vitest";
import { advance, hasSignal, initialData, visibleData } from "./data";
describe("Демонстрационные взаимодействия", () => {
  it("КАМ видит только свои записи", () => {
    expect(visibleData(initialData, "kam")).toHaveLength(4);
    expect(
      visibleData(initialData, "kam").every((i) => i.owner === "Анна Смирнова"),
    ).toBe(true);
  });
  it("переход сохраняет историю, закрывает задержку и не меняет исходные данные", () => {
    const updated = advance(initialData, "int-001", "Договор согласован");
    expect(updated[0].stage).toBe(6);
    expect(updated[0].history[0].text).toContain("Договор согласован");
    expect(hasSignal(updated[0])).toBe(false);
    expect(initialData[0].stage).toBe(5);
  });
  it("переход не закрывает независимый сигнал лицензии", () => {
    expect(
      hasSignal(advance(initialData, "int-002", "Занятия завершены")[1]),
    ).toBe(true);
  });
  it("пустой комментарий отклоняется", () => {
    expect(() => advance(initialData, "int-001", "  ")).toThrow(
      "COMMENT_REQUIRED",
    );
  });
  it("финальный этап не выходит за границы workflow", () => {
    const final = [{ ...initialData[0], stage: 13 }];
    expect(advance(final, "int-001", "Завершено")[0].stage).toBe(13);
  });
});
