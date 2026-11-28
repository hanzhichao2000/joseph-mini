import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tools" / "check_keywords.py"
MARKER = "synthetic-internal-marker"


def run_guard(keywords, root):
    return subprocess.run(
        [sys.executable, str(GUARD), str(keywords), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def keywords(tmp_path):
    path = tmp_path / "keywords.txt"
    path.write_text(MARKER + "\n")
    return path


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    return root


def track(root, path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    subprocess.run(["git", "-C", root, "add", "--", path], check=True)


@pytest.mark.parametrize(
    "path",
    [
        "src/package/nested/example.py",
        "tests/test_fixture.py",
        "tools/nested/sample.py",
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "README.md",
    ],
)
def test_public_text_rejects_keyword(keywords, repo, path):
    track(repo, path, MARKER.upper())
    result = run_guard(keywords, repo)
    assert result.returncode == 1
    assert "(0 path, 1 text matches)" in result.stderr
    assert MARKER not in result.stderr.casefold()


def test_clean_tree_passes(keywords, repo):
    track(repo, "README.md", "public text")
    assert run_guard(keywords, repo).returncode == 0


@pytest.mark.parametrize("invalid", [None, "", "# comment\n  \n"])
def test_list_is_required_and_nonempty(keywords, repo, invalid):
    if invalid is None:
        keywords.unlink()
    else:
        keywords.write_text(invalid)
    result = run_guard(keywords, repo)
    assert result.returncode == 2
    assert "list missing, unreadable, or empty" in result.stderr


@pytest.mark.parametrize("kind", ["missing", "not-a-repository"])
def test_invalid_root_fails(keywords, tmp_path, kind):
    root = tmp_path / kind
    if kind == "not-a-repository":
        root.mkdir()
    result = run_guard(keywords, root)
    assert result.returncode == 2
    assert "target Git working tree" in result.stderr


def test_current_repository_has_no_public_keywords():
    result = run_guard(ROOT / "keywords/public-boundary.txt", ROOT)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("path", [f"src/{MARKER}.py", f"src/{MARKER}/module.py"])
def test_public_path_rejects_keyword(keywords, repo, path):
    track(repo, path, "pass\n")
    result = run_guard(keywords, repo)
    assert result.returncode == 1
    assert "(1 path, 0 text matches)" in result.stderr
    assert MARKER not in result.stderr
