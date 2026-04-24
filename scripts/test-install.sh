#!/usr/bin/env bash
# Maintainer-run local smoke test for the curl plugin-based installer.
#
# Usage:
#   bash scripts/test-install.sh
#
# What it does (per spec §5.7 — "Local smoke test" and §8 Phase 3):
#   1. shellcheck install.sh (POSIX mode) if present
#   2. Package a local tarball of the repo assets that the CI release workflow
#      would publish (gse-one/plugin/, install.py, VERSION, CHANGELOG.md,
#      README.md, install.sh)
#   3. Run install.sh against a sandboxed HOME, pointing it at the local tarball
#      via the GSE_LOCAL_TARBALL override (if install.sh supports it — see the
#      "Local-tarball override" note below)
#   4. Verify the registry file ~/.gse-one (inside the sandbox HOME) exists and
#      contains an absolute path to a directory that holds a VERSION file
#   5. Verify "cat $(cat $HOME/.gse-one)/VERSION" equals the repo's VERSION
#   6. Run "sh install.sh uninstall" and verify cleanup (registry gone,
#      side-install dir gone)
#   7. Print a colored PASS/FAIL summary and exit non-zero on any failure
#
# Local-tarball override:
#   install.sh is being developed in a sibling PR (Unit 1 of the v0.63.0 work).
#   The spec mentions GSE_VERSION=latest (fetches from GitHub API) and pinning
#   to a specific release tag (e.g. GSE_VERSION=v0.62.1). For maintainer smoke
#   testing we need a third option: use a local tarball the maintainer just
#   built from the current working tree, without a GitHub round-trip.
#
#   This script communicates the local tarball to install.sh through the
#   GSE_LOCAL_TARBALL environment variable (an absolute path to a .tar.gz).
#   If install.sh lacks that hook, this script still performs the static
#   checks (shellcheck, sh -n, detection-logic trace) and reports the
#   end-to-end portion as SKIPPED with a clear message — that way the script
#   remains useful as soon as it is committed, and becomes a full e2e test
#   once Unit 1 adds the local-tarball hook.
#
# Dependencies: bash, shellcheck (optional, warns if missing), tar, python3.

set -eu

# ---------------------------------------------------------------------------
# Constants and helpers
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_SH="$REPO_ROOT/install.sh"
VERSION_FILE="$REPO_ROOT/VERSION"

# ANSI colors (only when stdout is a TTY).
if [ -t 1 ]; then
    C_RED=$'\033[0;31m'
    C_GREEN=$'\033[0;32m'
    C_YELLOW=$'\033[0;33m'
    C_BLUE=$'\033[0;34m'
    C_BOLD=$'\033[1m'
    C_RESET=$'\033[0m'
else
    C_RED=""
    C_GREEN=""
    C_YELLOW=""
    C_BLUE=""
    C_BOLD=""
    C_RESET=""
fi

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILURES=""

record_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '%s[PASS]%s %s\n' "$C_GREEN" "$C_RESET" "$1"
}

record_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILURES="${FAILURES}  - $1"$'\n'
    printf '%s[FAIL]%s %s\n' "$C_RED" "$C_RESET" "$1"
}

record_skip() {
    SKIP_COUNT=$((SKIP_COUNT + 1))
    printf '%s[SKIP]%s %s\n' "$C_YELLOW" "$C_RESET" "$1"
}

info() {
    printf '%s[INFO]%s %s\n' "$C_BLUE" "$C_RESET" "$1"
}

section() {
    printf '\n%s=== %s ===%s\n' "$C_BOLD" "$1" "$C_RESET"
}

# ---------------------------------------------------------------------------
# Temp dir & cleanup
# ---------------------------------------------------------------------------

TMP_ROOT="$(mktemp -d 2>/dev/null || mktemp -d -t gse-smoke)"
SANDBOX_HOME="$TMP_ROOT/home"
TARBALL="$TMP_ROOT/gse-one.tar.gz"
mkdir -p "$SANDBOX_HOME"

# shellcheck disable=SC2329  # cleanup is invoked indirectly via trap
cleanup() {
    rc=$?
    if [ -n "${TMP_ROOT:-}" ] && [ -d "$TMP_ROOT" ]; then
        rm -rf "$TMP_ROOT"
    fi
    return "$rc"
}
trap cleanup EXIT INT TERM

info "Repo root: $REPO_ROOT"
info "Sandbox:   $TMP_ROOT"

# ---------------------------------------------------------------------------
# Step 0 — Pre-flight: install.sh must exist (sibling PR may not have landed)
# ---------------------------------------------------------------------------

section "Pre-flight"

if [ ! -f "$INSTALL_SH" ]; then
    printf '%s[ERROR]%s install.sh not found at %s\n' "$C_RED" "$C_RESET" "$INSTALL_SH" >&2
    printf '\n' >&2
    printf 'This smoke test requires install.sh at the repo root. It is being\n' >&2
    printf 'developed in a sibling PR (Unit 1 of the curl-plugin-based-install\n' >&2
    printf 'feature). Run this test after the install.sh PR merges.\n' >&2
    printf '\n' >&2
    printf 'For a quick local iteration, copy install.sh from the sibling\n' >&2
    printf 'worktree into this repo root and re-run. Do NOT commit that copy.\n' >&2
    exit 1
fi

if [ ! -f "$VERSION_FILE" ]; then
    printf '%s[ERROR]%s VERSION not found at %s\n' "$C_RED" "$C_RESET" "$VERSION_FILE" >&2
    exit 1
fi

EXPECTED_VERSION="$(tr -d ' \t\n\r' < "$VERSION_FILE")"
info "Expected VERSION: $EXPECTED_VERSION"

for dep in tar python3; do
    if ! command -v "$dep" >/dev/null 2>&1; then
        printf '%s[ERROR]%s missing dependency: %s\n' "$C_RED" "$C_RESET" "$dep" >&2
        exit 1
    fi
done

record_pass "install.sh present, VERSION readable, dependencies available"

# ---------------------------------------------------------------------------
# Step 1 — shellcheck install.sh (POSIX-sh dialect) + sh -n syntax check
# ---------------------------------------------------------------------------

section "Static checks"

if command -v shellcheck >/dev/null 2>&1; then
    if shellcheck -s sh "$INSTALL_SH"; then
        record_pass "shellcheck -s sh install.sh"
    else
        record_fail "shellcheck -s sh install.sh"
    fi
else
    record_skip "shellcheck not installed (brew install shellcheck / apt install shellcheck)"
fi

if sh -n "$INSTALL_SH" 2>/dev/null; then
    record_pass "sh -n install.sh (syntax)"
else
    record_fail "sh -n install.sh (syntax)"
fi

# ---------------------------------------------------------------------------
# Step 2 — Package a local tarball mirroring the CI release asset layout
# ---------------------------------------------------------------------------

section "Package local tarball"

# These are the same paths the CI release workflow packages (spec §5.6).
# Relative to REPO_ROOT so the tarball contents match the release asset
# layout exactly.
PACK_PATHS="gse-one/plugin install.py VERSION CHANGELOG.md README.md install.sh"

missing=""
for p in $PACK_PATHS; do
    if [ ! -e "$REPO_ROOT/$p" ]; then
        missing="$missing $p"
    fi
done

if [ -n "$missing" ]; then
    record_fail "tarball contents missing:$missing"
else
    # shellcheck disable=SC2086
    if (cd "$REPO_ROOT" && tar -czf "$TARBALL" $PACK_PATHS) 2>/dev/null; then
        size=$(wc -c < "$TARBALL" | tr -d ' ')
        record_pass "packaged local tarball ($size bytes) at $TARBALL"
    else
        record_fail "tar -czf failed"
    fi
fi

# ---------------------------------------------------------------------------
# Step 3 — Detect whether install.sh supports a local-tarball override
# ---------------------------------------------------------------------------

section "Local-tarball override detection"

# Probe install.sh for a GSE_LOCAL_TARBALL hook. If absent, fall back to a
# dry trace of the detection logic + already-executed static checks, and mark
# the end-to-end steps as SKIPPED.
HAS_LOCAL_HOOK=0
if grep -q 'GSE_LOCAL_TARBALL' "$INSTALL_SH" 2>/dev/null; then
    HAS_LOCAL_HOOK=1
    record_pass "install.sh honors GSE_LOCAL_TARBALL (end-to-end test enabled)"
else
    record_skip "install.sh does not reference GSE_LOCAL_TARBALL — end-to-end test will be skipped"
    info "Add 'GSE_LOCAL_TARBALL' support to install.sh to enable full e2e:"
    info "  when set to an absolute .tar.gz path, skip curl and copy/extract locally"
fi

info "Detection logic trace (first 40 relevant lines of install.sh):"
grep -nE 'GSE_(PLATFORM|MODE|SCOPE|VERSION|PROJECT_DIR|LOCAL_TARBALL)|command -v (claude|cursor|opencode)|\.claude/|\.cursor/|\.opencode/' \
    "$INSTALL_SH" 2>/dev/null | head -40 || true

# ---------------------------------------------------------------------------
# Step 4 — Sandboxed install, if supported
# ---------------------------------------------------------------------------

section "Sandboxed install"

if [ "$HAS_LOCAL_HOOK" = "1" ] && [ -f "$TARBALL" ]; then
    # Default to claude plugin user-scope install — the simplest mode for
    # sandbox testing. The sandbox HOME is fresh, so ~/.gse-one.d/ and
    # ~/.gse-one won't exist yet. Set GSE_PLATFORM=claude to avoid depending
    # on which platform binaries are on the maintainer's PATH.
    install_log="$TMP_ROOT/install.log"
    set +e
    HOME="$SANDBOX_HOME" \
        GSE_LOCAL_TARBALL="$TARBALL" \
        GSE_PLATFORM="claude" \
        GSE_MODE="plugin" \
        GSE_SCOPE="user" \
        sh "$INSTALL_SH" >"$install_log" 2>&1
    install_rc=$?
    set -e

    if [ "$install_rc" -eq 0 ]; then
        record_pass "sh install.sh (sandboxed HOME, local tarball) exited 0"
    else
        record_fail "sh install.sh exited $install_rc (see $install_log)"
        tail -20 "$install_log" || true
    fi

    # ---------------------------------------------------------------
    # Step 5 — Verify registry
    # ---------------------------------------------------------------
    section "Registry verification"

    REG="$SANDBOX_HOME/.gse-one"
    if [ -f "$REG" ]; then
        record_pass "registry file $SANDBOX_HOME/.gse-one exists"
        REG_TARGET="$(tr -d '\n\r' < "$REG")"
        info "Registry target: $REG_TARGET"
        if [ -d "$REG_TARGET" ]; then
            record_pass "registry target directory exists"
        else
            record_fail "registry target directory does not exist: $REG_TARGET"
        fi
        if [ -f "$REG_TARGET/VERSION" ]; then
            record_pass "VERSION file present in registry target"
            INSTALLED_VERSION="$(tr -d ' \t\n\r' < "$REG_TARGET/VERSION")"
            info "Installed VERSION: $INSTALLED_VERSION"
            if [ "$INSTALLED_VERSION" = "$EXPECTED_VERSION" ]; then
                record_pass "installed VERSION matches repo VERSION ($EXPECTED_VERSION)"
            else
                record_fail "VERSION mismatch: installed=$INSTALLED_VERSION expected=$EXPECTED_VERSION"
            fi
        else
            record_fail "VERSION file missing in registry target"
        fi
    else
        record_fail "registry file $SANDBOX_HOME/.gse-one not created"
    fi

    # ---------------------------------------------------------------
    # Step 6 — Uninstall and verify cleanup
    # ---------------------------------------------------------------
    section "Uninstall"

    uninstall_log="$TMP_ROOT/uninstall.log"
    set +e
    HOME="$SANDBOX_HOME" \
        GSE_LOCAL_TARBALL="$TARBALL" \
        GSE_PLATFORM="claude" \
        GSE_MODE="plugin" \
        GSE_SCOPE="user" \
        sh "$INSTALL_SH" uninstall >"$uninstall_log" 2>&1
    uninstall_rc=$?
    set -e

    if [ "$uninstall_rc" -eq 0 ]; then
        record_pass "sh install.sh uninstall exited 0"
    else
        record_fail "sh install.sh uninstall exited $uninstall_rc (see $uninstall_log)"
        tail -20 "$uninstall_log" || true
    fi

    if [ ! -e "$SANDBOX_HOME/.gse-one" ]; then
        record_pass "registry file removed after uninstall"
    else
        record_fail "registry file $SANDBOX_HOME/.gse-one still exists after uninstall"
    fi

    if [ ! -e "$SANDBOX_HOME/.gse-one.d" ]; then
        record_pass "side-install dir ~/.gse-one.d removed after uninstall"
    else
        record_fail "side-install dir $SANDBOX_HOME/.gse-one.d still exists after uninstall"
    fi
else
    record_skip "end-to-end install/uninstall cycle (requires GSE_LOCAL_TARBALL hook in install.sh)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

section "Summary"
printf '  %sPASS%s : %d\n' "$C_GREEN" "$C_RESET" "$PASS_COUNT"
printf '  %sFAIL%s : %d\n' "$C_RED" "$C_RESET" "$FAIL_COUNT"
printf '  %sSKIP%s : %d\n' "$C_YELLOW" "$C_RESET" "$SKIP_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    printf '\n%sFailures:%s\n' "$C_RED" "$C_RESET"
    printf '%s' "$FAILURES"
    printf '\n%sRESULT: FAIL%s\n' "$C_RED$C_BOLD" "$C_RESET"
    exit 1
fi

printf '\n%sRESULT: PASS%s\n' "$C_GREEN$C_BOLD" "$C_RESET"
exit 0
