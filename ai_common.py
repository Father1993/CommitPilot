#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shared AI commit message generation utilities."""

import logging
import configparser

import requests

try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_COMMIT_MESSAGE = "chore: automatic changes commit"
COMMIT_PREFIXES = frozenset(
    ["feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "build", "ci"]
)
MAX_COMPLETION_TOKENS = 220
HF_API_URL = (
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
)
SYSTEM_PROMPT = (
    "You write Conventional Commit messages for developers scanning git history. "
    "Lead with intent (why), then what changed. Use concrete nouns from the diff "
    "(modules, APIs, config keys, behaviors). Never invent changes absent from the diff. "
    "Output only the commit message — no preamble, markdown fences, or quotes."
)
# OpenAI-protocol providers. "openai_compatible" = any host (RouterAI, OpenRouter, …).
OPENAI_PROVIDERS = {
    "openai_compatible": {
        "token_key": "api_token",
        "missing_msg": "❌ API token not configured. Set API_TOKEN in .env or api_token in config.ini.",
        "base_url_key": "api_base_url",
        "base_url_default": "https://api.openai.com/v1",
        "model_key": "api_model",
        "model_default": "gpt-4.1",
        "truncate_default": "5000",
        "timeout": 30,
        "api_name": "OpenAI-compatible API",
        "sdk_log": "Using OpenAI SDK (compatible provider)...",
        "http_log": "Sending request to OpenAI-compatible API (HTTP)...",
    },
    "openai": {
        "token_key": "openai_token",
        "missing_msg": "❌ OpenAI API token not configured. Update config file.",
        "model_default": "gpt-4o-mini",
        "http_model": "gpt-3.5-turbo",
        "truncate_default": "5000",
        "timeout": 10,
        "api_name": "OpenAI API",
        "sdk_log": "Using new OpenAI SDK...",
        "http_log": "Sending request to OpenAI API (HTTP)...",
        "sdk_error": "OpenAI SDK",
    },
}


def truncate_diff(diff: str, config: configparser.ConfigParser, default_size: str = "7000") -> str:
    max_size = int(config["DEFAULT"].get("max_diff_size", default_size))
    if len(diff) > max_size:
        logger.debug(f"Diff size exceeds limit. Truncated to {max_size} characters.")
        return diff[:max_size] + "\n... (truncated)"
    return diff


def changed_paths(status: str) -> list[str]:
    """Parse `git status --porcelain` paths for prompt context."""
    paths: list[str] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def _is_conventional_subject(line: str) -> bool:
    lower = line.lower()
    return any(
        lower.startswith(f"{prefix}:") or lower.startswith(f"{prefix}(")
        for prefix in COMMIT_PREFIXES
    )


def build_user_prompt(status: str, diff: str) -> str:
    paths = changed_paths(status)
    paths_block = "\n".join(f"- {p}" for p in paths) if paths else "- (see status/diff)"
    return f"""Write a Conventional Commits message for these changes.

Changed paths:
{paths_block}

Git Status:
{status}

Git Diff:
{diff}

Rules:
1. First line: type(scope): subject
   - type: feat | fix | docs | style | refactor | test | chore | perf | build | ci
   - scope: short area from the paths (omit only if unclear)
   - subject: imperative mood, max ~72 chars, concrete outcome — not "update X" / "rename Y"
   - Prefer why/impact when visible in the diff (e.g. "so secrets stay out of git")
2. Non-trivial changes (several files, behavior change, rename with ripple effects):
   after a blank line, add 1–3 short body lines with why / impact / migration notes.
   Skip the body for tiny one-file edits.
3. English only. No markdown fences, quotes, or commentary outside the message.

Good examples:

feat(auth): add OAuth2 login for API clients

fix(hooks): keep typed commit messages when regenerating
Skip AI generation if the user already wrote a non-empty message.

refactor(config): use openai_compatible for any OpenAI-protocol host
Replace vendor-specific aitunnel keys with api_token, api_base_url, and api_model."""


def extract_commit_message(raw: str) -> str:
    """Keep subject plus optional body; drop model preamble and fences."""
    text = (raw or "").strip()
    if not text:
        return DEFAULT_COMMIT_MESSAGE

    lines = [ln.rstrip() for ln in text.splitlines()]
    lines = [ln for ln in lines if not ln.strip().startswith("```")]

    start = next((i for i, ln in enumerate(lines) if _is_conventional_subject(ln.strip())), None)
    if start is None:
        for ln in lines:
            s = ln.strip().strip("\"'")
            if s:
                return s
        logger.debug(f"Failed to find format in message: {text}")
        return text

    block = lines[start:]
    while block and not block[-1].strip():
        block.pop()

    # Cap body so chatty models do not flood the commit
    subject = block[0].strip().strip("\"'")
    body_lines: list[str] = []
    if len(block) > 1:
        rest = block[1:]
        if rest and not rest[0].strip():
            rest = rest[1:]
        for ln in rest[:5]:
            s = ln.strip()
            if not s:
                break
            body_lines.append(s)

    if not body_lines:
        return subject
    return subject + "\n\n" + "\n".join(body_lines)


def _extract_hf_message(raw: str) -> str:
    message = extract_commit_message((raw or "").replace("</s>", ""))
    return message or DEFAULT_COMMIT_MESSAGE


def chat_completion(
    *,
    api_key: str,
    prompt: str,
    model: str,
    api_name: str,
    base_url: str | None = None,
    http_model: str | None = None,
    timeout: int = 30,
    sdk_log: str = "",
    http_log: str = "",
    sdk_error: str | None = None,
) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    payload = {
        "model": http_model or model,
        "messages": messages,
        "max_tokens": MAX_COMPLETION_TOKENS,
        "temperature": 0.2,
    }

    if OPENAI_SDK_AVAILABLE:
        try:
            logger.debug(sdk_log or f"Using OpenAI SDK for {api_name}...")
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=MAX_COMPLETION_TOKENS,
                temperature=0.2,
            )
            content = completion.choices[0].message.content or ""
            return extract_commit_message(content)
        except Exception as e:
            logger.error(f"❌ Error using {sdk_error or api_name}: {e}")
            return DEFAULT_COMMIT_MESSAGE

    url = f"{base_url.rstrip('/')}/chat/completions" if base_url else "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        logger.debug(http_log or f"Sending request to {api_name} (HTTP)...")
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return extract_commit_message(response.json()["choices"][0]["message"]["content"])
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Request timeout to {api_name}")
        return DEFAULT_COMMIT_MESSAGE
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error requesting {api_name}: {e}")
        return DEFAULT_COMMIT_MESSAGE
    except Exception as e:
        logger.error(f"❌ Error requesting {api_name}: {e}")
        return DEFAULT_COMMIT_MESSAGE


def generate_openai_provider(
    name: str, diff: str, status: str, config: configparser.ConfigParser
) -> str:
    spec = OPENAI_PROVIDERS[name]
    token = config["DEFAULT"].get(spec["token_key"], "")
    if not token:
        logger.error(spec["missing_msg"])
        return DEFAULT_COMMIT_MESSAGE

    base_url = None
    if "base_url_key" in spec:
        base_url = config["DEFAULT"].get(spec["base_url_key"], spec["base_url_default"])
    model = config["DEFAULT"].get(spec.get("model_key", ""), spec["model_default"]) if spec.get("model_key") else spec["model_default"]
    prompt = build_user_prompt(status, truncate_diff(diff, config, spec["truncate_default"]))

    return chat_completion(
        api_key=token,
        prompt=prompt,
        model=model,
        http_model=spec.get("http_model"),
        api_name=spec["api_name"],
        base_url=base_url,
        timeout=spec["timeout"],
        sdk_log=spec.get("sdk_log", ""),
        http_log=spec.get("http_log", ""),
        sdk_error=spec.get("sdk_error"),
    )


def generate_huggingface(
    diff: str, status: str, config: configparser.ConfigParser, *, soft_fail: bool = False
) -> str:
    token = config["DEFAULT"].get("huggingface_token", "")
    if not token:
        logger.error("❌ Hugging Face API token not configured. Update config file.")
        if soft_fail:
            return DEFAULT_COMMIT_MESSAGE
        raise SystemExit(1)

    max_size = int(config["DEFAULT"].get("max_diff_size", "7000"))
    if len(diff) > max_size:
        diff = diff[:max_size] + "\n... (truncated)"

    user_prompt = build_user_prompt(status, diff[:500] + ("..." if len(diff) > 500 else ""))
    payload = {
        "inputs": f"<s>[INST] {SYSTEM_PROMPT} [/INST]</s>\n<s>[INST] {user_prompt} [/INST]",
        "parameters": {
            "max_new_tokens": MAX_COMPLETION_TOKENS,
            "temperature": 0.2,
            "top_p": 0.95,
            "return_full_text": False,
        },
    }

    try:
        response = requests.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and result:
            return _extract_hf_message(result[0].get("generated_text", ""))
        return DEFAULT_COMMIT_MESSAGE
    except Exception as e:
        logger.error(f"❌ Error requesting Hugging Face API: {e}")
        return DEFAULT_COMMIT_MESSAGE
