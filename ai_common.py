#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shared AI commit message generation utilities."""

import logging
import configparser

try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    import requests

logger = logging.getLogger(__name__)

DEFAULT_COMMIT_MESSAGE = "chore: automatic changes commit"
COMMIT_PREFIXES = frozenset(["feat", "fix", "docs", "style", "refactor", "test", "chore"])
SYSTEM_PROMPT = (
    "You are an expert at creating high-quality commit messages in Conventional Commits format. "
    "Your messages must be informative, specific, and understandable for both developers and AI "
    "systems. Always use the format type(scope): description with specific details of changes."
)


def truncate_diff(diff: str, config: configparser.ConfigParser, default_size: str = "7000") -> str:
    max_size = int(config["DEFAULT"].get("max_diff_size", default_size))
    if len(diff) > max_size:
        logger.debug(f"Diff size exceeds limit. Truncated to {max_size} characters.")
        return diff[:max_size] + "\n... (truncated)"
    return diff


def build_user_prompt(status: str, diff: str) -> str:
    return f"""Analyze the git changes and create a brief but informative commit message in Conventional Commits format.

Git Status:
{status}

Git Diff:
{diff}

Message Requirements:
1. Format: type(scope): brief description
2. Type: feat, fix, docs, style, refactor, test, chore
3. Scope: module/component that changed (optional but recommended)
4. Description: what exactly changed and why (max 50 characters)

Good Examples:
- feat(auth): add OAuth2 authentication flow
- fix(api): resolve timeout error in user endpoint
- docs(readme): update installation instructions
- refactor(core): optimize database query performance
- style(ui): improve button spacing and colors

Important:
- Be specific: what changed, not just "update code"
- Use scope for grouping related changes
- Write in English
- Avoid generic phrases like "update", "fix", "change"
- Specify the exact functionality or issue

Return only the commit message, without additional explanations."""


def extract_commit_message(raw: str) -> str:
    message = raw.strip()
    lines = message.split("\n")
    for line in lines:
        line_stripped = line.strip()
        if any(line_stripped.startswith(prefix) for prefix in COMMIT_PREFIXES):
            return line_stripped
    for line in lines:
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith("```"):
            return line_stripped
    logger.debug(f"Failed to find format in message: {message}")
    return message


def chat_completion(
    *,
    api_key: str,
    prompt: str,
    model: str,
    api_name: str,
    base_url: str | None = None,
    http_model: str | None = None,
    http_url: str | None = None,
    timeout: int = 30,
    sdk_log: str = "",
    http_log: str = "",
    sdk_error: str | None = None,
) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    payload = {"model": http_model or model, "messages": messages, "max_tokens": 100, "temperature": 0.3}

    if OPENAI_SDK_AVAILABLE:
        try:
            logger.debug(sdk_log or f"Using OpenAI SDK for {api_name}...")
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            completion = client.chat.completions.create(model=model, messages=messages, max_tokens=100, temperature=0.3)
            return extract_commit_message(completion.choices[0].message.content)
        except Exception as e:
            logger.error(f"❌ Error using {sdk_error or api_name}: {e}")
            return DEFAULT_COMMIT_MESSAGE

    url = http_url or (f"{base_url.rstrip('/')}/chat/completions" if base_url else "https://api.openai.com/v1/chat/completions")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        logger.debug(http_log or f"Sending request to {api_name} (HTTP)...")
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]["content"]
        return extract_commit_message(message)
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Request timeout to {api_name}")
        return DEFAULT_COMMIT_MESSAGE
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error requesting {api_name}: {e}")
        return DEFAULT_COMMIT_MESSAGE
    except Exception as e:
        logger.error(f"❌ Error requesting {api_name}: {e}")
        return DEFAULT_COMMIT_MESSAGE
