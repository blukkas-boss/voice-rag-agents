"""UT-001 / VRAG-A001: package import + CLI smoke test (no external services)."""
import pytest

pytestmark = pytest.mark.unit


def test_package_imports():
    import voice_rag_agents

    assert isinstance(voice_rag_agents.__version__, str)
    assert voice_rag_agents.__version__


def test_cli_version_smoke(capsys):
    from voice_rag_agents.cli import main

    rc = main(["--version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "voice-rag" in out
