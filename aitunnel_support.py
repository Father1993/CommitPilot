#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module for generating commit messages using AITUNNEL API."""

import logging
import configparser

from ai_common import (
    DEFAULT_COMMIT_MESSAGE,
    build_user_prompt,
    chat_completion,
    truncate_diff,
)

logger = logging.getLogger(__name__)

AITUNNEL_BASE_URL = "https://api.aitunnel.ru/v1/"


def generate_commit_message_with_aitunnel(diff: str, status: str, config: configparser.ConfigParser) -> str:
    token = config["DEFAULT"].get("aitunnel_token", "")
    if not token:
        logger.error("❌ AITUNNEL API token not configured. Update config file or .env file.")
        return DEFAULT_COMMIT_MESSAGE

    base_url = config["DEFAULT"].get("aitunnel_base_url", AITUNNEL_BASE_URL)
    model = config["DEFAULT"].get("aitunnel_model", "gpt-4.1")
    prompt = build_user_prompt(status, truncate_diff(diff, config, "5000"))

    return chat_completion(
        api_key=token,
        prompt=prompt,
        model=model,
        api_name="AITUNNEL API",
        base_url=base_url,
        timeout=30,
        sdk_log="Using OpenAI SDK for AITUNNEL API...",
        http_log="Sending request to AITUNNEL API (HTTP)...",
    )
