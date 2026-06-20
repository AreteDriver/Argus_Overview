# Project Organization and Source Governance Guidelines

**Document type:** Project standard  
**Recommended filename:** `PROJECT_ORGANIZATION_GUIDELINES.md`  
**Applies to:** All flagship, active, incubating, and grouped projects  
**Owner:** AreteDriver  
**Last updated:** 2026-06-18  

---

## 1. Purpose

This document defines how a project should be organized, documented, classified, and maintained.

Its goals are to:

- Keep project context isolated and accurate.
- Prevent documentation and implementation from drifting apart.
- Give AI coding agents a reliable source package.
- Distinguish current reality from future plans.
- Make projects easier to review, transfer, rebuild, and maintain.
- Establish clear promotion, pause, and archive rules.

This file should be added to every serious project repository or project source folder.

---

## 2. Core Organizational Rule

Organize projects around **context boundaries**, not merely broad subject categories.

Two efforts should remain in the same project only when they share most of the same:

- Product goals
- Source documents
- Technical architecture
- Terminology
- Design system
- Roadmap
- Engineering decisions
- Release process

Separate them when sharing context creates confusion, conflicting requirements, or documentation drift.

---

## 3. Project Classification

Every project must have one declared classification.

### Flagship

A major project receiving sustained investment and intended to become a complete, polished product or platform.

A flagship should have:

- Its own project folder or workspace
- Its own repository
- A complete source package
- A maintained roadmap
- Defined architecture
- Testing and release standards
- Regular documentation reviews
- A truth-baseline process

### Active

A project with a current objective and ongoing work, but not necessarily flagship status.

An active project should have:

- A clear owner
- A current-state document
- A defined next milestone
- A maintained backlog
- Basic testing and documentation

### Incubating

An early concept, prototype, experiment, or research project that has not yet earned full investment.

An incubating project should have:

- A concise project charter
- A problem statement
- Success or promotion criteria
- A time-bounded validation plan
- Minimal documentation appropriate to its maturity

### Paused

A valid project that is not currently receiving work.

A paused project must document:

- Why it was paused
- Current known state
- Unresolved risks
- Conditions for resuming work
- Last reviewed date

### Archived

A completed, abandoned, superseded, or intentionally retired project.

An archived project must document:

- Final disposition
- Replacement project, when applicable
- Known reusable assets
- Repository and dependency status
- Reason for archival

---

## 4. Recommended Portfolio Structure

```text
01-Flagships/
    Animus/
    BenchGoblins/
    AI-Cards/
    Argus/
    Prima-Materia/

02-Games-Studio/
    Uncle-Grandpa-Game/
    Cytogenesis/
    Experiments/
    Shared-Game-Systems/

03-Developer-Infrastructure/
    AI-Skills/
    Memboot/
    Arete-Evals/
    Shared-MCP-Systems/

04-Repo-Planning-and-Standards/
    Documentation-Templates/
    Truth-Baseline-Standard/
    Engineering-Standards/
    Design-and-Build-Workflows/

05-Incubator/
    Early-Concepts/
    Research-Prototypes/
    Unvalidated-Ideas/

06-Archive/
    Paused-Projects/
    Superseded-Plans/
    Completed-Migrations/
```

The numbering is optional. It is useful when the interface sorts folders alphabetically.

---

## 5. Rules for Grouped Projects

Related projects may share a parent folder or workspace when they benefit from shared domain knowledge.

For example:

```text
Games-Studio/
├── Uncle-Grandpa-Game/
├── Cytogenesis/
├── Game-Experiments/
└── Shared-Game-Systems/
```

Each game must still maintain isolated:

- Requirements
- Roadmap
- Architecture
- Art direction
- Design system
- Backlog
- Decisions
- Testing strategy
- Release history

Do not combine multiple games into a single undifferentiated specification.

### Promote a grouped project into its own flagship workspace when:

- It has a substantial or growing codebase.
- It has a distinct visual identity.
- It needs a dedicated roadmap.
- It has multiple major systems or releases.
- It is intended for serious public release.
- Context from neighboring projects begins causing confusion.
- It needs dedicated design, engineering, production, or business planning.

---

## 6. Canonical Source of Truth

Each project must identify one authoritative implementation location.

Recommended metadata:

```yaml
project_name: PROJECT_NAME
classification: flagship
repository: https://github.com/OWNER/REPOSITORY
default_branch: main
documentation_root: /docs
project_owner: OWNER_NAME
last_reviewed: YYYY-MM-DD
```

GitHub should normally remain the canonical source of truth for:

- Application code
- Versioned documentation
- Tests
- Migrations
- Releases
- Architecture decisions
- CI configuration

ChatGPT, Claude, Codex, Figma, and other tools may help analyze or modify a project, but their conversations must not become the only place where important project knowledge exists.

Important decisions must be written back into the repository or approved source package.

---

## 7. Standard Project Source Package

A mature flagship should eventually include the following documents.

```text
PROJECT_CONTEXT.md
PROJECT_CHARTER.md
CURRENT_STATE.md
PRODUCT_REQUIREMENTS.md
ARCHITECTURE.md
DESIGN_SYSTEM.md
ENGINEERING_PLAN.md
ROADMAP.md
BACKLOG.md
DECISIONS.md
TESTING_STRATEGY.md
SECURITY.md
DEPLOYMENT.md
DOCUMENTATION_INDEX.md
TRUTH_BASELINE.md
CLAUDE.md
```

Not every project needs every file immediately. Documentation depth should match project maturity.

### Minimum for an incubating project

```text
PROJECT_CHARTER.md
CURRENT_STATE.md
ROADMAP.md
DECISIONS.md
```

### Minimum for an active project

```text
PROJECT_CONTEXT.md
PROJECT_CHARTER.md
CURRENT_STATE.md
PRODUCT_REQUIREMENTS.md
ARCHITECTURE.md
ROADMAP.md
BACKLOG.md
DECISIONS.md
TESTING_STRATEGY.md
```

### Minimum for a flagship

A flagship should maintain the complete source package or explicitly document why a file does not apply.

---

## 8. Document Roles

### Current-State Documents

Describe what exists now.

Examples:

- Implemented functionality
- Current architecture
- Existing dependencies
- Known defects
- Test coverage
- Deployment state
- Documentation gaps

Current-state statements must be verifiable.

### Target-State Documents

Describe the intended future.

Examples:

- Proposed features
- Planned architecture
- Design improvements
- Future integrations
- Scalability goals
- Release objectives

Target-state material must be labeled as planned, proposed, or aspirational.

### Decision Records

Explain important choices and their consequences.

Each major decision should include:

- Decision
- Date
- Context
- Alternatives considered
- Rationale
- Consequences
- Reversal conditions

### Execution Documents

Tell contributors and agents what to do next.

Examples:

- Engineering plan
- Migration plan
- Backlog
- Release checklist
- Testing plan
- Remediation plan

Execution work should reference authoritative requirements and architecture documents.

---

## 9. Truth and Drift Control

Never allow a roadmap, README, AI-generated plan, or aspirational specification to present planned functionality as implemented reality.

Every significant claim should be classified as one of:

```text
VERIFIED
PARTIALLY VERIFIED
UNVERIFIED
PLANNED
DEPRECATED
```

Projects should adopt a truth-baseline process that checks factual repository claims such as:

- Test count
- Test coverage
- Dependency versions
- Migration count
- API count
- Skill or agent count
- Supported integrations
- Build status
- Release version
- Documentation completeness

Where practical, CI should compare generated facts against claims in:

- `README.md`
- `CLAUDE.md`
- `CURRENT_STATE.md`
- Architecture documents
- Product documentation

Material divergence should fail CI or generate a blocking review item.

---

## 10. Shared Standards

Canonical templates and standards should live in a central planning repository or standards project.

Examples:

```text
Repo-Planning-and-Standards/
├── Documentation-Templates/
├── Truth-Baseline-Standard/
├── Engineering-Standards/
├── Security-Standards/
└── Design-and-Build-Workflows/
```

Projects should copy or adopt the relevant standard while recording its origin and version.

Recommended declaration:

```yaml
adopted_standard: Project Organization and Source Governance Guidelines
standard_version: 1.0
adopted_on: 2026-06-18
canonical_source: github-dev-project-planning
local_exceptions: none
```

A project may override a shared standard only when the exception is documented and justified.

---

## 11. Project Registry

Maintain a portfolio-level `PROJECT_REGISTRY.md`.

Each project record should include:

```yaml
project_name: PROJECT_NAME
repository: REPOSITORY_URL
classification: flagship | active | incubating | paused | archived
status: STATUS_SUMMARY
primary_objective: CURRENT_OBJECTIVE
technology: PRIMARY_STACK
documentation_health: green | yellow | red
truth_baseline_status: implemented | partial | missing
current_milestone: MILESTONE
last_reviewed: YYYY-MM-DD
next_review: YYYY-MM-DD
```

The registry is the portfolio control panel.

It should be reviewed regularly to prevent:

- Forgotten projects
- Duplicate projects
- False active status
- Outdated documentation
- Unowned repositories
- Unclear project priorities

---

## 12. Project Lifecycle

Use the following lifecycle:

```text
IDEA → INCUBATING → ACTIVE → FLAGSHIP
                       ↓
                    PAUSED
                       ↓
                    ARCHIVED
```

### Promotion from Idea to Incubating

Requires:

- A defined problem
- A proposed user or audience
- A concise value proposition
- A validation approach

### Promotion from Incubating to Active

Requires:

- Evidence the project is worth pursuing
- A repository or controlled source location
- A project owner
- A current milestone
- Basic architecture and requirements
- A maintained backlog

### Promotion from Active to Flagship

Requires:

- Strategic importance
- Sustained development
- A serious release or adoption goal
- Dedicated documentation
- Testing and reliability standards
- A distinct project context
- Regular maintenance commitment

### Movement to Paused

Occurs when:

- No current milestone exists
- Higher-priority work displaces it
- A dependency or decision blocks progress
- Continuing would create waste

### Movement to Archived

Occurs when:

- The project is complete
- The project is superseded
- The project is no longer strategically useful
- Required assumptions proved false
- Maintenance is intentionally ended

---

## 13. Conversation and Agent Discipline

Project conversations should be purpose-specific.

Recommended threads:

```text
Project Overview and Governance
Architecture Review
UI and Design System
Engineering Execution
Documentation Maintenance
Release Planning
Bug and Reliability Work
Research and Competitive Analysis
```

Do not use one endless conversation as the project’s unofficial knowledge base.

After a conversation produces a meaningful result:

1. Identify the decision, requirement, or plan.
2. Update the correct repository document.
3. Record significant decisions in `DECISIONS.md`.
4. Update the backlog or roadmap.
5. Reconcile any contradictions.
6. Commit the changes to the canonical repository.

AI agents should be instructed to read the source package before making substantial changes.

---

## 14. Recommended Repository Layout

```text
project-root/
├── README.md
├── CLAUDE.md
├── PROJECT_ORGANIZATION_GUIDELINES.md
├── src/
├── tests/
├── docs/
│   ├── DOCUMENTATION_INDEX.md
│   ├── PROJECT_CONTEXT.md
│   ├── PROJECT_CHARTER.md
│   ├── CURRENT_STATE.md
│   ├── PRODUCT_REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── DESIGN_SYSTEM.md
│   ├── ENGINEERING_PLAN.md
│   ├── ROADMAP.md
│   ├── BACKLOG.md
│   ├── DECISIONS.md
│   ├── TESTING_STRATEGY.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   └── TRUTH_BASELINE.md
├── scripts/
│   └── truth-baseline/
└── .github/
    └── workflows/
```

The exact structure may change by technology, but the separation between implementation, tests, documentation, scripts, and CI should remain clear.

---

## 15. Project Setup Checklist

When adding this standard to a project:

- [ ] Declare the project name.
- [ ] Declare its classification.
- [ ] Record the canonical repository.
- [ ] Record the default branch.
- [ ] Name the project owner.
- [ ] Create or verify `CURRENT_STATE.md`.
- [ ] Create or verify `PROJECT_CHARTER.md`.
- [ ] Create or verify `ROADMAP.md`.
- [ ] Create or verify `DECISIONS.md`.
- [ ] Separate current-state claims from future plans.
- [ ] Identify missing source documents.
- [ ] Add the project to `PROJECT_REGISTRY.md`.
- [ ] Record the adopted standards and versions.
- [ ] Define the current milestone.
- [ ] Define the next documentation review date.
- [ ] Add or plan a truth-baseline process.
- [ ] Confirm that important conversation outcomes are stored in the repository.

---

## 16. Ongoing Review Checklist

Review active projects regularly.

- [ ] Does the declared classification still fit?
- [ ] Is there a current milestone?
- [ ] Does the repository match `CURRENT_STATE.md`?
- [ ] Are README claims still accurate?
- [ ] Are architecture diagrams and dependency lists current?
- [ ] Are decisions recorded?
- [ ] Is the backlog prioritized?
- [ ] Are completed roadmap items marked correctly?
- [ ] Are planned features clearly labeled?
- [ ] Are abandoned approaches marked deprecated?
- [ ] Are tests and CI functioning?
- [ ] Does the project still deserve active investment?
- [ ] Should the project be promoted, paused, consolidated, or archived?

---

## 17. Project-Specific Adoption Record

Complete this section when adding the file to a project.

```yaml
project_name:
classification:
repository:
default_branch:
documentation_root:
project_owner:
current_milestone:
adopted_on:
guideline_version: 1.0
canonical_standard_source:
local_exceptions:
next_review:
```

### Project Notes

Document any project-specific interpretation or exceptions below.

```text
None recorded.
```

---

## 18. Governing Principle

A project is not organized merely because its files are in a folder.

A project is organized when:

- Its boundaries are clear.
- Its current reality is documented.
- Its future direction is explicit.
- Its decisions are traceable.
- Its source of truth is known.
- Its documentation matches its implementation.
- Its next action is visible.
- Its lifecycle status is honest.
