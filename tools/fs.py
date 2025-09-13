from pathlib import Path


def read_text(path: str) -> str | None:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else None


def write_text(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
