"""Minimal CLI entry point (scaffold).

Real subcommands (ingest, query, admin, eval) are wired by the API/Service and
LangGraph build agents in later waves. For now this proves the console script
installs and runs.
"""
from __future__ import annotations

import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {"-v", "--version", "version"}:
        print(f"voice-rag {__version__}")
        return 0
    print(
        "voice-rag scaffold. Subcommands (ingest/query/admin/eval) are not "
        "implemented yet. See docs/build_plan.md."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
