# ADR-001: ESI Integration Deprioritized

## Status

**Accepted** — 2026-07-26  
**Supersedes**: All prior ESI design sketches (none committed to code)  
**Author**: AreteDriver exocortex  

---

## Context

Argus Overview provides operational awareness for EVE Online multi-boxers. Two data sources were considered for character location, fleet state, and system intelligence:

1. **ESI (EVE Swagger Interface)** — CCP's OAuth-backed REST API
2. **Chat log parsing** — Reading `Chatlogs/` files written by EVE clients

An `esi/` package stub existed in the codebase (only `__pycache__` remained by 2026-07-26). No ESI integration had ever been committed to `main`.

### What ESI Would Provide

| Capability | ESI Endpoint | Value to Argus |
|---|---|---|
| Character location | `GET /characters/{id}/location/` | Real-time system name |
| Online status | `GET /characters/{id}/online/` | Detect logoff/logon |
| Fleet membership | `GET /characters/{id}/fleet/` | Auto-detect fleet composition |
| Ship type | `GET /characters/{id}/ship/` | Current ship for threat assessment |
| Jump fatigue | `GET /characters/{id}/ fatigue/` | Operational readiness |

### What Log Parsing Already Provides

| Capability | Source | Accuracy | Latency |
|---|---|---|---|
| Character location | `Local` chat log | Exact | ~1s (file write + parse) |
| Hostile count | `Intel` chat log | Human-reported | ~1s |
| Ship types | `Intel` chat log | Human-reported | ~1s |
| System jumps | `jumps.py` + static data | Calculated | Instant |
| Threat level | `parser.py` + heuristics | Inferred | ~1s |

---

## Decision

**ESI integration is deprioritized. Argus will continue to use chat-log parsing as its sole intelligence source.**

The `esi/` directory has been removed (commit 9c3d909). No ESI client, auth flow, or token store will be added unless a future use case emerges that chat logs cannot satisfy.

---

## Consequences

### Positive

1. **Zero auth complexity** — No OAuth2 redirects, no refresh tokens, no token expiry handling, no scopes negotiation.
2. **Zero rate-limit logic** — Chat logs are unthrottled; ESI is 20 req/s per IP with error-code backoff.
3. **Works for all alts simultaneously** — One `Chatlogs/` directory contains all characters' intel. ESI requires one token per character.
4. **No CCP dependency** — If ESI is down, rate-limited, or deprecated, Argus continues to function.
5. **No account-linking friction** — New users import windows and immediately get intel. No "authorize SSO" step.
6. **Fleet op privacy** — No API calls that could be logged or correlated by CCP.

### Negative

1. **Location is only as fresh as the last Local log write** — ESI would provide sub-second location; logs are ~1s behind.
2. **No automatic ship-type detection** — Human intel must include ship names (e.g., "3 Cynabals"). ESI would show actual fitted ship.
3. **No jump fatigue visibility** — Log parsing cannot detect fatigue; ESI would expose it.
4. **No auto-fleet-sync** — Fleet composition must be manually tracked or inferred from intel. ESI would provide exact fleet roster.

### Neutralized

| Negative | Mitigation | Verdict |
|---|---|---|
| 1s location latency | Local chat logs update on every system change; 1s is acceptable for operational use. | Tolerable |
| Manual ship reporting | Parser extracts ship names from intel messages; common ships in static database. | Tolerable |
| No fatigue data | Not required for window-preview / intel-overlay use case. | Out of scope |
| No auto-fleet-sync | Character manager already supports manual team creation; UI is fast. | Tolerable |

---

## Alternatives Considered

### A. Minimal ESI — location only

Scope: authenticate once, poll `/location/` every 5s for all linked characters.

**Rejected**: Adds OAuth, token refresh, rate-limit handling, and per-character account linking for marginal gain over log parsing. The 1s latency of logs is not a bottleneck for multi-boxing operations.

### B. Full ESI — fleet, ship, fatigue

Scope: full character sheet + fleet + ship + fatigue for all alts.

**Rejected**: Massive scope increase. Would require:
- SSO OAuth2 flow with PKCE
- Token store with encryption
- Refresh-token rotation
- Rate-limit queue + backoff
- Scope audit (which scopes are safe vs invasive)
- CCP ToS compliance review

This is a 2–3 month project. The operational truth value does not justify the engineering cost.

### C. Hybrid — logs primary, ESI optional fallback

Scope: log parsing as default; ESI as opt-in for users who want fleet-sync.

**Rejected**: Creates a two-tier user experience. Users without ESI get a subtly inferior product. Maintaining both paths doubles test surface and creates "works for me" bug reports.

---

## When to Revisit

Re-open this ADR if **any** of the following become true:

1. **CCP deprecates chat logs** or moves them to an unreadable binary format.
2. **A user need emerges** that logs genuinely cannot satisfy (e.g., real-time ship-type auto-detection for threat assessment).
3. **Fleet composition auto-sync** becomes a top-3 user-requested feature with no viable log-based workaround.
4. **Another project in the portfolio** builds a reusable ESI auth/token library (e.g., Herald, MCP Manager) that Argus could consume without adding its own OAuth code.

---

## References

- ESI Docs: https://docs.esi.evetech.net/
- ESI Rate Limits: https://docs.esi.evetech.net/docs/ESI_introduction.html#rate-limiting
- Argus Intel Subsystem: `src/argus_overview/intel/` (~1,970 LOC)
- Prior `esi/` stub: removed in commit 9c3d909
