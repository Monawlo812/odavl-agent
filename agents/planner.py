from typing import Any

from providers.llm import LLMProvider
from tools.router import LLMRouter


class Planner:
    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg
        self.router = LLMRouter(cfg)
        self.llm = LLMProvider(cfg)

    def make_plan(self, task: dict[str, Any]) -> dict[str, Any]:
        goal = task.get("goal", "Initialize Odavl and prove local loop")
        chosen_model = self.router.select_model(
            task_type="planning",
            risk="low",
            offline=self.cfg.get("runtime", {}).get("dry_run", True),
        )

        # اطلب ملاحظة تخطيط قصيرة من LLM (MOCK الآن لو dry_run=True)
        planning_hint = self.llm.generate("planning", f"Goal: {goal}")

        steps: list[dict[str, Any]] = [
            {"action": "append_readme", "path": "README.md"},
            {"action": "write_log", "path": "memory/agent.log"},
        ]

        if "logging" in goal.lower():
            steps.insert(
                0,
                {
                    "action": "append_readme_note",
                    "path": "README.md",
                    "note": "Planned: unify logging levels & reduce noise by ~30%.",
                },
            )

        return {
            "title": f"[Odavl] {goal}",
            "goal": goal,
            "steps": steps,
            "acceptance": task.get("acceptance", ["README updated", "log written"]),
            "meta": {"planning_model": chosen_model, "planning_hint": planning_hint},
        }
