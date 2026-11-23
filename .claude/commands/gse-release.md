---
description: "Run the mandatory GSE-One build pipeline for a commit to main: VERSION bump, CHANGELOG entry, generator --verify, add, commit, push, and the vX.Y.Z tag that triggers the release workflow. Thin executable checklist over CLAUDE.md > Critical rules > Build pipeline (canonical)."
argument-hint: "[patch] [commit subject]"
---

# /gse-release — Build pipeline checklist (maintainer)

Arguments: $ARGUMENTS

## Scope

Executes the **mandatory 6-step pipeline** for every commit to main, as defined canonically in `CLAUDE.md > Critical rules > Build pipeline` — this file is a thin checklist, not a second source of truth; on any divergence, CLAUDE.md wins.

**Skip entirely** when every edited file is gitignored (`_LOCAL/`, matched by `/_*/`) — local-only work artifacts take no pipeline (see the "Exception — gitignored / `_LOCAL/` files" rule).

## Workflow

### Step 1 — Bump VERSION

Read the current root `VERSION` and bump the **third number only** (`0.93.0` → `0.93.1`), for fixes and features alike — CLAUDE.md > Versioning — Version freeze. A minor or major bump happens only when the maintainer explicitly asks for it for this release; if `$ARGUMENTS` says `minor`/`major` without that explicit request, ask first.

### Step 2 — CHANGELOG entry

Add `## [X.Y.Z] - YYYY-MM-DD` at the top with only `### Added/Changed/Fixed/Removed/Deprecated/Security` sections, per the CHANGELOG style discipline (CLAUDE.md): bullets ≤ 25 words, verb-first, budget ≤ 15 lines, no rationale/notes sections, no per-file line-number enumeration. Migrate any needed synthesis to `docs/post-audit-reports/`.

### Step 3 — Generate

```
cd gse-one && python3 gse_generate.py --verify
```

Must exit clean. Never commit without regenerating — `plugin/` (except `plugin/tools/`) is generator output.

### Step 4 — Add all

`VERSION`, `CHANGELOG.md`, both plugin manifests, and every regenerated file under `gse-one/plugin/`, plus the source edits.

### Step 5 — Commit

Prefix `feat:` / `fix:` / `docs:` / `chore:` with the `vX.Y.Z —` pattern in the subject (check recent `git log` for the house style).

### Step 6 — Push + tag

```
git push origin main
```

Then the release act — pushing the matching tag triggers `.github/workflows/release.yml` (packages and publishes the `gse-one.tar.gz` asset consumed by `install.sh`):

```
git tag vX.Y.Z && git push origin vX.Y.Z
```

Tag push is a **Gate**: confirm with the maintainer before pushing the tag if the session did not already validate a release (it publishes a public GitHub release).

## Never

- Never skip a step. Never commit without regenerating. Never push without bumping. Never release without a matching CHANGELOG entry.
- Never edit `gse-one/plugin/` directly (except `plugin/tools/`).
