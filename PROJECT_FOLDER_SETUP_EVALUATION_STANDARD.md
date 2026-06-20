# Project Folder Setup Evaluation Standard

**Document type:** Audit and readiness standard  
**Recommended filename:** `PROJECT_FOLDER_SETUP_EVALUATION_STANDARD.md`  
**Companion standard:** `PROJECT_ORGANIZATION_GUIDELINES.md`  
**Applies to:** ChatGPT project workspaces, local project folders, GitHub repositories, and AI-agent source packages  
**Owner:** AreteDriver  
**Version:** 1.0  
**Last updated:** 2026-06-18  

---

## 1. Purpose

This standard defines how to determine whether a project folder is correctly structured, sufficiently documented, factually reliable, and ready for productive work by humans or AI agents.

A project folder is not correctly set up merely because it contains files.

It is correctly set up when:

- Its purpose and boundaries are unmistakable.
- Its repository and canonical sources are identified.
- Current reality is separated from future intent.
- Required source documents exist and agree with one another.
- Important decisions are traceable.
- An agent can determine what to read, what is true, and what to do next.
- Obsolete, duplicate, and unrelated material is controlled.
- Maintenance and review responsibilities are defined.

---

## 2. Evaluation Scope

Evaluate the project at two separate layers.

### Layer A — Project Workspace

This is the working context used in ChatGPT, Claude, Codex, Figma, a local planning folder, or another project-management environment.

Evaluate whether the workspace contains:

- The correct project only
- Appropriate source files
- Clear project instructions
- Current repository references
- A usable conversation or workstream structure
- No unrelated context
- No stale files presented as authoritative

### Layer B — Canonical Repository

This is the GitHub repository or other authoritative implementation location.

Evaluate whether the repository contains:

- Code and configuration
- Versioned documentation
- Tests
- CI workflows
- Architecture and decision records
- Current-state evidence
- Release and deployment information
- Truth-baseline controls

A strong workspace cannot compensate for a disorganized repository.  
A strong repository cannot compensate for a workspace filled with stale or conflicting sources.

Both layers must be evaluated.

---

## 3. Audit Outcomes

Every evaluation must produce one of four outcomes.

### PASS

The folder is correctly set up for its declared maturity level.

Minor improvements may remain, but no issue materially threatens accuracy, discoverability, or execution.

### PASS WITH CONDITIONS

The folder is usable, but one or more weaknesses should be corrected before major work begins.

Examples:

- A missing decision log
- An incomplete current-state document
- An outdated architecture diagram
- Minor duplication

### FAIL

The folder is not ready for reliable work.

Examples:

- No canonical repository
- Conflicting source documents
- Aspirational claims presented as implemented
- No defined project objective
- Multiple unrelated projects mixed together
- Critical documentation missing
- Agents cannot determine what is authoritative

### QUARANTINE

The folder contains material that may actively mislead work and must not be used until reviewed.

Examples:

- Contradictory versions of specifications with no authority markers
- Unknown-origin source files
- Sensitive material stored incorrectly
- Documentation from another project
- Unverified generated claims presented as fact
- Obsolete instructions that could cause destructive changes

---

## 4. Hard Gates

A project cannot pass if any hard gate fails.

### Gate 1 — Identity

The project has a unique, stable name.

Required:

- Project name
- Short purpose statement
- Declared classification
- Named owner
- Last reviewed date

### Gate 2 — Boundary

The folder contains one coherent project or an intentionally grouped project with isolated subprojects.

Fail when:

- Unrelated products are mixed together
- Shared systems and product-specific systems are indistinguishable
- Multiple games, applications, or research efforts share one undifferentiated specification
- The folder name no longer reflects its actual contents

### Gate 3 — Canonical Source

The project identifies the authoritative repository and branch.

Required:

```yaml
repository:
default_branch:
documentation_root:
canonical_source:
```

Fail when:

- The repository is unknown
- Multiple repositories appear authoritative without explanation
- Uploaded project files are treated as more authoritative than repository reality
- Important work exists only in chat history

### Gate 4 — Current Reality

The project contains a current-state record that distinguishes implemented, partial, planned, deprecated, and unknown capabilities.

Fail when:

- Future plans are described as current functionality
- Core claims cannot be verified
- The current state is materially outdated
- Known failures are omitted

### Gate 5 — Execution Direction

The project has a visible next objective.

Required:

- Current milestone
- Prioritized next actions
- Known blockers
- Acceptance criteria or definition of done

Fail when:

- The project is labeled active but has no active objective
- The backlog is an unprioritized idea dump
- Agents cannot determine what to work on next

### Gate 6 — Source Coherence

The primary documents do not materially contradict each other.

Fail when:

- README, architecture, roadmap, and current-state documents disagree on major facts
- Duplicate specifications conflict
- Old and new plans are not labeled
- Terminology is inconsistent enough to create implementation risk

### Gate 7 — Safety and Sensitivity

Secrets, credentials, private records, and sensitive information are handled correctly.

Fail or quarantine when:

- API keys or credentials are stored in source files
- `.env` secrets are committed
- Personal, legal, medical, or proprietary records are exposed without controls
- Generated artifacts contain data that should not leave the project boundary

---

## 5. Weighted Evaluation Score

After all hard gates pass, score the project out of 100 points.

| Category | Weight |
|---|---:|
| Identity and purpose | 10 |
| Context boundaries | 10 |
| Canonical source and repository linkage | 10 |
| Source-document completeness | 15 |
| Truthfulness and current-state accuracy | 15 |
| Architecture and implementation clarity | 10 |
| Execution readiness | 10 |
| Agent readiness | 10 |
| Maintenance, security, and lifecycle controls | 10 |
| **Total** | **100** |

### Score Interpretation

| Score | Rating | Meaning |
|---:|---|---|
| 90–100 | Excellent | Ready for sustained flagship work |
| 80–89 | Strong | Ready, with limited improvements |
| 70–79 | Functional | Usable, but weaknesses should be corrected |
| 60–69 | Fragile | Work may proceed only with explicit conditions |
| Below 60 | Not ready | Reorganize before major work |
| Any hard-gate failure | Fail | Score does not override the failure |

A score is not a substitute for judgment. A project with exposed secrets or false implementation claims fails regardless of total points.

---

## 6. Category Evaluation Criteria

## 6.1 Identity and Purpose — 10 Points

Award points when:

- [ ] Project name is unique and consistent.
- [ ] Purpose is described in one or two clear paragraphs.
- [ ] Primary user or audience is identified.
- [ ] Project classification is declared.
- [ ] Owner is identified.
- [ ] Current status and last review date are recorded.
- [ ] Success is defined.
- [ ] Non-goals are documented where needed.

### Strong evidence

```yaml
project_name: PROJECT_NAME
classification: flagship
owner: OWNER_NAME
purpose: CLEAR_PURPOSE
primary_users:
status:
last_reviewed:
```

### Warning signs

- The project is described only by features.
- The intended user is unknown.
- The title differs across documents.
- The project has several competing mission statements.
- No one can tell whether it is active, paused, or experimental.

---

## 6.2 Context Boundaries — 10 Points

Award points when:

- [ ] The folder contains only directly relevant sources.
- [ ] Shared components are separated from product-specific components.
- [ ] Grouped projects have clear subproject boundaries.
- [ ] Each product has isolated requirements and roadmaps.
- [ ] Cross-project dependencies are referenced rather than duplicated.
- [ ] Archive material is separated from active material.
- [ ] Experimental work is clearly labeled.

### Boundary test

Ask:

> Could an unfamiliar contributor read this folder without accidentally applying another project’s requirements, architecture, branding, or backlog?

If the answer is no, the boundary is weak.

### Warning signs

- “Miscellaneous” becomes a permanent home for important documents.
- Multiple games share one roadmap.
- Shared libraries are buried inside a single product plan.
- Old project names remain throughout the source package.
- Copy-pasted templates still contain another project’s details.

---

## 6.3 Canonical Source and Repository Linkage — 10 Points

Award points when:

- [ ] Repository URL is recorded.
- [ ] Default branch is recorded.
- [ ] Documentation root is recorded.
- [ ] Repository ownership is clear.
- [ ] Workspace sources point to repository versions.
- [ ] External design files identify their canonical location.
- [ ] Important discussions are written back into version control.
- [ ] Multiple repositories have documented roles.

### Required repository map

```yaml
primary_repository:
default_branch:
documentation_root:
design_source:
deployment_source:
issue_tracker:
supporting_repositories:
```

### Warning signs

- A local folder contains changes not reflected in GitHub.
- ChatGPT sources contain newer plans than the repository with no reconciliation.
- Two documents claim to be the master specification.
- Repository links are missing or stale.
- Agents are expected to infer which branch is current.

---

## 6.4 Source-Document Completeness — 15 Points

Evaluate completeness relative to project classification.

### Incubating minimum

- [ ] `PROJECT_CHARTER.md`
- [ ] `CURRENT_STATE.md`
- [ ] `ROADMAP.md`
- [ ] `DECISIONS.md`

### Active minimum

- [ ] `PROJECT_CONTEXT.md`
- [ ] `PROJECT_CHARTER.md`
- [ ] `CURRENT_STATE.md`
- [ ] `PRODUCT_REQUIREMENTS.md`
- [ ] `ARCHITECTURE.md`
- [ ] `ROADMAP.md`
- [ ] `BACKLOG.md`
- [ ] `DECISIONS.md`
- [ ] `TESTING_STRATEGY.md`

### Flagship expectation

- [ ] All active-project documents
- [ ] `DESIGN_SYSTEM.md`
- [ ] `ENGINEERING_PLAN.md`
- [ ] `SECURITY.md`
- [ ] `DEPLOYMENT.md`
- [ ] `DOCUMENTATION_INDEX.md`
- [ ] `TRUTH_BASELINE.md`
- [ ] `CLAUDE.md` or equivalent agent instructions

### Evaluation questions

- Does every document have a clear role?
- Are document owners or review dates recorded?
- Are missing documents intentional and explained?
- Are large documents divided logically?
- Can contributors find information without searching every file?

### Warning signs

- A huge README attempts to serve every purpose.
- Documents exist only to satisfy a checklist.
- Source files contain placeholders without useful content.
- There is no documentation index.
- The same information is maintained manually in several places.

---

## 6.5 Truthfulness and Current-State Accuracy — 15 Points

Award points when:

- [ ] Current functionality is verified against the repository.
- [ ] Planned functionality is explicitly labeled.
- [ ] Partially implemented features are marked partial.
- [ ] Deprecated systems are marked.
- [ ] Unknown claims are labeled unverified.
- [ ] Dates and versions are present where facts can age.
- [ ] README and agent instructions agree with repository reality.
- [ ] A truth-baseline process exists or is planned.

Use the following labels:

```text
VERIFIED
PARTIALLY VERIFIED
UNVERIFIED
PLANNED
DEPRECATED
```

### Verification targets

- Tests
- Coverage
- Dependencies
- Runtime versions
- API routes
- Migrations
- Environment variables
- Integrations
- Skills or agents
- Infrastructure resources
- Database objects
- Release versions

### Warning signs

- “Production ready” has no evidence.
- Test counts are manually maintained.
- Documentation claims integrations that do not exist.
- Architecture describes a target system instead of the actual system.
- Old screenshots are used as proof of current functionality.

---

## 6.6 Architecture and Implementation Clarity — 10 Points

Award points when:

- [ ] System boundaries are documented.
- [ ] Major components and responsibilities are defined.
- [ ] Data flow is understandable.
- [ ] External dependencies and integrations are listed.
- [ ] Deployment topology is documented.
- [ ] Major constraints are recorded.
- [ ] Technical debt is visible.
- [ ] Architecture diagrams match current reality.
- [ ] Proposed architecture is separated from current architecture.

### Contributor test

An unfamiliar engineer should be able to answer:

1. What are the major system components?
2. Where does data enter and leave?
3. What is the primary runtime?
4. What external systems are required?
5. How is the project tested?
6. How is it deployed?
7. Where are the dangerous or fragile areas?

### Warning signs

- Architecture consists only of a technology list.
- Diagrams have no date or version.
- There is no distinction between frontend, backend, data, and infrastructure.
- Design decisions exist only in commit messages or chat.
- The repository structure contradicts the architecture document.

---

## 6.7 Execution Readiness — 10 Points

Award points when:

- [ ] Current milestone is explicit.
- [ ] Backlog is prioritized.
- [ ] Work items are small enough to execute.
- [ ] Acceptance criteria exist.
- [ ] Dependencies and blockers are visible.
- [ ] Completed work is separated from future work.
- [ ] Release criteria are defined.
- [ ] The next action is unambiguous.

### Good work-item structure

```yaml
title:
objective:
current_state:
scope:
out_of_scope:
dependencies:
acceptance_criteria:
validation:
status:
```

### Warning signs

- The roadmap is a list of wishes.
- The backlog contains duplicate or obsolete tasks.
- Everything is labeled high priority.
- Tasks contain no acceptance criteria.
- Agents are asked to “improve the project” without bounded scope.

---

## 6.8 Agent Readiness — 10 Points

Award points when an AI coding agent can determine:

- [ ] What repository to use.
- [ ] What files to read first.
- [ ] Which claims are authoritative.
- [ ] What commands install, build, test, lint, and run the project.
- [ ] Which files must not be changed.
- [ ] What security restrictions apply.
- [ ] What coding and documentation conventions apply.
- [ ] What the current task and acceptance criteria are.
- [ ] How to report uncertainty or contradictions.
- [ ] How to validate completion.

### Recommended agent entry point

`CLAUDE.md`, `AGENTS.md`, or an equivalent file should contain:

```text
1. Project purpose
2. Canonical documents
3. Repository commands
4. Architecture summary
5. Current milestone
6. Coding standards
7. Testing requirements
8. Security rules
9. Documentation update requirements
10. Stop conditions and escalation rules
```

### Agent simulation test

Give a fresh agent only the source package and ask it to answer:

1. What does this project do?
2. What exists today?
3. What is planned?
4. What should be worked on next?
5. How will completion be tested?
6. Which files are authoritative?
7. What contradictions or missing information exist?

A strong setup produces consistent answers without relying on prior chat history.

---

## 6.9 Maintenance, Security, and Lifecycle Controls — 10 Points

Award points when:

- [ ] Review cadence is defined.
- [ ] Last-reviewed dates are present.
- [ ] Stale documents are detectable.
- [ ] Archive rules exist.
- [ ] Secrets are excluded.
- [ ] Dependency maintenance is defined.
- [ ] CI checks documentation or repository health.
- [ ] Ownership is visible.
- [ ] Pausing or archiving criteria are documented.
- [ ] The project registry is updated.

### Warning signs

- No review has occurred in months despite active development.
- Paused projects remain labeled active.
- Obsolete documents remain beside current documents.
- No one owns dependency or security maintenance.
- Secrets management is undocumented.
- The project can only be understood by its original creator.

---

## 7. Workspace Source Evaluation

When adding files to a ChatGPT or AI project workspace, evaluate every source before upload.

### Source Admission Checklist

- [ ] Is this file directly relevant to the project?
- [ ] Is it the newest approved version?
- [ ] Is its authority clear?
- [ ] Does it duplicate another source?
- [ ] Does it contradict another source?
- [ ] Does it contain another project’s context?
- [ ] Does it contain secrets or sensitive information?
- [ ] Is its date or version visible?
- [ ] Is it current-state, target-state, reference, or archive material?
- [ ] Will an agent know how to use it?

### Recommended source labels

At the top of each uploaded source, include:

```yaml
document_status: authoritative | supporting | draft | archived
document_type: current-state | target-state | execution | reference
version:
last_reviewed:
canonical_location:
owner:
```

### Remove or quarantine sources when:

- They are superseded.
- Their origin is unknown.
- They contain unresolved contradictions.
- They are irrelevant to the project.
- They mix verified facts with speculation.
- They are exports of conversations containing significant noise.
- They expose information that should not be broadly available.

---

## 8. Repository Structure Evaluation

A typical mature repository should resemble:

```text
project-root/
├── README.md
├── CLAUDE.md or AGENTS.md
├── PROJECT_ORGANIZATION_GUIDELINES.md
├── PROJECT_FOLDER_SETUP_EVALUATION_STANDARD.md
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
├── .github/
│   └── workflows/
└── archive/
```

This is a reference structure, not a rigid universal requirement.

Evaluate whether the structure:

- Makes responsibilities obvious
- Matches the technology
- Separates source, tests, documentation, automation, and archive material
- Avoids excessive nesting
- Avoids vague folders such as `stuff`, `misc`, `old`, or `temp`
- Keeps generated files out of source control where appropriate
- Uses consistent naming
- Provides an obvious entry point

---

## 9. Automated Checks

Automate objective checks wherever practical.

### Recommended checks

- Required files exist.
- Required metadata fields exist.
- Repository links resolve.
- Internal document links resolve.
- No secrets are detected.
- No empty placeholder documents remain.
- No duplicate filenames exist in conflicting locations.
- Documents do not reference obsolete project names.
- README claims match generated truth-baseline facts.
- Runtime and dependency versions match configuration.
- Test and coverage claims match CI output.
- Roadmap statuses use approved values.
- Last-reviewed dates are within policy.
- Archived files are not linked as current sources.

### Suggested audit outputs

```text
PASS
WARNING
FAIL
NOT_APPLICABLE
MANUAL_REVIEW_REQUIRED
```

Automation should flag issues. It should not silently rewrite governance documents without review.

---

## 10. Manual Review Tests

Some qualities require human judgment.

### Ten-Minute Orientation Test

Give the folder to someone unfamiliar with the project.

Within ten minutes, they should be able to identify:

- What the project is
- Who it serves
- What currently works
- What does not work
- Where the code lives
- What is planned next
- How to run tests
- Which documents are authoritative

Failure indicates weak discoverability or documentation.

### Contradiction Test

Compare:

- `README.md`
- `CURRENT_STATE.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `CLAUDE.md` or `AGENTS.md`

List every factual disagreement.

Any material contradiction must be resolved or explicitly explained.

### Cold-Agent Test

Start a new agent session with no previous conversation history.

Ask it to:

1. Summarize the project.
2. Identify current capabilities.
3. Identify planned capabilities.
4. Describe the architecture.
5. Propose the next valid work item.
6. State how that work would be validated.
7. Identify missing or conflicting information.

If the agent hallucinates structure, confuses plans with reality, or cannot identify the next task, the folder is not agent-ready.

### Change-Impact Test

Select one proposed feature and ask:

- Which documents must change?
- Which code areas are affected?
- Which tests are required?
- Which architectural decisions apply?
- Which release criteria must be satisfied?

A good setup makes the impact traceable.

### Exit Test

Ask whether another engineer could continue the project if the current owner disappeared.

If not, identify the undocumented knowledge and convert it into project sources.

---

## 11. Classification-Specific Pass Criteria

## Incubating Project

Pass when:

- Hard gates pass.
- Score is at least 65.
- The problem and validation approach are clear.
- No false implementation claims exist.
- Promotion or termination criteria are defined.

## Active Project

Pass when:

- Hard gates pass.
- Score is at least 75.
- Current milestone and backlog are usable.
- Architecture and tests are documented.
- Repository and workspace sources agree.

## Flagship Project

Pass when:

- Hard gates pass.
- Score is at least 90.
- No category scores below 70% of its available points.
- Truth-baseline controls are implemented or have a dated implementation plan.
- Security, deployment, testing, design, and documentation are maintained.
- Cold-agent and ten-minute orientation tests pass.
- There are no unresolved material contradictions.

## Paused Project

Pass when:

- Current state is frozen and documented.
- Pause reason is recorded.
- Resume conditions are defined.
- Open risks and dependencies are listed.
- Repository and data preservation are addressed.

## Archived Project

Pass when:

- Final disposition is recorded.
- Successor projects are linked.
- Reusable assets are identified.
- Sensitive data and obsolete deployment resources are handled.
- The archive cannot be mistaken for an active project.

---

## 12. Audit Frequency

Recommended cadence:

| Project type | Evaluation frequency |
|---|---|
| Flagship | Monthly and before major releases |
| Active | Every 6–8 weeks |
| Incubating | At validation checkpoints |
| Paused | Every 6 months |
| Archived | On archival and when reused |
| Grouped workspace | Whenever a subproject is added or promoted |

Also run an evaluation:

- Before handing the project to a new agent
- Before a major architecture change
- Before public release
- After repository consolidation
- After significant documentation generation
- When claims appear inconsistent
- When work repeatedly starts from the wrong assumptions

---

## 13. Audit Procedure

Use this sequence.

### Step 1 — Declare the Intended State

Record:

- Project classification
- Project owner
- Canonical repository
- Current milestone
- Intended audience
- Audit date

### Step 2 — Inventory the Folder

List:

- All source files
- All repositories
- All design sources
- All external references
- All active workstreams
- All archived or duplicate material

### Step 3 — Run Hard Gates

Stop and record failure if any hard gate fails.

### Step 4 — Score Each Category

Provide evidence for every score. Do not award points based on assumptions.

### Step 5 — Run Manual Tests

At minimum:

- Ten-minute orientation test
- Contradiction test
- Cold-agent test

### Step 6 — Classify Findings

Use:

```text
BLOCKER
HIGH
MEDIUM
LOW
OBSERVATION
```

### Step 7 — Produce a Remediation Plan

Every blocker and high-severity issue must include:

- Owner
- Required action
- Acceptance criteria
- Target milestone
- Validation method

### Step 8 — Re-evaluate

Do not mark the setup complete until hard gates pass and the required score is reached.

---

## 14. Evaluation Report Template

```markdown
# Project Folder Evaluation Report

## Audit Metadata

- Project:
- Classification:
- Owner:
- Repository:
- Default branch:
- Audit date:
- Reviewer:
- Previous score:

## Outcome

- Result: PASS | PASS WITH CONDITIONS | FAIL | QUARANTINE
- Score: /100
- Hard-gate failures:
- Summary:

## Hard Gates

| Gate | Result | Evidence | Required action |
|---|---|---|---|
| Identity | | | |
| Boundary | | | |
| Canonical source | | | |
| Current reality | | | |
| Execution direction | | | |
| Source coherence | | | |
| Safety and sensitivity | | | |

## Category Scores

| Category | Score | Maximum | Evidence |
|---|---:|---:|---|
| Identity and purpose | | 10 | |
| Context boundaries | | 10 | |
| Canonical source | | 10 | |
| Source completeness | | 15 | |
| Truthfulness | | 15 | |
| Architecture clarity | | 10 | |
| Execution readiness | | 10 | |
| Agent readiness | | 10 | |
| Maintenance and security | | 10 | |
| **Total** | | **100** | |

## Major Findings

### Blockers

### High Priority

### Medium Priority

### Low Priority

## Contradictions

| Source A | Source B | Conflict | Resolution |
|---|---|---|---|

## Missing Sources

| Document | Required for classification? | Action |
|---|---|---|

## Agent Readiness Results

- Project summary accuracy:
- Current versus planned separation:
- Next-task identification:
- Build and test command accuracy:
- Contradictions detected:
- Result:

## Remediation Plan

| Priority | Action | Owner | Acceptance criteria | Validation |
|---|---|---|---|---|

## Final Determination

State whether the project folder is ready for:

- Continued planning
- AI-agent implementation
- Human engineering handoff
- Major feature development
- Public release
```

---

## 15. AI Audit Prompt

Use this prompt with a capable coding or analysis agent.

```text
Evaluate this project folder using PROJECT_FOLDER_SETUP_EVALUATION_STANDARD.md.

Requirements:

1. Inspect the workspace sources and canonical repository separately.
2. Identify the declared project classification.
3. Inventory all project sources and determine which are authoritative.
4. Run every hard gate.
5. Score all evaluation categories with evidence.
6. Compare README.md, CURRENT_STATE.md, ARCHITECTURE.md, ROADMAP.md,
   PRODUCT_REQUIREMENTS.md, and CLAUDE.md or AGENTS.md for contradictions.
7. Distinguish verified, partially verified, unverified, planned, and
   deprecated claims.
8. Verify repository facts wherever possible instead of trusting prose.
9. Identify missing, duplicate, stale, irrelevant, or unsafe sources.
10. Perform a cold-agent readiness assessment.
11. Produce a completed Project Folder Evaluation Report.
12. Create a prioritized remediation plan with acceptance criteria.
13. Do not edit project files during the audit unless explicitly authorized.
14. Do not assume that documented features are implemented.
15. Mark uncertain findings as MANUAL_REVIEW_REQUIRED.

Final output must include:

- PASS, PASS WITH CONDITIONS, FAIL, or QUARANTINE
- Score out of 100
- Hard-gate results
- Evidence for each category
- Material contradictions
- Missing sources
- Agent-readiness result
- Prioritized remediation plan
```

---

## 16. Quick Evaluation Checklist

Use this before beginning substantial work.

- [ ] Correct project name
- [ ] Clear purpose and owner
- [ ] Correct classification
- [ ] Clean context boundary
- [ ] Canonical repository identified
- [ ] Default branch identified
- [ ] Current-state document exists
- [ ] Planned work is labeled
- [ ] Current milestone exists
- [ ] Backlog is prioritized
- [ ] Architecture matches implementation
- [ ] Tests and run commands are documented
- [ ] Important decisions are recorded
- [ ] Sources do not materially conflict
- [ ] No unrelated project files
- [ ] No exposed secrets
- [ ] Agent entry-point file exists
- [ ] Truth-baseline status is known
- [ ] Review date is current
- [ ] Project registry is updated

Any unchecked item should become either:

- A remediation task
- A documented exception
- A reason the project is not ready

---

## 17. Best-Practice Principles

1. **Evaluate against the declared maturity level.**  
   A prototype does not need flagship bureaucracy, but a flagship cannot operate on prototype documentation.

2. **Repository reality outranks prose.**  
   Documentation must match what can be verified.

3. **Separate present, future, and history.**  
   Current state, roadmap, and archive material must never blur together.

4. **One fact should have one canonical owner.**  
   Reference shared facts instead of manually duplicating them.

5. **Make authority visible.**  
   Every source should reveal its status, version, owner, and canonical location.

6. **Test with fresh eyes.**  
   A folder understood only by its creator is not properly documented.

7. **Use automation for facts and judgment for meaning.**  
   Scripts should count and compare; humans should evaluate purpose, boundaries, and tradeoffs.

8. **Treat contradictions as defects.**  
   Conflicting source documents are an engineering risk, not a cosmetic problem.

9. **Do not reward document volume.**  
   Ten accurate, purposeful files are better than fifty generated files nobody maintains.

10. **Reorganize before scaling.**  
    Structural confusion compounds as more agents, features, and contributors are added.

---

## 18. Governing Standard

A project folder is correctly set up only when a competent person or fresh AI agent can determine, without relying on hidden history:

- What the project is
- What it is not
- What exists now
- What is planned
- Where the truth lives
- What should happen next
- How work will be validated
- What risks and constraints apply
