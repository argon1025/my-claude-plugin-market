#!/usr/bin/env python3
"""SessionStart 훅 — 위키 규약·레포 지도·문서 목록을 세션 컨텍스트로 주입한다.

미등록·git 밖은 규약 없이 짧은 블록만 싣는다 — 규약은 레포 지도와 문서 목록을 읽는 법이다.
matcher가 없어 모든 source에서 돌지만 pull은 startup·resume만 한다 — clear·compact는 같은
세션의 재주입이고 fork는 부모가 이미 당겼다. 어떤 실패에서도 종료 코드 0으로 끝난다 — 0이
아니면 주입이 사라진다.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # 플러그인 캐시에 __pycache__를 남기지 않는다
PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN / "scripts"))
try:
    import catalog
    import graph
except Exception:
    sys.exit(0)

ALERT = "첫 응답에서 사용자에게 알릴 것"
# Claude Code는 additionalContext를 10,000자에서 경고 없이 자르므로(공식 문서 미기재,
# https://github.com/anthropics/claude-code/issues/94358) 한도 전에 정리 권고가 보이게 한다.
WARN_CHARS = 9_000


def git(cwd, *args: str) -> str:
    """성공하면 stdout, 실패하면 빈 문자열."""
    try:
        result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def sync(wiki: Path, source: str) -> str:
    """pull을 3초까지 기다리고 알릴 것이 있으면 그 한 줄. 세션 시작을 붙잡지 않는 것이 최신
    사본보다 중요하다 — 늦으면 pull은 뒤에서 마저 돌고 이번 주입은 이전 사본으로 간다."""
    if source not in ("startup", "resume") or not git(wiki, "remote", "get-url", "origin"):
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
        return f"# 위키가 {wiki} 에 없음 — {graph.SKILL_PREFIX}init 으로 clone 하거나 새로 만들 것"
    note = sync(wiki, source)

    # 포크에서는 upstream이 정본이고 노드에는 정본만 적으므로 upstream을 먼저 본다.
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    remote = git(project, "remote", "get-url", "upstream") or git(project, "remote", "get-url", "origin")
    common_dir = git(project, "rev-parse", "--path-format=absolute", "--git-common-dir")
    registry = graph.load_registry(wiki)
    slug, domain = graph.resolve_repo(registry, remote, common_dir)

    if not domain:
        rows = [f"# 위키 {wiki} — " + (f"미등록 레포 {slug}, 등록은 `{graph.SKILL_PREFIX}register`" if slug else "git 레포 밖")]
        domains = graph.domain_line(registry)
        if domains:
            rows.append(f"- **도메인**: {domains} — 노드·간선은 `{wiki}/registry.json`·`deps.json`, "
                        f"문서는 `{wiki}/knowledge/{{domain}}`")
        rows.append(f"- **수정**: 위키는 `{graph.SKILL_PREFIX}` 스킬로만 고침")
        return "\n".join(filter(None, [note, *rows]))

    # 다른 레포 사본 위치({REPOS_DIR})는 common dir(본 저장소의 .git)에서 세션마다 계산한다 —
    # worktree에서 열어도 본 저장소 옆을 가리킨다.
    knowledge = wiki / "knowledge" / domain
    guide = (PLUGIN / "rules" / "agent-guide.md").read_text(encoding="utf-8").strip()
    for key, value in {"{WIKI_ROOT}": wiki, "{REPOS_DIR}": Path(common_dir).parent.parent,
                       "{DOMAIN_DIR}": knowledge, "{SKILL_PREFIX}": graph.SKILL_PREFIX}.items():
        guide = guide.replace(key, str(value))

    # 목록은 어떤 크기에서도 줄이지 않는다 — 에이전트는 description만으로 문서를 열지 정하므로
    # 목록에서 빠진 문서는 없는 문서가 된다.
    blocks = [guide, note, graph.render_session(registry, graph.load_edges(wiki), domain, slug)]
    if knowledge.is_dir():
        blocks.append(catalog.build(knowledge, f"도메인 {domain}", shallow=True))
        if (knowledge / slug).is_dir():
            blocks.append(catalog.build(knowledge / slug, f"레포 {slug}"))
    context = "\n\n".join(filter(None, blocks))
    if len(context) > WARN_CHARS:
        context = (f"# 위키 주입 {len(context):,}자 — 10,000자를 넘으면 뒤가 잘리므로 {graph.SKILL_PREFIX}audit 로 정리 권장\n\n"
                   + context)
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
