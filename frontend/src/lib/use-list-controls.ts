import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  filterKeys,
  readListState,
  updateListState,
  type FilterKey,
} from "./list-state";
export function useListControls() {
  const [params, setParams] = useSearchParams();
  const latest = useRef(params);
  useEffect(() => {
    latest.current = params;
  }, [params]);
  const state = readListState(params);
  const [value, setValue] = useState(state.search.trim());
  useEffect(() => {
    const timer = setTimeout(() => setValue(state.search.trim()), 250);
    return () => clearTimeout(timer);
  }, [state.search]);
  const update = (
    patch: Partial<Record<FilterKey, string | number | null>>,
  ) => {
    // Router не объединяет несколько setSearchParams до следующего рендера.
    latest.current = updateListState(latest.current, patch);
    setParams(latest.current, { replace: true });
  };
  return {
    ...state,
    value,
    setSearch: (q: string) => update({ q }),
    setGroup: (group: string) => update({ group }),
    setKind: (kind: string) => update({ kind }),
    setSeverity: (severity: string) => update({ severity }),
    setStage: (stage: string) => update({ stage }),
    setDirection: (direction: string) => update({ direction }),
    setOwner: (owner: string) => update({ owner }),
    setPage: (page: number) => update({ page }),
    reset: () => {
      setValue("");
      const next = new URLSearchParams(latest.current);
      filterKeys.forEach((key) => next.delete(key));
      latest.current = next;
      setParams(next, { replace: true });
    },
    filtered: Boolean(
      state.search ||
      state.group ||
      state.kind ||
      state.severity ||
      state.stage ||
      state.owner ||
      state.direction,
    ),
  };
}
