#!/usr/bin/env python3
"""Dependency-free integrity checks for the German Quiz Tracker."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_JSON_FILES = [
    ROOT / "manifest.json",
    ROOT / "config" / "repository.json",
    ROOT / "config" / "tracking-policy.json",
    ROOT / "data" / "learner-state.json",
    ROOT / "data" / "concept-registry.json",
    ROOT / "data" / "issue-index.json",
]

VALID_ASSESSMENTS = {
    "correct",
    "incorrect",
    "understandable_but_grammatically_incorrect",
    "grammatically_acceptable_but_unnatural",
}

VALID_RESULTS = {
    "difficulty_passed_next_harder",
    "remain_current_difficulty",
    "difficulty_will_be_reduced",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing required file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as error:
        fail(f"Invalid JSON in {path.relative_to(ROOT)}: {error}")


def validate_base_files() -> tuple[set[str], dict]:
    for path in REQUIRED_JSON_FILES:
        load_json(path)

    concept_registry = load_json(ROOT / "data" / "concept-registry.json")
    concept_ids = set(concept_registry.get("concepts", {}).keys())

    learner_state = load_json(ROOT / "data" / "learner-state.json")
    state_concept_ids = set(learner_state.get("concepts", {}).keys())
    unknown_state = state_concept_ids - concept_ids
    if unknown_state:
        fail(f"Learner state references unknown concept IDs: {sorted(unknown_state)}")

    issue_index = load_json(ROOT / "data" / "issue-index.json")
    issue_concept_ids = set(issue_index.get("issues_by_concept", {}).keys())
    unknown_issues = issue_concept_ids - concept_ids
    if unknown_issues:
        fail(f"Issue index references unknown concept IDs: {sorted(unknown_issues)}")

    return concept_ids, learner_state


def validate_quiz_record(record: dict, path: Path, line_number: int, concept_ids: set[str]) -> str:
    location = f"{path.relative_to(ROOT)} line {line_number}"

    required = {
        "schema_version",
        "quiz_id",
        "completed_at",
        "topic",
        "level",
        "difficulty",
        "score",
        "max_score",
        "result",
        "questions",
        "strength_concept_ids",
        "review_concept_ids",
        "next_focus_concept_ids",
    }
    missing = required - set(record)
    if missing:
        fail(f"{location}: missing fields {sorted(missing)}")

    quiz_id = record["quiz_id"]
    if not isinstance(quiz_id, str) or not quiz_id:
        fail(f"{location}: quiz_id must be a non-empty string")

    if record["max_score"] != 10:
        fail(f"{location}: max_score must be 10")

    if record["result"] not in VALID_RESULTS:
        fail(f"{location}: invalid result value")

    questions = record["questions"]
    if not isinstance(questions, list) or len(questions) != 10:
        fail(f"{location}: questions must contain exactly 10 items")

    expected_numbers = list(range(1, 11))
    actual_numbers = [question.get("number") for question in questions]
    if actual_numbers != expected_numbers:
        fail(f"{location}: question numbers must be exactly 1 through 10 in order")

    calculated_score = 0
    referenced_concepts: set[str] = set()

    for question in questions:
        assessment = question.get("assessment")
        if assessment not in VALID_ASSESSMENTS:
            fail(f"{location}: invalid assessment {assessment!r}")

        credit = question.get("credit")
        if credit not in (0, 1):
            fail(f"{location}: question credit must be 0 or 1")
        calculated_score += credit

        if not isinstance(question.get("prompt"), str) or not question["prompt"]:
            fail(f"{location}: every question must store its prompt")
        if not isinstance(question.get("accepted_answer"), str) or not question["accepted_answer"]:
            fail(f"{location}: every question must store an accepted answer")

        targets = question.get("target_concept_ids")
        if not isinstance(targets, list) or not targets:
            fail(f"{location}: every question must have at least one target concept ID")
        referenced_concepts.update(targets)

    if record["score"] != calculated_score:
        fail(
            f"{location}: score is {record['score']} but question credits sum to {calculated_score}"
        )

    if not 0 <= record["score"] <= 10:
        fail(f"{location}: score must be between 0 and 10")

    all_summary_concepts = set()
    for field in ("strength_concept_ids", "review_concept_ids", "next_focus_concept_ids"):
        value = record[field]
        if not isinstance(value, list):
            fail(f"{location}: {field} must be a list")
        all_summary_concepts.update(value)

    unknown = (referenced_concepts | all_summary_concepts) - concept_ids
    if unknown:
        fail(f"{location}: references unknown concept IDs: {sorted(unknown)}")

    return quiz_id


def validate_logs(concept_ids: set[str]) -> None:
    seen_quiz_ids: set[str] = set()
    log_root = ROOT / "data" / "quiz-results"

    for path in sorted(log_root.rglob("*.jsonl")):
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                fail(f"{path.relative_to(ROOT)} line {line_number}: invalid JSON: {error}")

            if not isinstance(record, dict):
                fail(f"{path.relative_to(ROOT)} line {line_number}: record must be an object")

            quiz_id = validate_quiz_record(record, path, line_number, concept_ids)
            if quiz_id in seen_quiz_ids:
                fail(f"Duplicate quiz_id found: {quiz_id}")
            seen_quiz_ids.add(quiz_id)


def main() -> int:
    concept_ids, _ = validate_base_files()
    validate_logs(concept_ids)
    print("Tracker validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
