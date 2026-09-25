import {
  Children,
  isValidElement,
  useId,
  useRef,
  useState,
  type ReactNode,
  type SelectHTMLAttributes,
  type ChangeEvent,
} from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Check, ChevronDown, Search, X } from "lucide-react";
type Props = SelectHTMLAttributes<HTMLSelectElement>;
export function Select({
  children,
  value,
  onChange,
  disabled,
  className = "",
  id,
  ...props
}: Props) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const uid = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState({
    left: 16,
    top: 80,
    width: 320,
    maxHeight: 440,
  });

  const native = useRef<HTMLSelectElement>(null);
  const options: { value: string; label: ReactNode; disabled?: boolean }[] = [];
  function walk(nodes: ReactNode) {
    Children.forEach(nodes, (child) => {
      if (
        !isValidElement<{
          value?: string;
          children?: ReactNode;
          disabled?: boolean;
        }>(child)
      )
        return;
      if (child.type === "option")
        options.push({
          value: String(child.props.value ?? ""),
          label: child.props.children,
          disabled: child.props.disabled,
        });
      else walk(child.props.children);
    });
  }
  walk(children);
  const selected = options.find((o) => o.value === String(value ?? ""));
  return (
    <span className={`select-wrap ${className}`}>
      <select
        {...props}
        ref={native}
        value={value}
        onChange={onChange}
        disabled={disabled}
        tabIndex={-1}
        aria-hidden="true"
        className="select-native"
        onInvalid={() => setOpen(true)}
      >
        {children}
      </select>
      <Dialog.Root
        open={open}
        onOpenChange={(v) => {
          if (v && trigger.current) {
            const rect = trigger.current.getBoundingClientRect();
            const width = Math.min(
              Math.max(rect.width, 280),
              window.innerWidth - 32,
            );
            const height = Math.min(
              440,
              options.length * 48 + 96,
              window.innerHeight - 32,
            );
            const top =
              rect.bottom + height + 8 < window.innerHeight
                ? rect.bottom + 6
                : Math.max(16, rect.top - height - 6);
            setPosition({
              left: Math.min(
                Math.max(16, rect.left),
                window.innerWidth - width - 16,
              ),
              top,
              width,
              maxHeight: height,
            });
          }
          setOpen(v);
          setSearch("");
        }}
      >
        <Dialog.Trigger
          ref={trigger}
          id={id || uid}
          type="button"
          disabled={disabled}
          className="select-trigger"
          aria-label={props["aria-label"]}
          aria-haspopup="dialog"
        >
          <span>{selected?.label || "Выберите значение"}</span>
          <ChevronDown size={16} />
        </Dialog.Trigger>
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay select-overlay" />
          <Dialog.Content
            className="select-popup"
            style={position}
            aria-describedby={undefined}
          >
            <Dialog.Title>
              {props["aria-label"] || "Выберите значение"}
            </Dialog.Title>
            <Dialog.Close className="dialog-close" aria-label="Закрыть список">
              <X size={18} />
            </Dialog.Close>
            {options.length > 7 && (
              <label className="select-search">
                <Search size={16} />
                <input
                  autoFocus
                  placeholder="Найти в списке"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </label>
            )}
            <div
              className="select-options"
              onKeyDown={(e) => {
                if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key))
                  return;
                const buttons = Array.from(
                  e.currentTarget.querySelectorAll<HTMLButtonElement>(
                    "button:not(:disabled)",
                  ),
                );
                const index = buttons.indexOf(
                  document.activeElement as HTMLButtonElement,
                );
                const next =
                  e.key === "Home"
                    ? 0
                    : e.key === "End"
                      ? buttons.length - 1
                      : (index +
                          (e.key === "ArrowDown" ? 1 : -1) +
                          buttons.length) %
                        buttons.length;
                e.preventDefault();
                buttons[next]?.focus();
              }}
            >
              {options
                .filter((o) =>
                  String(o.label)
                    .toLocaleLowerCase("ru")
                    .includes(search.toLocaleLowerCase("ru")),
                )
                .map((o, i) => (
                  <button
                    type="button"
                    key={`${o.value}-${i}`}
                    disabled={o.disabled}
                    className={o.value === String(value ?? "") ? "chosen" : ""}
                    onClick={() => {
                      if (native.current) {
                        native.current.value = o.value;
                        onChange?.({
                          target: native.current,
                          currentTarget: native.current,
                        } as ChangeEvent<HTMLSelectElement>);
                      }
                      setOpen(false);
                    }}
                  >
                    <span>{o.label}</span>
                    {o.value === String(value ?? "") && <Check size={17} />}
                  </button>
                ))}
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </span>
  );
}
