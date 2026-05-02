"""Regression tests for the no-mutation Curator auto-run guard.

The real guard belongs in agent.curator.maybe_run_curator(); CLI and gateway
startup hooks must keep delegating through that guarded entrypoint instead of
calling mutation paths directly.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _startup_block(path: Path, needle: str) -> str:
    source = path.read_text(encoding="utf-8")
    idx = source.index(needle)
    return source[max(0, idx - 500): idx + 700]


def test_cli_startup_delegates_to_guarded_maybe_run_curator():
    block = _startup_block(ROOT / "cli.py", "from agent.curator import maybe_run_curator")

    assert "HERMES_DISABLE_AUTO_CURATOR" in block
    assert "maybe_run_curator(" in block
    assert "run_curator_review" not in block
    assert "apply_automatic_transitions" not in block


def test_gateway_ticker_delegates_to_guarded_maybe_run_curator():
    block = _startup_block(ROOT / "gateway" / "run.py", "from agent.curator import maybe_run_curator")

    assert "HERMES_DISABLE_AUTO_CURATOR" in block
    assert "maybe_run_curator(" in block
    assert "run_curator_review" not in block
    assert "apply_automatic_transitions" not in block
