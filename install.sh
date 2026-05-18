#!/bin/sh
# GSE-One — curl | sh bootstrap installer.
# Spec: docs/specs/curl-plugin-based-install.md
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | sh
#   curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | sh -s -- uninstall
#   curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | sh -s -- upgrade
#
# Env overrides:
#   GSE_PLATFORM   claude|cursor|opencode|all|both   (default: auto-detect)
#   GSE_MODE       plugin|no-plugin                  (default: auto-detect)
#   GSE_SCOPE      project|local|user                (default: user)
#   GSE_VERSION    vX.Y.Z|latest                     (default: latest)
#   GSE_PROJECT_DIR /abs/path                        (no-plugin only)
#   GSE_LOCAL_TARBALL /abs/path/gse-one.tar.gz       (maintainer-only: skip
#                                                     network fetch and use a
#                                                     local tarball instead;
#                                                     consumed by scripts/test-install.sh)
#   GSE_OWNER_REPO  owner/repo                       (override upstream repo for
#                                                     test forks, e.g.
#                                                     tjisousa/gensem)

set -eu

OWNER_REPO="${GSE_OWNER_REPO:-nicolasguelfi/gensem}"
API_LATEST="https://api.github.com/repos/${OWNER_REPO}/releases/latest"
REGISTRY_FILE="${HOME}/.gse-one"

info() { printf '[gse-one] %s\n' "$*" >&2; }
warn() { printf '[gse-one] warn: %s\n' "$*" >&2; }
fail() { printf '[gse-one] error: %s\n' "$*" >&2; exit 1; }

# OS-specific python3 install hint.
python_install_hint() {
    case "$(uname -s 2>/dev/null || echo unknown)" in
        Darwin) printf 'brew install python3'; return ;;
        Linux)  : ;;
        *)      printf 'install python3 for your OS'; return ;;
    esac
    if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release 2>/dev/null || true
        case "${ID:-}${ID_LIKE:-}" in
            *debian*|*ubuntu*)                         printf 'apt install python3' ;;
            *rhel*|*fedora*|*centos*|*rocky*|*alma*)   printf 'dnf install python3' ;;
            *arch*)                                    printf 'pacman -S python' ;;
            *)                                         printf 'install python3 via your package manager' ;;
        esac
    else
        printf 'install python3 via your package manager'
    fi
}

preflight() {
    command -v curl >/dev/null 2>&1 || fail "curl is required but not found in PATH."
    command -v tar  >/dev/null 2>&1 || fail "tar is required but not found in PATH."
    if ! command -v python3 >/dev/null 2>&1; then
        fail "python3 (>= 3.8) is required but not found. Try: $(python_install_hint)"
    fi
    if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
        pyver=$(python3 -c 'import sys; print(".".join(map(str,sys.version_info[:3])))' 2>/dev/null || echo unknown)
        fail "python3 >= 3.8 required; found ${pyver}. Try: $(python_install_hint)"
    fi
}

# Default mode is no-plugin — install artifacts into the current project, not
# globally. Users who want a user-scope plugin install must set GSE_MODE=plugin
# explicitly. This avoids surprise global installs for a casual one-liner run
# in an unrelated directory.
detect_mode() {
    if [ -n "${GSE_MODE:-}" ]; then printf '%s' "$GSE_MODE"; return; fi
    printf 'no-plugin'
}

# Translate detected platforms into install.py --platform value.
# Passes overrides through as-is; collapses 2+ PATH-detected binaries to 'all'.
detect_platform_flag() {
    if [ -n "${GSE_PLATFORM:-}" ]; then printf '%s' "$GSE_PLATFORM"; return; fi
    found=""
    command -v claude   >/dev/null 2>&1 && found="$found claude"
    command -v cursor   >/dev/null 2>&1 && found="$found cursor"
    command -v opencode >/dev/null 2>&1 && found="$found opencode"
    count=$(printf '%s' "$found" | wc -w | tr -d ' ')
    if   [ "$count" -ge 2 ]; then printf 'all'
    elif [ "$count" -eq 1 ]; then printf '%s' "$(printf '%s' "$found" | tr -d ' ')"
    fi
}

resolve_version() {
    if [ -n "${GSE_LOCAL_TARBALL:-}" ]; then printf 'local'; return; fi
    req="${GSE_VERSION:-latest}"
    if [ -n "$req" ] && [ "$req" != "latest" ]; then printf '%s' "$req"; return; fi
    info "Resolving latest release via GitHub API..."
    tag=$(curl -fsSL "$API_LATEST" 2>/dev/null \
        | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tag_name",""))
except Exception: pass' 2>/dev/null || true)
    [ -n "$tag" ] || fail "Could not resolve latest release from ${API_LATEST}"
    printf '%s' "$tag"
}

# Print installed tag (vX.Y.Z) if registry + VERSION file present; empty otherwise.
installed_version() {
    [ -f "$REGISTRY_FILE" ] || return 0
    target=$(cat "$REGISTRY_FILE" 2>/dev/null || true)
    [ -n "$target" ] && [ -f "$target/VERSION" ] || return 0
    v=$(tr -d '[:space:]' < "$target/VERSION" 2>/dev/null || true)
    [ -n "$v" ] && printf 'v%s' "$v"
}

# Download release tarball and extract into $dest; echo dir containing install.py.
download_and_extract() {
    tag=$1; dest=$2
    if [ -n "${GSE_LOCAL_TARBALL:-}" ]; then
        [ -f "$GSE_LOCAL_TARBALL" ] || fail "GSE_LOCAL_TARBALL=${GSE_LOCAL_TARBALL} not found."
        info "Using local tarball: ${GSE_LOCAL_TARBALL}"
        tar -xz -C "$dest" -f "$GSE_LOCAL_TARBALL" \
            || fail "Failed to extract local tarball ${GSE_LOCAL_TARBALL}"
    else
        url="https://github.com/${OWNER_REPO}/releases/download/${tag}/gse-one.tar.gz"
        info "Downloading ${url}"
        curl -fsSL "$url" | tar -xz -C "$dest" \
            || fail "Failed to download or extract tarball from ${url}"
    fi
    if [ -f "$dest/install.py" ]; then
        printf '%s' "$dest"; return
    fi
    nested=$(find "$dest" -maxdepth 2 -name install.py -print 2>/dev/null | head -n 1)
    [ -n "$nested" ] && [ -f "$nested" ] || fail "Tarball extracted but install.py not found under ${dest}"
    dirname "$nested"
}

# Create temp dir and echo it. Caller must register the cleanup trap (trap set
# inside a function consumed via `$(...)` fires when the subshell exits,
# which deletes the dir before the outer shell can use it).
make_tmp() {
    t=$(mktemp -d 2>/dev/null || mktemp -d -t gse-one)
    [ -n "$t" ] && [ -d "$t" ] || fail "Failed to create temp directory."
    printf '%s' "$t"
}

# Run install.py from the extracted directory (it asserts CWD contains install.py
# + gse-one/plugin + VERSION) with the given flags.
run_install_py() {
    install_root=$1; shift
    (cd "$install_root" && python3 install.py "$@")
}

# Shared prelude for install/uninstall: preflight, detect, resolve, download.
# Sets globals: mode, plat_flag, scope, project_dir, target_tag, install_root.
prepare() {
    preflight
    mode=$(detect_mode)
    plat_flag=$(detect_platform_flag)
    scope="${GSE_SCOPE:-user}"
    project_dir="${GSE_PROJECT_DIR:-}"
    if [ "$mode" = "no-plugin" ] && [ -z "$project_dir" ]; then
        project_dir=$(pwd)
    fi

    target_tag=$(resolve_version)
    tmp=$(make_tmp)
    # shellcheck disable=SC2064
    trap "rm -rf '$tmp'" EXIT INT TERM
    install_root=$(download_and_extract "$target_tag" "$tmp")
}

subcmd_install() {
    prepare
    [ -n "$plat_flag" ] || fail "No supported platform detected (claude, cursor, opencode). Set GSE_PLATFORM to override."

    current=$(installed_version)
    info "Target version : ${target_tag}"
    info "Mode           : ${mode}"
    info "Platforms      : ${plat_flag}"
    [ -n "$project_dir" ] && info "Project dir    : ${project_dir}"
    [ "$mode" = "plugin" ] && info "Scope          : ${scope}"

    # Version-match early-exit only applies to plugin mode (one global install
    # per machine). No-plugin is per-project — running the installer in a new
    # project dir must always provision that project, even if some earlier
    # project at the same version is already registered.
    if [ "$mode" = "plugin" ] && [ -n "$current" ] && [ "$current" = "$target_tag" ]; then
        info "already at ${current} — nothing to do."
        exit 0
    fi

    set -- --platform "$plat_flag" --mode "$mode"
    if [ "$mode" = "plugin" ]; then
        set -- "$@" --scope "$scope"
    else
        set -- "$@" --project-dir "$project_dir"
    fi

    info "Executing install.py with flags: $*"
    run_install_py "$install_root" "$@"

    if [ -n "$current" ] && [ "$current" != "$target_tag" ]; then
        info "upgraded ${current} → ${target_tag}"
    else
        info "installed ${target_tag}"
    fi
}

subcmd_uninstall() {
    # Idempotent per US-5: no registry file means nothing to uninstall.
    if [ ! -f "$REGISTRY_FILE" ]; then
        info "Nothing installed — ${REGISTRY_FILE} not found. Exiting 0 (idempotent)."
        exit 0
    fi

    prepare
    # If nothing in PATH but registry exists, fall back to 'all'.
    [ -n "$plat_flag" ] || plat_flag=all

    info "Uninstalling GSE-One (platforms: ${plat_flag}, mode: ${mode}, version: ${target_tag})"

    set -- --uninstall --platform "$plat_flag" --mode "$mode"
    if [ "$mode" = "no-plugin" ] && [ -n "$project_dir" ]; then
        set -- "$@" --project-dir "$project_dir"
    fi

    run_install_py "$install_root" "$@" || warn "install.py --uninstall reported a non-zero exit."
    info "uninstall complete."
}

subcmd_upgrade() {
    GSE_VERSION=latest
    export GSE_VERSION
    subcmd_install
}

usage() {
    cat <<'EOF'
GSE-One installer

Usage:
  install.sh [install]     install or upgrade GSE-One (default)
  install.sh uninstall     remove GSE-One
  install.sh upgrade       force-resolve latest and install
  install.sh -h|--help     show this help
EOF
}

main() {
    case "${1:-install}" in
        install)         subcmd_install ;;
        uninstall)       subcmd_uninstall ;;
        upgrade)         subcmd_upgrade ;;
        -h|--help|help)  usage ;;
        *)               usage; fail "Unknown subcommand: ${1:-}" ;;
    esac
}

main "$@"
