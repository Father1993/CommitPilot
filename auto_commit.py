#!/usr/bin/env python3

"""Automate git commits with AI-generated meaningful messages."""

import json
import os
import re
import sys
import shutil
import subprocess
import argparse
import configparser
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import quote

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from ai_common import (
    DEFAULT_COMMIT_MESSAGE,
    OPENAI_PROVIDERS,
    generate_huggingface,
    generate_openai_provider,
)

generate_commit_message_with_huggingface = generate_huggingface
generate_commit_message_with_openai_compatible = (
    lambda d, s, c: generate_openai_provider("openai_compatible", d, s, c)
)
generate_commit_message_with_openai = lambda d, s, c: generate_openai_provider("openai", d, s, c)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

VERSION = "1.1.0"
APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "config.ini"
ENV_FILE = APP_DIR / ".env"

# Env → config.ini (legacy first; modern names win if both are set)
ENV_OVERRIDES = (
    ("AI_TUNNEL", "api_token"),
    ("AITUNNEL_BASE_URL", "api_base_url"),
    ("AITUNNEL_MODEL", "api_model"),
    ("API_TOKEN", "api_token"),
    ("API_BASE_URL", "api_base_url"),
    ("API_MODEL", "api_model"),
)
PROVIDER_ALIASES = {
    "aitunnel": "openai_compatible",
}
PROVIDER_TOKEN = {
    "openai_compatible": ("api_token", "API_TOKEN", "OpenAI-compatible"),
    "huggingface": ("huggingface_token", None, "Hugging Face"),
    "openai": ("openai_token", None, "OpenAI"),
}
DEFAULT_INI = {
    "api_provider": "openai_compatible",
    "api_token": "",
    "api_base_url": "https://api.openai.com/v1",
    "api_model": "gpt-4.1",
    "huggingface_token": "",
    "openai_token": "",
    "branch": "master",
    "max_diff_size": "7000",
}
# Old config.ini keys → new (read-only migration when new key is empty)
_LEGACY_INI_KEYS = (
    ("aitunnel_token", "api_token"),
    ("aitunnel_base_url", "api_base_url"),
    ("aitunnel_model", "api_model"),
)

_config_cache: Optional[configparser.ConfigParser] = None
_config_file_mtime: Optional[float] = None
_config_env_mtime: Optional[float] = None
_env_loaded = False


def _file_mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime if path.exists() else None
    except OSError:
        return None


def setup_config(force_reload: bool = False) -> configparser.ConfigParser:
    global _config_cache, _config_file_mtime, _config_env_mtime, _env_loaded

    if force_reload:
        _env_loaded = False

    if DOTENV_AVAILABLE and not _env_loaded:
        load_dotenv(ENV_FILE, override=force_reload)
        _env_loaded = True

    config_mtime = _file_mtime(CONFIG_FILE)
    env_mtime = _file_mtime(ENV_FILE)
    if (
        not force_reload
        and _config_cache is not None
        and config_mtime == _config_file_mtime
        and env_mtime == _config_env_mtime
    ):
        return _config_cache

    if not CONFIG_FILE.exists():
        config = configparser.ConfigParser()
        config["DEFAULT"] = DEFAULT_INI
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        print(f"✅ Created configuration file {CONFIG_FILE}")
        print(f"⚠️ Add API token to {ENV_FILE} or config file")
        config_mtime = _file_mtime(CONFIG_FILE)

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    defaults = config["DEFAULT"]

    for old_key, new_key in _LEGACY_INI_KEYS:
        if not defaults.get(new_key) and defaults.get(old_key):
            defaults[new_key] = defaults.get(old_key)

    provider = defaults.get("api_provider", "openai_compatible")
    if provider in PROVIDER_ALIASES:
        defaults["api_provider"] = PROVIDER_ALIASES[provider]

    for env_key, config_key in ENV_OVERRIDES:
        if env_value := os.getenv(env_key):
            defaults[config_key] = env_value

    _config_cache = config
    _config_file_mtime = config_mtime
    _config_env_mtime = env_mtime
    return config


def normalize_provider(provider: str) -> str:
    name = (provider or "openai_compatible").lower()
    return PROVIDER_ALIASES.get(name, name)


def _git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    kwargs: dict = {"capture_output": True, "encoding": "utf-8"}
    if check:
        kwargs["check"] = True
    return subprocess.run(["git", *args], **kwargs)


def get_git_diff() -> str:
    try:
        result = _git("diff", "--cached")
        if not result.stdout.strip():
            result = _git("diff")
        return result.stdout.strip() or ""
    except Exception as e:
        logger.error(f"❌ Error getting git diff: {e}")
        sys.exit(1)


def get_git_status() -> str:
    try:
        return _git("status", "--porcelain").stdout.strip()
    except Exception as e:
        logger.error(f"❌ Error getting git status: {e}")
        sys.exit(1)


def get_token(config: configparser.ConfigParser, provider: str) -> tuple[str, str]:
    provider = normalize_provider(provider)
    config_key, env_key, name = PROVIDER_TOKEN.get(provider, (None, None, provider))
    token = config["DEFAULT"].get(config_key, "") if config_key else ""
    if env_key:
        token = token or os.getenv(env_key, "") or os.getenv("AI_TUNNEL", "")
    return token, name


def generate_commit_message(
    provider: str,
    diff: str,
    status: str,
    config: configparser.ConfigParser,
    *,
    soft_fail: bool = False,
) -> str:
    provider = normalize_provider(provider)
    if provider in OPENAI_PROVIDERS:
        return generate_openai_provider(provider, diff, status, config)
    return generate_huggingface(diff, status, config, soft_fail=soft_fail)


def git_add_all() -> None:
    try:
        _git("add", ".", check=True)
    except Exception as e:
        print(f"❌ Error staging changes: {e}")
        sys.exit(1)


def git_commit(message: str) -> bool:
    try:
        result = _git("commit", "-m", message)
        if result.returncode == 0:
            return True
        print(f"⚠️ Failed to create commit: {result.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error creating commit: {e}")
        sys.exit(1)


def git_push(branch: str) -> bool:
    try:
        result = _git("push", "-u", "origin", branch)
        if result.returncode == 0:
            print(f"✅ Changes pushed to branch {branch}")
            return True
        print(f"⚠️ Failed to push changes: {result.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error pushing changes: {e}")
        sys.exit(1)


def get_current_branch() -> Optional[str]:
    result = _git("branch", "--show-current")
    branch = (result.stdout or "").strip()
    return branch or None


def resolve_push_branch(explicit: Optional[str]) -> Optional[str]:
    """Resolve push target: -b override → current branch. Detached HEAD → None."""
    if explicit:
        return explicit
    current = get_current_branch()
    if current:
        return current
    print("⚠️ Detached HEAD — cannot determine branch for push")
    return None


def remote_branch_exists(name: str) -> bool:
    return _git("rev-parse", "--verify", "--quiet", f"origin/{name}").returncode == 0


def get_default_branch() -> str:
    result = _git("symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if result.returncode == 0:
        ref = (result.stdout or "").strip()
        if ref.startswith("refs/remotes/origin/"):
            return ref.rsplit("/", 1)[-1]
    for name in ("main", "master"):
        if remote_branch_exists(name):
            return name
    return "main"


def github_repo_url() -> Optional[str]:
    result = _git("remote", "get-url", "origin")
    if result.returncode != 0:
        return None
    url = (result.stdout or "").strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    # git@github.com:owner/repo | ssh://git@github.com/owner/repo | https://github.com/owner/repo
    m = re.match(r"(?:git@github\.com:|ssh://git@github\.com/|https?://github\.com/)(.+)", url)
    return f"https://github.com/{m.group(1)}" if m else None


def resolve_pr_base(head: str) -> Optional[str]:
    """BASE for compare/PR: feature→dev (or default), dev→default, production→None."""
    default = get_default_branch()
    if head in (default, "main", "master"):
        return None
    if head == "dev":
        return default
    if remote_branch_exists("dev"):
        return "dev"
    return default


def _find_open_pr_url(head: str, base: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--head", head, "--base", base, "--state", "open", "--json", "url"],
            capture_output=True, encoding="utf-8", timeout=10,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout or "[]")
        return data[0].get("url") if data else None
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
        return None


def print_deploy_link(head: str) -> None:
    base = resolve_pr_base(head)
    if not base:
        return
    repo = github_repo_url()
    if not repo:
        return
    pr_url = _find_open_pr_url(head, base)
    if pr_url:
        print(f"🔗 {pr_url}")
        return
    # quote path segments so feature/foo works in compare URLs
    print(f"🔗 {repo}/compare/{quote(base, safe='')}...{quote(head, safe='')}?expand=1")


def generate_message_only(config: configparser.ConfigParser) -> str:
    status = get_git_status()
    if not status:
        logger.warning("No changes to analyze")
        return DEFAULT_COMMIT_MESSAGE
    diff = get_git_diff()
    if not diff:
        logger.warning("Empty diff, nothing to analyze")
        return DEFAULT_COMMIT_MESSAGE
    provider = config["DEFAULT"].get("api_provider", "openai_compatible")
    logger.debug(f"Using AI provider: {provider}")
    return generate_commit_message(provider, diff, status, config, soft_fail=True)


def install_git_hooks() -> bool:
    try:
        git_dir = Path.cwd() / ".git"
        if not git_dir.exists():
            print("❌ .git directory not found. Are you in a git repository?")
            return False
        dst_hook = git_dir / "hooks" / "prepare-commit-msg"
        dst_hook.parent.mkdir(exist_ok=True)
        src_hook = APP_DIR / "prepare-commit-msg"
        if not src_hook.exists():
            print(f"❌ File not found: {src_hook}")
            return False
        shutil.copy2(src_hook, dst_hook)
        os.chmod(dst_hook, 0o755)
        print(f"✅ Git hook installed: {dst_hook}")
        return True
    except Exception as e:
        print(f"❌ Error installing Git hooks: {e}")
        return False


def _report_test(config: configparser.ConfigParser, *, setup: bool = False) -> None:
    provider = normalize_provider(config["DEFAULT"].get("api_provider", "openai_compatible"))
    if not setup:
        token, name = get_token(config, provider)
        print(f"✅ {'Token configured' if token else '❌ Token not configured'}: {name}")
        print(f"✅ Provider: {provider}")
        current = get_current_branch()
        print(f"✅ Push branch: {current or 'n/a'} (current branch; config branch is unused for push)")
        print("\n🧪 Generating test message...")
    elif not get_token(config, provider)[0]:
        print("⚠️ API token not configured. Add it to config.ini or .env")
        return
    test_message = generate_message_only(config)
    ok = test_message and test_message != DEFAULT_COMMIT_MESSAGE
    prefix = "✅ Example" if setup else "✅ Test"
    print(f'{prefix} message: "{test_message}"' if ok else ("⚠️ Failed to generate test message" if setup else "❌ Failed to generate test message"))


def main():
    parser = argparse.ArgumentParser(description="CommitPilot - automate git commits with AI-generated messages")
    parser.add_argument("-m", "--message", help="Custom commit message (disables AI generation)")
    parser.add_argument("-b", "--branch", help="Override push branch (default: current branch)")
    parser.add_argument("-c", "--commit-only", action="store_true", help="Commit only, no push")
    parser.add_argument("-d", "--deploy-link", action="store_true", help="Print PR/compare deploy link after push")
    parser.add_argument(
        "-p",
        "--provider",
        choices=["huggingface", "openai", "openai_compatible", "aitunnel"],
        help="AI provider (aitunnel is an alias for openai_compatible)",
    )
    parser.add_argument("--setup", action="store_true", help="Setup configuration")
    parser.add_argument("--get-message", action="store_true", help="Generate commit message only")
    parser.add_argument("--setup-hooks", action="store_true", help="Install Git hooks")
    parser.add_argument("--test", action="store_true", help="Test with current settings")
    parser.add_argument("-v", "--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print(f"CommitPilot v{VERSION}")
        return

    config = setup_config()

    if args.get_message:
        message = generate_message_only(config)
        print(f'Commit: "{message}"' if message and message != DEFAULT_COMMIT_MESSAGE else "⚠️ Failed to generate message. Check API token settings.")
        return

    if args.test:
        print("🧪 Testing CommitPilot settings...")
        _report_test(config)
        print("\n✅ Test completed")
        return

    if args.setup_hooks:
        install_git_hooks()
        return

    if args.setup:
        if not CONFIG_FILE.exists():
            setup_config()
        print("✅ Configuration file created")
        print(f"📝 Please edit {CONFIG_FILE} and add your API token")
        print(f"   Or create {ENV_FILE} with: API_TOKEN=your_token")
        print("   Optional: API_BASE_URL=...  API_MODEL=...")
        print("   OpenAI-compatible hosts: any OpenAI-protocol API (OpenRouter, RouterAI, etc.)")
        print("   Get Hugging Face token: https://huggingface.co/settings/tokens")
        print("   Get OpenAI token: https://platform.openai.com/api-keys")
        if input("Install Git hooks for auto commit messages? (y/n): ").lower() == "y":
            install_git_hooks()
        print("\n🧪 Testing CommitPilot...")
        try:
            _report_test(config, setup=True)
        except Exception as e:
            print(f"⚠️ Check error: {e}")
        print("✅ Setup completed")
        return

    status = get_git_status()
    if not status:
        print("ℹ️ No changes to commit")
        return

    git_add_all()
    diff = get_git_diff()
    commit_message = args.message or generate_commit_message(
        args.provider or config["DEFAULT"].get("api_provider", "openai_compatible"),
        diff,
        status,
        config,
    )
    print(f"📝 {commit_message}")
    git_commit(commit_message)
    if not args.commit_only:
        branch = resolve_push_branch(args.branch)
        if branch and git_push(branch) and args.deploy_link:
            print_deploy_link(branch)


if __name__ == "__main__":
    main()
