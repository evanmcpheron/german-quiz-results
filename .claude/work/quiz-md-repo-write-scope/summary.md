# PR Summary: Make QUIZ.md repository-aware and give the tracking agent an explicit write scope

**Ticket:** `.claude/work/quiz-md-repo-write-scope/tickets/01-repo-aware-quiz-prompt.md`
**Status: Complete**

## What changed
`QUIZ.md` — the file pasted into the ChatGPT project as the master prompt — previously contained no
reference to this repository, `AGENTS.md`, or any read/write protocol, and opened with an
unfilled "Fill in the Blank" header. With repo-write access but no instructions about where to
write, an agent would default to editing the one file it was told to read: `QUIZ.md` itself, instead
of the tracker data under `data/`.

- **`QUIZ.md`** — added a new `## 0. Repository Integration and Write Scope` section (before the
  existing `## 1.` section, no renumbering needed — no other section referenced section numbers).
  It tells the agent to follow `AGENTS.md`'s protocol when repo access is available, to never
  create/modify/patch `QUIZ.md` itself, that the header's Topic/Level/Difficulty/Special
  Instructions fields are session input and not something to persist back into the file, and what
  to do (state it plainly, proceed in-conversation only) when no repo access is available.
- **`AGENTS.md`** — added a new `## Write scope` section between the existing write protocol and
  the data-integrity rules, enumerating the only paths the agent may create or modify (the monthly
  JSONL logs, `learner-state.json`, `concept-registry.json`, `issue-index.json`, GitHub Issues) and
  explicitly marking every other path (`QUIZ.md`, `AGENTS.md`, `README.md`, `manifest.json`,
  `config/**`, `schemas/**`, `tools/**`, `.github/**`) read-only from the agent's perspective.
- **`README.md`** — replaced the stale "bootstrap copy... can later be replaced with a
  repository-aware version" note (which this ticket fulfills) with a statement that `QUIZ.md` is now
  repository-aware and is never itself a write target.

## Acceptance criteria
- AC1 (point to AGENTS.md's protocol) — `QUIZ.md:27`
- AC2 (never edit QUIZ.md) — `QUIZ.md:28`
- AC3 (header fields are session input) — `QUIZ.md:30`
- AC4 (fallback with no repo access) — `QUIZ.md:32-35`
- AC5 (explicit write-scope allowlist/denylist in AGENTS.md) — `AGENTS.md:40-61`
- AC6 (README's stale note updated) — `README.md:47`

All six satisfied.

## Gates
- **Test & Lint Gate:** No `package.json`, lint config, or CLAUDE.md exists in this repo (noted per
  precedence rules — platform facts normally sourced from CLAUDE.md are absent here). The only
  automated check is `tools/validate_tracker.py`, run after the edits:
  `python3 tools/validate_tracker.py` → `Tracker validation passed.` (exit 0). It doesn't cover
  markdown, but confirms the untouched JSON tracker files remain valid.
- **Unit Test Gate:** Does not fire — no logic changed, only markdown instruction text.
- **API Contract Gate:** Does not fire — this repo has no API/service surface.
- **Manual Verification Gate:** Skipped. The runtime behavior this ticket changes (what an LLM
  agent does with repo-write access in a live ChatGPT session) can only be observed inside such a
  session, which isn't launchable from here. The ticket's own Testing Guidance anticipated this and
  specifies the same check: paste the updated `QUIZ.md` into a fresh session with repo access,
  complete a round, and confirm the resulting patch touches only `data/**` files while `QUIZ.md`
  remains untouched. That step is on the user to run.

## Out of scope (per ticket)
- The optional CI write-scope guard (ticket `02-ci-write-scope-guard`) — not implemented, separate
  ticket by design.
- `config/repository.json`'s `repository_full_name` (still `null`) — unrelated connector-configuration
  step, not part of this ticket.
- No changes to quiz pedagogy content (`QUIZ.md` sections 1–18), schemas, or `tools/validate_tracker.py`.

## Files changed
- `QUIZ.md` (+16 lines)
- `AGENTS.md` (+23 lines)
- `README.md` (1 line changed)

## Completion status: Complete
Implemented, and every gate that fired passed. The one gate that didn't fire in the traditional
sense — Manual Verification — requires a live ChatGPT session the user needs to run themselves; the
exact verification steps are documented above and in the ticket's Testing Guidance.
