#!/usr/bin/env python3
"""SessionStart 훅 — 위키 규약·레포 지도·문서 목록을 세션 컨텍스트로 주입한다.

등록 레포는 규약(rules/agent-guide.md) → 동기화 알림 → 레포 지도 → 문서 목록(도메인 루트 +
현재 레포)을, 미등록·git 밖은 규약 없이 짧은 블록을 싣는다. 규약은 레포 지도와 문서 목록을
읽는 법이라 그것이 없는 세션에는 쓸 데가 없다.

hooks.json에 matcher가 없어 startup·resume·clear·compact·fork 모두에서 돈다. 원격 pull은
source가 startup·resume일 때만 한다 — clear·compact는 같은 세션의 재주입이고 fork는 부모가
이미 당겼다. 어떤 실패에서도 종료 코드 0으로 끝난다 — 0이 아닌 값을 내면 주입이 사라진다.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # 플러그인 캐시에 __pycache__를 남기지 않는다
PLUGIN = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN / "scripts"
sys.path.insert(0, str(SCRIPTS))
try:
    import catalog
    import graph
except Exception:
    sys.exit(0)

ALERT = "첫 응답에서 사용자에게 알릴 것"
# 주입 크기의 유일한 제어 수단은 이 권고 한 줄과 사용자의 문서 정리다.
SOFT_BUDGET = 8000


def git(cwd, *args: str) -> str:
    """성공하면 stdout, 실패하면 빈 문자열."""
    try:
        result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def sync(wiki: Path, source: str) -> str:
    """마지막 fetch가 주기보다 오래됐으면 pull을 걸고 3초까지 기다린다. 알릴 것이 있으면 그 한 줄.

    세션 시작을 붙잡지 않는 것이 최신 사본보다 중요하다 — 늦으면 pull은 뒤에서 마저 돌고
    이번 주입은 이전 사본으로 간다.
    """
    if source not in ("startup", "resume"):
        return ""
    git_dir = git(wiki, "rev-parse", "--absolute-git-dir")
    if not git_dir or not git(wiki, "remote", "get-url", "origin"):
        return ""
    minutes = os.environ.get("LLM_WIKI_SYNC_MINUTES", "")
    fetched = Path(git_dir, "FETCH_HEAD")
    if fetched.is_file() and time.time() - fetched.stat().st_mtime < (int(minutes) if minutes.isdecimal() else 10) * 60:
        return ""
    pull = subprocess.Popen(["git", "-C", str(wiki), "pull", "--ff-only", "--quiet"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    try:
        failed = pull.wait(timeout=3) != 0
    except subprocess.TimeoutExpired:
        return f"# 위키 동기화 지연 — 이전 사본으로 주입. {ALERT}"
    return f"# 위키 동기화 실패 — 이전 사본으로 주입. {ALERT}" if failed else ""


def build(source: str) -> str:
    wiki = Path(graph.DEFAULT_WIKI).expanduser()
    if not (wiki / "registry.json").is_file():
        return f"LLM-WIKI: 위키가 {wiki} 에 없음 — /llm-wiki:init 으로 clone 하거나 새로 만들 것"
    note = sync(wiki, source)

    # fork 워크플로에서 origin은 개인 포크이고 upstream이 정본이다. 노드에는 정본만 적으므로
    # upstream을 먼저 본다 — 둘 다 없거나 어긋나도 resolve_repo의 slug 폴백이 받는다.
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    remote = git(project, "remote", "get-url", "upstream") or git(project, "remote", "get-url", "origin")
    common_dir = git(project, "rev-parse", "--path-format=absolute", "--git-common-dir")
    registry = graph.load_registry(wiki)
    slug, domain = graph.resolve_repo(registry, remote, common_dir)
    graph_py = SCRIPTS / "graph.py"

    if not domain:
        rows = [f"# 위키 {wiki} — " + (f"미등록 레포 {slug}, 등록은 `/llm-wiki:register`" if slug else "git 레포 밖")]
        domains = graph.domain_line(registry)
        if domains:
            rows.append(f"- **도메인**: {domains} — 레포 지도는 `python3 {graph_py} map --domain {{domain}}`")
        rows.append("- **수정**: 위키는 `/llm-wiki:` 스킬로만 고침")
        return "\n".join([note, *rows] if note else rows)

    # 작업 사본 위치는 저장하면 worktree 삭제로 낡으므로 세션마다 common dir(본 저장소의 .git)에서
    # 계산한다 — worktree에서 열어도 본 저장소 옆을 가리킨다.
    knowledge = wiki / "knowledge" / domain
    guide = (PLUGIN / "rules" / "agent-guide.md").read_text(encoding="utf-8").strip()
    for key, value in {"{WIKI_ROOT}": wiki, "{GRAPH_PY}": graph_py,
                       "{REPOS_DIR}": Path(common_dir).parent.parent, "{DOMAIN_DIR}": knowledge}.items():
        guide = guide.replace(key, str(value))

    # 도메인 루트는 레포 폴더를 뺀 평면(shallow), 레포 폴더는 전수. 어떤 예산에서도 줄이지 않는다 —
    # 에이전트는 description만으로 문서를 열지 말지 정하므로 목록에서 빠진 문서는 없는 문서가 된다.
    blocks = [guide, note, graph.render_session(registry, graph.load_edges(wiki), domain, slug)]
    if knowledge.is_dir():
        blocks.append(catalog.build(knowledge, f"도메인 {domain}", shallow=True))
        if (knowledge / slug).is_dir():
            blocks.append(catalog.build(knowledge / slug, f"레포 {slug}"))
    context = "\n\n".join(block for block in blocks if block)
    tokens = catalog.estimate_tokens(context)
    if tokens > SOFT_BUDGET:
        context = f"# 위키 목록이 약 {tokens:,}토큰 — /llm-wiki:audit 로 정리 권장\n\n" + context
    return context


def main() -> None:
    try:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        source = json.loads(raw).get("source") or "startup"
    except (ValueError, AttributeError, OSError):
        source = "startup"
    try:
        context = build(source)
    except Exception:
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
