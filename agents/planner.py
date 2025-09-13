from typing import Dict, Any, List
from tools.router import LLMRouter

class Planner:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.router = LLMRouter(cfg)

    def make_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("goal", "Initialize Odavl and prove local loop")
        chosen_model = self.router.select_model(
            task_type="planning",
            risk="low",
            offline=self.cfg.get("runtime", {}).get("dry_run", True)
        )

        steps: List[Dict[str, Any]] = [
            {"action": "append_readme", "path": "README.md"},
            {"action": "write_log", "path": "memory/agent.log"}
        ]

        # لو الهدف فيه logging أضف سطر خطة بسيط في README لإثبات الفهم
        if "logging" in goal.lower():
            steps.insert(0, {"action": "append_readme_note", "path": "README.md", "note": "Planned: unify logging levels & reduce noise by ~30%."})

        return {
            "title": f"[Odavl] {goal}",
            "goal": goal,
            "steps": steps,
            "acceptance": task.get("acceptance", ["README updated", "log written"]),
            "meta": {
                "planning_model": chosen_model
            }
        }
