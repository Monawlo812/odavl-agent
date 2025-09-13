from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class Guard:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.cfg = self._load_security_cfg()

    def _load_security_cfg(self) -> dict[str, Any]:
        path = self.root / "configs" / "security.yaml"
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def kill_switch_tripped(self) -> bool:
        ks = self.cfg.get("kill_switch", "memory/STOP")
        return (self.root / ks).exists()

    def is_allowed(self, rel_path: str) -> bool:
        """
        يسمح فقط بمسارات ضمن permit_paths وغير متقاطعة مع protected_paths.
        """
        p = (self.root / rel_path).resolve()
        # منع الخروج من الجذر
        if self.root not in p.parents and p != self.root:
            return False

        # المحمية؟
        for prot in self.cfg.get("protected_paths", []):
            prot_p = (self.root / prot).resolve()
            if p == prot_p or prot_p in p.parents:
                return False

        # المسموح؟
        permit = self.cfg.get("permit_paths", [])
        if not permit:
            return True  # لا قيود
        for allow in permit:
            a = (self.root / allow).resolve()
            if p == a or a in p.parents or a == p.parent:
                return True
        return False
