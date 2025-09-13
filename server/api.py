from fastapi import FastAPI
from pydantic import BaseModel

from orchestrator.main import run_orchestrator

app = FastAPI(title="Odavl Agent API", version="0.1.0")


class RunBody(BaseModel):
    goal_path: str = ""  # مثال: "goals/logging.yaml"
    dry_run: bool = True
    gate: bool = True
    git_auto: bool = False


@app.post("/run")
def run(body: RunBody):
    report = run_orchestrator(
        goal_path=body.goal_path,
        dry_run=body.dry_run,
        no_dry_run=not body.dry_run,
        write_report=True,
        gate=body.gate,
        git_auto=body.git_auto,
    )
    return {"ok": report.get("success", False), "report": report}
