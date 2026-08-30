import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../lib/opsassist-api.ts", import.meta.url), "utf8");

test("browser workflow calls the versioned Python API", () => {
  for (const path of [
    "/incidents/simulate",
    "/investigate",
    "/simulate-action",
    "/approve",
    "/execute",
    "/verify",
    "/knowledge/search",
    "/evaluations",
    "/postmortem",
  ]) assert.match(source, new RegExp(path.replaceAll("/", "\\/")));
});

test("websocket client reconnects with a bounded delay", () => {
  assert.match(source, /new WebSocket/);
  assert.match(source, /Math\.min\(10_000/);
  assert.match(source, /socket\?\.close\(\)/);
});
