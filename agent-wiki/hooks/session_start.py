#!/usr/bin/env python3
# SessionStart 훅: 새 세션(startup·resume·clear)이면 위키 트리를 강제 정리(최대 3초 대기)한 뒤 현재 레포의 위키 주입 텍스트를 출력한다.
# 주입 텍스트는 scripts/generate_*.py 출력을 순서대로 합친 것이며, 같은 생성기의 --full 출력으로 {baseRoot}/.local/index/{domain}/{slug}.md 색인을 세션마다 쓴다.
# 어떤 실패에서도 종료 코드 0으로 끝내고, 로드 상태와 실패는 사용자 알림(systemMessage)으로 알린다.
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN / "scripts"
LIMIT = 10000


def source():
    try:
        return json.loads(sys.stdin.read() or "{}").get("source") or "startup"
    except (ValueError, AttributeError):
        return "startup"


def sync_wiki(base, wiki):
    p = subprocess.Popen([sys.executable, str(SCRIPTS / "sync_wiki.py"), str(base), wiki["remote"], wiki["baseBranch"]],
                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    try:
        out, _ = p.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        return "3초 초과, 이전 사본으로 로드함"
    if p.returncode == 0:
        return None
    return next((l.removeprefix("fail ").strip() for l in out.splitlines() if l.strip()), "") or f"exit {p.returncode}"


def generate(name, *args):
    try:
        g = subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)], capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    return g.stdout.strip() if g.returncode == 0 else None


def write_index(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def notice(first, warnings):
    return "\n".join([first, *(f"- {w}" for w in warnings)])


def synced_at(base):
    try:
        t = datetime.fromtimestamp((base / ".git" / "FETCH_HEAD").stat().st_mtime)
    except OSError:
        return "위키 동기화 기록 없음"
    return f"위키 동기화 {t.month}월 {t.day}일 {t:%H:%M}"


def main():
    config = json.loads((PLUGIN / "config.json").read_text())
    base, ws = Path(config["wiki"]["baseRoot"]).expanduser(), Path(config["workspace"]["root"]).expanduser()
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    r = subprocess.run(["git", "-C", project, "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5)
    if r.returncode != 0 or not r.stdout.strip():
        return "", ""
    slug = re.split(r"[/:]", r.stdout.strip().rstrip("/"))[-1].lower().removesuffix(".git")
    sync_fail = None
    if source() in ("startup", "resume", "clear") and (base / ".git").exists():
        sync_fail = sync_wiki(base, config["wiki"])
    warnings = [f"위키 최신화 실패 : {sync_fail}"] if sync_fail else []
    if not (base / "registry.json").exists():
        return ("# 위키 없음 — `/agent-wiki:init` 실행",
                "위키 초기 구성을 진행하지 않았습니다. 위키를 적용하지 않습니다. 먼저 /agent-wiki:init을 실행해 위키 초기 세팅을 진행하세요")
    domains = json.loads((base / "registry.json").read_text())["domains"]
    domain = next((d for d, g in domains.items() if slug in g.get("repos", {})), None)
    if domain is None:
        return f"# 위키 — 미등록 레포 {slug}, 등록은 `/agent-wiki:register`", notice(
            f"알 수 없는 프로젝트({slug})입니다. 위키를 적용하지 않습니다. 프로젝트는 /agent-wiki:register를 통해 등록하세요", warnings)
    key, index = f"{domain}/{slug}", base / ".local" / "index" / domain / f"{slug}.md"
    full = [generate("generate_repository_map.py", base, ws, key, "--full"), generate("generate_document_list.py", base, key, "--full")]
    try:
        write_index(index, "\n\n".join([f"# 위키 색인 — {key}", *filter(None, full)]) + "\n")
    except OSError:
        index = None
    blocks = {"위키 규칙": generate("generate_wiki_rules.py", key, *([index] if index else [])),
              "레포 지도": generate("generate_repository_map.py", base, ws, key),
              "문서 목록": generate("generate_document_list.py", base, key)}
    text = "\n\n".join(filter(None, blocks.values()))
    failed = [name for name, b in blocks.items() if b is None] + (["색인 파일"] if None in full or index is None else [])
    if len(text) > LIMIT:
        warnings.append(f"위키 세션훅 주입 한도 초과 상태({len(text):,}자 / {LIMIT:,}자), 문서를 정리하세요")
    if failed:
        warnings.append(f"위키 작동 실패 : {'·'.join(failed)} 생성 실패")
    if not text:
        return "", notice(f"{key} 프로젝트 위키를 로드하지 못했습니다.", warnings)
    docs = base / "knowledge" / domain
    counts = [sum(f.is_file() for f in folder.glob("*.md")) for folder in (docs, docs / slug)]
    return text, notice(f"{key} 프로젝트 위키가 로드되었습니다. "
                        f"(도메인 문서 {counts[0]}건 · 프로젝트 전용 문서 {counts[1]}건 · {synced_at(base)})", warnings)


if __name__ == "__main__":
    try:
        text, message = main()
    except Exception as e:
        text, message = "", notice("위키를 로드하지 못했습니다.",
                                   [f"위키 작동 실패 : {type(e).__name__}: {(str(e).splitlines() or [''])[0][:200]}"])
    out = {}
    if message:
        out["systemMessage"] = message
    if text:
        out["hookSpecificOutput"] = {"hookEventName": "SessionStart", "additionalContext": text}
    if out:
        print(json.dumps(out, ensure_ascii=False))
