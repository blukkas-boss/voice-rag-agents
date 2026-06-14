"""Unit tests for document_loader — no external services required."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from voice_rag_agents.dataflows.document_loader import load_documents


@pytest.fixture(autouse=True)
def _override_input_dir(monkeypatch):
    """Patch VOICE_RAG_INPUT_DIR to point at the per-test tmp_path.

    Each test sets tmp_path via a second autouse fixture below.
    """
    # This will be overridden per-test by _set_input_dir
    monkeypatch.setenv("VOICE_RAG_INPUT_DIR", str(Path("/tmp/nonexistent_vrag_test")))
    from voice_rag_agents.config import settings

    settings.get_settings.cache_clear()
    yield
    monkeypatch.delenv("VOICE_RAG_INPUT_DIR", raising=False)
    settings.get_settings.cache_clear()


def _setup_input(monkeypatch, tmp_path: Path) -> Path:
    """Redirect the allowed input dir to tmp_path and clear settings cache."""
    monkeypatch.setenv("VOICE_RAG_INPUT_DIR", str(tmp_path))
    from voice_rag_agents.config import settings

    settings.get_settings.cache_clear()
    return tmp_path


def test_load_txt(tmp_path: Path, monkeypatch) -> None:
    d = _setup_input(monkeypatch, tmp_path)
    f = d / "hello.txt"
    f.write_text("Hello world")
    docs = load_documents(str(f))
    assert len(docs) == 1
    assert docs[0]["page_content"] == "Hello world"
    assert docs[0]["metadata"]["source_type"] == "txt"


def test_load_md(tmp_path: Path, monkeypatch) -> None:
    d = _setup_input(monkeypatch, tmp_path)
    f = d / "notes.md"
    f.write_text("# Title\n\nSome content")
    docs = load_documents(str(f))
    assert len(docs) == 1
    assert "# Title" in docs[0]["page_content"]


def test_load_json(tmp_path: Path, monkeypatch) -> None:
    d = _setup_input(monkeypatch, tmp_path)
    f = d / "data.json"
    f.write_text(json.dumps({"key": "value"}))
    docs = load_documents(str(f))
    assert len(docs) == 1
    assert "key" in docs[0]["page_content"]


def test_load_csv(tmp_path: Path, monkeypatch) -> None:
    d = _setup_input(monkeypatch, tmp_path)
    f = d / "data.csv"
    f.write_text("a,b,c\n1,2,3\n")
    docs = load_documents(str(f))
    assert len(docs) == 1
    assert "a, b, c" in docs[0]["page_content"]


def test_load_directory(tmp_path: Path, monkeypatch) -> None:
    d = _setup_input(monkeypatch, tmp_path)
    (d / "a.txt").write_text("AAA")
    (d / "b.txt").write_text("BBB")
    docs = load_documents(str(d))
    assert len(docs) == 2


def test_path_traversal_rejected(tmp_path: Path, monkeypatch) -> None:
    _setup_input(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="outside allowed"):
        load_documents("/etc/passwd")


def test_nonexistent_path(tmp_path: Path, monkeypatch) -> None:
    d = _setup_input(monkeypatch, tmp_path)
    with pytest.raises(FileNotFoundError):
        load_documents(str(d / "missing.txt"))