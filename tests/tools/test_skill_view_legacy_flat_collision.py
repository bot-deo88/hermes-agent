"""Regression tests for skill_view legacy flat Markdown collisions.

Support files under references/templates/assets/scripts or archived skill trees are
not standalone skills. They must not collide with active SKILL.md files that share
the same basename. True duplicate SKILL.md candidates across active roots should
still be ambiguous.
"""

import json
from pathlib import Path


def _write_skill(root: Path, rel: str, name: str, body: str = "Body") -> None:
    skill_dir = root / rel
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {name}\n---\n\n{body}\n",
        encoding="utf-8",
    )


def _write_support(root: Path, rel: str, body: str = "reference") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _isolate_skill_roots(monkeypatch, local_root: Path, *external_roots: Path) -> None:
    monkeypatch.setattr("tools.skills_tool.SKILLS_DIR", local_root)
    monkeypatch.setattr(
        "agent.skill_utils.get_external_skills_dirs",
        lambda: [Path(p) for p in external_roots],
    )
    monkeypatch.setattr("tools.skills_tool._is_skill_disabled", lambda *args, **kwargs: False)


def test_references_markdown_does_not_shadow_active_skill(tmp_path, monkeypatch):
    from tools.skills_tool import skill_view

    local = tmp_path / "skills"
    _write_skill(local, "defi/morning-brief", "morning-brief", "Active morning brief")
    _write_support(
        local,
        "defi/daily-signal-operations/references/morning-brief.md",
        "Archived source reference, not a standalone skill",
    )
    _isolate_skill_roots(monkeypatch, local)

    result = json.loads(skill_view("morning-brief"))

    assert result["success"] is True
    assert result["name"] == "morning-brief"
    assert "Active morning brief" in result["content"]


def test_archive_markdown_does_not_shadow_active_skill(tmp_path, monkeypatch):
    from tools.skills_tool import skill_view

    local = tmp_path / "skills"
    _write_skill(local, "defi/skill-self-audit", "skill-self-audit", "Active audit skill")
    _write_support(
        local,
        ".archive/umbrella-2026-05-02/external-skill-scouting/skill/references/skill-self-audit.md",
        "Archived reference, not a standalone skill",
    )
    _isolate_skill_roots(monkeypatch, local)

    result = json.loads(skill_view("skill-self-audit"))

    assert result["success"] is True
    assert result["name"] == "skill-self-audit"
    assert "Active audit skill" in result["content"]


def test_templates_markdown_does_not_shadow_active_skill(tmp_path, monkeypatch):
    from tools.skills_tool import skill_view

    local = tmp_path / "skills"
    _write_skill(local, "productivity/airtable", "airtable", "Active airtable skill")
    _write_support(
        local,
        "creative/popular-web-designs/templates/airtable.md",
        "Template, not a standalone skill",
    )
    _isolate_skill_roots(monkeypatch, local)

    result = json.loads(skill_view("airtable"))

    assert result["success"] is True
    assert result["name"] == "airtable"
    assert "Active airtable skill" in result["content"]


def test_duplicate_active_skill_roots_still_report_ambiguity(tmp_path, monkeypatch):
    from tools.skills_tool import skill_view

    local = tmp_path / "local-skills"
    external = tmp_path / "global-skills"
    _write_skill(local, "github/github-pr-workflow", "github-pr-workflow", "Profile copy")
    _write_skill(external, "github/github-pr-workflow", "github-pr-workflow", "Global copy")
    _isolate_skill_roots(monkeypatch, local, external)

    result = json.loads(skill_view("github-pr-workflow"))

    assert result["success"] is False
    assert "Ambiguous skill name 'github-pr-workflow'" in result["error"]
    assert len(result["matches"]) == 2
