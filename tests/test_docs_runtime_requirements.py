"""Docs/runtime consistency tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_launch_docs_match_pyproject_python_floor() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    reddit = (REPO_ROOT / "docs" / "REDDIT_LAUNCH.md").read_text()
    forum = (REPO_ROOT / "docs" / "FORUM_POST.md").read_text()

    assert 'requires-python = ">=3.10"' in pyproject
    assert "Python 3.10+" in reddit
    assert "Python 3.10+" in forum


def test_launch_docs_do_not_claim_legacy_python_floor() -> None:
    reddit = (REPO_ROOT / "docs" / "REDDIT_LAUNCH.md").read_text()
    forum = (REPO_ROOT / "docs" / "FORUM_POST.md").read_text()

    for doc in (reddit, forum):
        assert "Python 3.8+" not in doc
        assert "Python 3.9+" not in doc


def test_runtime_guards_exist_for_python_floor() -> None:
    main_py = (REPO_ROOT / "src" / "main.py").read_text()
    conftest = (REPO_ROOT / "tests" / "conftest.py").read_text()
    run_sh = (REPO_ROOT / "run.sh").read_text()
    install_sh = (REPO_ROOT / "install.sh").read_text()

    assert "sys.version_info < (3, 10)" in main_py
    assert "Python 3.10+" in main_py
    assert "sys.version_info < (3, 10)" in conftest
    assert "tests require Python 3.10+" in conftest
    assert "Python 3.10+" in run_sh
    assert "sys.version_info >= (3, 10)" in run_sh
    assert "Python 3.10 or higher is required" in install_sh
