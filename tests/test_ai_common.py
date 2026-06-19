"""Tests for ai_common module."""
import configparser

from ai_common import (
    DEFAULT_COMMIT_MESSAGE,
    build_user_prompt,
    extract_commit_message,
    truncate_diff,
)


def test_extract_commit_message_conventional():
    raw = "Here is the message:\nfeat(auth): add OAuth2 flow\n"
    assert extract_commit_message(raw) == "feat(auth): add OAuth2 flow"


def test_extract_commit_message_fallback_line():
    raw = "Some text\nfix(api): resolve timeout\n"
    assert extract_commit_message(raw) == "fix(api): resolve timeout"


def test_extract_commit_message_skips_code_fence():
    raw = "```\nfeat(core): add feature\n```"
    assert extract_commit_message(raw) == "feat(core): add feature"


def test_truncate_diff_within_limit():
    config = configparser.ConfigParser()
    config["DEFAULT"] = {"max_diff_size": "100"}
    assert truncate_diff("short", config) == "short"


def test_truncate_diff_exceeds_limit():
    config = configparser.ConfigParser()
    config["DEFAULT"] = {"max_diff_size": "10"}
    result = truncate_diff("x" * 20, config)
    assert result == "x" * 10 + "\n... (truncated)"


def test_build_user_prompt_contains_status_and_diff():
    prompt = build_user_prompt("M file.txt", "diff content")
    assert "M file.txt" in prompt
    assert "diff content" in prompt
    assert "Conventional Commits" in prompt


def test_default_commit_message():
    assert DEFAULT_COMMIT_MESSAGE == "chore: automatic changes commit"
