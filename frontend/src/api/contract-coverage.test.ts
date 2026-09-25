import { expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import ts from "typescript";
// Проверяем вызовы новых экранов против метода и пути, объявленных бэкендом.
const contract = readFileSync(
  new URL("../../../contracts/openapi.yaml", import.meta.url),
  "utf8",
);
const routes = [
  ...contract.matchAll(
    /^  (\/api\/[^\n]+):\n([\s\S]*?)(?=^  \/api\/|^components:)/gm,
  ),
].map((m) => ({
  path: m[1],
  methods: [...m[2].matchAll(/^    (get|post|put|patch|delete):/gm)].map(
    (x) => x[1],
  ),
}));
function pathPattern(node: ts.Expression): string | null {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node))
    return node.text;
  if (ts.isTemplateExpression(node))
    return (
      node.head.text +
      node.templateSpans.map((s) => "*" + s.literal.text).join("")
    );
  return null;
}
it("новые страницы вызывают существующие методы контракта", () => {
  const invalid: string[] = [];
  let count = 0;
  for (const name of readdirSync(new URL("../pages/", import.meta.url)).filter(
    (n) => n.endsWith(".tsx"),
  )) {
    const source = ts.createSourceFile(
      name,
      readFileSync(new URL("../pages/" + name, import.meta.url), "utf8"),
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TSX,
    );
    function visit(node: ts.Node) {
      if (
        ts.isCallExpression(node) &&
        ts.isPropertyAccessExpression(node.expression) &&
        node.expression.expression.getText(source) === "api"
      ) {
        const method = node.expression.name.text;
        if (["get", "send", "upload"].includes(method) && node.arguments[0]) {
          const path = pathPattern(node.arguments[0]);
          if (path && !path.endsWith("/") && !path.endsWith("*")) {
            count++;
            const full =
              (path.startsWith("/api/") ? "" : "/api/v1") + path.split("?")[0];
            const verb =
              method === "get"
                ? "get"
                : method === "upload"
                  ? "post"
                  : node.arguments[2] && ts.isStringLiteral(node.arguments[2])
                    ? node.arguments[2].text.toLowerCase()
                    : "post";
            const matches = (p: string) => {
              const a = full.split("/"),
                b = p.split("/");
              return (
                a.length === b.length &&
                a.every(
                  (v, i) => v === "*" || b[i].startsWith("{") || v === b[i],
                )
              );
            };
            if (
              !routes.some((r) => matches(r.path) && r.methods.includes(verb))
            )
              invalid.push(`${name}: ${verb.toUpperCase()} ${full}`);
          }
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
  }
  expect(count).toBeGreaterThan(20);
  expect(invalid).toEqual([]);
});
