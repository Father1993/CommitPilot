#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module for generating commit messages using OpenAI API."""

import logging
import configparser

from ai_common import (
    DEFAULT_COMMIT_MESSAGE,
    build_user_prompt,
    chat_completion,
    truncate_diff,
)

logger = logging.getLogger(__name__)


def generate_commit_message_with_openai(diff: str, status: str, config: configparser.ConfigParser) -> str:
    token = config["DEFAULT"].get("openai_token", "")
    if not token:
        logger.error("❌ OpenAI API token not configured. Update config file.")
        return DEFAULT_COMMIT_MESSAGE

    prompt = build_user_prompt(status, truncate_diff(diff, config, "5000"))

    return chat_completion(
        api_key=token,
        prompt=prompt,
        model="gpt-4o-mini",
        http_model="gpt-3.5-turbo",
        api_name="OpenAI API",
        timeout=10,
        sdk_log="Using new OpenAI SDK...",
        http_log="Sending request to OpenAI API (HTTP)...",
        sdk_error="OpenAI SDK",
    )
