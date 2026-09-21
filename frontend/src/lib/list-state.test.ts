import { describe, expect, it } from "vitest";
import {
  listReturnTo,
  pageRange,
  readListState,
  updateListState,
} from "./list-state";
describe("Состояние списков", () => {
  it("восстанавливает фильтры и страницу из адреса", () => {
    expect(
      readListState(
        new URLSearchParams("q=МГТУ&severity=high&kind=stage_overdue&page=3"),
      ),
    ).toMatchObject({
      search: "МГТУ",
      severity: "high",
      kind: "stage_overdue",
      page: 3,
    });
  });
  it("не передаёт некорректные фильтры в API", () => {
    expect(
      readListState(
        new URLSearchParams(
          "severity=urgent&kind=unknown&group=bad&owner=bad&stage=%3Ctag%3E&page=-2",
        ),
      ),
    ).toMatchObject({
      severity: "",
      kind: "",
      group: "",
      owner: "",
      stage: "",
      page: 1,
    });
    expect(readListState(new URLSearchParams("page=1.5")).page).toBe(1);
  });
  it("смена группы сбрасывает этап и страницу, сохраняя поиск", () => {
    const original = new URLSearchParams(
      "q=Клиент&group=old&stage=signing&page=4",
    );
    const next = updateListState(original, { group: "new" });
    expect(next.toString()).toBe(
      "q=%D0%9A%D0%BB%D0%B8%D0%B5%D0%BD%D1%82&group=new",
    );
    expect(original.get("page")).toBe("4");
  });
  it("пагинация сохраняет фильтры, смена фильтра возвращает на первую страницу", () => {
    const params = new URLSearchParams("severity=high&page=3");
    expect(updateListState(params, { page: 4 }).get("severity")).toBe("high");
    expect(updateListState(params, { severity: null }).toString()).toBe("");
  });
  it("возвращает только на внутренние списки", () => {
    expect(listReturnTo("/radar?severity=high")).toBe("/radar?severity=high");
    for (const value of [
      "https://example.com",
      "//example.com",
      "/interactions/../admin",
      null,
    ])
      expect(listReturnTo(value)).toBe("/interactions");
  });
  it("правильно показывает диапазон последней и пустой страницы", () => {
    expect(pageRange(2, 23)).toBe("21–23 из 23");
    expect(pageRange(1, 0)).toBe("0 из 0");
    expect(pageRange(3, 23)).toBe("0 из 23");
  });
});
