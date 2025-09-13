from __future__ import annotations

import subprocess


def run(cmd: list[str], cwd: str | None = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"git error: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()


def current_branch() -> str:
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def ensure_main_branch() -> None:
    try:
        run(["git", "rev-parse", "--verify", "main"])
    except Exception:
        # لو ما في main، سمّي الحالي main
        run(["git", "branch", "-M", "main"])


def new_branch(name: str) -> str:
    # يحاول إنشاء فرع جديد
    run(["git", "checkout", "-b", name])
    return name


def checkout(name: str) -> None:
    run(["git", "checkout", name])


def add(paths: list[str]) -> None:
    if not paths:
        return
    run(["git", "add"] + paths)


def has_staged_changes() -> bool:
    # أي شيء staged؟
    try:
        out = run(["git", "diff", "--cached", "--name-only"])
    except Exception:
        return False
    return bool(out.strip())


def commit(message: str) -> bool:
    try:
        run(["git", "commit", "-m", message])
        return True
    except Exception:
        # غالبًا لا يوجد أي تغييرات staged
        return False


def merge_to_main(from_branch: str) -> None:
    ensure_main_branch()
    run(["git", "checkout", "main"])
    # استخدم --no-ff لمرئيّة الدمج
    run(
        [
            "git",
            "merge",
            "--no-ff",
            from_branch,
            "-m",
            f"merge({from_branch}): auto-merge by odavl agent",
        ]
    )


def changed_files_porcelain() -> list[str]:
    try:
        out = run(["git", "status", "--porcelain"])
    except Exception:
        return []
    files = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        files.append(parts[-1])
    return files
