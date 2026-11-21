"""Run synthetic-only regression cases and write a JSON report."""

from __future__ import annotations

import json

from evals.runner import write_artifacts


def main() -> int:
    report = write_artifacts()
    print(json.dumps(report["summary"], sort_keys=True))
    for case in report["cases"]:
        print(f"{case['status'].upper():6} {case['id']}: {case['detail']}")
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
