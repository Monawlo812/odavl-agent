from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# اجبر إخراج الكونسول على UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def create_pr(owner: str, repo: str, head: str, base: str, title: str, body: str = "") -> dict:
    token = os.getenv("GH_TOKEN", "")
    if not token:
        raise RuntimeError("GH_TOKEN is not set")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = json.dumps({"title": title, "head": head, "base": base, "body": body}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    # هيدرز ASCII فقط
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = str(e)
        raise RuntimeError(f"HTTP {e.code}: {err_body}") from e


def main():
    if len(sys.argv) < 6:
        print("usage: python -m tools.gh_pr <owner> <repo> <head_branch> <base_branch> <title>")
        sys.exit(2)
    owner, repo, head, base, title = sys.argv[1:6]
    body = os.environ.get("PR_BODY", "")
    try:
        data = create_pr(owner, repo, head, base, title, body)
        print(
            json.dumps(
                {"ok": True, "pr_number": data.get("number"), "html_url": data.get("html_url")},
                ensure_ascii=False,
            )
        )
    except Exception as e:
        # اطبع الرسالة بنطاق ASCII إذا لزم
        msg = str(e)
        try:
            print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
        except Exception:
            print(
                json.dumps(
                    {"ok": False, "error": msg.encode("utf-8", "ignore").decode("utf-8", "ignore")},
                    ensure_ascii=True,
                )
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
