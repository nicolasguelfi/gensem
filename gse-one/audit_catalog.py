#!/usr/bin/env python3
# @gse-tool audit_catalog 1.0
"""Audit catalog loader and validator.

Loads `.claude/audit-jobs.json` from the repo root, validates the schema,
resolves file globs, and exposes helpers for `audit.py` (cluster-aware
deterministic checks) and for the `/gse-audit` skill orchestrator
(which spawns one sub-agent per job in parallel).

Usage as a library:
    from audit_catalog import load_catalog, AuditJob
    jobs = load_catalog(repo_root)
    for job in jobs:
        files = job.resolved_files(repo_root)
        ...

Usage as a CLI (for inspection):
    python3 gse-one/audit_catalog.py --list          # list all jobs
    python3 gse-one/audit_catalog.py --show <id>     # show one job's details
    python3 gse-one/audit_catalog.py --validate      # check catalog validity
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

VALID_TYPES = {
    "file_quality",
    "intra_layer_group",
    "layer_pair",
    "horizontal_cluster",
    "qualitative_critique",
}

VALID_REFINEMENTS = {"none", "downward", "bidirectional"}

VALID_CATEGORIES = {"A", "B", "C", "D", "E"}

VALID_SEVERITIES = {"error", "warning", "info", "recommendation"}


# ---------------------------------------------------------------------------
# AuditJob dataclass
# ---------------------------------------------------------------------------


@dataclass
class AuditJob:
    id: str
    category: str
    type: str
    refinement: str
    files: list = field(default_factory=list)
    scope: str = ""
    checks: list = field(default_factory=list)

    def resolved_files(self, repo_root: Path) -> list:
        """Resolve globs in the files list to concrete Path objects."""
        resolved = []
        for entry in self.files:
            if "*" in entry:
                matches = sorted(repo_root.glob(entry))
                resolved.extend(matches)
            else:
                path = repo_root / entry
                resolved.append(path)
        return resolved

    def existing_files(self, repo_root: Path) -> list:
        """Return only the files that actually exist."""
        return [f for f in self.resolved_files(repo_root) if f.exists()]


# ---------------------------------------------------------------------------
# Loader + validator
# ---------------------------------------------------------------------------


class CatalogError(Exception):
    """Raised on invalid catalog schema or missing catalog."""


def _find_catalog_path(repo_root: Path) -> Path:
    """Return the standard catalog path for a gensem-like repo."""
    return repo_root / ".claude" / "audit-jobs.json"


def load_catalog(repo_root: Path, catalog_path: Optional[Path] = None) -> list:
    """Load and validate the catalog JSON.

    Args:
        repo_root: Repository root (where .claude/audit-jobs.json lives)
        catalog_path: Optional explicit override path

    Returns:
        List of AuditJob instances, validated.

    Raises:
        CatalogError: if the catalog is missing or invalid.
    """
    path = catalog_path or _find_catalog_path(repo_root)
    if not path.exists():
        raise CatalogError(f"Audit catalog not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CatalogError(f"Audit catalog is not valid JSON: {e}") from e

    if not isinstance(data, dict) or "jobs" not in data:
        raise CatalogError("Audit catalog must be a JSON object with a 'jobs' key")

    raw_jobs = data["jobs"]
    if not isinstance(raw_jobs, list):
        raise CatalogError("'jobs' must be a list")

    jobs = []
    seen_ids = set()
    for idx, raw in enumerate(raw_jobs):
        if not isinstance(raw, dict):
            raise CatalogError(f"Job at index {idx} is not an object")
        try:
            job = AuditJob(
                id=raw["id"],
                category=raw["category"],
                type=raw["type"],
                refinement=raw["refinement"],
                files=list(raw.get("files", [])),
                scope=raw.get("scope", ""),
                checks=list(raw.get("checks", [])),
            )
        except KeyError as e:
            raise CatalogError(
                f"Job at index {idx}: missing required field {e}"
            ) from e

        validate_job(job)

        if job.id in seen_ids:
            raise CatalogError(f"Duplicate job id: '{job.id}'")
        seen_ids.add(job.id)

        jobs.append(job)

    return jobs


def validate_job(job: AuditJob) -> None:
    """Validate a single job's schema. Raises CatalogError on failure."""
    if job.type not in VALID_TYPES:
        raise CatalogError(
            f"Job '{job.id}': invalid type '{job.type}'. "
            f"Expected one of: {sorted(VALID_TYPES)}"
        )
    if job.refinement not in VALID_REFINEMENTS:
        raise CatalogError(
            f"Job '{job.id}': invalid refinement '{job.refinement}'. "
            f"Expected one of: {sorted(VALID_REFINEMENTS)}"
        )
    if job.category not in VALID_CATEGORIES:
        raise CatalogError(
            f"Job '{job.id}': invalid category '{job.category}'. "
            f"Expected one of: {sorted(VALID_CATEGORIES)}"
        )

    # Semantic cross-checks
    if job.type == "file_quality" and len(job.files) != 1:
        raise CatalogError(
            f"Job '{job.id}': file_quality must have exactly 1 file "
            f"(got {len(job.files)})"
        )
    if job.type in ("file_quality", "intra_layer_group") and job.refinement != "none":
        raise CatalogError(
            f"Job '{job.id}': {job.type} must have refinement='none' "
            f"(got '{job.refinement}')"
        )
    if job.type == "qualitative_critique" and job.refinement != "bidirectional":
        raise CatalogError(
            f"Job '{job.id}': qualitative_critique must be bidirectional "
            f"(got '{job.refinement}')"
        )
    if not job.checks:
        raise CatalogError(f"Job '{job.id}': no checks defined")
    if not job.files:
        raise CatalogError(f"Job '{job.id}': no files defined")


# ---------------------------------------------------------------------------
# Cluster helpers (used by audit.py)
# ---------------------------------------------------------------------------


def find_job(jobs: list, job_id: str) -> Optional[AuditJob]:
    """Return the job with the given id, or None if not found."""
    for job in jobs:
        if job.id == job_id:
            return job
    return None


def files_in_cluster(job: AuditJob, repo_root: Path) -> set:
    """Return the set of existing file paths (as resolved strings) in a job."""
    return {str(f.resolve()) for f in job.existing_files(repo_root)}


def is_file_in_cluster(
    file_path: Path, job: AuditJob, repo_root: Path
) -> bool:
    """Check whether the given file is part of the job's file set."""
    return str(file_path.resolve()) in files_in_cluster(job, repo_root)


# ---------------------------------------------------------------------------
# CLI for inspection
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    """Compute the repo root (parent of gse-one/)."""
    return Path(__file__).resolve().parents[1]


def _cmd_list(jobs: list) -> None:
    by_category = {}
    for job in jobs:
        by_category.setdefault(job.category, []).append(job)

    for cat in sorted(by_category):
        print(f"\nCategory {cat}:")
        for job in by_category[cat]:
            file_count = len(job.files)
            print(
                f"  {job.id:40s} [{job.type:22s}] "
                f"refinement={job.refinement:15s} files={file_count}"
            )


def _cmd_show(jobs: list, job_id: str) -> int:
    job = find_job(jobs, job_id)
    if not job:
        print(f"error: job '{job_id}' not found", file=sys.stderr)
        return 1
    print(f"ID:          {job.id}")
    print(f"Category:    {job.category}")
    print(f"Type:        {job.type}")
    print(f"Refinement:  {job.refinement}")
    print(f"Scope:       {job.scope}")
    print(f"\nFiles ({len(job.files)}):")
    for f in job.files:
        print(f"  - {f}")
    print(f"\nChecks ({len(job.checks)}):")
    for i, c in enumerate(job.checks, 1):
        print(f"  {i}. {c}")
    return 0


def _cmd_validate(jobs: list, repo_root: Path) -> int:
    """Additional post-load validation: check that referenced files exist
    (or at least resolve to non-empty glob matches)."""
    print(f"Loaded {len(jobs)} jobs.")
    issues = 0
    for job in jobs:
        resolved = job.resolved_files(repo_root)
        existing = [f for f in resolved if f.exists()]
        missing = [f for f in resolved if not f.exists()]
        if not existing:
            print(
                f"  ✗ {job.id}: NO files exist "
                f"(all {len(resolved)} resolved paths missing)",
                file=sys.stderr,
            )
            issues += 1
        elif missing:
            rel_missing = [
                str(f.relative_to(repo_root)) if f.is_absolute() else str(f)
                for f in missing[:3]
            ]
            print(
                f"  ⚠ {job.id}: {len(missing)}/{len(resolved)} "
                f"path(s) missing, first: {', '.join(rel_missing)}"
            )
        else:
            print(f"  ✓ {job.id}: all {len(existing)} files exist")

    return 1 if issues else 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_catalog.py",
        description="Inspect and validate the audit catalog.",
    )
    parser.add_argument("--list", action="store_true", help="List all jobs")
    parser.add_argument("--show", metavar="JOB_ID", help="Show details of a job")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Check schema + verify referenced files exist",
    )
    args = parser.parse_args(argv)

    if not any([args.list, args.show, args.validate]):
        parser.print_help()
        return 0

    repo_root = _repo_root()
    try:
        jobs = load_catalog(repo_root)
    except CatalogError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.list:
        _cmd_list(jobs)
    if args.show:
        return _cmd_show(jobs, args.show)
    if args.validate:
        return _cmd_validate(jobs, repo_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
