
# German Quiz Tracker

This repository is the persistent data store for an adaptive German-learning quiz system.

## Design

The repository uses a hybrid text-based model:

- **Monthly JSONL quiz logs** are the authoritative historical record.
- **`learner-state.json`** is a small, rebuildable snapshot used to start future quizzes efficiently.
- **`concept-registry.json`** provides stable concept IDs so the same weakness is not recorded under inconsistent names.
- **`issue-index.json`** maps persistent learning weaknesses to GitHub Issues.
- **GitHub Issues** are the actionable tracking layer for weaknesses that persist across quiz rounds.

SQLite is intentionally not used. A SQLite database is binary, produces poor Git diffs, and is less practical for connector-based file updates. Monthly JSONL files keep individual updates small while preserving append-only history.

## Source-of-truth order

If files disagree, use this order:

1. Monthly JSONL quiz logs
2. Concept registry
3. GitHub Issues and issue index
4. Learner-state cache

`learner-state.json` may always be rebuilt from the quiz logs.

## Quiz result location

A completed quiz is appended to:

`data/quiz-results/YYYY/YYYY-MM.jsonl`

Example:

`data/quiz-results/2026/2026-08.jsonl`

One completed 10-question quiz round equals one JSON object on one line.

Do not create one file per quiz. Do not maintain one unbounded multi-year JSON file.

## Autonomous management

The user is not expected to maintain this repository manually. AI agents managing quizzes should read `AGENTS.md` before changing tracker data.

`QUIZ.md` is the quiz behavior prompt. The bootstrap copy is the version supplied before repository integration; it can later be replaced with a repository-aware version.

## Validation

`tools/validate_tracker.py` performs dependency-free integrity checks.

GitHub Actions runs the validator automatically on pushes and pull requests that affect tracker files.
