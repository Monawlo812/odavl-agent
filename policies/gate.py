from __future__ import annotations

import json
import os
import sys
from typing import Any


def evaluate(report: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    # 1) نجاح التنفيذ العام
    if not report.get("success", False):
        violations.append("Pipeline did not complete successfully.")

    # 2) عدد الملفات المتغيرة (نبسطه من النتائج)
    changed_paths = []
    for r in report.get("results", []):
        p = r.get("path")
        ok = r.get("ok", False)
        if ok and p and p not in changed_paths:
            changed_paths.append(p)
    if len(changed_paths) > int(policy.get("max_changed_files", 9999)):
        violations.append(f"Too many changed files: {len(changed_paths)}")

    # 3) تحقق من وجود ملاحظة خطة في README (PLAN)
    if policy.get("require_readme_plan_note", False):
        readme_ok = any(
            (r.get("path") == "README.md" and r.get("ok") is True)
            for r in report.get("results", [])
        )
        # تفحّص فعلي: يحتوي تقرير الخطة على meta؟ وإن لم يوجد، سنقبل إذا كان الإجراء append_readme_note نجح
        plan_step_done = any(
            (r.get("action") == "append_readme_note" and r.get("ok") is True)
            for r in report.get("results", [])
        )
        if not (readme_ok and plan_step_done):
            violations.append("README plan note missing.")

    # 4) فحوصات الجودة (ruff/black/mypy)
    if policy.get("require_quality_pass", False):
        q = report.get("quality", {})
        if not q or not q.get("ok", False):
            violations.append("Quality checks failed.")

    # 5) تحقق من وجود ملف السجل
    if policy.get("require_log_file", False):
        log_step_done = any(
            (r.get("path") == "memory/agent.log" and r.get("ok") is True)
            for r in report.get("results", [])
        )
        if not log_step_done:
            violations.append("Log file was not written.")

    return {"violations": violations, "changed_paths": changed_paths}


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m policies.gate <report.json> <policy.json>")
        sys.exit(2)
    report_path, policy_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(report_path) or not os.path.exists(policy_path):
        print("Report or policy file not found.")
        sys.exit(2)
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    with open(policy_path, encoding="utf-8") as f:
        policy = json.load(f)
    outcome = evaluate(report, policy)
    if outcome["violations"]:
        print("❌ Gate FAILED")
        for v in outcome["violations"]:
            print(" -", v)
        sys.exit(1)
    else:
        print("✅ Gate PASSED")
        print("Changed files:", ", ".join(outcome["changed_paths"]))
        sys.exit(0)


if __name__ == "__main__":
    main()
