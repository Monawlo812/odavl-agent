from __future__ import annotations

import json
import os
from typing import Any

import requests


class LLMProvider:
    """
    موحّد استدعاء LLM بأسلوب متوافق مع OpenAI:
    - اضبط عبر متغيرات البيئة:
      LLM_PROVIDER=openai|deepseek|custom
      LLM_API_KEY=...
      LLM_MODEL=gpt-4o-mini  (أو deepseek-chat أو غيره)
      LLM_BASE_URL=اختياري (مثلاً DeepSeek: https://api.deepseek.com)
      LLM_TIMEOUT=30  (ثواني)
      LLM_DRY_RUN=1 لتعطيل الاستدعاء الفعلي
    """
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.dry_run = os.getenv("LLM_DRY_RUN", "1") == "1"

        # قواعد بسيطة للاعتماد على mock إذا مافي مفتاح
        if not self.api_key or self.provider == "mock":
            self.provider = "mock"
            self.dry_run = True

        # نقاط نهاية متوافقة مع OpenAI
        if not self.base_url:
            if self.provider == "openai":
                self.base_url = "https://api.openai.com"
            elif self.provider == "deepseek":
                self.base_url = "https://api.deepseek.com"
            else:
                self.base_url = "https://api.openai.com"  # افتراضي متوافق

    def generate(self, task_type: str, prompt: str) -> str:
        # Mock محلي مضمون
        if self.provider == "mock" or self.dry_run:
            if task_type == "planning":
                return "MOCK_PLAN: plan steps; update README; write log."
            if task_type == "coding":
                return "MOCK_CODE: small diff; safe change; note in README."
            return "MOCK_GENERIC: proceed safely."

        # استدعاء فعلي (Chat Completions)
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"You are Odavl {task_type} assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # متوافق مع OpenAI/DeepSeek (تحت choices[0].message.content)
            return (data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip() or "[empty]")
        except Exception as e:
            return f"[LLM_ERROR] {e}"
