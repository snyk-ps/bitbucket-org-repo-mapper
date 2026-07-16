#!/usr/bin/env python3
"""Generate snyk-api-import batch JSON from a branch-mismatch delete manifest.

Run after ``delete_mismatched_targets.py`` (with ``--manifest``), then invoke::

    snyk-api-import import --file=branch-reimport-batch-001.json

Example::

    PYTHONPATH=src python scripts/generate_branch_reimport_targets.py \\
        --manifest delete-manifest.json \\
        --output-dir .
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

from common.output_state import assert_safe_filesystem_path  # noqa: E402
from snyk.branch_mismatch_import_targets import (  # noqa: E402
    BranchMismatchImportTargetsOptions,
    run_branch_mismatch_import_targets,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build snyk-api-import target batch files from a delete manifest.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        metavar="PATH",
        help="Delete manifest JSON from delete_mismatched_targets.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        metavar="PATH",
        help="Directory for branch-reimport-batch-*.json files.",
    )
    parser.add_argument(
        "--repos-per-batch",
        type=int,
        default=50,
        metavar="N",
        help="Targets per batch file (default: 50).",
    )
    parser.add_argument(
        "--output-stem",
        default="branch-reimport-batch",
        metavar="NAME",
        help="Batch file stem (default: branch-reimport-batch).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        assert_safe_filesystem_path(args.manifest)
        assert_safe_filesystem_path(args.output_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    options = BranchMismatchImportTargetsOptions(
        repos_per_batch=args.repos_per_batch,
        output_dir=args.output_dir,
        output_stem=args.output_stem,
    )

    try:
        report = run_branch_mismatch_import_targets(args.manifest, options)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
