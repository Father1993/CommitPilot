#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file: openai_support.py
@description: Модуль для генерации сообщений коммитов с помощью OpenAI API
@author: CommitPilot Team
@version: 1.0.0
@license: MIT
@requires: openai
"""

import logging
import configparser
from typing import Dict, Any

# Импортируем OpenAI SDK
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

# Множество префиксов для быстрого поиска (оптимизация парсинга)
COMMIT_PREFIXES = frozenset(["feat", "fix", "docs", "style", "refactor", "test", "chore"])

def generate_commit_message_with_openai(diff: str, status: str, config: configparser.ConfigParser) -> str:
    """
    Генерирует сообщение коммита с помощью OpenAI API
    
    Args:
        diff: Текст изменений (git diff)
        status: Статус репозитория (git status)
        config: Конфигурация с настройками и API ключами
        
    Returns:
        str: Сгенерированное сообщение для коммита
    """
    token = config['DEFAULT'].get('openai_token', '')
    if not token:
        logger.error("❌ OpenAI API токен не настроен. Обновите файл конфигурации.")
        return DEFAULT_COMMIT_MESSAGE
    
    # Ограничиваем размер diff для API запроса
    max_size = int(config['DEFAULT'].get('max_diff_size', '5000'))
    if len(diff) > max_size:
        diff = diff[:max_size] + "\n... (truncated)"
        logger.debug(f"Размер diff превышает лимит. Обрезано до {max_size} символов.")
    
    # Формируем промпт для модели
    prompt = f"""Проанализируй изменения в git и создай краткое, но информативное сообщение коммита в формате Conventional Commits.

Статус изменений:
{status}

Изменения (diff):
{diff}

Требования к сообщению:
1. Формат: type(scope): краткое описание
2. Тип (type): feat, fix, docs, style, refactor, test, chore
3. Область (scope): модуль/компонент, который изменился (опционально, но желательно)
4. Описание: что именно изменилось и зачем (максимум 50 символов)

Примеры хороших сообщений:
- feat(auth): add OAuth2 authentication flow
- fix(api): resolve timeout error in user endpoint
- docs(readme): update installation instructions
- refactor(core): optimize database query performance
- style(ui): improve button spacing and colors

Важно:
- Будь конкретным: что изменилось, а не просто "update code"
- Используй scope для группировки изменений
- Пиши на английском языке
- Избегай общих фраз типа "update", "fix", "change"
- Указывай конкретную функциональность или проблему

Верни только сообщение коммита, без дополнительных объяснений."""
    
    # Используем новый SDK если доступен
    if OPENAI_SDK_AVAILABLE:
        try:
            logger.debug("Используется новый OpenAI SDK...")
            client = OpenAI(api_key=token)
            
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по созданию качественных сообщений коммитов в формате Conventional Commits. Твои сообщения должны быть информативными, конкретными и понятными как для разработчиков, так и для AI-систем. Всегда используй формат type(scope): описание с конкретными деталями изменений."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            # Извлекаем сообщение из ответа
            message = completion.choices[0].message.content.strip()
            
            # Обрабатываем ответ для получения только строки коммита (оптимизировано)
            lines = message.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if any(line_stripped.startswith(prefix) for prefix in COMMIT_PREFIXES):
                    return line_stripped
            
            # Если не нашли формат, возвращаем первую непустую строку
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('```'):
                    return line_stripped
                    
            logger.debug(f"Не удалось найти формат в сообщении: {message}")
            return message
        except Exception as e:
            logger.error(f"❌ Ошибка при использовании OpenAI SDK: {e}")
            return DEFAULT_COMMIT_MESSAGE
    else:
        # Запасной вариант - старый метод через HTTP запрос
        API_URL = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Ты эксперт по созданию качественных сообщений коммитов в формате Conventional Commits. Твои сообщения должны быть информативными, конкретными и понятными как для разработчиков, так и для AI-систем. Всегда используй формат type(scope): описание с конкретными деталями изменений."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        try:
            logger.debug("Отправка запроса к OpenAI API (HTTP)...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем сообщение из ответа
            message = result["choices"][0]["message"]["content"].strip()
            
            # Обрабатываем ответ для получения только строки коммита (оптимизировано)
            lines = message.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if any(line_stripped.startswith(prefix) for prefix in COMMIT_PREFIXES):
                    return line_stripped
            
            # Если не нашли формат, возвращаем первую непустую строку
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('```'):
                    return line_stripped
                    
            logger.debug(f"Не удалось найти формат в сообщении: {message}")
            return message
        except requests.exceptions.Timeout:
            logger.error("⏱️ Превышено время ожидания запроса к OpenAI API")
            return DEFAULT_COMMIT_MESSAGE
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сети при запросе к OpenAI API: {e}")
            return DEFAULT_COMMIT_MESSAGE
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к OpenAI API: {e}")
            return DEFAULT_COMMIT_MESSAGE 