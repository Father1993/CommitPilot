#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file: openai_support.py
@description: Модуль для генерации сообщений коммитов с помощью OpenAI API
@author: CommitPilot Team
@version: 1.0.0
@license: MIT
@requires: requests
"""

import requests
import logging
import configparser
from typing import Dict, Any

# Настройка логгера
logger = logging.getLogger(__name__)

# Константы
DEFAULT_COMMIT_MESSAGE = "chore: автоматический коммит изменений"

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
    prompt = f"""Проанализируй изменения в git и создай краткое, но информативное сообщение для коммита.
    
Статус изменений:
{status}

Изменения (diff):
{diff}

Создай однострочное сообщение коммита в формате: тип(область): сообщение
Где тип - один из: feat, fix, docs, style, refactor, test, chore
Например: "feat(auth): добавлена авторизация через OAuth"
Пиши только сообщение коммита, без дополнительного текста.
"""
    
    # Запрос к OpenAI API
    API_URL = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Ты - ассистент, который создает качественные сообщения для git-коммитов."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100,
        "temperature": 0.5
    }
    
    try:
        logger.debug("Отправка запроса к OpenAI API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Извлекаем сообщение из ответа
        message = result["choices"][0]["message"]["content"].strip()
        
        # Обрабатываем ответ для получения только строки коммита
        lines = message.split('\n')
        for line in lines:
            if any(line.startswith(prefix) for prefix in ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']):
                return line.strip()
        
        # Если не нашли формат, возвращаем первую непустую строку
        for line in lines:
            if line.strip() and not line.strip().startswith('```'):
                return line.strip()
                
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