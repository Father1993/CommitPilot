"""Tests for ai_common module."""
import configparser

from ai_common import (
    DEFAULT_COMMIT_MESSAGE,
    build_user_prompt,
    changed_paths,
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


def test_extract_commit_message_keeps_body():
    raw = (
        "refactor(config): use openai_compatible for any OpenAI-protocol host\n"
        "\n"
        "Replace vendor-specific aitunnel keys with api_token.\n"
        "Keep legacy aliases for old configs.\n"
    )
    assert extract_commit_message(raw) == (
        "refactor(config): use openai_compatible for any OpenAI-protocol host\n"
        "\n"
        "Replace vendor-specific aitunnel keys with api_token.\n"
        "Keep legacy aliases for old configs."
    )


def test_extract_commit_message_caps_body_lines():
    raw = "feat(api): add rate limit\n\n" + "\n".join(f"line {i}" for i in range(8))
    result = extract_commit_message(raw)
    body = result.split("\n\n", 1)[1]
    assert len(body.splitlines()) == 5


def test_changed_paths_porcelain():
    status = "M  ai_common.py\nA  tests/test_ai_common.py\nR  old.py -> new.py"
    assert changed_paths(status) == [
        "ai_common.py",
        "tests/test_ai_common.py",
        "new.py",
    ]


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
    prompt = build_user_prompt("M  file.txt", "diff content")
    assert "M  file.txt" in prompt
    assert "diff content" in prompt
    assert "file.txt" in prompt
    assert "Conventional Commits" in prompt


def test_default_commit_message():
    assert DEFAULT_COMMIT_MESSAGE == "chore: automatic changes commit"
