import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tools" / "check_keywords.py"


def run_guard(lists, root):
    return subprocess.run(
        [sys.executable, str(GUARD), str(lists), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def lists(tmp_path):
    directory = tmp_path / "lists"
    directory.mkdir()
    for filename, term in (
        ("private-paths.txt", "/synthetic/private/path"),
        ("proprietary-strategies.txt", "QT" + "5m"),
        ("vendor.txt", "synthetic_vendor_marker"),
    ):
        (directory / filename).write_text(term + "\n")
    return directory


@pytest.mark.parametrize(
    "path,content",
    [
        ("src/package/nested/strategy.py", "QT" + "5m = 'strategy specific'"),
        ("tests/nested/test_sample.py", "synthetic_vendor_marker"),
        ("tools/nested/sample.py", "/synthetic/private/path"),
        (".github/workflows/ci.yml", "synthetic_vendor_marker"),
        ("pyproject.toml", "synthetic_vendor_marker"),
        ("README.md", "/synthetic/private/path"),
    ],
)
def test_public_text_rejects_keyword(lists, tmp_path, path, content):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\n")
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    result = run_guard(lists, root)
    assert result.returncode != 0
    assert "keyword match" in result.stderr
    assert path in result.stderr


def test_clean_tree_passes(lists, tmp_path):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\n")
    (root / "README.md").write_text("public text")
    assert run_guard(lists, root).returncode == 0


def test_missing_list_fails(lists, tmp_path):
    (lists / "vendor.txt").unlink()
    (tmp_path / "src").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    result = run_guard(lists, tmp_path)
    assert result.returncode != 0
    assert "keyword list unavailable" in result.stderr


def test_missing_root_fails(lists, tmp_path):
    result = run_guard(lists, tmp_path / "missing")
    assert result.returncode != 0
    assert "scan root" in result.stderr


def test_empty_list_fails(lists, tmp_path):
    (lists / "vendor.txt").write_text("# empty\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    result = run_guard(lists, tmp_path)
    assert result.returncode != 0
    assert "keyword list empty" in result.stderr


def test_wrong_root_fails(lists, tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    result = run_guard(lists, root)
    assert result.returncode != 0
    assert "scan root" in result.stderr


def test_current_repository_has_no_public_keywords():
    lists = ROOT / ".boundary-docs" / "keywords"
    if not lists.exists():
        pytest.skip("docs-public checkout is supplied by CI")
    result = run_guard(lists, ROOT)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("path", ["src/QT" + "5m.py", "src/synthetic_vendor_marker/module.py"])
def test_public_path_rejects_keyword(lists, tmp_path, path):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\n")
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("pass\n")
    result = run_guard(lists, root)
    assert result.returncode != 0
    assert "keyword match" in result.stderr
