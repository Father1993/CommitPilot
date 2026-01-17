#!/usr/bin/env python

"""
@file: auto_commit.py
@description: Automate git commits with AI-generated meaningful messages
@author: Andrej Spinej
@version: 1.0.0
@license: MIT
@requires: requests
"""

import os
import sys
import subprocess
import argparse
import requests
from pathlib import Path
import configparser
import logging
from functools import lru_cache
from typing import Dict, Optional, Any, Tuple

# Try to load variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Configure logging (errors and warnings only)
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants
VERSION = "1.0.0"
CONFIG_FILE = Path(__file__).resolve().parent / "config.ini"
DEFAULT_COMMIT_MESSAGE = "chore: automatic changes commit"
API_URL = (
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
)

# Cache for configuration (updated when file changes)
_config_cache: Optional[configparser.ConfigParser] = None
_config_file_mtime: Optional[float] = None

# Множество префиксов для быстрого поиска (оптимизация парсинга)
COMMIT_PREFIXES = frozenset(["feat", "fix", "docs", "style", "refactor", "test", "chore"])

# Import AI provider support modules
OPENAI_SUPPORT = False
AITUNNEL_SUPPORT = False

try:
    from .openai_support import generate_commit_message_with_openai
    OPENAI_SUPPORT = True
except (ImportError, ModuleNotFoundError):
    try:
        sys.path.append(str(Path(__file__).parent))
        from openai_support import generate_commit_message_with_openai
        OPENAI_SUPPORT = True
    except (ImportError, ModuleNotFoundError):
        logger.debug("OpenAI support module not found.")

try:
    from .aitunnel_support import generate_commit_message_with_aitunnel
    AITUNNEL_SUPPORT = True
except (ImportError, ModuleNotFoundError):
    try:
        sys.path.append(str(Path(__file__).parent))
        from aitunnel_support import generate_commit_message_with_aitunnel
        AITUNNEL_SUPPORT = True
    except (ImportError, ModuleNotFoundError):
        logger.debug("Модуль поддержки AITUNNEL не найден.")


def setup_config(force_reload: bool = False) -> configparser.ConfigParser:
    """
    Create config file if it doesn't exist, or read existing one.
    Also loads variables from .env file if available.
    Uses caching for performance optimization.

    Args:
        force_reload: Force reload configuration from file

    Returns:
        ConfigParser: Application settings object
    """
    global _config_cache, _config_file_mtime
    
    # Load variables from .env file (only once)
    if DOTENV_AVAILABLE and not hasattr(setup_config, '_env_loaded'):
        load_dotenv()
        setup_config._env_loaded = True
    
    # Check cache
    if not force_reload and _config_cache is not None:
        if CONFIG_FILE.exists():
            try:
                if CONFIG_FILE.stat().st_mtime == _config_file_mtime:
                    return _config_cache
            except OSError:
                _config_cache = None
                _config_file_mtime = None
        elif _config_file_mtime is None:
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
        print("⚠️ Add API token to config file or .env")
    
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    # Override values from .env file if present
    for env_key, config_key in [
        ("AI_TUNNEL", "aitunnel_token"),
        ("AITUNNEL_BASE_URL", "aitunnel_base_url"),
        ("AITUNNEL_MODEL", "aitunnel_model")
    ]:
        env_value = os.getenv(env_key)
        if env_value:
            config["DEFAULT"][config_key] = env_value
    
    # Update cache
    _config_cache = config
    try:
        _config_file_mtime = CONFIG_FILE.stat().st_mtime if CONFIG_FILE.exists() else None
    except OSError:
        _config_file_mtime = None
    
    return config


def get_git_diff() -> str:
    """
    Get changes in git repository.

    Returns:
        str: Changes text (git diff)

    Raises:
        SystemExit: On git command execution error
    """
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
    """
    Get git repository status.

    Returns:
        str: Git repository status text

    Raises:
        SystemExit: On git command execution error
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, encoding="utf-8"
        )
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"❌ Error getting git status: {e}")
        sys.exit(1)


def generate_commit_message_with_huggingface(
    diff: str, status: str, config: configparser.ConfigParser
) -> str:
    """
    Generate commit message using Hugging Face API.

    Args:
        diff: Changes text (git diff)
        status: Repository status (git status)
        config: Configuration with settings and API keys

    Returns:
        str: Generated commit message

    Raises:
        SystemExit: If API key is not configured
    """
    token = config["DEFAULT"].get("huggingface_token", "")
    if not token:
        logger.error("❌ Hugging Face API token not configured. Update config file.")
        if "--test" in sys.argv or "--get-message" in sys.argv:
            return DEFAULT_COMMIT_MESSAGE
        sys.exit(1)

    max_size = int(config["DEFAULT"].get("max_diff_size", "7000"))
    if len(diff) > max_size:
        diff = diff[:max_size] + "\n... (truncated)"

    headers = {"Authorization": f"Bearer {token}"}
    system_prompt = "You are a helpful AI assistant that specializes in creating conventional commit messages."
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
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and result:
            message = result[0].get("generated_text", "").replace("</s>", "").strip()
            lines = message.split("\n")
            
            # Find Conventional Commits format line
            for line in lines:
                line = line.strip()
                if line and any(line.startswith(prefix) for prefix in COMMIT_PREFIXES):
                    return line
            
            # Return first non-empty line or full message
            for line in lines:
                if line.strip():
                    return line.strip()
            return message if message and "\n" not in message else DEFAULT_COMMIT_MESSAGE

        return DEFAULT_COMMIT_MESSAGE
    except Exception as e:
        logger.error(f"❌ Error requesting Hugging Face API: {e}")
        return DEFAULT_COMMIT_MESSAGE


def git_add_all() -> None:
    """
    Stage all changes.

    Raises:
        SystemExit: On git command execution error
    """
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
    except Exception as e:
        print(f"❌ Error staging changes: {e}")
        sys.exit(1)


def git_commit(message: str) -> bool:
    """
    Создает коммит с указанным сообщением

    Args:
        message: Текст сообщения для коммита

    Returns:
        bool: True если коммит создан успешно, False в случае ошибки

    Raises:
        SystemExit: При критической ошибке
    """
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message], capture_output=True, encoding="utf-8"
        )
        if result.returncode == 0:
            return True
        else:
            print(f"⚠️ Не удалось создать коммит: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при создании коммита: {e}")
        sys.exit(1)


def git_push(branch: str) -> bool:
    """
    Push changes to remote repository.

    Args:
        branch: Branch name for pushing changes

    Returns:
        bool: True if changes pushed successfully, False on error

    Raises:
        SystemExit: On critical error
    """
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
    """
    Generate commit message only without performing other actions.

    Args:
        config: Configuration with settings

    Returns:
        str: Generated commit message
    """
    status = get_git_status()
    if not status:
        logger.warning("No changes to analyze")
        return DEFAULT_COMMIT_MESSAGE

    diff = get_git_diff()
    if not diff:
        logger.warning("Empty diff, nothing to analyze")
        return DEFAULT_COMMIT_MESSAGE

    # Выбираем провайдера AI
    provider = config["DEFAULT"].get("api_provider", "aitunnel")
    logger.debug(f"Using AI provider: {provider}")

    if provider.lower() == "aitunnel" and AITUNNEL_SUPPORT:
        return generate_commit_message_with_aitunnel(diff, status, config)
    elif provider.lower() == "openai" and OPENAI_SUPPORT:
        return generate_commit_message_with_openai(diff, status, config)
    else:
        if provider.lower() == "aitunnel" and not AITUNNEL_SUPPORT:
            logger.warning(
                "AITUNNEL API выбран, но модуль не установлен. Используется Hugging Face."
            )
        elif provider.lower() == "openai" and not OPENAI_SUPPORT:
            logger.warning(
                "OpenAI API выбран, но модуль не установлен. Используется Hugging Face."
            )
        return generate_commit_message_with_huggingface(diff, status, config)


def main():
    parser = argparse.ArgumentParser(
        description="CommitPilot - automate git commits with AI-generated messages"
    )
    parser.add_argument(
        "-m", "--message", help="Custom commit message (disables AI generation)"
    )
    parser.add_argument(
        "-b", "--branch", help="Branch for push (default from config)"
    )
    parser.add_argument(
        "-c", "--commit-only", action="store_true", help="Commit only, no push"
    )
    parser.add_argument(
        "-p", "--provider",
        choices=["huggingface", "openai", "aitunnel"],
        help="AI provider (huggingface, openai or aitunnel)"
    )
    parser.add_argument("--setup", action="store_true", help="Setup configuration")
    parser.add_argument(
        "--get-message", action="store_true",
        help="Generate commit message only and print it"
    )
    parser.add_argument(
        "--setup-hooks", action="store_true", help="Install Git hooks"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test with current settings"
    )
    parser.add_argument("-v", "--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print("CommitPilot v1.0.0")
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
        
        token_map = {
            "aitunnel": ("aitunnel_token", "AI_TUNNEL", "AITUNNEL"),
            "huggingface": ("huggingface_token", None, "Hugging Face"),
            "openai": ("openai_token", None, "OpenAI")
        }
        
        config_key, env_key, name = token_map.get(provider, (None, None, provider))
        token = config["DEFAULT"].get(config_key, "") if config_key else ""
        if env_key:
            token = token or os.getenv(env_key, "")
        
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
        try:
            script_dir = Path(__file__).parent
            git_dir = Path().absolute() / ".git"

            if not git_dir.exists():
                print("❌ .git directory not found. Are you in a git repository?")
                return

            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir(exist_ok=True)
            src_hook = script_dir / "prepare-commit-msg"
            dst_hook = hooks_dir / "prepare-commit-msg"

            if not src_hook.exists():
                print(f"❌ File not found: {src_hook}")
                return

            import shutil
            shutil.copy2(src_hook, dst_hook)
            os.chmod(dst_hook, 0o755)
            print(f"✅ Git hook installed: {dst_hook}")
        except Exception as e:
            print(f"❌ Error installing Git hooks: {e}")
        return

    if args.setup:
        if not CONFIG_FILE.exists():
            setup_config()

        print("✅ Configuration file created")
        print(f"📝 Please edit {CONFIG_FILE} and add your API token")
        print("   Or create .env file in project root:")
        print("   AI_TUNNEL=sk-aitunnel-your_token")
        print("   Get AITUNNEL token: https://aitunnel.ru/")
        print("   Get Hugging Face token: https://huggingface.co/settings/tokens")
        print("   Get OpenAI token: https://platform.openai.com/api-keys")

        if input("Install Git hooks for auto commit messages? (y/n): ").lower() == "y":
            args.setup_hooks = True
            main()

        print("\n🧪 Testing CommitPilot...")
        try:
            provider = config["DEFAULT"].get("api_provider", "aitunnel")
            token_map = {
                "aitunnel": ("aitunnel_token", "AI_TUNNEL", "AITUNNEL"),
                "huggingface": ("huggingface_token", None, "Hugging Face"),
                "openai": ("openai_token", None, "OpenAI")
            }
            config_key, env_key, name = token_map.get(provider, (None, None, provider))
            token = config["DEFAULT"].get(config_key, "") if config_key else ""
            if env_key:
                token = token or os.getenv(env_key, "")
            
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
        if provider.lower() == "aitunnel" and AITUNNEL_SUPPORT:
            commit_message = generate_commit_message_with_aitunnel(diff, status, config)
        elif provider.lower() == "openai" and OPENAI_SUPPORT:
            commit_message = generate_commit_message_with_openai(diff, status, config)
        else:
            if provider.lower() == "aitunnel" and not AITUNNEL_SUPPORT:
                logger.warning("AITUNNEL API selected but module not installed. Using Hugging Face.")
            elif provider.lower() == "openai" and not OPENAI_SUPPORT:
                logger.warning("OpenAI API selected but module not installed. Using Hugging Face.")
            commit_message = generate_commit_message_with_huggingface(diff, status, config)

    print(f'📝 {commit_message}')
    git_commit(commit_message)

    if not args.commit_only:
        branch = args.branch or config["DEFAULT"]["branch"]
        git_push(branch)


if __name__ == "__main__":
    main()
