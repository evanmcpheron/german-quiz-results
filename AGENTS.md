
# AGENTS.md

## Purpose

This repository is designed to be managed by an AI tutor/assessment agent on behalf of the learner. Do not require the learner to edit tracker files manually.

## Required read order before a quiz

When repository access is available, read:

1. `manifest.json`
2. `config/tracking-policy.json`
3. `data/learner-state.json`
4. `data/concept-registry.json`
5. `data/issue-index.json`
6. the current month's quiz log, if it exists
7. prior monthly logs only when needed for history, reconstruction, or weakness verification
8. `QUIZ.md`

Do not load every historical quiz by default. Use the state cache for normal startup and consult historical logs only when needed.

## Write protocol after every completed quiz

After all 10 questions are graded:

1. Create a stable `quiz_id`.
2. Normalize every assessed skill to a stable concept ID in `data/concept-registry.json`.
3. Fetch the current monthly JSONL file.
4. Confirm that `quiz_id` is not already present.
5. Append exactly one quiz record.
6. Update `data/learner-state.json`.
7. Apply the weakness policy in `config/tracking-policy.json`.
8. Create, update, or close GitHub Issues when the policy requires it.
9. Update `data/issue-index.json` to match GitHub.
10. Keep all files valid according to `tools/validate_tracker.py`.

If an update fails midway, the JSONL log is authoritative. Repair derived files from the log rather than changing historical evidence.

## Write scope

The assessment agent may create or modify only the following paths:

- `data/quiz-results/YYYY/YYYY-MM.jsonl` — new monthly quiz-log files, created and appended to per the write protocol above.
- `data/learner-state.json`
- `data/concept-registry.json`
- `data/issue-index.json`
- GitHub Issues, via the GitHub API, per the weakness policy in `config/tracking-policy.json`.

Every other file in this repository is read-only from the assessment agent's perspective, including but not limited to:

- `QUIZ.md`
- `AGENTS.md`
- `README.md`
- `manifest.json`
- everything under `config/`
- everything under `schemas/`
- everything under `tools/`
- everything under `.github/`

Never create, modify, or patch any of these files as part of recording a quiz result. If a change to one of these files genuinely seems necessary, stop and ask the learner instead of writing to it.

## Data integrity rules

- Historical quiz records are append-only.
- Never silently edit an old quiz result.
- If a historical record must be corrected, add a new correction record through an explicit future schema revision rather than rewriting evidence.
- Never fabricate a quiz, answer, score, timestamp, weakness, or mastery result.
- Do not infer completed quiz results from conversational confidence.
- Use ISO 8601 timestamps with an explicit UTC offset.
- Store German text as UTF-8 with correct umlauts and `ß`.
- Each normal quiz round contains exactly 10 scored questions.
- Each question record must store the exact prompt, the learner's answer, the accepted answer, target concept IDs, assessment category, and binary score credit.
- The quiz score must equal the sum of question credit values.
- Concept IDs are permanent once created. Labels may be clarified, but IDs must not be casually renamed.

## Storage rules

### Quiz history

Path:

`data/quiz-results/YYYY/YYYY-MM.jsonl`

Each line is one complete quiz-round JSON object.

Monthly partitioning is mandatory. Do not collapse logs into one global file.

### Current state

`data/learner-state.json` is a cache for efficient quiz startup. It is not authoritative evidence.

Keep it compact. It should summarize:

- broad demonstrated level
- topic-level working level and difficulty
- per-concept attempts and accuracy
- recent performance
- open weakness status
- recent quiz IDs
- next recommended focus

### Concept registry

`data/concept-registry.json` prevents concept-name drift.

Before creating a new concept, check whether an existing concept ID already represents the same underlying skill.

Prefer IDs such as:

- `verbs.present.weak.du`
- `verbs.present.weak.er_sie_es`
- `pronouns.subject.basic`
- `word_order.main_clause.basic`

Use lowercase ASCII IDs with dots and underscores. Human-readable labels may contain German characters.

### GitHub Issues

GitHub Issues are for persistent weaknesses, not individual wrong answers.

Do not create an issue after a single isolated mistake unless an explicit future policy revision requires it.

Use `data/issue-index.json` to prevent duplicate issues for the same concept.

Issue titles should follow:

`Learning: <human-readable concept label>`

Issue bodies should summarize evidence and mastery criteria without exposing unnecessary question text.

## Idempotency

Before appending a result, check for the exact `quiz_id` in the target monthly log.

If it already exists, do not append it again.

When updating an existing weakness issue, use the issue number in `data/issue-index.json` rather than creating a new issue.

## Rebuilding state

If `data/learner-state.json` is missing, invalid, or inconsistent:

1. Read the concept registry.
2. Read quiz logs in chronological order.
3. Recompute topic and concept statistics.
4. Reapply the current tracking policy.
5. Recreate learner state.
6. Reconcile issue index with actual GitHub Issues when issue access is available.

Never treat a corrupted cache as evidence that historical performance changed.

## Repository changes

Prefer small, descriptive commits.

Examples:

- `Record quiz 2026-08-19 weak verb conjugation`
- `Update learner state after quiz`
- `Track persistent weakness: du weak-verb ending`
- `Resolve mastered weakness: du weak-verb ending`

Do not make unrelated repository changes during quiz tracking.
