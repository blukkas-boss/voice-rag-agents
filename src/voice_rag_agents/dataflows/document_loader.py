"""Document loader — read files from disk into DocumentRecord dicts.

Supports: .txt, .md, .json, .csv, .pdf (optional).
Filters by allowed extensions and guards against path traversal.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from voice_rag_agents.config.settings import get_settings


# Configuration
_EXTENSIONS = {".txt", ".md", ".json", ".csv"}
_PDF_AVAILABLE = False
try:
    import pypdf  # noqa: F401

    _PDF_AVAILABLE = True
    _EXTENSIONS = _EXTENSIONS | {".pdf"}
except ImportError:
    pass


def _resolve_safe(path: str, allowed_root: str) -> Path:
    """Resolve *path* and ensure it stays within *allowed_root*.

    Raises ValueError on path traversal.
    """
    root = Path(allowed_root).resolve()
    target = Path(path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError(
            f"Path '{target}' is outside allowed directory '{root}'"
        )
    return target


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2, ensure_ascii=False)


def _load_csv(path: Path) -> str:
    rows: list[list[str]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        for row in reader:
            rows.append(row)
    return "\n".join(", ".join(row) for row in rows)


def _load_pdf(path: Path) -> str:
    if not _PDF_AVAILABLE:
        raise ImportError(
            "pypdf is required for PDF support. Install with: pip install pypdf"
        )
    import pypdf

    parts: list[str] = []
    with path.open("rb") as fh:
        reader = pypdf.PdfReader(fh)
        for page in reader.pages:
            text = page.extract_text() or ""
            parts.append(text)
    return "\n\n".join(parts)


_LOADERS = {
    ".txt": _load_text,
    ".md": _load_text,
    ".json": _load_json,
    ".csv": _load_csv,
    ".pdf": _load_pdf,
}


def load_documents(path: str) -> list[dict]:
    """Load documents from a file or directory.

    Each returned dict has keys: ``page_content`` (str), ``metadata`` (dict).
    ``metadata`` always includes ``source_file`` and ``source_type``.
    """
    settings = get_settings()
    allowed_root = settings.input_dir
    ext_filter = _EXTENSIONS

    target = _resolve_safe(path, allowed_root)

    files: list[Path] = []
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(
            p
            for p in target.rglob("*")
            if p.is_file() and p.suffix.lower() in ext_filter
        )
    else:
        raise FileNotFoundError(f"Path not found: {target}")

    documents: list[dict] = []
    for fpath in files:
        ext = fpath.suffix.lower()
        loader = _LOADERS.get(ext)
        if loader is None:
            continue
        try:
            text = loader(fpath)
        except Exception as exc:  # noqa: BLE001 — skip unreadable files
            documents.append(
                {
                    "page_content": "",
                    "metadata": {
                        "source_file": str(fpath),
                        "source_type": ext.lstrip("."),
                        "error": str(exc),
                    },
                }
            )
            continue

        documents.append(
            {
                "page_content": text,
                "metadata": {
                    "source_file": str(fpath),
                    "source_type": ext.lstrip("."),
                    "file_size_bytes": fpath.stat().st_size,
                },
            }
        )

    return documents
