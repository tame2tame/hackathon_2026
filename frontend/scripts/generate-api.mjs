import { format } from "prettier";
import openapiTS, { astToString } from "openapi-typescript";
import { readFile, writeFile } from "node:fs/promises";
const source = new URL("../../contracts/openapi.yaml", import.meta.url);
const target = new URL("../src/api/schema.d.ts", import.meta.url);
const output = await format("// Generated from contracts/openapi.yaml. Do not edit.\n" + astToString(await openapiTS(source)), { parser: "typescript" });
if (process.argv.includes("--check")) {
  if ((await readFile(target, "utf8")) !== output) {
    console.error("Типы API устарели. Выполните npm run api:generate.");
    process.exit(1);
  }
} else await writeFile(target, output);
