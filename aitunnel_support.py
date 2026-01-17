#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file: aitunnel_support.py
@description: Модуль для генерации сообщений коммитов с помощью AITUNNEL API
@author: CommitPilot Team
@version: 1.0.0
@license: MIT
@requires: openai
"""

import logging
import configparser
from typing import Dict, Any

# Импортируем OpenAI SDK (AITUNNEL совместим с OpenAI API)
try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    import requests

# Настройка логгера
logger = logging.getLogger(__name__)

# Константы
DEFAULT_COMMIT_MESSAGE = "chore: automatic changes commit"
AITUNNEL_BASE_URL = "https://api.aitunnel.ru/v1/"

# Множество префиксов для быстрого поиска (оптимизация парсинга)
COMMIT_PREFIXES = frozenset(["feat", "fix", "docs", "style", "refactor", "test", "chore"])

def generate_commit_message_with_aitunnel(diff: str, status: str, config: configparser.ConfigParser) -> str:
    """
    Генерирует сообщение коммита с помощью AITUNNEL API
    
    Args:
        diff: Текст изменений (git diff)
        status: Статус репозитория (git status)
        config: Конфигурация с настройками и API ключами
        
    Returns:
        str: Сгенерированное сообщение для коммита
    """
    token = config['DEFAULT'].get('aitunnel_token', '')
    if not token:
        logger.error("❌ AITUNNEL API токен не настроен. Обновите файл конфигурации или .env файл.")
        return DEFAULT_COMMIT_MESSAGE
    
    # Получаем base_url из конфигурации или используем по умолчанию
    base_url = config['DEFAULT'].get('aitunnel_base_url', AITUNNEL_BASE_URL)
    
    # Получаем модель из конфигурации или используем по умолчанию
    model = config['DEFAULT'].get('aitunnel_model', 'deepseek-r1')
    
    # Ограничиваем размер diff для API запроса
    max_size = int(config['DEFAULT'].get('max_diff_size', '5000'))
    if len(diff) > max_size:
        diff = diff[:max_size] + "\n... (truncated)"
        logger.debug(f"Размер diff превышает лимит. Обрезано до {max_size} символов.")
    
    # Формируем промпт для модели
    prompt = f"""Analyze the git changes and create a brief but informative commit message.

Git Status:
{status}

Git Diff:
{diff}

Create a single-line commit message in format: type(scope): message
Where type is one of: feat, fix, docs, style, refactor, test, chore
Example: "feat(auth): add OAuth authentication"
Write only the commit message, without additional text."""
    
    # Используем OpenAI SDK (AITUNNEL совместим с OpenAI API)
    if OPENAI_SDK_AVAILABLE:
        try:
            logger.debug("Используется OpenAI SDK для AITUNNEL API...")
            client = OpenAI(
                api_key=token,
                base_url=base_url
            )
            
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that specializes in creating conventional commit messages."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            # Извлекаем сообщение из ответа
            message = completion.choices[0].message.content.strip()
            
            # Обрабатываем ответ для получения только строки коммита
            lines = message.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if any(line_stripped.startswith(prefix) for prefix in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']):
                    return line_stripped
            
            # Если не нашли формат, возвращаем первую непустую строку
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('```'):
                    return line_stripped
                    
            logger.debug(f"Не удалось найти формат в сообщении: {message}")
            return message
        except Exception as e:
            logger.error(f"❌ Ошибка при использовании AITUNNEL API: {e}")
            return DEFAULT_COMMIT_MESSAGE
    else:
        # Запасной вариант - HTTP запрос напрямую
        API_URL = f"{base_url}chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant that specializes in creating conventional commit messages."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.5
        }
        
        try:
            logger.debug("Отправка запроса к AITUNNEL API (HTTP)...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем сообщение из ответа
            message = result["choices"][0]["message"]["content"].strip()
            
            # Обрабатываем ответ для получения только строки коммита
            lines = message.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if any(line_stripped.startswith(prefix) for prefix in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']):
                    return line_stripped
            
            # Если не нашли формат, возвращаем первую непустую строку
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('```'):
                    return line_stripped
                    
            logger.debug(f"Не удалось найти формат в сообщении: {message}")
            return message
        except requests.exceptions.Timeout:
            logger.error("⏱️ Превышено время ожидания запроса к AITUNNEL API")
            return DEFAULT_COMMIT_MESSAGE
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сети при запросе к AITUNNEL API: {e}")
            return DEFAULT_COMMIT_MESSAGE
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к AITUNNEL API: {e}")
            return DEFAULT_COMMIT_MESSAGE
