from __future__ import annotations

import json
import subprocess
from typing import Any


def _run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"cmd": " ".join(cmd), "code": p.returncode, "out": p.stdout, "err": p.stderr}


def run_all() -> dict[str, Any]:
    checks = {
        "ruff": _run(["ruff", "check", "."]),
        "black": _run(["black", "--check", "."]),
        "mypy": _run(["mypy", "."]),
    }
    ok = all(v["code"] == 0 for v in checks.values())
    return {"ok": ok, "checks": checks}


if __name__ == "__main__":
    res = run_all()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit(0 if res["ok"] else 1)
