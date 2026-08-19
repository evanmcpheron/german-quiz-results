# PR Summary: Add a CI guard that flags quiz-tracking commits touching non-data files

**Ticket:** `.claude/work/quiz-md-repo-write-scope/tickets/02-ci-write-scope-guard.md`
**Status: Complete**

## What changed
Added an advisory, dependency-free CI check that warns (never fails) when a commit/PR touches
tracker data under `data/` alongside a file outside the write scope defined in `AGENTS.md`
(`QUIZ.md`, `AGENTS.md`, `README.md`, `manifest.json`, `config/**`, `schemas/**`, `tools/**`,
`.github/**`). This is the technical backstop behind ticket 01's prompt-level fix.

- **`tools/check_write_scope.py`** (new) — pure functions `is_non_writable(path)` and
  `find_violations(changed_files)` implement the AC2 logic; `main()` reads `BASE_SHA`/`HEAD_SHA`
  from the environment, skips (exit 0) when there's no prior commit to diff against (new branch's
  first push, where GitHub sets `before` to the all-zero SHA), otherwise shells out to
  `git diff --name-only` and prints a warning listing the offending files. Always exits 0 — it never
  fails the build, per AC3.
- **`tools/test_check_write_scope.py`** (new) — stdlib `unittest` covering `is_non_writable` (exact
  top-level matches, nested directory-prefix matches, data paths excluded, unrelated files excluded)
  and `find_violations` (data+non-data flagged, data-only clean, non-data-only clean, empty change
  set clean, unrelated file alongside data clean, multiple violations reported sorted). 10 tests, all
  passing. This is the first test file in the repo — added because the new logic in
  `check_write_scope.py` needed one; `tools/validate_tracker.py` was left untouched.
- **`.github/workflows/validate-tracker.yml`** — added `tools/check_write_scope.py` to both `push`
  and `pull_request` path filters, set `fetch-depth: 0` on the checkout step (required so arbitrary
  base/head SHAs are available locally for `git diff`), and added a new "Check write scope
  (advisory)" step after the existing validator, passing `BASE_SHA`/`HEAD_SHA` from the appropriate
  GitHub event fields (`github.event.pull_request.base.sha` for PRs, `github.event.before` for
  pushes).

## Acceptance criteria
- AC1 (new step in the workflow, runs on push and pull_request) — `.github/workflows/
  validate-tracker.yml:38-42`
- AC2 (flag data + non-writable combination with a clear warning) — `tools/
  check_write_scope.py:find_violations` + `main()`'s warning block; unit-tested directly
  (`test_data_plus_non_writable_file_is_flagged`, `test_multiple_non_writable_files_are_all_
  reported_sorted`)
- AC3 (advisory only, exit 0 always) — `main()` always `return 0`; no branch raises or exits
  non-zero
- AC4 (no effect on data-only or non-data-only changes) — unit-tested
  (`test_data_only_is_not_flagged`, `test_non_writable_only_without_data_is_not_flagged`)

All four satisfied.

## Gates
- **Test & Lint Gate:** No lint config in this repo (confirmed in ticket 01's summary — no
  `package.json`, no CLAUDE.md). `python3 -m py_compile tools/check_write_scope.py
  tools/test_check_write_scope.py` → compiles clean. `python3 tools/validate_tracker.py` →
  `Tracker validation passed.` (unaffected, per the ticket's "keep validate_tracker.py untouched").
- **Unit Test Gate:** Fired — new logic in `check_write_scope.py`. `python3
  tools/test_check_write_scope.py -v` → 10/10 passed.
- **API Contract Gate:** Does not fire — no API surface.
- **Manual Verification Gate:** Partially run, partially blocked — see below.

## Manual verification
Ran directly against real commits/values, read-only, no repo mutation:
- `BASE_SHA=abb23a4 HEAD_SHA=8c95b93 python3 tools/check_write_scope.py` (the repo's real two
  commits — neither touches `data/`) → `check_write_scope: no write-scope violations found.`,
  exit 0. Confirms the subprocess `git diff` plumbing and env-var reading work end to end.
- `BASE_SHA=0000...0000 HEAD_SHA=8c95b93` → `check_write_scope: no prior commit to diff against,
  skipping.`, exit 0. Confirms the null-SHA skip path (new-branch first push).
- `BASE_SHA="" HEAD_SHA=""` → same skip message, exit 0. Confirms the empty-env-var fallback.

**Blocked:** the "violation found and printed" branch's exact CLI output (as opposed to the
`find_violations` logic behind it, which the unit tests exercise directly) was not run against a
real `git diff` of two commits that actually mix a `data/**` change with a non-writable file,
because building that pair requires creating commits in a scratch repo, and that command was denied
when I attempted it. The `main()` warning-printing code is a thin, directly-inspectable loop over
`find_violations`'s already-unit-tested output, so the risk here is low, but it is not the same as
having watched it print. If you'd like this closed out, the fastest path is: on a throwaway local
branch, touch `data/learner-state.json` and `QUIZ.md` in the same commit, then run
`BASE_SHA=<parent> HEAD_SHA=<that commit> python3 tools/check_write_scope.py` yourself, or just push
such a branch and watch the Action run.

## Out of scope (per ticket)
- Making the check blocking, or adding branch protection — explicitly advisory only per AC3.
- Any change to `tools/validate_tracker.py`'s existing logic.

## Files changed
- `tools/check_write_scope.py` (new, 71 lines)
- `tools/test_check_write_scope.py` (new, 47 lines)
- `.github/workflows/validate-tracker.yml` (+9/-0 lines, modified)

## Completion status: Implemented, verification blocked
All four acceptance criteria are met and unit-tested. The one gap is that the CLI's exact printed
warning output was not observed against a live `git diff` mixing a data and non-data file in the
same commit — that specific scenario is fully covered by unit tests against `find_violations`
directly, but the end-to-end CLI print path for that branch specifically was not exercised, because
the scratch-repo commit needed to construct it was denied. Everything else — the logic, the other
three CLI paths, `py_compile`, and `validate_tracker.py` regression — was run and passed.
