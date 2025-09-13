import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any

import yaml

from agents.coder import Coder
from agents.planner import Planner
from policies.risk import RiskScorer
from tools import git_local
from tools.quality import run_all as run_quality

DEFAULT_TASK = {
    "goal": "Initialize Odavl repo and prove local loop",
    "acceptance": ["README updated", "log written"],
}


def load_cfg() -> dict[str, Any]:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "configs", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def load_goal(path: str) -> dict[str, Any]:
    if not path or not os.path.exists(path):
        return DEFAULT_TASK
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        data.setdefault("goal", "Unnamed goal")
        data.setdefault("acceptance", [])
        return data


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Odavl Orchestrator")
    p.add_argument("--goal", type=str, default="", help="Path to goal YAML")
    p.add_argument("--dry-run", action="store_true", help="Force dry_run mode")
    p.add_argument("--no-dry-run", action="store_true", help="Force disable dry_run")
    p.add_argument("--write-report", action="store_true", help="Write report to memory/report.json")
    p.add_argument(
        "--gate", action="store_true", help="Run gate using policies/config.json and report.json"
    )
    p.add_argument(
        "--git-auto",
        action="store_true",
        help="Auto: create feature branch, commit, and merge to main if gate passes",
    )
    return p.parse_args()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60] or "change"


def run_gate(report: dict[str, Any]) -> int:
    # كتابة التقرير
    report_path = os.path.join(os.path.dirname(__file__), "..", "memory", "report.json")
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "memory"), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    # استدعاء gate
    policy_path = os.path.join(os.path.dirname(__file__), "..", "policies", "config.json")
    print("== Gate ==")
    return subprocess.call([sys.executable, "-m", "policies.gate", report_path, policy_path])


def run_orchestrator(
    goal_path: str = "",
    dry_run: bool | None = None,
    no_dry_run: bool | None = None,
    write_report: bool = False,
    gate: bool = False,
    git_auto: bool = False,
) -> dict:
    """
    واجهة برمجية لتشغيل الأوركستريتور مرة واحدة وإرجاع تقرير مبسّط.
    """

    class _Args:
        def __init__(self):
            self.goal = goal_path or ""
            self.dry_run = bool(dry_run) if dry_run is not None else False
            self.no_dry_run = bool(no_dry_run) if no_dry_run is not None else False
            self.write_report = bool(write_report)
            self.gate = bool(gate)
            self.git_auto = bool(git_auto)

    args = _Args()
    cfg = load_cfg()

    runtime = cfg.setdefault("runtime", {})
    if args.dry_run:
        runtime["dry_run"] = True
    if args.no_dry_run:
        runtime["dry_run"] = False

    planner = Planner(cfg)
    coder = Coder(cfg)
    _risk = RiskScorer(cfg)

    task = load_goal(args.goal)
    plan = planner.make_plan(task)

    results = []
    for step in plan["steps"]:
        res = coder.run_step(step)
        results.append(res)

    success = all(r.get("ok") for r in results)
    quality = run_quality()
    report = {"success": success, "results": results, "plan": plan, "quality": quality}

    if args.gate or args.write_report or args.git_auto:
        _ = args  # keep signature same as CLI path
        # ret removed (unused)
        # إعادة استخدام منطق الـ Gate والـ git-auto عبر استدعاء الـ main بسطر أوامر لتجنّب التكرار
        import subprocess
        import sys

        cmd = [sys.executable, "-m", "orchestrator.main"]
        if goal_path:
            cmd += ["--goal", goal_path]
        if dry_run:
            cmd += ["--dry-run"]
        if no_dry_run:
            cmd += ["--no-dry-run"]
        if write_report or git_auto:
            cmd += ["--write-report"]
        if gate or git_auto:
            cmd += ["--gate"]
        if git_auto:
            cmd += ["--git-auto"]
        # نشغّل المسار الكامل لكتابة التقرير/الـ Gate/الـ git
        subprocess.run(cmd, check=False)

    return report


def main():
    args = parse_args()
    cfg = load_cfg()

    runtime = cfg.setdefault("runtime", {})
    if args.dry_run:
        runtime["dry_run"] = True
    if args.no_dry_run:
        runtime["dry_run"] = False

    planner = Planner(cfg)
    coder = Coder(cfg)
    _risk = RiskScorer(cfg)

    print("== Perceive ==")
    task = load_goal(args.goal)
    print(json.dumps(task, ensure_ascii=False, indent=2))

    feature_branch = None
    if args.git_auto:
        base = slugify(task.get("goal", "change"))
        feature_branch = f"odavl/{base}"
        try:
            git_local.new_branch(feature_branch)
        except Exception:
            # الفرع موجود؟ جرّب checkout بدل ما تفشل
            try:
                git_local.checkout(feature_branch)
            except Exception as e:
                print("Git: cannot switch to feature branch:", e)

        print(f"Git feature branch: {feature_branch}")

    print("== Plan ==")
    plan = planner.make_plan(task)
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    print("== Act ==")
    # Kill-switch check
    import os

    from tools.guard import Guard

    guard = Guard(root=os.path.dirname(__file__) + "/..")
    if guard.kill_switch_tripped():
        print("Kill-switch detected. Aborting before Act.")
        return
    results: list[dict[str, Any]] = []
    for step in plan["steps"]:
        res = coder.run_step(step)
        results.append(res)
        print(" step:", res)

    print("== Check ==")
    success = all(r.get("ok") for r in results)
    quality = run_quality()
    report = {"success": success, "results": results, "plan": plan, "quality": quality}
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("== Risk ==")
    r = _risk.score(report)
    print(json.dumps(r, ensure_ascii=False, indent=2))

    # ret removed (unused)
    if args.gate or args.git_auto:
        ret = run_gate(report)
        if ret != 0:
            print("Gate failed. No merge.")

    if args.git_auto:
        # حدد الملفات التي غيّرها الوكيل + التقرير
        files = set()
        for rr in results:
            p = rr.get("path")
            if rr.get("ok") and p:
                files.add(p)
        files.add(os.path.join("memory", "report.json"))
        # أضف فقط إن وُجدت
        from os.path import exists

        staged = []
        for f in sorted(files):
            if exists(f):
                staged.append(f)
        git_local.add(staged)
        # لو ما في staged changes، تخطَ الـ commit بدل الفشل
        if git_local.has_staged_changes():
            msg = plan.get("title", "Odavl change")
            committed = git_local.commit(f"{msg}\n\nAuto-committed by Odavl agent.")
            print("Git: commit", "✓" if committed else "skipped (no changes).")
        else:
            print("Git: no changes to commit (skipped).")
        # دمج إلى main لو الـ gate نجح
        if ret == 0 and feature_branch:
            try:
                git_local.merge_to_main(feature_branch)
                print("Git: merged to main ✓")
            except Exception as e:
                print("Git merge skipped/error:", e)

    print("== Done ==")
    if success:
        print("Local loop succeeded ✓")
    else:
        print("Local loop failed ✗")


if __name__ == "__main__":
    main()
