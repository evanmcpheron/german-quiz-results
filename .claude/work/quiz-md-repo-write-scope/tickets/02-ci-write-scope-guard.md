# Add a CI guard that flags quiz-tracking commits touching non-data files

**Type:** Chore
**Repos:** german-quiz-results
**Depends on:** 01-repo-aware-quiz-prompt
**Size:** S

## User Story
As the learner relying on an LLM agent to write directly to this repo, I want a second, technical
line of defense beyond the prompt instructions, so that if an agent ever ignores its instructions and
patches `QUIZ.md` (or another non-data file) instead of the tracker data, CI catches it before I
merge the patch.

## Context
Ticket `01-repo-aware-quiz-prompt` fixes the root cause (missing instructions) but is inherently a
prompt-level guardrail — it cannot force a non-compliant LLM agent to obey it. This ticket adds an
optional, mechanical backstop: a CI check that flags a commit/PR that looks like a "quiz tracking
write" (touches something under `data/`) but also touches a file outside the writable allowlist
defined in `AGENTS.md`'s new `## Write scope` section (added in ticket 01): `QUIZ.md`, `AGENTS.md`,
`README.md`, `manifest.json`, `config/**`, `schemas/**`, `tools/**`, `.github/**`.

This is explicitly optional polish (see "Options considered" in
`.claude/work/quiz-md-repo-write-scope/findings.md`) — the repo is a personal data store with no
branch protection today, and the user may legitimately hand-edit `QUIZ.md` later (e.g., to tune
difficulty pacing), which this check must not block, only flag.

## Acceptance Criteria
AC1 - A new step is added to `.github/workflows/validate-tracker.yml` (or a new workflow file) that
runs on `push` and `pull_request` and inspects the changed file list for the commit/PR.

AC2 - If the changed files include at least one path under `data/` AND at least one path from the
non-writable list (`QUIZ.md`, `AGENTS.md`, `README.md`, `manifest.json`, `config/**`, `schemas/**`,
`tools/**`, `.github/**`), the job prints a clear warning identifying which non-data files were
touched alongside data files.

AC3 - The check is advisory, not blocking: it must not fail the job (exit 0) — this repo has no
branch protection, and the user may deliberately combine a manual doc edit with a data change. The
warning must be visible in the Action run summary/logs regardless.

AC4 - The check has no effect on PRs/pushes that only touch `data/**` (the normal case) or only touch
non-`data/**` files — no warning in either case.

## Implementation Plan
1. Add a small script (e.g., `tools/check_write_scope.py`, dependency-free like
   `tools/validate_tracker.py`) that takes a list of changed file paths (from `git diff --name-only`
   against the merge-base, or `${{ github.event.pull_request.base.sha }}`/`before` SHA on push) and
   applies the AC2 logic.
2. Wire it into `.github/workflows/validate-tracker.yml` as an additional step after checkout, using
   `git diff --name-only` against the appropriate base ref for both `push` and `pull_request` events.
3. Keep the existing `tools/validate_tracker.py` step untouched — this is additive, not a replacement.

## API Contract Changes
None.

## Postman Updates
None.

## Out of Scope
- Making the check blocking/failing the build — explicitly advisory per AC3.
- Branch protection rules requiring the check to pass — not requested, and would contradict AC3's
  advisory intent.
- Any change to `tools/validate_tracker.py`'s existing validation logic.

## Testing Guidance
No existing test harness for GitHub Actions workflows in this repo. Manually verify by pushing a
branch that modifies both a `data/**` file and `QUIZ.md` in the same commit and confirming the
workflow run shows the warning without failing; then push a branch touching only `data/**` and
confirm no warning appears.

## Edge Cases
Commit touches only files outside both `data/**` and the non-writable list (e.g., a new top-level
file) -> no warning; the check only fires on the specific data+non-data combination in AC2.

Initial commit / first push with no prior SHA to diff against -> script should treat this as no
prior state and skip the check rather than erroring (mirrors how `git diff` behaves against an empty
base).

## Open Questions
Blocking: none.

Non-blocking: Should this eventually become blocking once the user is confident in the false-positive
rate? Deferred to a future revisit; ship advisory-only first per AC3.
