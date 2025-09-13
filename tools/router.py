from __future__ import annotations
from typing import Optional, Dict, Any
import os, yaml

class LLMRouter:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.models_cfg = self._load_models_cfg()

    def _load_models_cfg(self) -> Dict[str, Any]:
        path = os.path.join(os.path.dirname(__file__), "..", "configs", "models.yaml")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def select_model(self, task_type: str, risk: str = "low", offline: bool = False) -> str:
        # منطق بسيط: offline أولًا، ثم planning/high، ثم coding
        if offline:
            return self._rule("offline") or "local"
        if task_type in ("planning",) or risk in ("high",):
            return self._rule("planning_or_high_risk") or "gpt-4.1"
        if task_type in ("coding",):
            return self._rule("coding") or "deepseek-coder"
        # افتراضي
        return "deepseek-coder"

    def _rule(self, when: str) -> Optional[str]:
        rules = (self.models_cfg.get("router") or {}).get("rules") or []
        for r in rules:
            if r.get("when") == when:
                return r.get("use")
        return None
