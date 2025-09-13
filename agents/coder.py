from typing import Dict, Any
from tools.fs import read_text, write_text
from tools.router import LLMRouter

class Coder:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.router = LLMRouter(cfg)

    def run_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        action = step.get("action")
        path = step.get("path")
        coding_model = self.router.select_model(
            task_type="coding",
            risk="low",
            offline=self.cfg.get("runtime", {}).get("dry_run", True)
        )

        if action == "append_readme_note":
            note = step.get("note", "Odavl note.")
            current = read_text(path) or "# Odavl\n"
            new_content = current.rstrip() + f"\n\n> PLAN: {note}\n"
            write_text(path, new_content)
            return {"ok": True, "action": action, "path": path, "model": coding_model}

        if action == "append_readme":
            current = read_text(path) or "# Odavl\n"
            new_content = current.rstrip() + f"\n\n> Odavl Agent: local run ✓ (coding via: {coding_model}).\n"
            write_text(path, new_content)
            return {"ok": True, "action": action, "path": path, "model": coding_model}

        if action == "write_log":
            write_text(path, f"Odavl Agent log: proof-of-life ✓ (coding via: {coding_model})\n")
            return {"ok": True, "action": action, "path": path, "model": coding_model}

        return {"ok": False, "action": action, "error": "unknown action", "model": coding_model}
