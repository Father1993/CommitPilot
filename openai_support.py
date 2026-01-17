#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file: openai_support.py
@description: Module for generating commit messages using OpenAI API
@author: CommitPilot Team
@version: 1.0.0
@license: MIT
@requires: openai
"""

import logging
import configparser
from typing import Dict, Any

# Import OpenAI SDK
try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    import requests

# Configure logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_COMMIT_MESSAGE = "chore: automatic changes commit"

# Set of prefixes for fast search (parsing optimization)
COMMIT_PREFIXES = frozenset(["feat", "fix", "docs", "style", "refactor", "test", "chore"])

def generate_commit_message_with_openai(diff: str, status: str, config: configparser.ConfigParser) -> str:
    """
    Generate commit message using OpenAI API
    
    Args:
        diff: Changes text (git diff)
        status: Repository status (git status)
        config: Configuration with settings and API keys
        
    Returns:
        str: Generated commit message
    """
    token = config['DEFAULT'].get('openai_token', '')
    if not token:
        logger.error("❌ OpenAI API token not configured. Update config file.")
        return DEFAULT_COMMIT_MESSAGE
    
    # Limit diff size for API request
    max_size = int(config['DEFAULT'].get('max_diff_size', '5000'))
    if len(diff) > max_size:
        diff = diff[:max_size] + "\n... (truncated)"
        logger.debug(f"Diff size exceeds limit. Truncated to {max_size} characters.")
    
    # Form prompt for the model
    prompt = f"""Analyze the git changes and create a brief but informative commit message in Conventional Commits format.

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
    
    # Use new SDK if available
    if OPENAI_SDK_AVAILABLE:
        try:
            logger.debug("Using new OpenAI SDK...")
            client = OpenAI(api_key=token)
            
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at creating high-quality commit messages in Conventional Commits format. Your messages must be informative, specific, and understandable for both developers and AI systems. Always use the format type(scope): description with specific details of changes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            # Extract message from response
            message = completion.choices[0].message.content.strip()
            
            # Process response to get only commit line (optimized)
            lines = message.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if any(line_stripped.startswith(prefix) for prefix in COMMIT_PREFIXES):
                    return line_stripped
            
            # If format not found, return first non-empty line
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('```'):
                    return line_stripped
                    
            logger.debug(f"Failed to find format in message: {message}")
            return message
        except Exception as e:
            logger.error(f"❌ Error using OpenAI SDK: {e}")
            return DEFAULT_COMMIT_MESSAGE
    else:
        # Fallback - old method via HTTP request
        API_URL = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an expert at creating high-quality commit messages in Conventional Commits format. Your messages must be informative, specific, and understandable for both developers and AI systems. Always use the format type(scope): description with specific details of changes."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        try:
            logger.debug("Sending request to OpenAI API (HTTP)...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Extract message from response
            message = result["choices"][0]["message"]["content"].strip()
            
            # Process response to get only commit line (optimized)
            lines = message.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if any(line_stripped.startswith(prefix) for prefix in COMMIT_PREFIXES):
                    return line_stripped
            
            # If format not found, return first non-empty line
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('```'):
                    return line_stripped
                    
            logger.debug(f"Failed to find format in message: {message}")
            return message
        except requests.exceptions.Timeout:
            logger.error("⏱️ Request timeout to OpenAI API")
            return DEFAULT_COMMIT_MESSAGE
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error requesting OpenAI API: {e}")
            return DEFAULT_COMMIT_MESSAGE
        except Exception as e:
            logger.error(f"❌ Error requesting OpenAI API: {e}")
            return DEFAULT_COMMIT_MESSAGE 