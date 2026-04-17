---
gse:
  type: decision
  sprint: 0
  branch: main
  status: draft
  created: "2026-04-17"
  updated: "2026-04-17"
  traces:
    derives_from: []
    implements: []
    tested_by: []
    decided_by: []
---

## COLLECT (Sprint 0 baseline) — gensem repo inventory

### Repository shape (top-level)
- `install.py` — installer entry point
- `gse-one/` — GSE-One sources + generated plugin
- `assets/` — images/branding
- `gse-one-spec.md`, `gse-one-implementation-design.md` — high-level specification/design docs
- `CHANGELOG.md`, `VERSION`, `LICENSE`, `README.md`, `CLAUDE.md`

### Source-of-truth vs generated outputs
- **Source-of-truth**: `gse-one/src/`
  - `activities/` (activity definitions)
  - `agents/` (specialized agents + orchestrator)
  - `principles/` (methodology principles)
  - `templates/` (artefact/config templates)
- **Generated**: `gse-one/plugin/`
  - `skills/`, `agents/`, `templates/`, `tools/`, `commands/`, `hooks/`, manifests

### Primary scripts
- `install.py`
- `gse-one/gse_generate.py`
- `gse-one/plugin/tools/dashboard.py`

### GSE tracking (repo-local)
- `gensem/.gse/` and `gensem/docs/` were created for sprint-0 tracking (separate from any workspace-level tracking).

