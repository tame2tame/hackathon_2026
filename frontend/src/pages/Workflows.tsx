import { CreateProcess } from "./Groups";
import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Heading } from "../App";
import { api } from "../api/runtime";
import type { Me, Schema } from "../api/types";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import {
  Failure,
  Field,
  Panel,
  State,
  enc,
  useAction,
  useResource,
} from "./shared";
export function WorkflowsPage({ me }: { me: Me }) {
  const q = useResource<Schema["WorkflowSummaryOut"][]>("/workflows");
  const [selected, setSelected] = useState("");
  const id = selected || q.data?.[0]?.id || "";
  return (
    <>
      <Heading
        eyebrow="УПРАВЛЕНИЕ"
        title="Этапы взаимодействий"
        text="Настройте процесс и нормы сроков. Перед применением изменений покажем их влияние на записи."
      />
      <CreateProcess />
      <Field label="Процесс">
        <Select value={id} onChange={(e) => setSelected(e.target.value)}>
          {q.data?.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </Select>
      </Field>
      <State query={q}>
        {id && (
          <Process
            key={id}
            id={id}
            me={me}
            draftId={q.data?.find((w) => w.id === id)?.draft_version_id || null}
          />
        )}
      </State>
    </>
  );
}
function Process({
  id,
  me,
  draftId,
}: {
  id: string;
  me: Me;
  draftId: string | null;
}) {
  const q = useResource<Schema["WorkflowOut"]>(`/workflows/${id}`);
  const norms = useResource<Schema["StageNormOut"][]>(`/workflows/${id}/norms`);
  const [draft, setDraft] = useState<Schema["VersionOut"] | null>(null);
  const [stages, setStages] = useState<Schema["StageDraft"][]>([]);
  const [transitions, setTransitions] = useState<Schema["TransitionDraft"][]>(
    [],
  );
  const [preview, setPreview] = useState<Schema["PublishPreview"] | null>(null);
  const begin = useAction(async () => {
    const d = draftId
      ? await api.send<Schema["VersionOut"]>(
          `/workflow-versions/${draftId}`,
          {},
          "PATCH",
        )
      : await api.send<Schema["VersionOut"]>(`/workflows/${id}/versions`);
    setDraft(d);
    setStages(
      d.stages.map((s) => ({
        ...s,
        kind: s.kind as Schema["StageDraft"]["kind"],
      })),
    );
    setTransitions(
      d.transitions.map((t) => ({
        from_code: d.stages.find((s) => s.id === t.from_stage_id)!.code,
        to_code: d.stages.find((s) => s.id === t.to_stage_id)!.code,
        requires_comment: t.requires_comment,
        requires_attachment: t.requires_attachment,
      })),
    );
    return d;
  });
  const check = useAction(async () => {
    await api.send(
      `/workflow-versions/${draft!.id}`,
      {
        stages: stages.map((s, i) => ({ ...s, position: i + 1 })),
        transitions,
      },
      "PATCH",
    );
    const p = await api.send<Schema["PublishPreview"]>(
      `/workflow-versions/${draft!.id}/publish-preview`,
    );
    setPreview(p);
    return p;
  });
  const publish = useAction(async () => {
    const p = await api.send(`/workflow-versions/${draft!.id}/publish`, {});
    setDraft(null);
    setPreview(null);
    return p;
  });
  return (
    <>
      <Panel
        title="Действующий процесс"
        action={
          <Button disabled={begin.isPending} onClick={() => begin.mutate()}>
            {draftId ? "Продолжить изменения" : "Подготовить изменения"}
          </Button>
        }
      >
        <Failure error={begin.error} />
        <State query={q}>
          <div className="process-chain">
            {q.data?.stages.map((s, i) => (
              <div key={s.id}>
                <b>{i + 1}</b>
                <span>
                  {s.name}
                  <small>{s.norm_days ?? "—"} дней</small>
                </span>
              </div>
            ))}
          </div>
        </State>
      </Panel>
      <Panel title="Нормы сроков">
        <State query={norms}>
          {norms.data?.map((n) => (
            <Norm key={`${n.stage_code}-${n.norm_days}`} norm={n} id={id} />
          ))}
        </State>
      </Panel>
      {draft && (
        <Panel title="Изменения до применения">
          <p>
            Этапы применятся ко всем открытым записям. Переименовать
            существующий этап может только администратор.
          </p>
          {stages.map((s, i) => (
            <div className="stage-editor" key={s.code}>
              <span className="count-pill">{i + 1}</span>
              <Field label="Название этапа">
                <input
                  value={s.name}
                  disabled={
                    me.role !== "admin" &&
                    draft.stages.some((old) => old.code === s.code)
                  }
                  onChange={(e) =>
                    setStages(
                      stages.map((v, j) =>
                        i === j ? { ...v, name: e.target.value } : v,
                      ),
                    )
                  }
                />
              </Field>
              <Field label="Норма, дней">
                <input
                  type="number"
                  min="1"
                  value={s.norm_days ?? ""}
                  onChange={(e) =>
                    setStages(
                      stages.map((v, j) =>
                        i === j
                          ? {
                              ...v,
                              norm_days: e.target.value
                                ? Number(e.target.value)
                                : null,
                            }
                          : v,
                      ),
                    )
                  }
                />
              </Field>
              <Field label="Тип этапа">
                <Select
                  value={s.kind}
                  onChange={(e) =>
                    setStages(
                      stages.map((v, j) =>
                        i === j
                          ? {
                              ...v,
                              kind: e.target
                                .value as Schema["StageDraft"]["kind"],
                            }
                          : v,
                      ),
                    )
                  }
                >
                  <option value="start">Начальный</option>
                  <option value="normal">Обычный</option>
                  <option value="final">Финальный</option>
                </Select>
              </Field>
              <label>
                <input
                  type="checkbox"
                  checked={s.bulk_allowed}
                  onChange={(e) =>
                    setStages(
                      stages.map((v, j) =>
                        i === j ? { ...v, bulk_allowed: e.target.checked } : v,
                      ),
                    )
                  }
                />
                Групповой переход
              </label>
              <Button
                variant="ghost"
                disabled={i === 0}
                onClick={() => {
                  const next = [...stages];
                  [next[i - 1], next[i]] = [next[i], next[i - 1]];
                  setStages(next);
                }}
              >
                ↑
              </Button>
              <Button
                variant="ghost"
                disabled={i === stages.length - 1}
                onClick={() => {
                  const next = [...stages];
                  [next[i + 1], next[i]] = [next[i], next[i + 1]];
                  setStages(next);
                }}
              >
                ↓
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setStages(stages.filter((_, j) => j !== i));
                  setTransitions(
                    transitions.filter(
                      (t) => t.from_code !== s.code && t.to_code !== s.code,
                    ),
                  );
                }}
              >
                Убрать
              </Button>
            </div>
          ))}
          <Button
            variant="outline"
            onClick={() =>
              setStages([
                ...stages,
                {
                  code: `stage_${Date.now()}`,
                  name: "Новый этап",
                  position: stages.length + 1,
                  kind: "normal",
                  bulk_allowed: false,
                  required_document_types: [],
                  norm_days: 14,
                },
              ])
            }
          >
            Добавить этап
          </Button>
          <h3 className="subsection-title">Разрешённые переходы</h3>
          {transitions.map((t, i) => (
            <div className="service-row" key={i}>
              <Select
                aria-label="Откуда"
                value={t.from_code}
                onChange={(e) =>
                  setTransitions(
                    transitions.map((v, j) =>
                      i === j ? { ...v, from_code: e.target.value } : v,
                    ),
                  )
                }
              >
                {stages.map((s) => (
                  <option key={s.code} value={s.code}>
                    {s.name}
                  </option>
                ))}
              </Select>
              <span>→</span>
              <Select
                aria-label="Куда"
                value={t.to_code}
                onChange={(e) =>
                  setTransitions(
                    transitions.map((v, j) =>
                      i === j ? { ...v, to_code: e.target.value } : v,
                    ),
                  )
                }
              >
                {stages.map((s) => (
                  <option key={s.code} value={s.code}>
                    {s.name}
                  </option>
                ))}
              </Select>
              <label>
                <input
                  type="checkbox"
                  checked={t.requires_comment}
                  onChange={(e) =>
                    setTransitions(
                      transitions.map((v, j) =>
                        i === j
                          ? { ...v, requires_comment: e.target.checked }
                          : v,
                      ),
                    )
                  }
                />{" "}
                Комментарий
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={t.requires_attachment}
                  onChange={(e) =>
                    setTransitions(
                      transitions.map((v, j) =>
                        i === j
                          ? { ...v, requires_attachment: e.target.checked }
                          : v,
                      ),
                    )
                  }
                />{" "}
                Документ
              </label>
              <Button
                variant="ghost"
                onClick={() =>
                  setTransitions(transitions.filter((_, j) => i !== j))
                }
              >
                Убрать
              </Button>
            </div>
          ))}
          <div className="service-toolbar">
            <Button
              variant="outline"
              disabled={stages.length < 2}
              onClick={() =>
                setTransitions([
                  ...transitions,
                  {
                    from_code: stages[0].code,
                    to_code: stages[1].code,
                    requires_comment: true,
                    requires_attachment: false,
                  },
                ])
              }
            >
              Добавить переход
            </Button>
            <Button
              disabled={!stages.length || check.isPending}
              onClick={() => check.mutate()}
            >
              Проверить и применить
            </Button>
          </div>
          <Failure error={check.error} />
        </Panel>
      )}
      <Dialog.Root
        open={!!preview}
        onOpenChange={(v) => {
          if (!v && !publish.isPending) setPreview(null);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content className="dialog-content">
            <Dialog.Title>Применить изменения процесса?</Dialog.Title>
            <Dialog.Description>
              Открытых записей перейдёт на новый процесс:{" "}
              {preview?.moved_interactions ?? 0}.
            </Dialog.Description>
            {preview?.renamed.map((r) => (
              <p key={r.code}>
                {r.old_name} → {r.new_name}
              </p>
            ))}
            {preview?.moves.map((r) => (
              <p key={r.from_code}>
                {r.from_name} → {r.to_name}: {r.open_interactions} записей{" "}
                {r.automatic ? "(автоматически)" : ""}
              </p>
            ))}
            {preview?.added.map((s) => (
              <p key={s.id}>Добавлен этап: {s.name}</p>
            ))}
            {preview?.requires_admin && me.role !== "admin" && (
              <p className="error-copy">
                Для переименования нужен администратор.
              </p>
            )}
            <Failure error={publish.error} />
            <div className="dialog-actions">
              <Button
                variant="outline"
                disabled={publish.isPending}
                onClick={() => setPreview(null)}
              >
                Отмена
              </Button>
              <Button
                disabled={
                  publish.isPending ||
                  (preview?.requires_admin && me.role !== "admin")
                }
                onClick={() => publish.mutate()}
              >
                Применить
              </Button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
function Norm({ norm: n, id }: { norm: Schema["StageNormOut"]; id: string }) {
  const [value, setValue] = useState(n.norm_days);
  const save = useAction(() =>
    api.send(
      `/workflows/${id}/norms/${enc(n.stage_code)}`,
      { norm_days: value },
      "PUT",
    ),
  );
  const accept = useAction(() =>
    api.send(`/workflows/${id}/norms/${enc(n.stage_code)}/accept-suggestion`),
  );
  return (
    <form
      className="service-row"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <div className="grow">
        <h3>{n.stage_name}</h3>
        <small>
          {n.suggested_median_days === null
            ? "Недостаточно наблюдений"
            : `Медиана: ${n.suggested_median_days} дн. · 80%: ${n.suggested_percentile_days} дн. · Выборка: ${n.sample_size}`}
        </small>
      </div>
      <Field label="Норма, дней">
        <input
          type="number"
          min="1"
          max="3650"
          required
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
        />
      </Field>
      <Button variant="outline" disabled={save.isPending}>
        Сохранить
      </Button>
      <Button
        type="button"
        variant="ghost"
        disabled={n.suggested_median_days === null || accept.isPending}
        onClick={() => accept.mutate()}
      >
        Принять подсказку
      </Button>
      <Failure error={save.error || accept.error} />
    </form>
  );
}
