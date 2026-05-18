# Specification: curl plugin based install

**Feature slug:** `curl-plugin-based-install`
**Status:** Draft — spec finalized 2026-04-24
**Target version:** v0.63.0 (next minor — new distribution surface)

---

## 1. Overview

Deliver a `curl | sh` one-liner installer for GSE-One that complements the current `git clone + python3 install.py` flow. The one-liner is a thin shell bootstrap that auto-detects the user's coding environment (Claude Code, Cursor, opencode), downloads the latest release tarball from GitHub, and hands off to `install.py` with resolved flags.

**Canonical one-liner (MVP):**

```
curl -fsSL https://raw.githubusercontent.com/<owner>/gensem/main/install.sh | sh
```

Subcommands via `sh -s --`:

```
curl -fsSL https://raw.githubusercontent.com/<owner>/gensem/main/install.sh | sh -s -- uninstall
curl -fsSL https://raw.githubusercontent.com/<owner>/gensem/main/install.sh | sh -s -- upgrade
```

## 2. Problem Statement

Current install path:

```
git clone https://github.com/<owner>/gensem
cd gensem
python3 install.py
```

Three friction points:

1. **Not copy-paste-friendly.** Three commands cannot be pasted from a README or Slack message.
2. **Leaves a source repo artifact.** Users don't know the v0.61.0 registry refactor made the clone disposable.
3. **Adoption ceiling.** Every peer (rustup, ollama, oh-my-zsh, Homebrew) trains users to expect a `curl … | sh` idiom.

A `curl | sh` one-liner eliminates all three.

## 3. Scope

### 3.1 In Scope (MVP)

- **Single POSIX-sh bootstrap** `install.sh` at the repo root, hosted via `raw.githubusercontent.com/<owner>/gensem/main/install.sh`.
- **Zero-prompt one-liner.** No interactive questions; the script auto-detects and acts.
- **Full parity with `install.py`:**
  - All 6 install modes (claude plugin user/project, claude no-plugin, cursor plugin global, cursor no-plugin, opencode plugin global, opencode no-plugin).
  - Install (default), `uninstall`, and `upgrade` subcommands.
- **GitHub release tarball** as source of plugin files — tag-pinned, built by CI on tag push.
- **Auto-detection:**
  - Mode default: `no-plugin`, with `project-dir = $PWD`. Whatever platforms are detected get installed into the current directory (`.claude/` / `.cursor/` / `.opencode/` subfolders are created as needed). This avoids surprise global installs when a user pastes the one-liner in a random directory.
  - `GSE_MODE=plugin` (opt-in) switches to user-scope plugin install.
  - Platform scan: install on **all** detected platforms (equivalent of `install.py --platform all`).
- **Env-var overrides:** `GSE_PLATFORM`, `GSE_MODE`, `GSE_SCOPE`, `GSE_VERSION`, `GSE_PROJECT_DIR`.
- **Runtime version resolution.** `GSE_VERSION=latest` → `https://api.github.com/repos/<owner>/gensem/releases/latest`. User may pin with `GSE_VERSION=v0.63.0`.
- **Re-install detection.** If `$(cat ~/.gse-one)/VERSION` equals target, print `already at vX.Y.Z` and exit 0. Otherwise upgrade in place.
- **CI release workflow** (`.github/workflows/release.yml`) triggered on `v*` tag push.
- **Local smoke test script** (`scripts/test-install.sh`) for maintainer-driven regression testing.

### 3.2 Out of Scope

- Windows native shell (`.ps1`). Windows users go via WSL or `python3 install.py`.
- `npx` / `uvx` wrappers.
- Interactive / TTY prompts.
- Multi-version side-by-side installs.
- Checksum / signature verification (HTTPS-only trust; see §7.3).
- Auto-installing python3 if absent (see §7.2).
- Migration tooling for existing `git clone`-based installs (re-running via curl overwrites safely).

## 4. User Stories

### US-1 — Zero-prompt happy-path install (plugin, user scope)

**As** a first-time GSE-One user with Claude Code installed, **I want** to run a single copy-pasted command from the README, **so that** the plugin appears in my Claude Code session without further setup.

**Acceptance criteria:**
- [ ] `curl -fsSL https://raw.githubusercontent.com/<owner>/gensem/main/install.sh | sh` exits 0 on macOS and Linux default shells.
- [ ] `~/.gse-one` exists and points to `~/.gse-one.d/`.
- [ ] `cat $(cat ~/.gse-one)/VERSION` prints the latest release tag.
- [ ] `gse-orchestrator` agent is discoverable by Claude Code.
- [ ] Total runtime < 30 seconds on a 50 Mbps connection.

### US-2 — Zero-prompt multi-platform install

**As** a user with both Claude Code and Cursor installed, **I want** the one-liner to provision both, **so that** I don't run it twice.

**Acceptance criteria:**
- [ ] With `claude` and `cursor` both in PATH, the one-liner installs on both.
- [ ] `~/.gse-one` points to the Claude side-install dir (priority: claude > cursor > opencode).
- [ ] Cursor plugin is discoverable in Cursor settings.
- [ ] Log output lists both installs under a per-platform summary.

### US-3 — No-plugin project-scope auto-detection

**As** a user in a project dir that already has a `.claude/` folder, **I want** the one-liner to install in no-plugin mode inside that project.

**Acceptance criteria:**
- [ ] `cd myproject && ls .claude && curl … | sh` installs in `$PWD/.claude/` (not `~/.claude.d/`).
- [ ] `$(cat ~/.gse-one)` resolves to `$PWD/.claude/`.
- [ ] Running the one-liner twice is idempotent (second run prints `already at vX.Y.Z`).

### US-4 — Env-var-driven explicit install

**As** an advanced user scripting GSE-One deployment, **I want** to bypass auto-detection with explicit env vars.

**Acceptance criteria:**
- [ ] `GSE_PLATFORM=cursor GSE_MODE=plugin sh install.sh` installs only on Cursor.
- [ ] `GSE_VERSION=v0.62.1 sh install.sh` installs that exact version.
- [ ] `GSE_MODE=no-plugin GSE_PROJECT_DIR=/tmp/foo sh install.sh` installs into `/tmp/foo/.claude/`.
- [ ] Missing `GSE_PROJECT_DIR` with `GSE_MODE=no-plugin` and no platform dir in CWD → exit 1 with clear message.

### US-5 — Uninstall via curl

**As** a user who wants a clean uninstall, **I want** to re-use the same one-liner URL.

**Acceptance criteria:**
- [ ] `curl … | sh -s -- uninstall` removes the registry file and all common assets.
- [ ] After uninstall, `~/.gse-one` does not exist.
- [ ] After uninstall, `~/.gse-one.d/` is gone.
- [ ] Uninstall is idempotent (exit 0 if nothing installed).

### US-6 — Upgrade via curl

**As** a user on a stale version, **I want** `sh -s -- upgrade` to migrate me to latest.

**Acceptance criteria:**
- [ ] `curl … | sh -s -- upgrade` resolves latest via GitHub API.
- [ ] If installed == latest, prints `already at vX.Y.Z` and exits 0.
- [ ] If different, performs full install and reports `upgraded vA → vB`.
- [ ] Registry path is preserved across upgrade.

### US-7 — CI-published tarball per release

**As** a maintainer, **I want** every `git tag v*` push to produce a release with `gse-one.tar.gz` attached.

**Acceptance criteria:**
- [ ] `.github/workflows/release.yml` triggers on tag push matching `v*`.
- [ ] Workflow runs `cd gse-one && python3 gse_generate.py --verify`.
- [ ] Workflow packages `gse-one/plugin/`, `install.py`, `VERSION`, `CHANGELOG.md`, `README.md`, `install.sh` into `gse-one.tar.gz`.
- [ ] Workflow attaches the tarball via `gh release create`.
- [ ] URL pattern: `https://github.com/<owner>/gensem/releases/download/vX.Y.Z/gse-one.tar.gz`.

### US-8 — Missing python3 diagnostic

**As** a user on a fresh machine without python3, **I want** a clear actionable error.

**Acceptance criteria:**
- [ ] Script exits 1 if `python3 --version` fails or reports < 3.8.
- [ ] Error names OS-specific install command: `brew install python3` (Darwin), `apt install python3` (Debian/Ubuntu), `dnf install python3` (RHEL).
- [ ] Error written to stderr.

## 5. Technical Design

### 5.1 Bootstrap flow

```
1. parse subcommand (install | uninstall | upgrade)
2. preflight: check curl, tar, python3 ≥ 3.8
3. detect platforms (claude, cursor, opencode)
4. detect mode from CWD (.claude / .cursor / .opencode)
5. resolve GSE_VERSION (default → GitHub API latest)
6. read existing install version if any
7. skip if target == existing
8. mktemp -d; trap EXIT rm -rf
9. curl -fsSL <tarball-URL> | tar -xz -C $tmp
10. exec python3 $tmp/install.py --flags ...
11. cleanup via trap
```

### 5.2 Flag translation (shell → Python)

| Shell detection | `install.py` invocation |
|---|---|
| `GSE_PLATFORM=auto`, multiple detected | `--platform all` |
| `GSE_PLATFORM=claude` | `--platform claude` |
| `GSE_MODE=plugin`, `GSE_SCOPE=user` | `--mode plugin --scope user` |
| `GSE_MODE=no-plugin`, CWD has `.claude/` | `--mode no-plugin --project-dir $PWD` |
| Subcommand `uninstall` | `--uninstall --platform <detected>` |
| Subcommand `upgrade` | same as install, forces `GSE_VERSION=latest` |

### 5.3 Auto-detection algorithm

```
resolve_mode():
    if GSE_MODE set:     return (GSE_MODE, GSE_PROJECT_DIR or PWD)
    return ("no-plugin", PWD)   # default — install into current directory

resolve_platform():
    platforms = []
    if command -v claude:   platforms += [claude]
    if command -v cursor:   platforms += [cursor]
    if command -v opencode: platforms += [opencode]
    if empty(platforms):    fail("no supported platform detected")
    return platforms  # install on ALL
```

Registry priority for multi-platform installs: **claude > cursor > opencode**.

### 5.4 Version resolution

```
resolve_version():
    if GSE_VERSION and GSE_VERSION != "latest":
        return GSE_VERSION
    api = "https://api.github.com/repos/<owner>/gensem/releases/latest"
    tag = curl -fsSL $api | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])"
    if empty(tag): fail("could not resolve latest release")
    return tag
```

We use `python3` (already a hard dep) to parse JSON, avoiding a `jq` dependency.

### 5.5 Hosting

- `install.sh` lives at the repo root, served via `raw.githubusercontent.com/<owner>/gensem/main/install.sh`.
- Any commit to `main` deploys the updated script instantly.
- The script is decoupled from release tags — it resolves the tag at runtime.
- Implication: install.sh fixes deploy without a release bump. Tarball-level issues require a new release.

### 5.6 CI workflow

`.github/workflows/release.yml`:

```yaml
on:
  push:
    tags: ['v*']
jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: cd gse-one && python3 gse_generate.py --verify
      - run: tar -czf gse-one.tar.gz
               gse-one/plugin install.py VERSION
               CHANGELOG.md README.md install.sh
      - run: gh release create ${{ github.ref_name }}
               --title ${{ github.ref_name }}
               gse-one.tar.gz
        env: { GH_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
```

### 5.7 Local smoke test

`scripts/test-install.sh`:

```
- shellcheck install.sh
- run install.sh against a sandbox (mocked $HOME)
- verify ~/.gse-one exists
- verify VERSION matches expected
- run uninstall
- verify cleanup
```

## 6. Requirements

### 6.1 Functional Requirements

- **FR-1** `install.sh` is POSIX-sh compatible (shellcheck `-s sh` passes).
- **FR-2** Script exits non-zero with OS-specific message if `python3 ≥ 3.8` is absent.
- **FR-3** Script exits non-zero with clear error if `curl` or `tar` are absent.
- **FR-4** Auto-detection finds claude / cursor / opencode via PATH binaries.
- **FR-5** Multiple detected platforms without `GSE_PLATFORM` override → install on all.
- **FR-6** Env vars `GSE_PLATFORM`, `GSE_MODE`, `GSE_SCOPE`, `GSE_VERSION`, `GSE_PROJECT_DIR` override auto-detection.
- **FR-7** Presence of `.claude/`, `.cursor/`, or `.opencode/` in CWD sets `MODE=no-plugin`, `PROJECT_DIR=$PWD` (unless overridden).
- **FR-8** Mode check (CWD) evaluated before platform detection.
- **FR-9** `uninstall` subcommand invokes `install.py --uninstall` with detected platform.
- **FR-10** `upgrade` subcommand forces `GSE_VERSION=latest` and re-runs install.
- **FR-11** `latest` → GitHub API `/releases/latest` → `tag_name`.
- **FR-12** Tarball downloaded to `mktemp -d`, extracted, removed on exit via trap.
- **FR-13** Installed version detection: read `$(cat ~/.gse-one)/VERSION` when registry exists.
- **FR-14** Re-install skip: installed == target → exit 0, no file writes.
- **FR-15** CI publishes `gse-one.tar.gz` as release asset on every `v*` tag.
- **FR-16** CI validates via `gse_generate.py --verify` before packaging.
- **FR-17** Local smoke test covers shellcheck + sandboxed install/uninstall cycle.

### 6.2 Non-Functional Requirements

- **NFR-1** Install completes in < 30s on 50 Mbps (tarball target size < 5 MB).
- **NFR-2** `install.sh` stays under 300 lines for auditability.
- **NFR-3** No dependencies beyond `curl`, `tar`, `python3`, POSIX `sh`.
- **NFR-4** HTTPS-only; no unverified redirects.
- **NFR-5** Errors on stderr, progress on stdout; exit codes follow `install.py` conventions.
- **NFR-6** No checksum / signature in MVP (HTTPS trust model; see §7.3).

## 7. Trade-offs and Risk Notes

### 7.1 raw.githubusercontent.com vs. release asset

Chose `main/install.sh` URL over release-asset URL: single stable URL, script decoupled from release cadence, fixes deploy with next commit. Risk: broken commit to `main` breaks new installs. Mitigation: local smoke test before merge.

### 7.2 Python3 auto-install — deliberately skipped

No `brew install python3` attempt. `sudo` prompts break zero-prompt contract; package-manager detection has edge cases. Users missing python3 likely lack other basics — a clear message is better.

### 7.3 HTTPS-only, no checksum — rationale

GitHub TLS is the trust anchor. Unsigned checksums are pseudo-security. Peers (rustup, ollama, bun) ship HTTPS-only. SHA-256 is backward-compatible to add later: publish `.sha256` alongside, check opportunistically.

### 7.4 No Windows PowerShell in MVP

Windows adoption signal is unknown. Doubling maintenance surface now is premature. WSL users get Linux path; native Windows users fall back to `python3 install.py`.

### 7.5 No retry / resilience on flaky network

MVP assumes `curl -fsSL` succeeds or user retries. `curl --retry 3` is a trivial future addition if needed.

### 7.6 CWD heuristic false positives

A user in a dir with `.claude/` for unrelated reasons gets no-plugin mode there. Deliberate trade — `.claude/` is a strong enough signal. Override with `GSE_MODE=plugin`.

## 8. Implementation Phases

### Phase 1 — Shell bootstrap with flag translation

**Goal:** `install.sh` delegates to `install.py` with correctly resolved flags. Assumes tarball is manually published for testing.

**Tasks:**
- [ ] Write `install.sh` at repo root (POSIX-sh, < 300 lines).
- [ ] Preflight: curl, tar, python3 ≥ 3.8.
- [ ] CWD-based mode detection.
- [ ] Platform binary detection.
- [ ] `GSE_*` env-var overrides.
- [ ] Version resolution via GitHub API.
- [ ] Re-install skip when version matches.
- [ ] Tarball download + extract + exec install.py.
- [ ] `uninstall` and `upgrade` subcommands.
- [ ] OS-specific python3 error messages.
- [ ] README one-liner as primary install method.

**Verification:**

```
shellcheck -s sh install.sh
GSE_VERSION=v0.63.0-test sh install.sh
```

### Phase 2 — CI release workflow

**Goal:** every `git tag v*` push produces a release with `gse-one.tar.gz`.

**Tasks:**
- [ ] Create `.github/workflows/release.yml`.
- [ ] Run `gse_generate.py --verify` before packaging.
- [ ] Package plugin/, install.py, VERSION, CHANGELOG.md, README.md, install.sh.
- [ ] Publish with CHANGELOG section as release notes.
- [ ] Dry-run with `v0.63.0-rc1` pre-release tag.
- [ ] Extend Build pipeline section of CLAUDE.md.

**Verification:**

```
git tag v0.63.0-rc1 && git push origin v0.63.0-rc1
gh release view v0.63.0-rc1 --json assets
curl -fsSL https://github.com/<owner>/gensem/releases/download/v0.63.0-rc1/gse-one.tar.gz \
  | tar -tz | head
```

### Phase 3 — Local smoke test + documentation polish

**Goal:** maintainer-run smoke test catching regressions, plus user-facing doc updates.

**Tasks:**
- [ ] Write `scripts/test-install.sh` (shellcheck + sandboxed install/uninstall).
- [ ] Sandbox uses temporary HOME.
- [ ] README "Environment variables" section documenting `GSE_*`.
- [ ] README Troubleshooting section (python3 missing, curl missing, API rate limit).
- [ ] CHANGELOG entry under v0.63.0.
- [ ] CLAUDE.md cross-references updated where install flow is mentioned.

**Verification:**

```
bash scripts/test-install.sh
# Manual: follow README one-liner on a clean macOS VM
```

## 9. Open Questions

None at finalization. Future iterations may revisit:

- Checksum / signature verification (§7.3).
- Windows PowerShell counterpart (§7.4).
- CI matrix testing of install.sh on macOS + Ubuntu.
- npx / uvx wrappers.

## 10. Related Work & Precedents

- **rustup** (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`) — POSIX sh, zero-prompt, multi-arch detection.
- **Ollama** (`curl -fsSL https://ollama.com/install.sh | sh`) — POSIX sh, OS detection, downloads binary.
- **Homebrew** (`/bin/bash -c "$(curl -fsSL …)"`) — bash-only, more interactive.
- **Bun** (`curl -fsSL https://bun.sh/install | bash`) — bash-only, auto-installs to `~/.bun/`.

GSE-One follows the rustup / ollama school: strict POSIX, zero-prompt, detect-before-act.
