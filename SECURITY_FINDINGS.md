# Security Findings — Argus_Overview

**Sweep date:** 2026-05-28 (Wave 3 of the fleet sweep)
**Tools:** semgrep (auto) · bandit · gitleaks · pip-audit
**Triage model:** claude-opus-4-7 (manual)
**Posture:** **CLEAN** — zero HIGH / MEDIUM / ERROR findings across all scanners.

---

## Summary

| Tool | Findings | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| semgrep (auto) | 0 | 0 | 0 | 0 |
| bandit | 86 | 0 | 0 | 86 |
| gitleaks | 0 | 0 | 0 | 0 |
| pip-audit | 0 | 0 | 0 | 0 |

The 86 bandit findings are all LOW (B101 `assert_used` in tests, B404/B603 subprocess noise, B311 `random` for non-crypto). Standard noise pattern — no real security implications.

No HIGH/MEDIUM findings to triage, no patches needed.

---

## Verification

```bash
semgrep --config=auto --json --quiet --exclude=.venv --exclude=node_modules -o /tmp/argus-semgrep.json .
bandit -r . -f json -q -x .venv,tests
gitleaks detect --no-banner
pip-audit -r requirements.txt
```

Existing CI provides ongoing coverage. No additional gates recommended.
