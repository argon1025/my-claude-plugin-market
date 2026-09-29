#!/usr/bin/env python3
# SessionStart 훅: startup·resume이면 위키 트리를 강제 정리(최대 3초 대기)한 뒤 현재 레포의 위키 주입 텍스트를 출력한다.
# 주입 텍스트는 scripts/generate_*.py 출력을 순서대로 합친 것이며, 어떤 실패에서도 출력 없이 종료 코드 0으로 끝낸다.
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN / "scripts"


def source():
    try:
        return json.loads(sys.stdin.read() or "{}").get("source") or "startup"
    except (ValueError, AttributeError):
        return "startup"


def sync_wiki(base, wiki):
    p = subprocess.Popen([sys.executable, str(SCRIPTS / "sync_wiki.py"), str(base), wiki["remote"], wiki["baseBranch"]],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass


def main():
    config = json.loads((PLUGIN / "config.json").read_text())
    base, ws = Path(config["wiki"]["baseRoot"]).expanduser(), Path(config["workspace"]["root"]).expanduser()
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    r = subprocess.run(["git", "-C", project, "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5)
    if r.returncode != 0 or not r.stdout.strip():
        return ""
    slug = re.split(r"[/:]", r.stdout.strip().rstrip("/"))[-1].lower().removesuffix(".git")
    if source() in ("startup", "resume") and (base / ".git").exists():
        sync_wiki(base, config["wiki"])
    if not (base / "registry.json").exists():
        return "# 위키 없음 — `/agent-wiki:init` 실행"
    domains = json.loads((base / "registry.json").read_text())["domains"]
    domain = next((d for d, g in domains.items() if slug in g.get("repos", {})), None)
    if domain is None:
        return f"# 위키 — 미등록 레포 {slug}, 등록은 `/agent-wiki:register`"
    key = f"{domain}/{slug}"
    blocks = []
    for name, *args in (("generate_wiki_rules.py", key), ("generate_repository_map.py", base, ws, key),
                        ("generate_document_list.py", base, key)):
        try:
            g = subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)], capture_output=True, text=True, timeout=5)
        except subprocess.TimeoutExpired:
            continue
        if g.returncode == 0 and g.stdout.strip():
            blocks.append(g.stdout.strip())
    return "\n\n".join(blocks)


if __name__ == "__main__":
    try:
        text = main()
    except Exception:
        text = ""
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))
