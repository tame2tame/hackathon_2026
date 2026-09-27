import { Mail, Send, MessageCircle, Bell } from "lucide-react";
import { Markdown } from "../components/Markdown";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Heading } from "../App";
import { api } from "../api/runtime";
import { mode } from "../auth/config";
import type { Me, Schema } from "../api/types";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import {
  EmptyData,
  Failure,
  Field,
  Panel,
  State,
  enc,
  when,
  useAction,
  useResource,
  Pager,
} from "./shared";
export function LiveUpdates({ identity }: { identity: string }) {
  const cache = useQueryClient();
  const [offline, setOffline] = useState(false);
  useEffect(() => {
    if (mode === "mock") return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let stopped = false;
    let cursor = "";
    const run = async () => {
      try {
        cursor = await api.events(
          controller.signal,
          (_event, id) => {
            cursor = id;
            setOffline(false);
            void cache.invalidateQueries({
              predicate: (q) => q.queryKey[0] !== "interaction",
            });
          },
          cursor,
        );
      } catch {
        if (!stopped) setOffline(true);
      }
      if (!stopped) timer = setTimeout(() => void run(), 5000);
    };
    void run();
    return () => {
      stopped = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [identity, cache]);
  return offline ? (
    <div className="live-warning" role="status">
      Живые обновления временно недоступны. Можно обновить данные кнопкой на
      странице.
    </div>
  ) : null;
}
export function MessagesPage({ me }: { me: Me }) {
  const dialogs = useResource<Schema["DialogsOut"]>("/messages");
  const users = useResource<Schema["UserOut"][]>("/users");
  const [peer, setPeer] = useState("");
  const [body, setBody] = useState("");
  const messages = useResource<Schema["MessageOut"][]>(
    `/messages/${peer}`,
    {},
    !!peer,
  );
  const send = useAction(async () => {
    const r = await api.send("/messages", { recipient_id: peer, body });
    setBody("");
    return r;
  });
  const read = useAction(() => api.send(`/messages/${peer}/read`));
  return (
    <>
      <Heading
        eyebrow="РАБОЧЕЕ ПРОСТРАНСТВО"
        title="Сообщения"
        text="Обсуждайте работу с коллегами внутри сервиса."
      />
      <div className="messages-layout">
        <Panel title={`Диалоги · ${dialogs.data?.unread_total ?? 0} новых`}>
          <Field label="Начать диалог">
            <Select value={peer} onChange={(e) => setPeer(e.target.value)}>
              <option value="">Выберите коллегу</option>
              {users.data
                ?.filter((u) => u.id !== me.id)
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name}
                  </option>
                ))}
            </Select>
          </Field>
          <State query={dialogs}>
            {dialogs.data?.items.map((d) => (
              <button
                className={`dialog-peer ${peer === d.peer.id ? "active" : ""}`}
                key={d.peer.id}
                onClick={() => setPeer(d.peer.id)}
              >
                <strong>{d.peer.full_name}</strong>
                <small>{d.last_message}</small>
                {d.unread > 0 && <b>{d.unread}</b>}
              </button>
            ))}
          </State>
        </Panel>
        <Panel
          title={
            users.data?.find((u) => u.id === peer)?.full_name ||
            "Выберите диалог"
          }
        >
          {peer ? (
            <>
              <State query={messages}>
                <div className="message-stream">
                  {messages.data?.map((m) => (
                    <article
                      key={m.id}
                      className={`message-bubble ${m.sender.id === me.id ? "mine" : ""}`}
                    >
                      <p>{m.body}</p>
                      {m.interaction && (
                        <Link to={`/interactions/${m.interaction.id}`}>
                          Открыть взаимодействие ↗
                        </Link>
                      )}
                      <small>{when(m.created_at)}</small>
                    </article>
                  ))}
                </div>
              </State>
              <Button
                variant="ghost"
                disabled={read.isPending}
                onClick={() => read.mutate()}
              >
                Отметить прочитанным
              </Button>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  send.mutate();
                }}
              >
                <Field label="Сообщение">
                  <textarea
                    maxLength={4000}
                    required
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                  />
                </Field>
                <Button disabled={!body.trim() || send.isPending}>
                  Отправить
                </Button>
                <Failure error={send.error || read.error} />
              </form>
            </>
          ) : (
            <EmptyData />
          )}
        </Panel>
      </div>
    </>
  );
}
export function NotificationsPage() {
  const [page, setPage] = useState(1);
  const q = useResource<Schema["Page_NotificationOut_"]>("/notifications", {
    page,
    page_size: 20,
  });
  const read = useAction(() => api.send("/notifications/read-all"));
  const addresses = useResource<Schema["AddressOut"][]>(
    "/me/notification-addresses",
  );
  return (
    <>
      <Heading
        eyebrow="РАБОЧЕЕ ПРОСТРАНСТВО"
        title="Уведомления"
        text="Изменения этапов, важные события и зависшие записи."
      />
      <Panel
        title="Лента событий"
        action={
          <Button
            variant="outline"
            disabled={read.isPending || !q.data?.items.some((n) => !n.read_at)}
            onClick={() => read.mutate()}
          >
            Прочитать все
          </Button>
        }
      >
        <Failure error={read.error} />
        <State query={q}>
          {q.data?.items.map((n) => (
            <article key={n.id} className="service-row">
              <span className={`notification-dot ${n.read_at ? "read" : ""}`} />
              <div className="grow">
                <h3>{n.title}</h3>
                <p>{n.body}</p>
                <small>{when(n.created_at)}</small>
              </div>
              {n.interaction_id && (
                <Link to={`/interactions/${n.interaction_id}`}>Открыть ↗</Link>
              )}
            </article>
          ))}
          {!q.data?.items.length && (
            <div className="notification-empty">
              <Bell size={28} />
              <h3>Вы ничего не пропустили</h3>
              <p>
                Здесь появятся изменения этапов, важные события и напоминания.
              </p>
            </div>
          )}
          {!!q.data?.total && (
            <Pager page={page} total={q.data.total} onPage={setPage} />
          )}
        </State>
      </Panel>
      <Panel title="Куда доставлять уведомления">
        <p className="chart-hint">
          Подключите удобные каналы. Настройки каждого канала сохраняются
          отдельно.
        </p>
        <State query={addresses}>
          {addresses.data?.map((a) => (
            <Address key={a.channel_kind} item={a} />
          ))}
        </State>
      </Panel>
    </>
  );
}
export function Address({ item: a }: { item: Schema["AddressOut"] }) {
  const [address, setAddress] = useState(a.address || "");
  const [enabled, setEnabled] = useState(a.is_enabled);
  const save = useAction(() =>
    api.send(
      `/me/notification-addresses/${a.channel_kind}`,
      { address: address.trim(), is_enabled: enabled },
      "PUT",
    ),
  );
  const dirty =
    address.trim() !== (a.address || "") || enabled !== a.is_enabled;
  const Icon =
    a.channel_kind === "email"
      ? Mail
      : a.channel_kind === "telegram"
        ? Send
        : MessageCircle;
  return (
    <form
      className="notification-channel"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <div className={`channel-identity channel-${a.channel_kind}`}>
        <span className="channel-icon">
          <Icon size={22} />
        </span>
        <div>
          <h3>{a.channel_name}</h3>
          <small>
            {a.channel_enabled
              ? "Доступен для подключения"
              : "Выключен администратором"}
          </small>
        </div>
      </div>
      <Field
        label={
          a.channel_kind === "email"
            ? "Адрес электронной почты"
            : a.channel_kind === "max"
              ? "Идентификатор пользователя Max"
              : "Идентификатор чата Telegram"
        }
      >
        <input
          required
          disabled={!a.channel_enabled || save.isPending}
          type={a.channel_kind === "email" ? "email" : "text"}
          placeholder={
            a.channel_kind === "email"
              ? "name@example.com"
              : a.channel_kind === "max"
                ? "ID пользователя"
                : "ID чата"
          }
          value={address}
          onChange={(e) => {
            setAddress(e.target.value);
            save.reset();
          }}
        />
      </Field>
      <div className="channel-delivery">
        <span>Доставка уведомлений</span>
        <button
          className="delivery-switch"
          type="button"
          role="switch"
          aria-label={`Уведомления в ${a.channel_name}`}
          aria-checked={enabled}
          disabled={!a.channel_enabled || save.isPending}
          onClick={() => {
            setEnabled(!enabled);
            save.reset();
          }}
        >
          <i />
          <span>{enabled ? "Включена" : "Выключена"}</span>
        </button>
      </div>
      <Button
        disabled={
          save.isPending || !a.channel_enabled || !dirty || !address.trim()
        }
        variant="outline"
      >
        {save.isPending ? "Сохранение…" : "Сохранить"}
      </Button>
      <div className="channel-feedback">
        <Failure error={save.error} />
        {save.isSuccess && !dirty && (
          <span role="status">Настройки сохранены</span>
        )}
        {dirty && <small>Есть несохранённые изменения</small>}
      </div>
    </form>
  );
}
export function HelpPage() {
  const { "*": slug } = useParams();
  const topics = useResource<Schema["HelpTopicRef"][]>("/help");
  const q = useResource<Schema["HelpTopicOut"]>(
    "/help/" + enc(slug || ""),
    {},
    !!slug,
  );
  return (
    <>
      <Heading
        eyebrow="ПОМОЩЬ"
        title={q.data?.title || "Справка"}
        text={
          q.data?.summary ||
          "Руководство пользователя и ответы по рабочим сценариям."
        }
      />
      {slug ? (
        <Panel title={q.data?.title || "Руководство"}>
          <Link className="text-link" to="/help">
            ← Все разделы
          </Link>
          <State query={q}>{q.data && <Markdown text={q.data.body} />}</State>
        </Panel>
      ) : (
        <State query={topics}>
          <div className="analytics-grid">
            {topics.data?.map((t) => (
              <Panel key={t.slug} title={t.title}>
                <p>{t.summary}</p>
                <Link className="text-link" to={`/help/${t.slug}`}>
                  Читать руководство →
                </Link>
              </Panel>
            ))}
          </div>
        </State>
      )}
    </>
  );
}
