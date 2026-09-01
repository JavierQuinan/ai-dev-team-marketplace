// Real, runnable tests for plugins/ai-dev-team/scripts/devsecops-inventory.mjs
// using Node's built-in test runner (no external dependencies). Run with:
//   node --test tests/devsecops_inventory.test.mjs

import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(__dirname, "..", "plugins", "ai-dev-team", "scripts", "devsecops-inventory.mjs");

function makeFixture() {
  const dir = mkdtempSync(join(tmpdir(), "devsecops-inventory-test-"));
  return dir;
}

function writeFile(root, relPath, content) {
  const full = join(root, relPath);
  mkdirSync(dirname(full), { recursive: true });
  writeFileSync(full, content);
}

function runInventory(root) {
  const out = execFileSync("node", [SCRIPT, "--root", root, "--json"], {
    encoding: "utf-8",
  });
  return JSON.parse(out);
}

function signalsOf(result, ruleId) {
  return result.signals.filter((s) => s.rule_id === ruleId);
}

test("SEC-SCRIPT-01: unpinned GitHub action is detected", () => {
  const root = makeFixture();
  try {
    writeFile(
      root,
      ".github/workflows/ci.yml",
      "name: CI\non:\n  push:\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n"
    );
    const result = runInventory(root);
    const found = signalsOf(result, "GHA_UNPINNED_ACTION");
    assert.equal(found.length, 1);
    assert.match(found[0].message, /actions\/checkout@v4/);
    assert.equal(found[0].path, ".github/workflows/ci.yml");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SEC-SCRIPT-02: a full 40-char SHA-pinned action is NOT flagged", () => {
  const root = makeFixture();
  try {
    const realSha = "3d3c42e5aac5ba805825da76410c181273ba90b1"; // 40 hex chars
    assert.equal(realSha.length, 40);
    writeFile(
      root,
      ".github/workflows/ci.yml",
      `name: CI\non:\n  push:\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@${realSha} # v7.0.1\n`
    );
    const result = runInventory(root);
    const found = signalsOf(result, "GHA_UNPINNED_ACTION");
    assert.equal(found.length, 0, "a genuine 40-char commit SHA must never be flagged as unpinned");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SEC-SCRIPT-03: 'permissions: write-all' produces a broad-permissions signal", () => {
  const root = makeFixture();
  try {
    writeFile(
      root,
      ".github/workflows/ci.yml",
      "name: CI\non:\n  push:\npermissions: write-all\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n"
    );
    const result = runInventory(root);
    const found = signalsOf(result, "GHA_BROAD_PERMISSIONS");
    assert.equal(found.length, 1);
    // Must not also claim "no explicit permissions" -- it IS explicit, just broad.
    assert.equal(signalsOf(result, "GHA_NO_EXPLICIT_PERMISSIONS").length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SEC-SCRIPT-04: pull_request_target trigger produces a review signal", () => {
  const root = makeFixture();
  try {
    writeFile(
      root,
      ".github/workflows/ci.yml",
      "name: CI\non:\n  pull_request_target:\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n"
    );
    const result = runInventory(root);
    const found = signalsOf(result, "GHA_PULL_REQUEST_TARGET");
    assert.equal(found.length, 1);
    assert.equal(found[0].classification, "review-signal");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SEC-SCRIPT-05: a manifest without its expected lockfile produces a reproducibility signal", () => {
  const root = makeFixture();
  try {
    writeFile(root, "package.json", '{"name":"fixture","version":"0.0.0"}');
    const result = runInventory(root);
    const found = signalsOf(result, "REPRODUCIBILITY_MISSING_LOCKFILE");
    assert.equal(found.length, 1);
    assert.equal(found[0].path, "package.json");

    // Control: presence of a matching lockfile must suppress the signal.
    writeFile(root, "package-lock.json", '{"name":"fixture","lockfileVersion":3}');
    const result2 = runInventory(root);
    assert.equal(signalsOf(result2, "REPRODUCIBILITY_MISSING_LOCKFILE").length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SEC-SCRIPT-06: a tracked sensitive filename is reported, but its content never appears in the output", () => {
  const root = makeFixture();
  const secretValue = "sk-THIS_MUST_NEVER_APPEAR_IN_OUTPUT_abcdef123456";
  try {
    writeFile(root, ".env", `API_KEY=${secretValue}\n`);
    execFileSync("git", ["init", "-q"], { cwd: root });
    execFileSync("git", ["config", "user.email", "test@example.com"], { cwd: root });
    execFileSync("git", ["config", "user.name", "Test"], { cwd: root });
    execFileSync("git", ["add", "."], { cwd: root });
    execFileSync("git", ["commit", "-q", "-m", "fixture"], { cwd: root });

    const rawOut = execFileSync("node", [SCRIPT, "--root", root, "--json"], { encoding: "utf-8" });

    assert.doesNotMatch(rawOut, new RegExp(secretValue.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));

    const result = JSON.parse(rawOut);
    const found = signalsOf(result, "SENSITIVE_FILENAME_TRACKED");
    assert.equal(found.length, 1);
    assert.equal(found[0].path, ".env");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SEC-SCRIPT-07: a source file containing eval(...) is not scanned/reported -- this script is not a SAST tool", () => {
  const root = makeFixture();
  try {
    writeFile(
      root,
      "src/dangerous.js",
      "function run(userInput) {\n  return eval(userInput); // deliberately dangerous fixture content\n}\n"
    );
    const result = runInventory(root);
    const touchingDangerousFile = result.signals.filter((s) => s.path === "src/dangerous.js");
    assert.equal(
      touchingDangerousFile.length,
      0,
      "the script must never inspect or report on general source file content"
    );
    // Also confirm no rule_id anywhere hints at source-level pattern matching.
    const ruleIds = result.signals.map((s) => s.rule_id);
    for (const id of ruleIds) {
      assert.doesNotMatch(id, /EVAL|SAST|CODE_PATTERN/i);
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SEC-SCRIPT-08: JSON output is valid and deterministic across repeated runs", () => {
  const root = makeFixture();
  try {
    writeFile(root, "package.json", '{"name":"fixture","version":"0.0.0"}');
    writeFile(
      root,
      ".github/workflows/ci.yml",
      "name: CI\non:\n  push:\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n"
    );
    const out1 = execFileSync("node", [SCRIPT, "--root", root, "--json"], { encoding: "utf-8" });
    const out2 = execFileSync("node", [SCRIPT, "--root", root, "--json"], { encoding: "utf-8" });

    const parsed1 = JSON.parse(out1); // throws if invalid JSON
    const parsed2 = JSON.parse(out2);
    assert.deepEqual(parsed1, parsed2, "identical input must produce identical output (no timestamps/randomness)");
    assert.ok(Array.isArray(parsed1.signals));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("script never writes any file (read-only contract)", () => {
  const root = makeFixture();
  try {
    writeFile(root, "package.json", '{"name":"fixture","version":"0.0.0"}');
    const before = execFileSync("node", ["-e", "console.log(require('fs').readdirSync(process.argv[1]).sort().join(','))", root], { encoding: "utf-8" });
    runInventory(root);
    const after = execFileSync("node", ["-e", "console.log(require('fs').readdirSync(process.argv[1]).sort().join(','))", root], { encoding: "utf-8" });
    assert.equal(before, after, "directory listing must be identical before and after running the script");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
