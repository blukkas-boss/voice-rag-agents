"""CLI entry point — ingest / query / serve / version.

Subcommands run the same graphs the API uses, so the CLI and API share one
implementation. Mock profile is default; no external services required.
"""
from __future__ import annotations

import argparse
import json

from . import __version__


def _cmd_ingest(args: argparse.Namespace) -> int:
    from voice_rag_agents.dataflows.document_loader import load_documents
    from voice_rag_agents.graph.ingestion_graph import run_ingestion_graph

    docs = load_documents(args.path)
    state = {
        "run_id": "cli-ingest",
        "request_type": "ingest",
        "user_id": "cli",
        "session_id": "cli",
        "runtime_profile": "mock",
        "input_documents": [
            {"text": d["page_content"], **d.get("metadata", {})} for d in docs
        ],
    }
    result = run_ingestion_graph(state)
    report = result.get("ingestion_report", {})
    print(json.dumps(report, indent=2))
    return 0 if report.get("status") == "success" else 1


def _cmd_query(args: argparse.Namespace) -> int:
    from voice_rag_agents.graph.query_graph import run_query_graph

    state = {
        "run_id": "cli-query",
        "request_type": "query",
        "user_id": "cli",
        "session_id": "cli",
        "runtime_profile": "mock",
        "input_text": args.question,
    }
    result = run_query_graph(state)
    print(result.get("answer", "(no answer)"))
    citations = result.get("citations", [])
    if citations:
        print("\nSources:")
        for c in citations:
            label = c.get("label", "?") if isinstance(c, dict) else getattr(c, "label", "?")
            src = c.get("source_file", "") if isinstance(c, dict) else getattr(c, "source_file", "")
            print(f"  [{label}] {src}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "voice_rag_agents.service.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voice-rag", description="Voice RAG agents CLI")
    parser.add_argument("-v", "--version", action="store_true", help="Print version")
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="Ingest documents from a file or directory")
    p_ingest.add_argument("path", help="File or directory path (within allowed input dir)")
    p_ingest.set_defaults(func=_cmd_ingest)

    p_query = sub.add_parser("query", help="Ask a question against ingested documents")
    p_query.add_argument("question", help="The question to answer")
    p_query.set_defaults(func=_cmd_query)

    p_serve = sub.add_parser("serve", help="Run the FastAPI service")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8088)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=_cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"voice-rag {__version__}")
        return 0

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
