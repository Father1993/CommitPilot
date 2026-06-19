#!/usr/bin/env python

"""Automate git commits with AI-generated meaningful messages."""

import os
import sys
import shutil
import subprocess
import argparse
import configparser
import logging
from pathlib import Path
from typing import Optional

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
generate_commit_message_with_aitunnel = lambda d, s, c: generate_openai_provider("aitunnel", d, s, c)
generate_commit_message_with_openai = lambda d, s, c: generate_openai_provider("openai", d, s, c)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

VERSION = "1.0.1"
APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "config.ini"
ENV_FILE = APP_DIR / ".env"
ENV_OVERRIDES = (
    ("AI_TUNNEL", "aitunnel_token"),
    ("AITUNNEL_BASE_URL", "aitunnel_base_url"),
    ("AITUNNEL_MODEL", "aitunnel_model"),
)
PROVIDER_TOKEN = {
    "aitunnel": ("aitunnel_token", "AI_TUNNEL", "AITUNNEL"),
    "huggingface": ("huggingface_token", None, "Hugging Face"),
    "openai": ("openai_token", None, "OpenAI"),
}
DEFAULT_INI = {
    "api_provider": "aitunnel",
    "aitunnel_token": "",
    "aitunnel_base_url": "https://api.aitunnel.ru/v1/",
    "aitunnel_model": "gpt-4.1",
    "huggingface_token": "",
    "openai_token": "",
    "branch": "master",
    "max_diff_size": "7000",
}

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
    for env_key, config_key in ENV_OVERRIDES:
        if env_value := os.getenv(env_key):
            config["DEFAULT"][config_key] = env_value

    _config_cache = config
    _config_file_mtime = config_mtime
    _config_env_mtime = env_mtime
    return config


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
    config_key, env_key, name = PROVIDER_TOKEN.get(provider, (None, None, provider))
    token = config["DEFAULT"].get(config_key, "") if config_key else ""
    if env_key:
        token = token or os.getenv(env_key, "")
    return token, name


def generate_commit_message(
    provider: str,
    diff: str,
    status: str,
    config: configparser.ConfigParser,
    *,
    soft_fail: bool = False,
) -> str:
    provider = provider.lower()
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
        result = _git("push", "origin", branch)
        if result.returncode == 0:
            print(f"✅ Changes pushed to branch {branch}")
            return True
        print(f"⚠️ Failed to push changes: {result.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error pushing changes: {e}")
        sys.exit(1)


def generate_message_only(config: configparser.ConfigParser) -> str:
    status = get_git_status()
    if not status:
        logger.warning("No changes to analyze")
        return DEFAULT_COMMIT_MESSAGE
    diff = get_git_diff()
    if not diff:
        logger.warning("Empty diff, nothing to analyze")
        return DEFAULT_COMMIT_MESSAGE
    provider = config["DEFAULT"].get("api_provider", "aitunnel")
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
    provider = config["DEFAULT"].get("api_provider", "aitunnel")
    if not setup:
        token, name = get_token(config, provider)
        print(f"✅ {'Token configured' if token else '❌ Token not configured'}: {name}")
        print(f"✅ Provider: {provider}")
        print(f"✅ Default branch: {config['DEFAULT']['branch']}")
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
    parser.add_argument("-b", "--branch", help="Branch for push (default from config)")
    parser.add_argument("-c", "--commit-only", action="store_true", help="Commit only, no push")
    parser.add_argument("-p", "--provider", choices=["huggingface", "openai", "aitunnel"], help="AI provider")
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
        print(f"   Or create {ENV_FILE} with: AI_TUNNEL=sk-aitunnel-your_token")
        print("   Get AITUNNEL token: https://aitunnel.ru/")
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
        args.provider or config["DEFAULT"].get("api_provider", "aitunnel"), diff, status, config
    )
    print(f"📝 {commit_message}")
    git_commit(commit_message)
    if not args.commit_only:
        git_push(args.branch or config["DEFAULT"]["branch"])


if __name__ == "__main__":
    main()
