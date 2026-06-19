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
COMMIT_PREFIXES = frozenset(["feat", "fix", "docs", "style", "refactor", "test", "chore"])
HF_API_URL = (
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
)
SYSTEM_PROMPT = (
    "You are an expert at creating high-quality commit messages in Conventional Commits format. "
    "Your messages must be informative, specific, and understandable for both developers and AI "
    "systems. Always use the format type(scope): description with specific details of changes."
)
OPENAI_PROVIDERS = {
    "aitunnel": {
        "token_key": "aitunnel_token",
        "missing_msg": "❌ AITUNNEL API token not configured. Update config file or .env file.",
        "base_url_key": "aitunnel_base_url",
        "base_url_default": "https://api.aitunnel.ru/v1/",
        "model_key": "aitunnel_model",
        "model_default": "gpt-4.1",
        "truncate_default": "5000",
        "timeout": 30,
        "api_name": "AITUNNEL API",
        "sdk_log": "Using OpenAI SDK for AITUNNEL API...",
        "http_log": "Sending request to AITUNNEL API (HTTP)...",
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


def _extract_hf_message(raw: str) -> str:
    message = raw.replace("</s>", "").strip()
    lines = message.split("\n")
    for line in lines:
        line = line.strip()
        if line and any(line.startswith(prefix) for prefix in COMMIT_PREFIXES):
            return line
    for line in lines:
        if line.strip():
            return line.strip()
    return message if message and "\n" not in message else DEFAULT_COMMIT_MESSAGE


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

    user_prompt = f"""Generate a commit message for the following changes:

Git Status:
{status}

Git Diff (partial):
{diff[:500]}...

Instructions:
- Create a single-line commit message in format: 'type(scope): message'
- Choose 'type' from: feat, fix, docs, style, refactor, test, chore
- Focus on WHAT changed and WHY
- Keep it under 72 characters
- Be specific and descriptive

Format your response as just the commit message text without explanations.
"""
    system_prompt = (
        "You are a helpful AI assistant that specializes in creating conventional commit messages."
    )
    payload = {
        "inputs": f"<s>[INST] {system_prompt} [/INST]</s>\n<s>[INST] {user_prompt} [/INST]",
        "parameters": {"max_new_tokens": 100, "temperature": 0.2, "top_p": 0.95, "return_full_text": False},
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
