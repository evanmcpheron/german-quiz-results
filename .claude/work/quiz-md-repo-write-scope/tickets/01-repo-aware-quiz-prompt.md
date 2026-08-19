# Make QUIZ.md repository-aware and give the tracking agent an explicit write scope

**Type:** Bug
**Repos:** german-quiz-results
**Depends on:** Nothing
**Size:** S

## User Story
As the learner using this repo as the persistent store behind my ChatGPT German-tutor project, I
want the quiz prompt I paste into the conversation to know how to read and write the tracker data in
this repo, so that completed quiz results land in `data/quiz-results/`, `data/learner-state.json`,
`data/concept-registry.json`, and `data/issue-index.json` — never in `QUIZ.md` itself.

## Context
`QUIZ.md` is the only file the user actually references as "the prompt" inside the ChatGPT project.
As written, it contains zero mention of this repository, `AGENTS.md`, `manifest.json`, or the
read/write protocol — confirmed by grep across `QUIZ.md` for repo/write-related terms (one false
positive: "preposition" substring-matches "repo"). All of the repo-integration contract lives in
`AGENTS.md`, a separate file `QUIZ.md` never points to (`AGENTS.md:8-19` read order,
`AGENTS.md:23-36` write protocol). `README.md:47` already documents this exact gap: *"The bootstrap
copy is the version supplied before repository integration; it can later be replaced with a
repository-aware version."*

`QUIZ.md` also opens with a literal "Fill in the Blank" header (`QUIZ.md:1-9`) containing unfilled
placeholder fields (`[ENTER GERMAN TOPIC]`, etc.). With no instruction telling the agent otherwise,
and with repo-write access available, an agent naturally treats the one file it was told to read as
the one file it's allowed to edit — which is exactly the reported symptom: the write "patch" targets
`QUIZ.md` instead of the tracker data files.

Separately, `AGENTS.md` currently has no explicit, enumerated write-scope list. The closest thing is
the vague `AGENTS.md:141` line ("Do not make unrelated repository changes during quiz tracking.")
and the implicit `storage_model` list in `manifest.json:5-11`. Neither explicitly forbids touching
`QUIZ.md`, `AGENTS.md`, `README.md`, `config/**`, `schemas/**`, `tools/**`, or `.github/**`.

See `.claude/work/quiz-md-repo-write-scope/findings.md` for the full trace.

## Acceptance Criteria
AC1 - `QUIZ.md` contains an explicit instruction that, when repository file access is available in
the session, the agent must follow the read/write protocol defined in `AGENTS.md` for loading
learner state before a round and recording results after a round.

AC2 - `QUIZ.md` contains an explicit instruction that `QUIZ.md` itself must never be created,
modified, or patched by the assessment agent under any circumstance — it is a static behavior prompt,
not a data file.

AC3 - `QUIZ.md` clarifies that the Topic / Level / Starting Difficulty / Special Instructions fields
in its header (`QUIZ.md:1-9`) are session input supplied by the user (via the header text as pasted,
or via a chat message) and are never something the agent fills in and writes back to this file.

AC4 - `QUIZ.md` states the fallback behavior when no repository file access is available in a given
session: the agent must say so plainly and proceed with the quiz using only in-conversation memory,
rather than inventing a persistence target.

AC5 - `AGENTS.md` contains an explicit, enumerated write-scope section listing the only paths the
agent may create or modify: `data/quiz-results/YYYY/YYYY-MM.jsonl` (new monthly files), `data/
learner-state.json`, `data/concept-registry.json`, `data/issue-index.json`, and GitHub Issues
(external, via the API). The same section explicitly states that every other file in the repository
— including but not limited to `QUIZ.md`, `AGENTS.md`, `README.md`, `manifest.json`, `config/**`,
`schemas/**`, `tools/**`, `.github/**` — is read-only from the assessment agent's perspective.

AC6 - `README.md:47`'s "bootstrap copy ... supplied before repository integration" note is updated
so it no longer contradicts the now-repository-aware `QUIZ.md` (either removed or reworded to
reflect that the repository-aware version has shipped).

## Implementation Plan
1. Edit `QUIZ.md`: add a short new subsection (placed near section 19, "Beginning the Assessment",
   or as an early section before section 1) covering AC1–AC4. Keep it terse and imperative to match
   the existing style of the rest of the file (e.g., section 9's "Do Not Give Feedback During the
   Round" bullet style).
2. Edit `AGENTS.md`: add a new `## Write scope` section (near the existing "Write protocol after
   every completed quiz" and "Repository changes" sections) enumerating the writable paths from
   `manifest.json`'s `storage_model` (`manifest.json:5-11`) plus GitHub Issues, and explicitly listing
   the non-writable paths per AC5. Keep the existing "Repository changes" section's commit-message
   guidance as-is; this is additive.
3. Edit `README.md`: update or remove the sentence at `README.md:47` referring to the "bootstrap
   copy" so it reflects the shipped repository-aware `QUIZ.md`.
4. Re-read all three files together once done to confirm no contradictions (e.g., `AGENTS.md`'s read
   order at `AGENTS.md:8-19` still lists `QUIZ.md` as item 8 — leave that as-is, it's still correct
   that the agent should read the prompt; only the write side changes).

## API Contract Changes
None — this repo has no API surface.

## Postman Updates
None.

## Out of Scope
- The optional CI write-scope guard (separate ticket `02-ci-write-scope-guard`).
- Setting `config/repository.json`'s `repository_full_name` (`config/repository.json:3`, currently
  `null`) — that's a separate configuration step for whoever wires up the ChatGPT-side connector, not
  part of this ticket's fix.
- Any change to the quiz pedagogy content in `QUIZ.md` sections 1–18 (question design, difficulty
  progression, etc.) — this ticket only adds repo-awareness and write-scope instructions.
- Any change to `data/*.json` schemas or `tools/validate_tracker.py`.

## Testing Guidance
No automated test covers prompt text. Manual verification: paste the updated `QUIZ.md` into a fresh
ChatGPT session with repo access, start a quiz, complete a round, and confirm (a) the resulting patch
touches only `data/quiz-results/<month>.jsonl` and/or `data/learner-state.json` /
`data/concept-registry.json` / `data/issue-index.json`, (b) `QUIZ.md` is untouched, and (c)
`python tools/validate_tracker.py` still passes after the write.

## Edge Cases
No repository access available this session -> agent states that persistence is unavailable and
proceeds with the quiz in-conversation only (AC4), rather than inventing a target file.

User pastes an older, un-patched copy of `QUIZ.md` (before this fix) -> out of scope; this ticket
only fixes the canonical copy in this repo going forward.

Agent has repo access but the monthly JSONL file for the current month doesn't exist yet -> already
covered by existing behavior (`data/quiz-results/README.md:14`, `AGENTS.md:23-36` step 3): the file
is created on first write that month. No change needed here.

## Open Questions
Blocking: none.

Non-blocking: Should the AC5 write-scope list also be duplicated into `manifest.json` as a formal
field (e.g., `writable_paths`) so `tools/validate_tracker.py` could someday check it mechanically?
Deferred — `manifest.json`'s existing `storage_model` already implies this list; duplicating it as
prose in `AGENTS.md` is enough for the immediate fix. Revisit if ticket 02 is picked up.
