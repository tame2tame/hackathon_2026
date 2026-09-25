import { useEffect, useState, type ReactNode } from "react";
import { api } from "../api/runtime";
function inline(text: string): ReactNode[] {
  return text
    .split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g)
    .map((part, i) => {
      if (part.startsWith("**"))
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      if (part.startsWith("`")) return <code key={i}>{part.slice(1, -1)}</code>;
      const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (link && /^(https?:\/\/|\/(?!\/))/.test(link[2]))
        return (
          <a key={i} href={link[2]}>
            {link[1]}
          </a>
        );
      return part;
    });
}
export function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const blocks: ReactNode[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    if (line.startsWith("![")) {
      const match = line.match(
        /^!\[([^\]]*)\]\((\/api\/v1\/help\/images\/[a-zA-Z0-9_-]+\.png)\)$/,
      );
      if (match)
        blocks.push(<HelpImage key={i} alt={match[1]} path={match[2]} />);
      continue;
    }
    if (line.startsWith("```")) {
      const code = [];
      while (++i < lines.length && !lines[i].startsWith("```"))
        code.push(lines[i]);
      blocks.push(
        <pre key={i}>
          <code>{code.join("\n")}</code>
        </pre>,
      );
      continue;
    }
    if (line.startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        if (!/^\|[\s:|-]+\|$/.test(lines[i]))
          rows.push(
            lines[i]
              .split("|")
              .slice(1, -1)
              .map((s) => s.trim()),
          );
        i++;
      }
      i--;
      blocks.push(
        <div className="table-scroll" key={i}>
          <table className="service-table">
            <thead>
              <tr>
                {rows[0]?.map((s, k) => (
                  <th key={k}>{inline(s)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.slice(1).map((r, j) => (
                <tr key={j}>
                  {r.map((s, k) => (
                    <td key={k}>{inline(s)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }
    if (/^#{1,6} /.test(line)) {
      blocks.push(<h3 key={i}>{inline(line.replace(/^#+\s*/, ""))}</h3>);
      continue;
    }
    if (/^[-*] /.test(line)) {
      const entries = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        entries.push(<li key={i}>{inline(lines[i].slice(2))}</li>);
        i++;
      }
      i--;
      blocks.push(<ul key={i}>{entries}</ul>);
      continue;
    }
    blocks.push(<p key={i}>{inline(line)}</p>);
  }
  return <div className="help-markdown">{blocks}</div>;
}

function HelpImage({ path, alt }: { path: string; alt: string }) {
  const [url, setUrl] = useState("");
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    api
      .file(path)
      .then((blob) => {
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);
  return (
    <figure className="help-figure">
      {url ? (
        <img src={url} alt={alt} />
      ) : (
        <p>{failed ? "Изображение недоступно" : "Загружаем иллюстрацию…"}</p>
      )}
      <figcaption>{alt}</figcaption>
    </figure>
  );
}
