# Research: QUIZ.md gets patched instead of the tracker data files

## Request
The user pastes `QUIZ.md` as the "master prompt" into a ChatGPT project that has (some form of)
write access back to this repo. When the assistant tries to persist a completed quiz, the patch it
produces edits `QUIZ.md` itself rather than the tracker data files under `data/`. The user wants the
repo set up so the intended target of any write is the actual tracker data, not the prompt file.
Classification: **bug** (the repo's own instruction set does not produce the documented behavior).

## Summary
`QUIZ.md` — the only file the user actually references as "the prompt" — contains zero mention of
this repository, `AGENTS.md`, `manifest.json`, or any read/write protocol; it is a pure quiz-behavior
prompt (`QUIZ.md:1-427`). All of the repo-integration logic (required read order, write protocol,
write scope) lives in `AGENTS.md`, a separate file `QUIZ.md` never points to. `README.md:47`
confirms this directly: *"The bootstrap copy is the version supplied before repository integration;
it can later be replaced with a repository-aware version."* — i.e., the repo's own docs already flag
that the current `QUIZ.md` is not yet wired to the tracking system. Nothing in either file states
that `QUIZ.md` is off-limits for writes, and nothing enumerates which files an agent may write to.
When an agent with repo-write access decides to "save" something and the only file it was told to
read is `QUIZ.md`, editing `QUIZ.md` is the path of least resistance — reinforced by the fact that
`QUIZ.md` literally opens with a "Fill in the Blank" template (`QUIZ.md:1-9`) containing unfilled
bracket placeholders, which reads like an invitation to edit.

## Current behavior
- `QUIZ.md:1-9` is a literal fill-in-the-blank header (`# Fill in the Blank`) with placeholder
  fields `[ENTER GERMAN TOPIC]`, `[Auto | A1.1 | ...]`, `[Easy | Moderate | Hard | Auto]`,
  `[None, or enter any additional constraints]`.
- `QUIZ.md` section 19 (`QUIZ.md:415-427`) tells the model to "read the configuration at the top of
  this prompt" before starting — the only self-reference in the whole file. No other file is named.
- Grep of `QUIZ.md` for `AGENTS|manifest|data/|learner-state|concept-registry|quiz-results|repo|
  commit|github|jsonl|write protocol|append` returns one match, and it's a false positive
  (`"preposition"` contains the substring `"repo"`). Confirmed: **no real references exist.**
- `AGENTS.md:8-19` defines the required read order (manifest → tracking-policy → learner-state →
  concept-registry → issue-index → monthly log → `QUIZ.md` last) and `AGENTS.md:23-36` defines the
  write protocol (append to the monthly JSONL, update `learner-state.json`, apply weakness policy,
  touch GitHub Issues, update `issue-index.json`). This is the correct, well-designed contract — but
  it lives entirely in a file `QUIZ.md` never mentions.
- `AGENTS.md:141` ("Do not make unrelated repository changes during quiz tracking.") is the closest
  thing to a write-scope restriction that exists anywhere in the repo, and it's advisory/vague
  enough that an LLM could rationalize filling in `QUIZ.md`'s own header fields as "related" to quiz
  tracking, since that's literally the session's config.
- `manifest.json:5-11` (`storage_model`) names exactly four writable targets (monthly JSONL,
  `learner-state.json`, `concept-registry.json`, `issue-index.json`) but nothing marks the remaining
  files (`QUIZ.md`, `AGENTS.md`, `README.md`, `config/**`, `schemas/**`, `tools/**`, `.github/**`) as
  explicitly non-writable.
- `README.md:47` already predicts this exact gap: the shipped `QUIZ.md` is called a "bootstrap copy
  ... supplied before repository integration."

## Root cause
`QUIZ.md` was never updated to the "repository-aware version" `README.md:47` says should eventually
replace the bootstrap copy. It has no instruction telling the agent (a) that `AGENTS.md` exists and
governs persistence, (b) which files are the actual write targets, or (c) that `QUIZ.md` itself must
never be modified. Combined with `QUIZ.md`'s own editable-looking header, an agent with repo-write
access defaults to treating the one file it was told to read as the one file it's allowed to touch.

## Affected surface area
Single repo (`german-quiz-results`), docs/prompt files only — no application code:
- `QUIZ.md` — needs an explicit pointer to `AGENTS.md`'s protocol and an explicit
  "never edit this file" instruction, plus clarification that the header fields are session input,
  not persisted state.
- `AGENTS.md` — needs an explicit enumerated write-scope allowlist/denylist (currently only implied
  by `manifest.json`'s `storage_model` and one vague sentence).
- `README.md` — its "bootstrap copy" note (`README.md:47`) becomes stale once `QUIZ.md` is made
  repository-aware and should be updated to avoid contradicting the fix.

No other repo (this is a single-repo, docs-only fix).

## Existing patterns to follow
- `AGENTS.md`'s existing structure (numbered protocol lists, `##` sections) is the right place to add
  a write-scope section — follow its existing terse, imperative style (see `AGENTS.md:40-52` "Data
  integrity rules" for the tone to match).
- `manifest.json`'s `storage_model` (`manifest.json:5-11`) is the existing enumeration of writable
  paths and should be treated as the source list for the new explicit allowlist rather than
  redefining it differently.

## API contract impact
None — this repo has no API/service surface; it's a static data store read/written by an external
LLM agent. Not applicable.

## Data and migration impact
None. No schema, storage path, or data shape changes. This is a prompt/instruction-text fix only.

## Test coverage today
`tools/validate_tracker.py` (run in CI via `.github/workflows/validate-tracker.yml`) validates JSON
shape and cross-references of the four data files and quiz logs — it has no coverage of which files
an agent is allowed to write to, and can't, since that's an instruction-following concern, not a data
shape concern. No test would need to change for this fix; a new lightweight CI check could be added
(see ticket 02 below) but is optional polish, not required for the core fix.

## Options considered
**Where to put the write-scope guardrail:**
1. **Prompt-only fix (recommended):** add explicit instructions to `QUIZ.md` (pointer to `AGENTS.md`
   + "never edit this file") and an explicit allowlist/denylist to `AGENTS.md`. Cheap, matches the
   repo's existing design (instructions-as-contract), and directly closes the gap `README.md:47`
   already flagged as pending work.
2. **Technical CI guard:** a GitHub Action that fails a PR/commit if it touches both a data path and
   a non-data path (or touches `QUIZ.md`/`AGENTS.md`/etc. at all) in what looks like a quiz-tracking
   commit. More robust against a misbehaving agent, but heavier, and this repo has no branch
   protection or PR-gating today (only a validation job) — behavioral enforcement of "which commit
   is a quiz-tracking commit" is inherently fuzzy since the user could legitimately edit `QUIZ.md`
   by hand later (e.g., to tune difficulty pacing).

Recommendation: do option 1 as the required fix (it's the direct cause), and offer option 2 as a
separate, optional ticket since it's real but non-essential belt-and-suspenders.

## Constraints and risks
- This fix only changes what instructions say; it cannot force a non-compliant LLM agent to obey
  them. It closes the documented gap but is not a hard technical guarantee. Flagged directly in the
  ticket's Open Questions.
- `config/repository.json:3` (`repository_full_name: null`) is still unset. Whether/how the ChatGPT
  project's repo-connector actually resolves which GitHub repo to write to is a ChatGPT-side setup
  question this repo's files can't answer from static inspection — flagged as a non-blocking open
  question, not part of the root cause (the wrong-file-edited symptom is explained fully by the
  `QUIZ.md` gap above regardless of connector wiring).

## Open questions
**Blocking:** none — the fix is self-contained within this repo's docs.

**Non-blocking:**
- Does the user want the optional CI write-scope guard (ticket 02) or is the prompt-level fix
  sufficient on its own? Assumption: prompt-level fix only, ship first; CI guard is separate/optional.
- Is `config/repository.json`'s `repository_full_name` still meant to be filled in, and does the
  ChatGPT-side connector actually consume it? Unknown from this repo alone — ask the user how their
  ChatGPT project is currently wired to this repo (uploaded file vs. live connector vs. Codex-style
  agent) to confirm the fix in ticket 01 is sufficient once the connector points at a real repo.

## Suggested ticket slicing
- `01-repo-aware-quiz-prompt` — make `QUIZ.md` repository-aware (pointer to `AGENTS.md`, explicit
  "never edit this file" instruction, header-fields-are-session-input clarification) and add an
  explicit write-scope allowlist/denylist to `AGENTS.md`, updating `README.md`'s stale "bootstrap
  copy" note to match. Depends on: nothing. Repos: german-quiz-results. Reason for being its own
  ticket: this is the complete, required fix — one vertical slice, one PR.
- `02-ci-write-scope-guard` — optional GitHub Action that flags a commit/PR touching both tracker
  data and non-data files in a way that looks like an unintended quiz-tracking write. Depends on:
  01. Repos: german-quiz-results. Reason for being separate: explicitly optional polish per the
  Options-considered section, not required to fix the reported symptom.

## Confidence
High. The root cause is directly verified by reading `QUIZ.md` in full (no repo/write references
exist, confirmed by grep with a checked false positive), reading `AGENTS.md`'s write protocol in
full, and reading `README.md:47`'s own acknowledgment that the shipped `QUIZ.md` is a pre-integration
bootstrap copy. No inference required for the core claim.
