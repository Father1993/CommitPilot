#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file: auto_commit.py
@description: Автоматизация git-коммитов с использованием AI для создания осмысленных сообщений
@author: CommitPilot Team
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
from typing import Dict, Optional, Any, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Константы
VERSION = "1.0.0"
CONFIG_FILE = Path('.commits', 'config.ini')
DEFAULT_COMMIT_MESSAGE = "chore: automatic changes commit"

# Импортируем модуль поддержки OpenAI, если он доступен
try:
    from .openai_support import generate_commit_message_with_openai
    OPENAI_SUPPORT = True
except (ImportError, ModuleNotFoundError):
    try:
        # Пробуем импортировать из текущей директории
        sys.path.append(str(Path(__file__).parent))
        from openai_support import generate_commit_message_with_openai
        OPENAI_SUPPORT = True
    except (ImportError, ModuleNotFoundError):
        OPENAI_SUPPORT = False
        logger.debug("Модуль поддержки OpenAI не найден. Будет использоваться только Hugging Face API.")

def setup_config() -> configparser.ConfigParser:
    """
    Создает конфигурационный файл, если он не существует, или читает существующий
    
    Returns:
        ConfigParser: Объект с настройками приложения
    """
    if not CONFIG_FILE.exists():
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'api_provider': 'huggingface',
            'huggingface_token': '',
            'openai_token': '',
            'branch': 'main',
            'max_diff_size': '5000'
        }
        
        os.makedirs(CONFIG_FILE.parent, exist_ok=True)
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        
        logger.info(f"✅ Создан конфигурационный файл {CONFIG_FILE}")
        logger.warning("⚠️ Пожалуйста, добавьте API токен для выбранного провайдера в файл конфигурации")
        return config
    
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config

def get_git_diff() -> str:
    """
    Получает изменения в git репозитории
    
    Returns:
        str: Текст с изменениями (git diff)
    
    Raises:
        SystemExit: При ошибке выполнения git команд
    """
    try:
        # Проверяем, отслеживаются ли файлы
        result = subprocess.run(['git', 'diff', '--cached'], capture_output=True, encoding='utf-8')
        if not result.stdout.strip():
            # Если нет отслеживаемых изменений, то смотрим неотслеживаемые
            result = subprocess.run(['git', 'diff'], capture_output=True, encoding='utf-8')
        
        # Защита от ошибки
        if not result.stdout:
            return ""
            
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"❌ Ошибка при получении git diff: {e}")
        sys.exit(1)

def get_git_status() -> str:
    """
    Получает статус git репозитория
    
    Returns:
        str: Текст со статусом git репозитория
    
    Raises:
        SystemExit: При ошибке выполнения git команд
    """
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, encoding='utf-8')
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"❌ Ошибка при получении git status: {e}")
        sys.exit(1)

def generate_commit_message_with_huggingface(diff: str, status: str, config: configparser.ConfigParser) -> str:
    """
    Генерирует сообщение коммита с помощью Hugging Face Inference API
    
    Args:
        diff: Текст изменений (git diff)
        status: Статус репозитория (git status)
        config: Конфигурация с настройками и API ключами
        
    Returns:
        str: Сгенерированное сообщение для коммита
        
    Raises:
        SystemExit: Если API ключ не настроен
    """
    token = config['DEFAULT'].get('huggingface_token', '')
    if not token:
        logger.error("❌ Hugging Face API токен не настроен. Обновите файл конфигурации.")
        # Для тестового режима не завершаем программу, а возвращаем стандартное сообщение
        if '--test' in sys.argv or '--get-message' in sys.argv:
            return DEFAULT_COMMIT_MESSAGE
        sys.exit(1)
    
    # Ограничиваем размер diff для API запроса
    max_size = int(config['DEFAULT'].get('max_diff_size', '5000'))
    if len(diff) > max_size:
        diff = diff[:max_size] + "\n... (truncated)"
        logger.debug(f"Размер diff превышает лимит. Обрезано до {max_size} символов.")
    
    # Используем модель Mixtral вместо Zephyr для лучших результатов
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Системный промпт и пользовательский промпт
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

    # Формируем запрос к API в формате chat completion
    payload = {
        "inputs": f"<s>[INST] {system_prompt} [/INST]</s>\n<s>[INST] {user_prompt} [/INST]",
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.2,
            "top_p": 0.95,
            "return_full_text": False
        }
    }
    
    try:
        logger.debug("Отправка запроса к Hugging Face API (Mixtral)...")
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        logger.debug(f"Ответ API: {result}")
        
        # Обработка ответа API
        if isinstance(result, list) and len(result) > 0:
            message = result[0].get('generated_text', '').strip()
            logger.debug(f"Сгенерированный текст: {message}")
            
            # Очищаем от возможных маркеров
            message = message.replace('</s>', '').strip()
            
            # Ищем строки в формате Conventional Commits
            lines = message.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(line.startswith(prefix) for prefix in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']):
                    return line
            
            # Если не нашли формат, возвращаем первую непустую строку
            for line in lines:
                if line.strip():
                    return line.strip()
            
            # Если сообщение одно и не содержит переносов строк, возвращаем его целиком
            if message and '\n' not in message:
                return message
                
        logger.warning("Не удалось извлечь сообщение из ответа API. Используется стандартное сообщение.")
        return DEFAULT_COMMIT_MESSAGE
    except Exception as e:
        logger.error(f"❌ Ошибка при запросе к Hugging Face API: {e}")
        return DEFAULT_COMMIT_MESSAGE

def git_add_all() -> None:
    """
    Добавляет все изменения в индекс
    
    Raises:
        SystemExit: При ошибке выполнения git команды
    """
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        logger.info("✅ Добавлены все изменения в индекс")
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении изменений: {e}")
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
        result = subprocess.run(['git', 'commit', '-m', message], capture_output=True, encoding='utf-8')
        if result.returncode == 0:
            logger.info(f"✅ Создан коммит с сообщением: \"{message}\"")
            return True
        else:
            logger.warning(f"⚠️ Не удалось создать коммит: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при создании коммита: {e}")
        sys.exit(1)

def git_push(branch: str) -> bool:
    """
    Отправляет изменения в удаленный репозиторий
    
    Args:
        branch: Имя ветки для отправки изменений
        
    Returns:
        bool: True если изменения отправлены успешно, False в случае ошибки
        
    Raises:
        SystemExit: При критической ошибке
    """
    try:
        result = subprocess.run(['git', 'push', 'origin', branch], capture_output=True, encoding='utf-8')
        if result.returncode == 0:
            logger.info(f"✅ Изменения отправлены в ветку {branch}")
            return True
        else:
            logger.warning(f"⚠️ Не удалось отправить изменения: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке изменений: {e}")
        sys.exit(1)

def generate_message_only(config: configparser.ConfigParser) -> str:
    """
    Генерирует только сообщение коммита без выполнения других действий
    
    Args:
        config: Конфигурация с настройками
    
    Returns:
        str: Сгенерированное сообщение для коммита
    """
    status = get_git_status()
    if not status:
        logger.warning("Нет изменений для анализа")
        return DEFAULT_COMMIT_MESSAGE
    
    diff = get_git_diff()
    if not diff:
        logger.warning("Пустой diff, нечего анализировать")
        return DEFAULT_COMMIT_MESSAGE
    
    # Выбираем провайдера AI
    provider = config['DEFAULT'].get('api_provider', 'huggingface')
    logger.debug(f"Используется провайдер AI: {provider}")
    
    if provider.lower() == 'openai' and OPENAI_SUPPORT:
        return generate_commit_message_with_openai(diff, status, config)
    else:
        if provider.lower() == 'openai' and not OPENAI_SUPPORT:
            logger.warning("OpenAI API выбран, но модуль не установлен. Используется Hugging Face.")
        return generate_commit_message_with_huggingface(diff, status, config)

def main():
    parser = argparse.ArgumentParser(description='CommitPilot - автоматизация git коммитов с AI-генерацией сообщений')
    parser.add_argument('-m', '--message', help='Пользовательское сообщение коммита (отключает AI-генерацию)')
    parser.add_argument('-b', '--branch', help='Ветка для push (по умолчанию из конфигурации)')
    parser.add_argument('-c', '--commit-only', action='store_true', help='Только коммит без push')
    parser.add_argument('-p', '--provider', choices=['huggingface', 'openai'], help='Провайдер AI (huggingface или openai)')
    parser.add_argument('--setup', action='store_true', help='Настройка конфигурации')
    parser.add_argument('--get-message', action='store_true', help='Только сгенерировать сообщение коммита и вывести его')
    parser.add_argument('--setup-hooks', action='store_true', help='Установить Git hooks')
    parser.add_argument('--test', action='store_true', help='Проверить работу с текущими настройками')
    parser.add_argument('-v', '--version', action='store_true', help='Показать версию')
    args = parser.parse_args()
    
    # Показать версию и выйти
    if args.version:
        print("CommitPilot v1.0.0")
        return

    # Загружаем или создаем конфигурацию
    config = setup_config()
    
    if args.get_message:
        # Только генерируем сообщение коммита
        message = generate_message_only(config)
        if message and message != DEFAULT_COMMIT_MESSAGE:
            print(f"Коммит: \"{message}\"")
        else:
            print("⚠️ Не удалось сгенерировать сообщение. Проверьте настройки API токена.")
        return
        
    # Тестирование системы
    if args.test:
        print("🧪 Проверка настроек CommitPilot...")
        if config['DEFAULT']['api_provider'] == 'huggingface':
            if config['DEFAULT']['huggingface_token']:
                print("✅ Hugging Face API токен настроен")
            else:
                print("❌ Hugging Face API токен не настроен")
        elif config['DEFAULT']['api_provider'] == 'openai':
            if config['DEFAULT']['openai_token']:
                print("✅ OpenAI API токен настроен")
            else:
                print("❌ OpenAI API токен не настроен")
                
        print(f"✅ Ветка по умолчанию: {config['DEFAULT']['branch']}")
        
        # Тестируем генерацию сообщения
        print("\n🧪 Генерация тестового сообщения...")
        test_message = generate_message_only(config)
        if test_message and test_message != DEFAULT_COMMIT_MESSAGE:
            print(f"✅ Тестовое сообщение: \"{test_message}\"")
        else:
            print("❌ Не удалось сгенерировать тестовое сообщение")
            
        print("\n✅ Проверка завершена")
        return
    
    if args.setup_hooks:
        # Устанавливаем Git hooks
        try:
            script_dir = Path(__file__).parent
            git_dir = Path().absolute() / '.git'
            
            if not git_dir.exists():
                print("❌ Директория .git не найдена. Вы находитесь в git-репозитории?")
                return
            
            hooks_dir = git_dir / 'hooks'
            hooks_dir.mkdir(exist_ok=True)
            
            # Копируем prepare-commit-msg хук
            src_hook = script_dir / 'prepare-commit-msg'
            dst_hook = hooks_dir / 'prepare-commit-msg'
            
            if not src_hook.exists():
                print(f"❌ Файл {src_hook} не найден")
                return
            
            # Копируем хук и делаем его исполняемым
            import shutil
            shutil.copy2(src_hook, dst_hook)
            os.chmod(dst_hook, 0o755)
            
            print(f"✅ Git hook установлен: {dst_hook}")
        except Exception as e:
            print(f"❌ Ошибка при установке Git hooks: {e}")
        return
    
    if args.setup:
        # Создаем файл конфигурации, если он не существует
        if not CONFIG_FILE.exists():
            setup_config()
            
        print("✅ Конфигурационный файл создан")
        print(f"📝 Пожалуйста, отредактируйте файл {CONFIG_FILE} вручную и добавьте ваш API токен")
        print("   Для получения токена Hugging Face: https://huggingface.co/settings/tokens")
        print("   Для получения токена OpenAI: https://platform.openai.com/api-keys")
        
        # Спрашиваем про установку Git hooks
        setup_hooks = input("Установить Git hooks для автоматической генерации сообщений коммитов? (y/n): ").lower() == 'y'
        if setup_hooks:
            args.setup_hooks = True
            main()  # Рекурсивно вызываем функцию для установки хуков
        
        # Проверяем работу системы
        print("\n🧪 Проверка работы CommitPilot...")
        try:
            # Проверяем валидность токена
            if config['DEFAULT']['api_provider'] == 'huggingface' and config['DEFAULT']['huggingface_token']:
                print("✅ Hugging Face API токен настроен")
                test_message = generate_message_only(config)
                if test_message and test_message != DEFAULT_COMMIT_MESSAGE:
                    print(f"✅ Пример сгенерированного сообщения: \"{test_message}\"")
                else:
                    print("⚠️ Не удалось сгенерировать тестовое сообщение")
            elif config['DEFAULT']['api_provider'] == 'openai' and config['DEFAULT']['openai_token']:
                print("✅ OpenAI API токен настроен")
                test_message = generate_message_only(config)
                if test_message and test_message != DEFAULT_COMMIT_MESSAGE:
                    print(f"✅ Пример сгенерированного сообщения: \"{test_message}\"")
                else:
                    print("⚠️ Не удалось сгенерировать тестовое сообщение")
            else:
                print("⚠️ API токен не настроен. Пожалуйста, добавьте его в config.ini")
        except Exception as e:
            print(f"⚠️ Ошибка при проверке: {e}")
        
        print("✅ Настройка CommitPilot завершена")
        return
    
    # Получаем статус git
    status = get_git_status()
    if not status:
        print("ℹ️ Нет изменений для коммита")
        return

    # Добавляем все изменения
    git_add_all()
    
    # Получаем diff
    diff = get_git_diff()
    
    # Генерируем или используем сообщение коммита
    if args.message:
        commit_message = args.message
    else:
        print("🤖 Генерация сообщения коммита с помощью AI...")
        
        # Выбираем провайдера AI
        provider = args.provider or config['DEFAULT'].get('api_provider', 'huggingface')
        
        if provider.lower() == 'openai' and OPENAI_SUPPORT:
            commit_message = generate_commit_message_with_openai(diff, status, config)
        else:
            commit_message = generate_commit_message_with_huggingface(diff, status, config)
    
    # Выводим сгенерированное сообщение перед созданием коммита
    print(f"📝 Сообщение коммита: \"{commit_message}\"")
    
    # Создаем коммит
    git_commit(commit_message)
    
    # Отправляем изменения, если не указан флаг --commit-only
    if not args.commit_only:
        branch = args.branch or config['DEFAULT']['branch']
        print(f"🚀 Отправка изменений в ветку {branch} с сообщением: \"{commit_message}\"...")
        git_push(branch)

if __name__ == "__main__":
    main() 