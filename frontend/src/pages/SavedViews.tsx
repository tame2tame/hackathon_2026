import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import { Failure, useAction, useResource } from "./shared";
export function SavedViews({ page }: { page: "interactions" | "radar" }) {
  const [params, setParams] = useSearchParams();
  const [name, setName] = useState("");
  const q = useResource<Schema["SavedViewOut"][]>("/saved-views", { page });
  const save = useAction(async () => {
    const r = await api.send("/saved-views", {
      page,
      name,
      filters: Object.fromEntries(params),
    });
    setName("");
    return r;
  });
  return (
    <div className="saved-views">
      <Select
        aria-label="Сохранённый вид"
        value=""
        onChange={(e) => {
          const view = q.data?.find((v) => v.id === e.target.value);
          if (view) {
            const p = new URLSearchParams();
            for (const [k, v] of Object.entries(view.filters))
              if (typeof v === "string" || typeof v === "number")
                p.set(k, String(v));
            setParams(p);
          }
        }}
      >
        <option value="">Сохранённые виды</option>
        {q.data?.map((v) => (
          <option key={v.id} value={v.id}>
            {v.name}
          </option>
        ))}
      </Select>
      <input
        aria-label="Название вида"
        placeholder="Название текущего вида"
        maxLength={100}
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Button
        variant="ghost"
        disabled={!name.trim() || save.isPending}
        onClick={() => save.mutate()}
      >
        Сохранить вид
      </Button>
      <Failure error={save.error || q.error} />
    </div>
  );
}
