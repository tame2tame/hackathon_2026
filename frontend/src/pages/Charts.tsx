import { useRef, useState } from "react";
import { BarChart3, ChartPie, CircleDot, Download } from "lucide-react";
import type { Schema } from "../api/types";
import { number, palette, slices } from "./analytics-data";
import { Button } from "../components/ui/button";
export type ChartType = "bar" | "donut" | "dot";
export function Bars({
  chart,
  onPick,
  dots = false,
}: {
  chart: Schema["ChartOut"];
  onPick?: (index: number) => void;
  dots?: boolean;
}) {
  const max = Math.max(1, ...chart.values);
  return (
    <div className={`chart-bars ${dots ? "dot-chart" : ""}`}>
      <div className="chart-scale" aria-hidden="true">
        <span>0</span>
        <span>{number(max / 2)}</span>
        <span>{number(max)}</span>
      </div>
      {chart.labels.map((label, i) => (
        <button
          key={`${label}-${i}`}
          disabled={!onPick}
          onClick={() => onPick?.(i)}
          className="chart-bar-row"
          title={`${label}: ${number(chart.values[i] || 0)}`}
        >
          <span>{label}</span>
          <span className="chart-track">
            <i style={{ width: `${((chart.values[i] || 0) / max) * 100}%` }}>
              {dots && <b className="chart-dot" />}
            </i>
          </span>
          <strong>{number(chart.values[i] || 0)}</strong>
        </button>
      ))}
      {!chart.values.some(Boolean) && (
        <p className="service-empty">Нет данных для отображения</p>
      )}
    </div>
  );
}
export function Donut({
  chart,
  onPick,
}: {
  chart: Schema["ChartOut"];
  onPick?: (index: number) => void;
}) {
  const rows = slices(chart);
  const total = chart.values.reduce((a, b) => a + b, 0);
  const [active, setActive] = useState<number | null>(null);
  const current = rows.find((r) => r.index === active);
  return (
    <div className="donut-layout">
      <div className="donut-figure">
        <svg viewBox="0 0 240 240" role="img" aria-label={chart.title}>
          <circle
            cx="120"
            cy="120"
            r="90"
            fill="none"
            stroke="#efedf4"
            strokeWidth="30"
          />
          {rows.map((r, i) => (
            <circle
              key={r.index}
              cx="120"
              cy="120"
              r="90"
              fill="none"
              stroke={palette[i % palette.length]}
              strokeWidth={active === r.index ? 36 : 30}
              pathLength="100"
              strokeDasharray={`${r.share * 100} ${100 - r.share * 100}`}
              strokeDashoffset={-r.offset * 100}
              transform="rotate(-90 120 120)"
              onMouseEnter={() => setActive(r.index)}
              onMouseLeave={() => setActive(null)}
              onClick={() => onPick?.(r.index)}
              style={{
                cursor: onPick ? "pointer" : "default",
                opacity: active === null || active === r.index ? 1 : 0.35,
              }}
            >
              <title>
                {r.label}: {number(r.value)} ({number(r.share * 100)}%)
              </title>
            </circle>
          ))}
          <text
            x="120"
            y="119"
            textAnchor="middle"
            fill="#171e2e"
            fontSize="34"
            fontWeight="700"
          >
            {number(current?.value ?? total)}
          </text>
          <text
            x="120"
            y="142"
            textAnchor="middle"
            fill="#707787"
            fontSize="12"
          >
            {current
              ? `${number(current.share * 100)}% от общего`
              : "взаимодействий"}
          </text>
        </svg>
      </div>
      <div className="chart-legend">
        {rows.map((r, i) => (
          <button
            key={r.index}
            disabled={!onPick}
            onMouseEnter={() => setActive(r.index)}
            onMouseLeave={() => setActive(null)}
            onFocus={() => setActive(r.index)}
            onBlur={() => setActive(null)}
            onClick={() => onPick?.(r.index)}
            title={`${r.label}: ${r.value}`}
          >
            <i style={{ background: palette[i % palette.length] }} />
            <span>{r.label}</span>
            <strong>{number(r.value)}</strong>
            <small>{number(r.share * 100)}%</small>
          </button>
        ))}
        {!rows.length && (
          <p className="service-empty">Нет данных для отображения</p>
        )}
      </div>
    </div>
  );
}
export function ChartView({
  chart,
  initial = "bar",
  duration = false,
  onPick,
}: {
  chart: Schema["ChartOut"];
  initial?: ChartType;
  duration?: boolean;
  onPick?: (index: number) => void;
}) {
  const [type, setType] = useState<ChartType>(initial);
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <div className="chart-view">
      <div className="chart-controls">
        <div
          className="chart-type-control"
          role="group"
          aria-label={`Вид графика: ${chart.title}`}
        >
          {(
            [
              { id: "bar", name: "Столбчатый", Icon: BarChart3 },
              ...(duration
                ? [{ id: "dot", name: "Точечный", Icon: CircleDot }]
                : [{ id: "donut", name: "Круговая", Icon: ChartPie }]),
            ] as const
          ).map(({ id, name, Icon }) => (
            <button
              type="button"
              key={id}
              aria-pressed={type === id}
              onClick={() => setType(id as ChartType)}
            >
              <Icon size={15} />
              {name}
            </button>
          ))}
        </div>
        <Button
          variant="ghost"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await exportChart(ref.current!, chart.title);
            } catch {
              setError("Не удалось сохранить изображение. Повторите загрузку.");
            } finally {
              setBusy(false);
            }
          }}
        >
          <Download size={14} /> PNG
        </Button>
      </div>
      <div ref={ref} className="chart-export-surface">
        {type === "donut" ? (
          <Donut chart={chart} onPick={onPick} />
        ) : (
          <Bars chart={chart} onPick={onPick} dots={type === "dot"} />
        )}
      </div>
      {error && <p role="alert">{error}</p>}
      <details className="chart-data">
        <summary>Данные таблицей</summary>
        <table>
          <thead>
            <tr>
              <th>Категория</th>
              <th>{duration ? "Дней" : "Количество"}</th>
            </tr>
          </thead>
          <tbody>
            {chart.labels.map((l, i) => (
              <tr key={i}>
                <td>{l}</td>
                <td>{number(chart.values[i] || 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
// Inline computed styles keep PNG exports faithful to the selected chart, including legends.
async function exportChart(element: HTMLElement, title: string) {
  await document.fonts.ready;
  const clone = element.cloneNode(true) as HTMLElement;
  const source = [element, ...element.querySelectorAll("*")];
  const dest = [clone, ...clone.querySelectorAll("*")];
  source.forEach((node, i) => {
    const style = getComputedStyle(node);
    let css = "";
    for (const key of style) css += `${key}:${style.getPropertyValue(key)};`;
    dest[i].setAttribute("style", css);
  });
  const width = element.offsetWidth,
    height = element.offsetHeight;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height + 64}"><rect width="100%" height="100%" fill="white"/><text x="20" y="35" font-size="${Math.min(18, (width - 40) / (title.length * 0.58))}" font-family="sans-serif" fill="#171e2e">${title.replace(/[<>&]/g, "")}</text><foreignObject x="0" y="64" width="${width}" height="${height}">${new XMLSerializer().serializeToString(clone)}</foreignObject></svg>`;
  const img = new Image();
  img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  await img.decode();
  const canvas = document.createElement("canvas");
  canvas.width = width * 2;
  canvas.height = (height + 64) * 2;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw Error();
  ctx.scale(2, 2);
  ctx.drawImage(img, 0, 0);
  const blob = await new Promise<Blob>((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(Error())), "image/png"),
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = title + ".png";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
