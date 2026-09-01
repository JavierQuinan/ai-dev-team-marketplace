#!/usr/bin/env node
// Deterministic repository posture inventory for the DevSecOps extension of
// ai-dev-team:auditing-security.
//
// This is NOT a SAST/SCA engine. It never reads or greps general source
// file *content* for vulnerability patterns, never maintains a CVE/advisory
// database, and never labels anything "confirmed vulnerability" -- it only
// reports deterministic, low-false-positive REVIEW SIGNALS (file/config
// evidence) for auditing-security to inspect and classify. Real dependency
// vulnerability data comes from real ecosystem tools (npm audit, pip-audit,
// osv-scanner, cargo audit, etc.), never from this script.
//
// Contract: read-only, deterministic, offline (no network), no package
// installs, no writes anywhere (not in the target repo, not in this
// plugin's own directory), no secret values in output, Node built-ins only.
//
// Usage:
//   node devsecops-inventory.mjs --root <path> [--json]

import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { execFileSync } from "node:child_process";

const IGNORED_DIRS = new Set([
  "node_modules",
  ".git",
  "dist",
  "build",
  ".next",
  ".venv",
  "venv",
  "vendor",
  "target",
  "__pycache__",
]);

const SHA_RE = /^[0-9a-f]{40}$/i;
const SENSITIVE_FILENAME_PATTERNS = [
  { re: /(^|\/)\.env(\..+)?$/i, label: ".env-style file" },
  { re: /\.pem$/i, label: "PEM key/certificate" },
  { re: /\.key$/i, label: "key file" },
  { re: /(^|\/)credentials\..+$/i, label: "credentials file" },
  { re: /\.pfx$/i, label: "PKCS#12 bundle" },
  { re: /\.p12$/i, label: "PKCS#12 bundle" },
  { re: /(^|\/)id_rsa$/i, label: "SSH private key" },
];

function parseArgs(argv) {
  const args = { root: process.cwd(), json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--root") {
      args.root = argv[++i];
    } else if (a === "--json") {
      args.json = true;
    }
  }
  return args;
}

function walk(dir, root, out) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const entry of entries) {
    if (entry.isDirectory()) {
      if (IGNORED_DIRS.has(entry.name)) continue;
      walk(join(dir, entry.name), root, out);
    } else if (entry.isFile()) {
      out.push(relative(root, join(dir, entry.name)).split(sep).join("/"));
    }
  }
}

function readText(root, relPath) {
  try {
    return readFileSync(join(root, relPath), "utf-8");
  } catch {
    return null;
  }
}

// -- Ecosystem / lockfile detection ------------------------------------

// Grouped by manifest: a manifest is reproducible if ANY ONE of its
// candidate lockfiles is present (a project needs exactly one package
// manager's lockfile, not all of them) -- this must never fan out into
// one false "missing lockfile" signal per package-manager candidate.
const MANIFEST_GROUPS = [
  {
    manifest: "package.json",
    candidates: [
      { lockfile: "package-lock.json", ecosystem: "node-npm", tool: "npm audit" },
      { lockfile: "pnpm-lock.yaml", ecosystem: "node-pnpm", tool: "pnpm audit" },
      { lockfile: "yarn.lock", ecosystem: "node-yarn", tool: "yarn npm audit" },
      { lockfile: "bun.lockb", ecosystem: "node-bun", tool: "bun audit" },
    ],
  },
  {
    manifest: "pyproject.toml",
    candidates: [
      { lockfile: "poetry.lock", ecosystem: "python-poetry", tool: "pip-audit" },
      { lockfile: "uv.lock", ecosystem: "python-uv", tool: "pip-audit" },
    ],
  },
  {
    // requirements.txt is its own de-facto manifest; whether it pins exact
    // versions is a content question out of scope for this deterministic,
    // non-content-scanning inventory -- never flagged as missing a lockfile.
    manifest: "requirements.txt",
    candidates: [{ lockfile: "requirements.txt", ecosystem: "python-requirements", tool: "pip-audit" }],
  },
  {
    manifest: "Cargo.toml",
    candidates: [{ lockfile: "Cargo.lock", ecosystem: "rust-cargo", tool: "cargo audit" }],
  },
  {
    manifest: "go.mod",
    candidates: [{ lockfile: "go.sum", ecosystem: "go-modules", tool: "govulncheck" }],
  },
  {
    manifest: "Gemfile",
    candidates: [{ lockfile: "Gemfile.lock", ecosystem: "ruby-bundler", tool: "bundler-audit" }],
  },
];

function detectEcosystems(root, files, signals) {
  const fileSet = new Set(files);
  const detected = [];

  for (const group of MANIFEST_GROUPS) {
    if (!fileSet.has(group.manifest)) continue;
    const matched = group.candidates.filter((c) => fileSet.has(c.lockfile));

    if (matched.length === 0) {
      const candidateNames = group.candidates.map((c) => c.lockfile).join(" / ");
      detected.push({
        ecosystem: group.candidates[0].ecosystem,
        manifest: group.manifest,
        lockfile_present: false,
        recommended_audit_tools: Array.from(new Set(group.candidates.map((c) => c.tool))),
      });
      signals.push({
        rule_id: "REPRODUCIBILITY_MISSING_LOCKFILE",
        category: "supply-chain",
        path: group.manifest,
        line: 0,
        message: `${group.manifest} is present but none of its candidate lockfiles (${candidateNames}) were found -- dependency resolution may not be reproducible across installs.`,
        classification: "review-signal",
      });
    } else {
      for (const m of matched) {
        detected.push({
          ecosystem: m.ecosystem,
          manifest: group.manifest,
          lockfile_present: true,
          recommended_audit_tools: [m.tool],
        });
      }
    }
  }
  return detected;
}

// -- GitHub Actions workflow scanning ------------------------------------

function scanWorkflow(root, relPath, signals) {
  const text = readText(root, relPath);
  if (text === null) return;
  const lines = text.split("\n");

  let hasExplicitPermissions = false;
  let hasWriteAll = false;

  lines.forEach((line, idx) => {
    const lineNo = idx + 1;

    const usesMatch = line.match(/^\s*-?\s*uses:\s*([^\s#]+)/);
    if (usesMatch) {
      const ref = usesMatch[1];
      // Local actions (./path) and Docker actions (docker://...) don't
      // pin the same way -- not applicable to the SHA-pinning check.
      if (!ref.startsWith("./") && !ref.startsWith("docker://")) {
        const atIdx = ref.lastIndexOf("@");
        const refPin = atIdx >= 0 ? ref.slice(atIdx + 1) : null;
        if (!refPin || !SHA_RE.test(refPin)) {
          signals.push({
            rule_id: "GHA_UNPINNED_ACTION",
            category: "supply-chain",
            path: relPath,
            line: lineNo,
            message: `Action '${ref}' is not pinned to a full commit SHA (pinned to '${
              refPin ?? "no ref"
            }' instead) -- a tag or branch can be moved to point at different, unreviewed code.`,
            classification: "review-signal",
          });
        }
      }
    }

    if (/^\s*permissions\s*:/.test(line)) {
      hasExplicitPermissions = true;
      if (/write-all/.test(line)) hasWriteAll = true;
    }
    if (/^\s*permissions\s*:\s*write-all\b/.test(line)) hasWriteAll = true;

    if (/pull_request_target/.test(line)) {
      signals.push({
        rule_id: "GHA_PULL_REQUEST_TARGET",
        category: "ci-security",
        path: relPath,
        line: lineNo,
        message:
          "Workflow uses 'pull_request_target', which runs with the base repo's secrets/permissions even for fork PRs -- high-attention signal only; auditing-security must trace whether this workflow also checks out PR-head code and/or uses secrets/write permissions before classifying severity.",
        classification: "review-signal",
      });
    }
  });

  if (hasWriteAll) {
    signals.push({
      rule_id: "GHA_BROAD_PERMISSIONS",
      category: "ci-security",
      path: relPath,
      line: 0,
      message: "Workflow declares 'permissions: write-all' -- broader than least privilege; review whether every job actually needs write access.",
      classification: "review-signal",
    });
  } else if (!hasExplicitPermissions) {
    signals.push({
      rule_id: "GHA_NO_EXPLICIT_PERMISSIONS",
      category: "ci-security",
      path: relPath,
      line: 0,
      message: "Workflow declares no explicit 'permissions' block -- the effective permissions come from repo/org defaults, which this script cannot see; not a confirmed issue, just something to verify.",
      classification: "review-signal",
    });
  }
}

function scanGithubActions(root, files, signals) {
  const workflowFiles = files.filter(
    (f) => f.startsWith(".github/workflows/") && (f.endsWith(".yml") || f.endsWith(".yaml"))
  );
  for (const f of workflowFiles) scanWorkflow(root, f, signals);
  return workflowFiles;
}

// -- Sensitive tracked filenames (names only, never content) ------------

function scanSensitiveFilenames(root, signals) {
  let tracked;
  try {
    const out = execFileSync("git", ["ls-files"], {
      cwd: root,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    });
    tracked = out.split("\n").filter(Boolean);
  } catch {
    return { checked: false, tracked_count: 0 };
  }

  for (const path of tracked) {
    for (const pattern of SENSITIVE_FILENAME_PATTERNS) {
      if (pattern.re.test(path)) {
        signals.push({
          rule_id: "SENSITIVE_FILENAME_TRACKED",
          category: "secrets",
          path,
          line: 0,
          message: `'${path}' matches a sensitive-filename pattern (${pattern.label}) and is tracked in git -- file name only, content was not read or printed by this script.`,
          classification: "review-signal",
        });
        break;
      }
    }
  }
  return { checked: true, tracked_count: tracked.length };
}

// -- Minimal Docker hardening signal -------------------------------------

function scanDockerfiles(root, files, signals) {
  const dockerfiles = files.filter((f) => /(^|\/)Dockerfile([./].*)?$/.test(f));
  for (const path of dockerfiles) {
    const text = readText(root, path);
    if (text === null) continue;
    const hasNonRootUser = /^\s*USER\s+(?!root\b|0\b)\S+/m.test(text);
    if (!hasNonRootUser) {
      signals.push({
        rule_id: "DOCKER_NO_NONROOT_USER",
        category: "hardening",
        path,
        line: 0,
        message: "No 'USER <non-root>' instruction found -- the image likely runs as root by default; consider adding a non-root USER for defense-in-depth.",
        classification: "review-signal",
      });
    }
  }
  return dockerfiles;
}

// -- Main -----------------------------------------------------------------

function main() {
  const args = parseArgs(process.argv.slice(2));
  const root = args.root;

  if (!existsSync(root) || !statSync(root).isDirectory()) {
    process.stderr.write(`devsecops-inventory: root '${root}' does not exist or is not a directory\n`);
    process.exit(1);
  }

  const files = [];
  walk(root, root, files);

  const signals = [];
  const ecosystems = detectEcosystems(root, files, signals);
  const workflowFiles = scanGithubActions(root, files, signals);
  const sensitiveFileCheck = scanSensitiveFilenames(root, signals);
  const dockerfiles = scanDockerfiles(root, files, signals);

  const recommendedExternalTools = Array.from(
    new Set(ecosystems.flatMap((e) => e.recommended_audit_tools))
  );
  if (recommendedExternalTools.length === 0) {
    recommendedExternalTools.push(
      "osv-scanner (multi-ecosystem, run manually against detected manifests once an ecosystem is confirmed)"
    );
  }

  const result = {
    root: "<sanitized: absolute path not echoed>",
    files_scanned: files.length,
    ecosystems,
    workflows_scanned: workflowFiles,
    dockerfiles_scanned: dockerfiles,
    sensitive_filename_scan: sensitiveFileCheck,
    signals,
    recommended_external_tools: recommendedExternalTools,
    notes: [
      "This inventory reports deterministic review signals only -- it is not a vulnerability scanner and does not consult any CVE/advisory database.",
      "No signal here is a 'confirmed vulnerability' by itself; auditing-security inspects each signal's actual context before classifying it.",
      "This script never reads or reports the *content* of source files -- only manifest/lockfile presence, GitHub Actions workflow YAML, tracked filenames, and Dockerfile USER presence.",
    ],
  };

  process.stdout.write(JSON.stringify(result, null, 2) + "\n");
}

main();
