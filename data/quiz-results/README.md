
# Quiz Result Logs

Completed quiz rounds are stored as monthly JSON Lines files:

`YYYY/YYYY-MM.jsonl`

Example:

`2026/2026-08.jsonl`

Each non-empty line is one complete quiz result object.

The first quiz completed in a month creates that month's file. This directory intentionally contains no empty `.jsonl` bootstrap file.

Historical records are append-only.
