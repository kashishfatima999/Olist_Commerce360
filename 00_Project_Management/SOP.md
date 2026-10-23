# Standard Operating Procedures — Olist Commerce360

These procedures apply to all three team members and to AI-assisted work (Claude, ChatGPT).

## 1. Branches and commits
- `main` holds reviewed work only.
- Each member works on a personal branch: `<name>-phase<N>` (e.g. `kashish-phase1`).
- Commits and pushes are made by the human owner of the branch. AI assistants edit files but never commit or push.
- Merge to `main` through a pull request reviewed by at least one other member.
- Commit messages: `<area>: <what changed>`, e.g. `phase1: add grain definition document`.

## 2. Daily log
- One file per working day: `daily_log/YYYY-MM-DD.md`.
- Anyone who changes the repository on that day adds an entry. Use the template below.

```markdown
## <Name or "Claude (for <Name>)"> — <HH:MM>
**Worked on:** <task id from task_board.md>
**Changes:**
- <file> — added / modified / removed — <why>
**Decisions made:** DEC-NNN, ... (or "none")
**Blockers / next:** ...
```

## 3. Decision log (judgment calls)
A decision needs an entry in `decision_log.md` when it affects any of the following:
- table grain, fact or dimension design, keys, or relationships
- the definition of a business measure, such as revenue or "late delivery"
- a data-cleaning or exclusion rule
- how a rubric requirement is interpreted
- tools, folder structure, or the team process

Template:

```markdown
### DEC-NNN — <short title>
- **Date:** YYYY-MM-DD | **Proposed by:** <name> | **Status:** Proposed / Accepted / Rejected / Superseded by DEC-XXX
- **Context:** why a decision is needed (cite data evidence or rubric line)
- **Options considered:** A) ... B) ...
- **Decision:** ...
- **Rationale:** ...
- **Consequences / affected artifacts:** ...
- **Approved by:** <name, date>
```

Rules:
- Number entries sequentially and do not delete them. A reversed decision is marked `Superseded` and a new entry is added.
- A `Proposed` decision may be used in drafts. It must be `Accepted` before the deliverable is submitted.
- Each member should be able to explain every `Accepted` decision at the viva.

## 4. Assumptions and open questions
- Record these in `assumptions_and_questions.md` with an ID (`A-NN` for assumptions, `Q-NN` for questions).
- When an assumption is verified against the data, mark it `Verified` and record the evidence, e.g. a row count or query.

## 5. Data handling
- Raw Kaggle CSVs are kept in `02_Data/raw_data/`, which git ignores. Never edit raw files.
- All cleaning is done in scripts (Phase 2), so results can be reproduced.
- Never put credentials (database passwords, Kaggle tokens) in the repository. Keep them in a local `.env` file, which is also git-ignored.

## 6. Deliverable workflow
1. Draft: author writes the document and the task status becomes `In progress`.
2. Self-check against the acceptance criteria in `01_Project_Documentation/phase1/README.md`.
3. Peer review by the reviewer named in `task_board.md`, with comments in the daily log or on the PR.
4. Consistency check: table names, keys, and grains must match across the documents, diagram, and data dictionary.
5. Export the final file and set the task status to `Done`.

## 7. AI assistance policy
- AI tools may draft, analyse, and generate code.
- A team member must review and understand every AI output before it is accepted.
- AI-made judgment calls are logged like any other decision and stay `Proposed` until a human accepts them.
- Findings must not be fabricated. Anything not checked against the actual data is labelled `[ASSUMPTION]`.

## 8. File naming
- Phase 1 deliverables: `P1_<NN>_<Name>.<ext>`, e.g. `P1_05_Grain_Definition.pdf`.
- Lower-case snake_case for SQL and Python files, e.g. `load_dim_customer.sql`.
- Dates in ISO format (YYYY-MM-DD).
