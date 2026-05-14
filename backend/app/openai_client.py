# backend/app/openai_client.py
import os
import requests

class OpenAIError(Exception):
    pass

class OpenAIClient:
    def __init__(self, api_key: str | None = None, timeout: int = 30):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout = timeout
        self.base = "https://api.openai.com/v1"

    def _headers(self):
        if not self.api_key:
            raise OpenAIError("OPENAI_API_KEY not set")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def simple_completion(self, prompt: str) -> str:
        url = f"{self.base}/chat/completions"
        payload = {
            "model": "gpt-4o-mini", 
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.7
        }
        try:
            r = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            raise OpenAIError(f"request failed: {e}")
        if r.status_code != 200:
            # try to extract message
            try:
                err = r.json()
            except Exception:
                err = r.text
            raise OpenAIError(f"OpenAI API error {r.status_code}: {err}")
        data = r.json()
        # safe extraction
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            raise OpenAIError("unexpected OpenAI response structure")
