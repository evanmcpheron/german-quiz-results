#!/usr/bin/env python3
"""Unit tests for tools/check_write_scope.py. Run directly: python tools/test_check_write_scope.py"""

import unittest

from check_write_scope import find_violations, is_non_writable


class IsNonWritableTests(unittest.TestCase):
    def test_exact_top_level_file_matches(self):
        self.assertTrue(is_non_writable("QUIZ.md"))
        self.assertTrue(is_non_writable("AGENTS.md"))
        self.assertTrue(is_non_writable("README.md"))
        self.assertTrue(is_non_writable("manifest.json"))

    def test_nested_paths_under_directory_prefixes_match(self):
        self.assertTrue(is_non_writable("config/tracking-policy.json"))
        self.assertTrue(is_non_writable("schemas/quiz-result.schema.json"))
        self.assertTrue(is_non_writable("tools/validate_tracker.py"))
        self.assertTrue(is_non_writable(".github/workflows/validate-tracker.yml"))

    def test_data_paths_do_not_match(self):
        self.assertFalse(is_non_writable("data/learner-state.json"))
        self.assertFalse(is_non_writable("data/quiz-results/2026/2026-08.jsonl"))

    def test_unrelated_top_level_file_does_not_match(self):
        self.assertFalse(is_non_writable("some-new-file.txt"))


class FindViolationsTests(unittest.TestCase):
    def test_data_plus_non_writable_file_is_flagged(self):
        changed = ["data/learner-state.json", "QUIZ.md"]
        self.assertEqual(find_violations(changed), ["QUIZ.md"])

    def test_data_only_is_not_flagged(self):
        changed = ["data/learner-state.json", "data/quiz-results/2026/2026-08.jsonl"]
        self.assertEqual(find_violations(changed), [])

    def test_non_writable_only_without_data_is_not_flagged(self):
        changed = ["QUIZ.md", "AGENTS.md"]
        self.assertEqual(find_violations(changed), [])

    def test_empty_change_set_is_not_flagged(self):
        self.assertEqual(find_violations([]), [])

    def test_unrelated_top_level_file_alongside_data_is_not_flagged(self):
        changed = ["data/learner-state.json", "some-new-file.txt"]
        self.assertEqual(find_violations(changed), [])

    def test_multiple_non_writable_files_are_all_reported_sorted(self):
        changed = ["data/learner-state.json", "README.md", "AGENTS.md"]
        self.assertEqual(find_violations(changed), ["AGENTS.md", "README.md"])


if __name__ == "__main__":
    unittest.main()
