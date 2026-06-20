#!/usr/bin/env python3
"""
truth-baseline.py — Validate documented claims against repository reality.

Usage:
    python scripts/truth-baseline.py [config.toml]

If config path is omitted, reads truth-baseline.toml from repo root.
Outputs truth-baseline.json and exits non-zero on mismatch.

Python 3.11+ required (uses tomllib).
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path.cwd()


# ── Data structures ─────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    name: str
    check_type: str
    status: str  # "PASS" | "FAIL" | "SKIP" | "ERROR"
    expected: Any = None
    actual: Any = None
    claim_source: str = ""
    message: str = ""


@dataclass
class BaselineReport:
    project: str
    timestamp: str
    summary: dict[str, int] = field(default_factory=dict)
    checks: list[dict[str, Any]] = field(default_factory=list)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: str) -> str:
    p = REPO_ROOT / path
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def _run(cmd: str, cwd: str | None = None, timeout: int = 60) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd or str(REPO_ROOT),
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return -1, "", str(e)


def _json_extract(data: Any, path: str) -> Any:
    parts = path.split(".")
    for part in parts:
        if isinstance(data, dict):
            data = data.get(part)
        elif isinstance(data, list) and part.isdigit():
            idx = int(part)
            data = data[idx] if 0 <= idx < len(data) else None
        else:
            return None
        if data is None:
            return None
    return data


# ── Check implementations ─────────────────────────────────────────────────

def check_count(cfg: dict[str, Any]) -> CheckResult:
    """Count files matching glob(s), compare against expected."""
    name = cfg["name"]
    globs = cfg["glob"] if isinstance(cfg["glob"], list) else [cfg["glob"]]
    expected = cfg.get("expected")
    op = cfg.get("op", "==")

    files = set()
    for g in globs:
        files.update(glob.glob(g, root_dir=REPO_ROOT, recursive=True))
    actual = len(files)

    # Coerce expected to int when actual is int (TOML strings vs Python ints)
    if isinstance(actual, int) and isinstance(expected, str):
        try:
            expected = int(expected)
        except ValueError:
            pass

    passed = True
    if expected is not None:
        if op == "==":
            passed = actual == expected
        elif op == ">=":
            passed = actual >= expected
        elif op == "<=":
            passed = actual <= expected
        elif op == ">":
            passed = actual > expected
        elif op == "<":
            passed = actual < expected
        elif op == "!=":
            passed = actual != expected

    msg = f"Found {actual} files matching {globs}"
    if expected is not None:
        msg += f"; expected {op} {expected}"

    return CheckResult(
        name=name,
        check_type="count",
        status="PASS" if passed else "FAIL",
        expected=expected,
        actual=actual,
        claim_source=cfg.get("claim_source", ""),
        message=msg,
    )


def check_version_consistency(cfg: dict[str, Any]) -> CheckResult:
    """Extract version from multiple sources; fail if divergent."""
    name = cfg["name"]
    sources = cfg["sources"]
    versions: dict[str, str] = {}
    errors: list[str] = []

    for src in sources:
        path = src["file"]
        text = _read_text(path)
        if not text:
            errors.append(f"{path}: file not found or empty")
            continue

        pattern = src.get("pattern", r'(\d+\.\d+(?:\.\d+)?)')
        m = re.search(pattern, text)
        if m:
            versions[path] = m.group(1)
        else:
            errors.append(f"{path}: no version matched with {pattern}")

    if errors:
        return CheckResult(
            name=name,
            check_type="version_consistency",
            status="ERROR" if not versions else "FAIL",
            expected="same version across all sources",
            actual=versions,
            claim_source=cfg.get("claim_source", ""),
            message="; ".join(errors),
        )

    unique = set(versions.values())
    passed = len(unique) == 1
    msg = f"Versions: {versions}"
    if not passed:
        msg = f"Version mismatch: {unique} — {versions}"

    return CheckResult(
        name=name,
        check_type="version_consistency",
        status="PASS" if passed else "FAIL",
        expected=list(unique)[0] if passed else "consistent",
        actual=versions,
        claim_source=cfg.get("claim_source", ""),
        message=msg,
    )


def check_test_count(cfg: dict[str, Any]) -> CheckResult:
    """Run test collection command, parse count."""
    name = cfg["name"]
    cmd = cfg.get("command", "python -m pytest --collect-only -q")
    pattern = cfg.get("pattern", r'(\d+) tests? collected')
    expected = cfg.get("expected")
    op = cfg.get("op", "==")
    cwd = cfg.get("cwd")

    rc, stdout, stderr = _run(cmd, cwd=cwd)
    combined = stdout + stderr
    m = re.search(pattern, combined)
    actual = int(m.group(1)) if m else 0

    # Coerce expected to int when actual is int (TOML strings vs Python ints)
    if isinstance(actual, int) and isinstance(expected, str):
        try:
            expected = int(expected)
        except ValueError:
            pass

    passed = False
    if expected is None:
        passed = True
    elif op == "==":
        passed = actual == expected
    elif op == ">=":
        passed = actual >= expected
    elif op == "<=":
        passed = actual <= expected

    msg = f"Collected {actual} tests"
    if expected is not None:
        msg += f"; expected {op} {expected}"
    if rc != 0 and actual == 0:
        msg += f" (command failed: {stderr[:200]})"

    return CheckResult(
        name=name,
        check_type="test_count",
        status="PASS" if passed else "FAIL",
        expected=expected,
        actual=actual,
        claim_source=cfg.get("claim_source", ""),
        message=msg,
    )


def check_file_exists(cfg: dict[str, Any]) -> CheckResult:
    """Check files or directories exist (or should not exist)."""
    name = cfg["name"]
    paths = cfg["paths"] if isinstance(cfg["paths"], list) else [cfg["paths"]]
    should_exist = cfg.get("should_exist", True)
    missing: list[str] = []
    unexpected: list[str] = []

    for p in paths:
        exists = (REPO_ROOT / p).exists()
        if should_exist and not exists:
            missing.append(p)
        elif not should_exist and exists:
            unexpected.append(p)

    passed = not missing and not unexpected
    parts: list[str] = []
    if missing:
        parts.append(f"missing: {missing}")
    if unexpected:
        parts.append(f"unexpected: {unexpected}")

    return CheckResult(
        name=name,
        check_type="file_exists",
        status="PASS" if passed else "FAIL",
        expected=paths if should_exist else [],
        actual={"missing": missing, "unexpected": unexpected},
        claim_source=cfg.get("claim_source", ""),
        message="; ".join(parts) if parts else "All paths match expectation",
    )


def check_regex_match(cfg: dict[str, Any]) -> CheckResult:
    """Extract value via regex from file, compare against expected."""
    name = cfg["name"]
    path = cfg["file"]
    pattern = cfg["pattern"]
    expected = cfg.get("expected")
    op = cfg.get("op", "==")
    group = cfg.get("group", 1)

    text = _read_text(path)
    m = re.search(pattern, text)
    actual = None
    if m:
        try:
            actual = m.group(group)
        except IndexError:
            actual = m.group(0)

    passed = False
    if expected is None:
        passed = m is not None
    elif op == "==":
        passed = str(actual) == str(expected) or (actual is None and expected == "")
    elif op == "!=":
        passed = str(actual) != str(expected)
    elif op in (">=", "<=", ">", "<") and actual is not None:
        passed = eval(f"{actual} {op} {expected}")

    msg = f"Extracted '{actual}' from {path}"
    if expected is not None:
        msg += f"; expected {op} '{expected}'"

    return CheckResult(
        name=name,
        check_type="regex_match",
        status="PASS" if passed else "FAIL",
        expected=expected,
        actual=actual,
        claim_source=cfg.get("claim_source", ""),
        message=msg,
    )


def check_command_output(cfg: dict[str, Any]) -> CheckResult:
    """Run command, parse output with regex."""
    name = cfg["name"]
    cmd = cfg["command"]
    pattern = cfg.get("pattern")
    expected = cfg.get("expected")
    op = cfg.get("op", "==")
    cwd = cfg.get("cwd")
    timeout = cfg.get("timeout", 60)

    rc, stdout, stderr = _run(cmd, cwd=cwd, timeout=timeout)
    combined = stdout + stderr
    actual = None
    if pattern:
        m = re.search(pattern, combined)
        actual = m.group(1) if m else None
    else:
        actual = combined.strip()

    passed = False
    if expected is None:
        passed = rc == 0
    elif op == "==":
        passed = str(actual) == str(expected)
    elif op == "!=":
        passed = str(actual) != str(expected)
    elif actual is not None:
        try:
            passed = eval(f"{actual} {op} {expected}")
        except Exception:
            passed = False

    msg = f"Command returned {rc}; output: '{str(actual)[:200]}'"
    if expected is not None:
        msg += f"; expected {op} '{expected}'"

    return CheckResult(
        name=name,
        check_type="command_output",
        status="PASS" if passed else "FAIL",
        expected=expected,
        actual=actual,
        claim_source=cfg.get("claim_source", ""),
        message=msg,
    )


def check_json_path(cfg: dict[str, Any]) -> CheckResult:
    """Extract value from JSON file via dotted path."""
    name = cfg["name"]
    path = cfg["file"]
    jpath = cfg["path"]
    expected = cfg.get("expected")
    op = cfg.get("op", "==")

    text = _read_text(path)
    if not text:
        return CheckResult(
            name=name,
            check_type="json_path",
            status="ERROR",
            expected=expected,
            actual=None,
            message=f"JSON file not found: {path}",
        )

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return CheckResult(
            name=name,
            check_type="json_path",
            status="ERROR",
            expected=expected,
            actual=None,
            message=f"Invalid JSON in {path}: {e}",
        )

    actual = _json_extract(data, jpath)
    passed = False
    if expected is None:
        passed = actual is not None
    elif op == "==":
        passed = actual == expected
    elif op == "!=":
        passed = actual != expected
    elif actual is not None:
        try:
            passed = eval(f"{actual} {op} {expected}")
        except Exception:
            passed = False

    return CheckResult(
        name=name,
        check_type="json_path",
        status="PASS" if passed else "FAIL",
        expected=expected,
        actual=actual,
        claim_source=cfg.get("claim_source", ""),
        message=f"{path}@{jpath} = {actual}; expected {op} {expected}",
    )


def check_package_unused(cfg: dict[str, Any]) -> CheckResult:
    """Check if a declared dependency is actually imported in source code."""
    name = cfg["name"]
    package = cfg["package"]
    import_name = cfg.get("import_name", package)
    source_globs = cfg.get("source_globs", ["src/**/*.py", "src/**/*.ts", "src/**/*.tsx"])
    expected_unused = cfg.get("expected_unused", True)

    files = set()
    for g in source_globs:
        files.update(glob.glob(g, root_dir=REPO_ROOT, recursive=True))

    imported = False
    for f in sorted(files):
        text = _read_text(f)
        if re.search(rf'\b(import\s+{re.escape(import_name)}|from\s+{re.escape(import_name)}|require\(["\']{re.escape(import_name)}["\']\))', text):
            imported = True
            break

    passed = imported != expected_unused  # if expected_unused=True, passed when imported==False
    msg = f"Package '{package}' imported: {imported}"
    if expected_unused:
        msg += "; expected UNUSED"
    else:
        msg += "; expected USED"

    return CheckResult(
        name=name,
        check_type="package_unused",
        status="PASS" if passed else "FAIL",
        expected=not expected_unused,
        actual=imported,
        claim_source=cfg.get("claim_source", ""),
        message=msg,
    )


def check_markdown_claim(cfg: dict[str, Any]) -> CheckResult:
    """Extract claim from markdown by header text."""
    name = cfg["name"]
    path = cfg["file"]
    header = cfg.get("header")
    pattern = cfg.get("pattern")
    expected = cfg.get("expected")
    op = cfg.get("op", "==")

    text = _read_text(path)
    if not text:
        return CheckResult(
            name=name,
            check_type="markdown_claim",
            status="ERROR",
            expected=expected,
            actual=None,
            message=f"File not found: {path}",
        )

    actual = None
    if header:
        # Find text under a specific markdown header
        escaped = re.escape(header.lstrip("# ").strip())
        # Match header line, then capture until next header
        m = re.search(
            rf'^#+\s*{escaped}\s*\n(.*?)(?=\n#+\s|\Z)',
            text,
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        if m:
            section = m.group(1)
            if pattern:
                mm = re.search(pattern, section)
                actual = mm.group(1) if mm else None
            else:
                actual = section.strip()
        else:
            actual = None
    elif pattern:
        mm = re.search(pattern, text)
        actual = mm.group(1) if mm else None

    passed = False
    if expected is None:
        passed = actual is not None
    elif op == "==":
        passed = str(actual) == str(expected)
    elif op == "!=":
        passed = str(actual) != str(expected)
    elif actual is not None:
        try:
            passed = eval(f"{actual} {op} {expected}")
        except Exception:
            passed = False

    return CheckResult(
        name=name,
        check_type="markdown_claim",
        status="PASS" if passed else "FAIL",
        expected=expected,
        actual=actual,
        claim_source=path,
        message=f"Claim: '{actual}'; expected {op} '{expected}'",
    )


# ── Dispatcher ───────────────────────────────────────────────────────────────

CHECK_DISPATCH = {
    "count": check_count,
    "version_consistency": check_version_consistency,
    "test_count": check_test_count,
    "file_exists": check_file_exists,
    "regex_match": check_regex_match,
    "command_output": check_command_output,
    "json_path": check_json_path,
    "package_unused": check_package_unused,
    "markdown_claim": check_markdown_claim,
}


# ── Main ────────────────────────────────────────────────────────────────────

def run_checks(config_path: str) -> BaselineReport:
    raw = _read_text(config_path)
    if not raw:
        print(f"ERROR: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    cfg = tomllib.loads(raw)
    project = cfg.get("metadata", {}).get("name", "unknown")
    checks_cfg = cfg.get("checks", [])
    results: list[CheckResult] = []

    for check in checks_cfg:
        ctype = check["type"]
        handler = CHECK_DISPATCH.get(ctype)
        if not handler:
            results.append(CheckResult(
                name=check.get("name", ctype),
                check_type=ctype,
                status="ERROR",
                message=f"Unknown check type: {ctype}",
            ))
            continue

        try:
            results.append(handler(check))
        except Exception as e:
            results.append(CheckResult(
                name=check.get("name", ctype),
                check_type=ctype,
                status="ERROR",
                message=f"Exception: {e}",
            ))

    summary = {"pass": 0, "fail": 0, "skip": 0, "error": 0}
    for r in results:
        summary[r.status.lower()] += 1

    report = BaselineReport(
        project=project,
        timestamp=_now(),
        summary=summary,
        checks=[asdict(r) for r in results],
    )
    return report


def main() -> None:
    config_path = sys.argv[1] if len(sys.argv) > 1 else "truth-baseline.toml"
    report = run_checks(config_path)

    # Write JSON
    out_path = REPO_ROOT / "truth-baseline.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Console summary
    print(f"\n{'=' * 60}")
    print(f"Truth Baseline — {report.project}")
    print(f"{'=' * 60}")
    total = sum(report.summary.values())
    ok = report.summary["pass"] + report.summary["skip"]
    for r in report.checks:
        icon = "✓" if r["status"] == "PASS" else "✗" if r["status"] == "FAIL" else "?"
        print(f"  {icon} [{r['check_type']}] {r['name']}: {r['status']}")
        if r["status"] in ("FAIL", "ERROR"):
            print(f"      → {r['message']}")
    print(f"{'-' * 60}")
    print(f"Summary: {ok}/{total} passed  ({report.summary['fail']} fail, {report.summary['error']} error, {report.summary['skip']} skip)")
    print(f"Output: {out_path}")

    if report.summary["fail"] > 0 or report.summary["error"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
