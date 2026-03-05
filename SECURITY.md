# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.0.x | Yes |
| < 3.0 | No |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email **jamesyng79@gmail.com** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
3. You will receive an acknowledgment within 48 hours
4. A fix will be prioritized based on severity

## Security Measures

This project uses:
- **CodeQL** — static analysis on every push
- **gitleaks** — secret scanning on every push
- **pip-audit** — dependency vulnerability scanning
- **Dependabot** — automated dependency updates

## Scope

The following are in scope for security reports:
- Code injection vulnerabilities
- Credential exposure
- Dependency vulnerabilities with known exploits
- Privilege escalation via hotkey or window management APIs

Out of scope:
- Denial of service
- Social engineering
- EVE Online EULA compliance (this is CCP's domain, not a security issue)
