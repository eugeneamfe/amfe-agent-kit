"""Developer-only check: relocated bundle, relative links, metadata, attribution.
Run from repository root: uv run --with PyYAML python docs/validation/threads-workflow-v1/check_package.py
Not a skill runtime dependency or a behavioral test.
"""
from pathlib import Path
import re
import shutil
import tempfile
import yaml

repo = Path(__file__).resolve().parents[3]
source = repo / "skills" / "threads-workflow"
with tempfile.TemporaryDirectory(prefix="threads-portable-") as workspace:
    installed = Path(workspace) / ".agents" / "skills" / "threads-workflow"
    assert not any(p.is_symlink() for p in source.rglob("*")), "bundle contains symlink"
    shutil.copytree(source, installed)
    installed = installed.resolve()
    assert (installed / "LICENSE").read_bytes() == (repo / "LICENSE").read_bytes()
    links = 0
    for file in installed.rglob("*.md"):
        text = file.read_text()
        assert not re.search(r"/Users/|/home/|t\.me/|threads\.com/@|TODO|TBD", text), file
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target:
                continue
            rel = target.split("#", 1)[0]
            if not rel:
                continue
            resolved = (file.parent / rel).resolve()
            assert resolved.is_relative_to(installed), (file, "escapes bundle", target)
            assert resolved.is_file(), (file, "broken link", target)
            links += 1
    entry = (installed / "SKILL.md").read_text()
    metadata = yaml.safe_load(entry.split("---", 2)[1])
    assert metadata["name"] == installed.name
    assert metadata["description"]
    assert "https://github.com/eugeneamfe/amfe-agent-kit" in entry
    ui = yaml.safe_load((installed / "agents" / "openai.yaml").read_text())
    assert 25 <= len(ui["interface"]["short_description"]) <= 64
    assert "$threads-workflow" in ui["interface"]["default_prompt"]
    assert ui["policy"]["allow_implicit_invocation"] is True
    assert not ui.get("dependencies"), "base mode must not require tools"
    profile = (installed / "assets" / "threads-profile.template.md").read_text()
    assert "example.com" not in profile and "UTC+" not in profile
    print(f"PASS: relocated bundle; {links} relative links; YAML; license; privacy markers")
