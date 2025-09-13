import os
from typing import Any, cast

from providers.llm import LLMProvider
from tools.fs import read_text, write_text
from tools.guard import Guard
from tools.router import LLMRouter


class Coder:
    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg
        self.router = LLMRouter(cfg)
        self.llm = LLMProvider(cfg)
        self.guard = Guard(root=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    def _check(self, path: str) -> bool:
        return self.guard.is_allowed(path)

    def run_step(self, step: dict[str, Any]) -> dict[str, Any]:
        action = step.get("action")
        raw_path: Any = step.get("path")

        coding_model = self.router.select_model(
            task_type="coding",
            risk="low",
            offline=self.cfg.get("runtime", {}).get("dry_run", True),
        )

        # زر الإيقاف
        if self.guard.kill_switch_tripped():
            return {
                "ok": False,
                "action": action,
                "path": raw_path,
                "model": coding_model,
                "error": "kill-switch tripped",
            }

        # تأكيد وجود path ونوعه
        if raw_path is None or not isinstance(raw_path, str):
            return {
                "ok": False,
                "action": action,
                "path": raw_path,
                "model": coding_model,
                "error": "missing or invalid path",
            }
        path: str = cast(str, raw_path)

        # تحقق الأذونات لكل خطوة تلامس ملفات
        file_actions = {"append_readme_note", "append_readme", "write_log"}
        if action in file_actions and not self._check(path):
            return {
                "ok": False,
                "action": action,
                "path": path,
                "model": coding_model,
                "error": "path not permitted or protected",
            }

        if action == "append_readme_note":
            note = step.get("note", "Odavl note.")
            current = read_text(path) or "# Odavl\n"
            extra = self.llm.generate("coding", f"Add note in README for: {note}")
            new_content = current.rstrip() + f"\n\n> PLAN: {note}\n> LLM: {extra}\n"
            write_text(path, new_content)
            return {"ok": True, "action": action, "path": path, "model": coding_model}

        if action == "append_readme":
            current = read_text(path) or "# Odavl\n"
            extra = self.llm.generate("coding", "Append success marker.")
            new_content = (
                current.rstrip()
                + f"\n\n> Odavl Agent: local run ✓ (coding via: {coding_model}).\n> LLM: {extra}\n"
            )
            write_text(path, new_content)
            return {"ok": True, "action": action, "path": path, "model": coding_model}

        if action == "write_log":
            extra = self.llm.generate("coding", "Write a short log line.")
            write_text(
                path,
                f"Odavl Agent log: proof-of-life ✓ (coding via: {coding_model}) | {extra}\n",
            )
            return {"ok": True, "action": action, "path": path, "model": coding_model}

        return {
            "ok": False,
            "action": action,
            "path": path,
            "model": coding_model,
            "error": "unknown action",
        }
