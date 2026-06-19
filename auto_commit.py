#!/usr/bin/env python

"""
@file: auto_commit.py
@description: Automate git commits with AI-generated meaningful messages
@author: Andrej Spinej
@version: 1.0.1
@license: MIT
@requires: requests
"""

import os
import sys
import shutil
import subprocess
import argparse
import requests
from pathlib import Path
import configparser
import logging
from typing import Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from ai_common import COMMIT_PREFIXES, DEFAULT_COMMIT_MESSAGE

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
API_URL = (
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
)
PROVIDER_TOKEN = {
    "aitunnel": ("aitunnel_token", "AI_TUNNEL", "AITUNNEL"),
    "huggingface": ("huggingface_token", None, "Hugging Face"),
    "openai": ("openai_token", None, "OpenAI"),
}

_config_cache: Optional[configparser.ConfigParser] = None
_config_file_mtime: Optional[float] = None
_config_env_mtime: Optional[float] = None

OPENAI_SUPPORT = False
AITUNNEL_SUPPORT = False

try:
    from .openai_support import generate_commit_message_with_openai
    OPENAI_SUPPORT = True
except (ImportError, ModuleNotFoundError):
    try:
        sys.path.append(str(APP_DIR))
        from openai_support import generate_commit_message_with_openai
        OPENAI_SUPPORT = True
    except (ImportError, ModuleNotFoundError):
        logger.debug("OpenAI support module not found.")

try:
    from .aitunnel_support import generate_commit_message_with_aitunnel
    AITUNNEL_SUPPORT = True
except (ImportError, ModuleNotFoundError):
    try:
        sys.path.append(str(APP_DIR))
        from aitunnel_support import generate_commit_message_with_aitunnel
        AITUNNEL_SUPPORT = True
    except (ImportError, ModuleNotFoundError):
        logger.debug("AITUNNEL support module not found.")


def _file_mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime if path.exists() else None
    except OSError:
        return None


def setup_config(force_reload: bool = False) -> configparser.ConfigParser:
    global _config_cache, _config_file_mtime, _config_env_mtime

    if force_reload and hasattr(setup_config, "_env_loaded"):
        delattr(setup_config, "_env_loaded")

    if DOTENV_AVAILABLE and not hasattr(setup_config, "_env_loaded"):
        load_dotenv(ENV_FILE, override=force_reload)
        setup_config._env_loaded = True

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
        config["DEFAULT"] = {
            "api_provider": "aitunnel",
            "aitunnel_token": "",
            "aitunnel_base_url": "https://api.aitunnel.ru/v1/",
            "aitunnel_model": "gpt-4.1",
            "huggingface_token": "",
            "openai_token": "",
            "branch": "master",
            "max_diff_size": "7000",
        }
        os.makedirs(CONFIG_FILE.parent, exist_ok=True)
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


def get_git_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, encoding="utf-8"
        )
        if not result.stdout.strip():
            result = subprocess.run(
                ["git", "diff"], capture_output=True, encoding="utf-8"
            )
        return result.stdout.strip() or ""
    except Exception as e:
        logger.error(f"❌ Error getting git diff: {e}")
        sys.exit(1)


def get_git_status() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, encoding="utf-8"
        )
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"❌ Error getting git status: {e}")
        sys.exit(1)


def get_token(config: configparser.ConfigParser, provider: str) -> tuple[str, str]:
    config_key, env_key, name = PROVIDER_TOKEN.get(provider, (None, None, provider))
    token = config["DEFAULT"].get(config_key, "") if config_key else ""
    if env_key:
        token = token or os.getenv(env_key, "")
    return token, name


def generate_commit_message_with_huggingface(
    diff: str, status: str, config: configparser.ConfigParser, *, soft_fail: bool = False
) -> str:
    token = config["DEFAULT"].get("huggingface_token", "")
    if not token:
        logger.error("❌ Hugging Face API token not configured. Update config file.")
        if soft_fail:
            return DEFAULT_COMMIT_MESSAGE
        sys.exit(1)

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
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.2,
            "top_p": 0.95,
            "return_full_text": False,
        },
    }

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and result:
            message = result[0].get("generated_text", "").replace("</s>", "").strip()
            lines = message.split("\n")
            for line in lines:
                line = line.strip()
                if line and any(line.startswith(prefix) for prefix in COMMIT_PREFIXES):
                    return line
            for line in lines:
                if line.strip():
                    return line.strip()
            return message if message and "\n" not in message else DEFAULT_COMMIT_MESSAGE
        return DEFAULT_COMMIT_MESSAGE
    except Exception as e:
        logger.error(f"❌ Error requesting Hugging Face API: {e}")
        return DEFAULT_COMMIT_MESSAGE


def generate_commit_message(
    provider: str,
    diff: str,
    status: str,
    config: configparser.ConfigParser,
    *,
    soft_fail: bool = False,
) -> str:
    provider = provider.lower()
    if provider == "aitunnel" and AITUNNEL_SUPPORT:
        return generate_commit_message_with_aitunnel(diff, status, config)
    if provider == "openai" and OPENAI_SUPPORT:
        return generate_commit_message_with_openai(diff, status, config)
    if provider == "aitunnel" and not AITUNNEL_SUPPORT:
        logger.warning("AITUNNEL API selected but module not installed. Using Hugging Face.")
    elif provider == "openai" and not OPENAI_SUPPORT:
        logger.warning("OpenAI API selected but module not installed. Using Hugging Face.")
    return generate_commit_message_with_huggingface(diff, status, config, soft_fail=soft_fail)


def git_add_all() -> None:
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
    except Exception as e:
        print(f"❌ Error staging changes: {e}")
        sys.exit(1)


def git_commit(message: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message], capture_output=True, encoding="utf-8"
        )
        if result.returncode == 0:
            return True
        print(f"⚠️ Failed to create commit: {result.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error creating commit: {e}")
        sys.exit(1)


def git_push(branch: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "push", "origin", branch], capture_output=True, encoding="utf-8"
        )
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
        git_dir = Path().absolute() / ".git"
        if not git_dir.exists():
            print("❌ .git directory not found. Are you in a git repository?")
            return False
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        src_hook = APP_DIR / "prepare-commit-msg"
        dst_hook = hooks_dir / "prepare-commit-msg"
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


def main():
    parser = argparse.ArgumentParser(
        description="CommitPilot - automate git commits with AI-generated messages"
    )
    parser.add_argument("-m", "--message", help="Custom commit message (disables AI generation)")
    parser.add_argument("-b", "--branch", help="Branch for push (default from config)")
    parser.add_argument("-c", "--commit-only", action="store_true", help="Commit only, no push")
    parser.add_argument(
        "-p", "--provider",
        choices=["huggingface", "openai", "aitunnel"],
        help="AI provider (huggingface, openai or aitunnel)",
    )
    parser.add_argument("--setup", action="store_true", help="Setup configuration")
    parser.add_argument("--get-message", action="store_true", help="Generate commit message only and print it")
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
        if message and message != DEFAULT_COMMIT_MESSAGE:
            print(f'Commit: "{message}"')
        else:
            print("⚠️ Failed to generate message. Check API token settings.")
        return

    if args.test:
        print("🧪 Testing CommitPilot settings...")
        provider = config["DEFAULT"].get("api_provider", "aitunnel")
        token, name = get_token(config, provider)
        print(f"✅ {'Token configured' if token else '❌ Token not configured'}: {name}")
        print(f"✅ Provider: {provider}")
        print(f"✅ Default branch: {config['DEFAULT']['branch']}")
        print("\n🧪 Generating test message...")
        test_message = generate_message_only(config)
        if test_message and test_message != DEFAULT_COMMIT_MESSAGE:
            print(f'✅ Test message: "{test_message}"')
        else:
            print("❌ Failed to generate test message")
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
            provider = config["DEFAULT"].get("api_provider", "aitunnel")
            token, _ = get_token(config, provider)
            if token:
                test_message = generate_message_only(config)
                if test_message and test_message != DEFAULT_COMMIT_MESSAGE:
                    print(f'✅ Example message: "{test_message}"')
                else:
                    print("⚠️ Failed to generate test message")
            else:
                print("⚠️ API token not configured. Add it to config.ini or .env")
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
    if args.message:
        commit_message = args.message
    else:
        provider = args.provider or config["DEFAULT"].get("api_provider", "aitunnel")
        commit_message = generate_commit_message(provider, diff, status, config)

    print(f'📝 {commit_message}')
    git_commit(commit_message)
    if not args.commit_only:
        git_push(args.branch or config["DEFAULT"]["branch"])


if __name__ == "__main__":
    main()
