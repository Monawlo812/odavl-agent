from typing import Dict, Any
import yaml, json, os, sys, argparse, subprocess
from agents.planner import Planner
from agents.coder import Coder
from policies.risk import RiskScorer

DEFAULT_TASK = {
    "goal": "Initialize Odavl repo and prove local loop",
    "acceptance": ["README updated", "log written"]
}

def load_cfg() -> Dict[str, Any]:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "configs", "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def load_goal(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return DEFAULT_TASK
    with open(path, "r", encoding="utf-8") as f:
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
    p.add_argument("--gate", action="store_true", help="Run gate using policies/config.json and report.json")
    return p.parse_args()

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
    risk = RiskScorer(cfg)

    print("== Perceive ==")
    task = load_goal(args.goal)
    print(json.dumps(task, ensure_ascii=False, indent=2))

    print("== Plan ==")
    plan = planner.make_plan(task)
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    print("== Act ==")
    results = []
    for step in plan["steps"]:
        res = coder.run_step(step)
        results.append(res)
        print(" step:", res)

    print("== Check ==")
    success = all(r.get("ok") for r in results)
    report = {"success": success, "results": results, "plan": plan}
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("== Risk ==")
    r = risk.score(report)
    print(json.dumps(r, ensure_ascii=False, indent=2))

    # كتابة تقرير JSON لاستخدامه في الـ Gate
    report_path = os.path.join(os.path.dirname(__file__), "..", "memory", "report.json")
    if args.write_report or args.gate:
        os.makedirs(os.path.join(os.path.dirname(__file__), "..", "memory"), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Report written to {report_path}")

    # استدعاء Gate كموديول (اختياري)
    if args.gate:
        policy_path = os.path.join(os.path.dirname(__file__), "..", "policies", "config.json")
        print("== Gate ==")
        cmd = [sys.executable, "-m", "policies.gate", report_path, policy_path]
        ret = subprocess.call(cmd)
        if ret != 0:
            print("Gate failed. Exiting with non-zero code.")
            sys.exit(ret)

    print("== Done ==")
    if success:
        print("Local loop succeeded ✓")
    else:
        print("Local loop failed ✗")

if __name__ == "__main__":
    main()
