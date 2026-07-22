#!/usr/bin/env python3
"""Delete Snyk targets listed in a branch-mismatch diff.json.

Matches targets by org name (``apm_code``) and ``repository_name`` (target
``display_name``) only — not by branch on the Targets API (often absent on
single-tenant). Writes an optional delete manifest for the reimport step.

Example::

    export SNYK_TOKEN='...'
    export SNYK_GROUP_ID='...'
    PYTHONPATH=src python scripts/delete_mismatched_targets.py \\
        --input diff.json \\
        --manifest delete-manifest.json \\
        --dry-run \\
        --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from common.output_state import assert_safe_filesystem_path, atomic_write_json  # noqa: E402
from config import load_dotenv_file  # noqa: E402
from config.snyk_settings import load_snyk_settings  # noqa: E402
from integrations.snyk.client import SnykRestClient  # noqa: E402
from snyk.branch_mismatch_delete import (  # noqa: E402
    BranchMismatchDeleteOptions,
    run_branch_mismatch_delete,
)
from snyk.branch_mismatch_reimport import load_diff_entries  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Delete Snyk targets from diff.json (match by repository display name). "
            "Optionally write a delete manifest for generate_branch_reimport_targets.py."
        ),
    )
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        metavar="PATH",
        help="diff.json file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("branch-delete-report.json"),
        metavar="PATH",
        help="Delete report JSON.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write reimport manifest JSON after successful deletes.",
    )
    parser.add_argument(
        "--discovery",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Stage 1 discovery.json for projectKey/repoSlug when target GET omits them "
            "(common on single-tenant)."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, metavar="N")
    parser.add_argument("--delay-ms", type=int, default=0, metavar="MS")
    return parser


def _report_has_failures(report: dict[str, object]) -> bool:
    failed = report.get("failed")
    return isinstance(failed, list) and bool(failed)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    load_dotenv_file(args.env_file)

    try:
        settings = load_snyk_settings()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        assert_safe_filesystem_path(args.input)
        assert_safe_filesystem_path(args.output)
        if args.manifest is not None:
            assert_safe_filesystem_path(args.manifest)
        if args.discovery is not None:
            assert_safe_filesystem_path(args.discovery)
        entries = load_diff_entries(args.input)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    options = BranchMismatchDeleteOptions(
        dry_run=args.dry_run,
        limit=args.limit,
        delay_ms=args.delay_ms,
        manifest_path=args.manifest,
        discovery_path=args.discovery,
    )

    client = SnykRestClient(settings)
    try:
        report = run_branch_mismatch_delete(client, entries, options)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(report, indent=2))
    else:
        atomic_write_json(args.output, report)
        print(f"Wrote report to {args.output}")
        if args.manifest and report.get("manifest_entries"):
            print(f"Wrote manifest to {args.manifest}")

    if _report_has_failures(report):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
