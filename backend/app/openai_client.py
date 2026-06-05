import os
import asyncio
from typing import Optional

import aiohttp

# Модель DeepSeek через OpenRouter
MODEL_NAME = "deepseek/deepseek-chat-v3-0324"

# Ключ берём из Render
OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")


def _require_api_key():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in environment")


async def create_completion(prompt: str, timeout: int = 30) -> str:
    _require_api_key()

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    timeout_cfg = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                text = await resp.text()

                if resp.status != 200:
                    raise RuntimeError(
                        f"OpenRouter API error {resp.status}: {text}"
                    )

                data = await resp.json()

        except asyncio.TimeoutError:
            raise RuntimeError("OpenRouter request timed out")

    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError("Malformed OpenRouter response: " + str(e))
