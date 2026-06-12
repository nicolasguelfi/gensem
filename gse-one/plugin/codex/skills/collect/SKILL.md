---
name: collect
description: "Inventory artefacts from internal project and external sources. Triggered by /gse:collect."
---

# GSE-One Collect — Artefact Inventory & External Sources

Arguments: $ARGUMENTS

## Options

| Flag / Sub-command | Description |
|--------------------|-------------|
| (no args)          | Scan and summarize current project artefacts |
| `<path>`           | Scan a local directory as an external source |
| `<url>`            | Scan a GitHub repository URL as an external source |
| `--sources`        | List all registered external sources |
| `--help`           | Show this command's usage summary |

## Prerequisites

Before executing, read:
1. `.gse/status.yaml` — current sprint context
2. `.gse/config.yaml` — project configuration
3. `.gse/sources.yaml` — existing source inventory (if any)
4. `.gse/backlog.yaml` — current backlog (for cross-referencing)
5. `.gse/profile.yaml` — user profile (apply P9 Adaptive Communication to all output)

## Workflow

> **Workflow structure note.** `/gse:collect` exposes two disjoint modes (Internal — no args, current-project inventory; External — path/URL, external source analysis). Each mode defines its own Step sequence (`#### Step 0..N`), numbering resets per mode. The user invokes exactly one mode per call. This **multi-mode `### Mode → #### Step N` structure** is shared with `/gse:backlog`, `/gse:plan`, `/gse:learn`; see CLAUDE.md — §Activity structural conventions for the full catalog.

### Internal Mode (No Args)

Triggered when no arguments are provided. Inventories the current project.

#### Step 0 — Verify Intent Exists (greenfield preflight)

Before running the inventory, check if the project has an intent artefact:

1. Run the greenfield detection (same exclusion list as `/gse:go` Step 1: `.cursor`, `.claude`, `.gse`, `.git`, `.vscode`, `.idea`, `.fleet`, `node_modules`, `__pycache__`, `.venv`, `target`, `dist`, `build`; also exclude pure-documentation files `*.md`, `*.txt`, `LICENSE`, `README`). If source file count is 0 → project is greenfield.
2. If greenfield AND `docs/intent.md` does **not** exist:
   - Report: *"This project is greenfield and has no project intent artefact. COLLECT expects something to inventory — for an empty project, the first step is to capture what you want to build."*
   - Redirect: invoke `/gse:go` Step 7 (Intent Capture) inline. After the `INT-001` artefact is written, resume COLLECT at Step 1.
   - For beginners, this happens automatically without asking — the redirection is transparent.
3. If greenfield AND `docs/intent.md` exists → proceed to Step 1 (there is an artefact to inventory even if no code exists).
4. If not greenfield → proceed to Step 1 normally.

#### Step 1 — Scan Project Files

Recursively scan the project directory, excluding `.git/`, `__pycache__/`, `node_modules/`, `.gse/local/`.

For each file, record:
- Path (relative to project root)
- Artefact type (inferred from location and extension)
- Size
- Last modified date
- Frontmatter status (has valid frontmatter / missing / malformed)
- Sprint association (from frontmatter or directory)

#### Step 2 — Scan Sprint Artefacts

For each sprint directory in `docs/sprints/`:
- List plan, requirements, design, review, and test report files
- Check completeness (which expected artefacts are missing)
- Check status consistency (frontmatter status vs file content)

#### Step 3 — Scan Learning Notes

List all files in `docs/learning/`:
- Count by topic and mode (quick/deep)
- Identify stale notes (not updated in > 5 sprints)

#### Step 4 — Git State

Capture:
- Current branch
- Uncommitted changes (count)
- Branches with unpushed commits
- Stale branches (no commits in > 2 sprints)

#### Step 5 — Dependencies

Read project manifest (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`):
- List direct dependencies with versions
- Flag outdated dependencies (if version info available)
- Flag dependencies with known vulnerabilities (if audit tool available)

#### Step 6 — Output Internal Inventory

Display summary (the scan result is ephemeral — `/gse:assess` runs its own scan or invokes `/gse:collect` inline when it needs artefact coverage data):

```
Internal Inventory — 2026-01-20
───────────────────────────────
Files scanned:        47
Tracked artefacts:    32 (with frontmatter)
Untracked files:       8 (infrastructure)
Orphan files:          7 (no frontmatter, not in manifest)

Sprint S02:
  Plan:         ✓ complete
  Requirements: ✓ 5 REQs defined
  Design:       ⚠ partial (2/4 components documented)
  Code:         ● 3 files in-progress
  Tests:        ✗ not started

Learning notes:  12 (2 stale)
Dependencies:    15 direct (1 outdated)
Git state:       clean, 2 branches ahead of remote
```

### External Mode (Path or URL)

Triggered when arguments contain a file path or URL.

#### Step 1 — Source Acquisition

**For local paths:**
1. Verify the path exists and is readable
2. Scan recursively, respecting `.gitignore` if present
3. Catalog files by type, size, and structure

**For GitHub URLs:**
1. Parse owner/repo from URL
2. Perform shallow clone to a temporary directory
3. Read README, manifest files, and directory structure
4. Do NOT clone the full history — shallow clone only

#### Step 2 — Element Analysis

For each significant element in the source (files, modules, components):

Evaluate:
- **What it is** — Brief description of the element's purpose
- **Relevance** — How it relates to project goals
- **Quality** — Code quality signals (tests present, documentation, linting)
- **Reusability assessment:**

| Assessment | Meaning |
|-----------|---------|
| **Reusable as-is** | Can be copied/referenced directly with no changes |
| **Adaptable** | Useful but requires modification for this project |
| **Reference only** | Useful to study but cannot be directly reused |
| **Incompatible** | Does not fit this project (wrong language, paradigm, license) |

#### Step 3 — Gate Decision

Present each element group as a Gate decision:

```
External Source: github.com/example/auth-library
──────────────────────────────────────────────

SRC-001  auth/jwt.py          Reusable as-is    JWT token generation/validation
SRC-002  auth/oauth.py        Adaptable         OAuth2 flow (needs config changes)
SRC-003  auth/tests/          Reusable as-is    Test suite for auth module
SRC-004  docs/api-guide.md    Reference only    API documentation patterns
SRC-005  auth/ldap.py         Incompatible      LDAP integration (not needed)

For each element, choose: [Include] / [Skip] / [Discuss]
```

Wait for user decision on each element (or batch approval).

#### Step 4 — Save Sources

Save accepted elements to `.gse/sources.yaml`:

```yaml
sources:
  - id: SRC-001
    origin: "github.com/example/auth-library"
    path: "auth/jwt.py"
    assessment: reusable-as-is
    description: "JWT token generation and validation"
    included: true
    local_path: null  # set when actually imported
    imported_at: null
    provenance:
      url: "https://github.com/example/auth-library"
      commit: "a1b2c3d"
      license: "MIT"
      scanned_at: "2026-01-20"

  - id: SRC-002
    origin: "github.com/example/auth-library"
    path: "auth/oauth.py"
    assessment: adaptable
    description: "OAuth2 flow implementation"
    included: true
    adaptation_notes: "Needs config refactoring for our settings pattern"
    local_path: null
    imported_at: null
    provenance:
      url: "https://github.com/example/auth-library"
      commit: "a1b2c3d"
      license: "MIT"
      scanned_at: "2026-01-20"
```

#### Step 5 — Provenance Traceability

When included sources are later used in production:
- Add `traces.source: SRC-NNN` to the produced artefact's frontmatter
- Maintain license compliance by preserving provenance metadata
- Flag any license incompatibilities at inclusion time
