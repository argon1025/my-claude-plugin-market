#!/usr/bin/env python3
"""무인 갱신의 범위 계산 — 등록 레포를 커서부터 훑어 머지별 diff를 파일로 꺼낸다.

스킬이 이 스크립트를 쓰는 이유는 재현성이다. 레포 N개 순회·부트스트랩·대상 ref 선택·
force-push 검사·diff 절단·제외 pathspec을 에이전트가 bash 여러 번으로 하면 실행마다
결과가 달라진다. 판정과 문서 편집은 스킬이 하고, 여기서는 "무엇을 볼지"만 정한다.

`pending`은 레포별로 커서 이후 first-parent 커밋을 세고 그 diff를 {out}/{slug}/{sha7}.diff로
꺼낸 뒤 work.json 경로를 마지막 줄에 낸다. 종료 코드는 0(작업 있음 또는 부트스트랩),
10(미처리 없음), 1(오류)이다.

`advance`는 state/{slug}.json의 커서를 전진시킨다. 커서 파일을 레포별로 나눈 것은 여러
사람과 여러 머신이 서로 다른 레포를 갱신할 때 같은 파일에서 충돌하지 않게 하려는 것이다.
레포별 상태 표는 여기 없다 — registry.json·state/*.json·.local/paths.json 3파일을 읽으면
되는 일이라 register 스킬이 직접 조립한다.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

DEFAULT_WIKI = os.environ.get("LLM_WIKI_ROOT", "~/.ai-docs/wiki")
DEFAULT_MAX_MERGES = 20
DIFF_MAX_BYTES = 400_000
# 머지 머리말에 싣는 딸린 커밋 수 상한. 대형 머지에서 머리말이 diff를 밀어내지 않게 한다.
MESSAGE_MAX_COMMITS = 20

# diff 사전 추출에서 빼는 경로. 생성물·잠금 파일처럼 사실이 나올 수 없는 것만 뺀다.
EXCLUDE_PATHSPECS = [
    ":(exclude)**/package-lock.json",
    ":(exclude)**/yarn.lock",
    ":(exclude)**/pnpm-lock.yaml",
    ":(exclude)**/poetry.lock",
    ":(exclude)**/composer.lock",
    ":(exclude)**/gradle.lockfile",
    ":(exclude)**/*.min.js",
    ":(exclude)**/*.min.css",
    ":(exclude)**/*.svg",
    ":(exclude)**/dist/**",
    ":(exclude)**/node_modules/**",
]

SKIP_NO_PATH = "로컬 경로 없음 — 그 레포에서 세션을 한 번 열면 등록됨"
SKIP_NOT_ANCESTOR = "커서가 HEAD 조상이 아님(force-push 의심) — advance로 재설정"


def git(cwd: str | Path, *args: str, timeout: int = 60) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)
    return result.returncode, (result.stdout if result.returncode == 0 else result.stderr).strip()


def load_json(path: Path, fallback):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return fallback


def target_ref(path: str, branch: str) -> str:
    """대상 ref. 원격 추적 ref가 있으면 그것을 쓴다 — 워킹트리가 어느 브랜치에 있든 같은 결과."""
    code, _ = git(path, "rev-parse", "--verify", "--quiet", f"origin/{branch}")
    return f"origin/{branch}" if code == 0 else branch


def first_parent(path: str, rev_range: str) -> list[dict]:
    code, out = git(path, "log", "--first-parent", "--reverse",
                    "--format=%H%x09%P%x09%ad%x09%s", "--date=short", rev_range)
    if code != 0:
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        sha, parents, when, subject = parts
        rows.append({"sha": sha, "parents": len(parents.split()), "date": when, "subject": subject})
    return rows


def extract_diff(path: str, slug: str, row: dict, out_dir: Path) -> dict:
    """머지 diff를 머리말과 함께 파일로 꺼낸다. 서브에이전트는 이 파일만 읽는다.

    머지 커밋은 `sha^1...sha`로 봐야 한다 — diff-tree는 머지에서 아무 경로도 내놓지 않아
    변경 파일 목록이 통째로 비어버린다.
    """
    merge = row["parents"] >= 2
    head = ["diff"] if merge else ["show", "--format="]
    span = [f"{row['sha']}^1...{row['sha']}"] if merge else [row["sha"]]

    _, name_status = git(path, *head, "--name-status", *span)
    row["files_changed"] = sum(1 for line in name_status.splitlines() if line.strip())
    # 머지 커밋의 메시지는 "Merged in ..." 한 줄뿐이라, 결정 근거가 적히는 자리인
    # 딸린 커밋 메시지를 함께 싣는다. 이 문장이 없으면 근거는 어디에도 남지 않는다.
    if merge:
        _, message = git(path, "log", f"--max-count={MESSAGE_MAX_COMMITS}",
                         "--format=%h %s%n%b", f"{row['sha']}^1..{row['sha']}")
    else:
        _, message = git(path, "log", "-1", "--format=%s%n%b", row["sha"])
    _, body = git(path, *head, *span, "--", ".", *EXCLUDE_PATHSPECS, timeout=300)

    encoded = body.encode("utf-8")
    row["truncated"] = len(encoded) > DIFF_MAX_BYTES
    if row["truncated"]:
        body = encoded[:DIFF_MAX_BYTES].decode("utf-8", errors="ignore")

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{row['sha'][:7]}.diff"
    header = (
        f"# {slug} {row['sha']} ({row['date']})\n"
        f"# 제목: {row['subject']}\n"
        f"# 변경 파일 {row['files_changed']}건"
        + (" — diff가 400KB에서 절단됨, 아래 파일 목록은 온전함\n" if row["truncated"] else "\n")
        + ("# --- 딸린 커밋 메시지 ---\n" if merge else "# --- 커밋 메시지 ---\n")
        + "\n".join(f"# {line}" for line in message.splitlines())
        + "\n# --- 변경 파일 목록 (제외 규칙 미적용 전체) ---\n"
        + name_status
        + "\n# --- diff (제외 규칙 적용) ---\n"
    )
    target.write_text(header + body, encoding="utf-8")
    row["diff_path"] = str(target)
    return row


def baseline_before(path: str, ref: str, days: int) -> str | None:
    """{days}일 전 시점의 first-parent 커밋. 커서 없는 레포를 소급 시작할 때 쓴다."""
    code, out = git(path, "rev-list", "--first-parent", "-1", f"--before={days} days ago", ref)
    return out.strip() if code == 0 and out.strip() else None


def cmd_pending(args) -> int:
    wiki = Path(args.wiki).expanduser()
    registry = load_json(wiki / "registry.json", {})
    repos = registry.get("repos", {}) if isinstance(registry, dict) else {}
    if not repos:
        print(f"# 등록된 레포가 없음: {wiki}/registry.json — /llm-wiki:register", file=sys.stderr)
        return 1

    paths = load_json(wiki / ".local" / "paths.json", {})
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = set(args.repo or [])
    work = {"wiki": str(wiki), "repos": {}, "skipped": {}, "range_only": bool(args.range)}

    for slug, info in sorted(repos.items()):
        if selected and slug not in selected:
            continue
        path = paths.get(slug)
        if not path or not Path(path).is_dir():
            work["skipped"][slug] = SKIP_NO_PATH
            continue

        notes = []
        if git(path, "fetch", "--quiet", "origin")[0] != 0:
            notes.append("fetch 실패 — 로컬 ref 기준")

        branch = info.get("branch") or "main"
        ref = target_ref(path, branch)
        code, head = git(path, "rev-parse", ref)
        if code != 0:
            work["skipped"][slug] = f"대상 ref를 찾지 못함 ({ref})"
            continue

        state = load_json(wiki / "state" / f"{slug}.json", {})
        cursor = state.get("cursor") if isinstance(state, dict) else None
        bootstrapped = False
        if args.range:
            span = args.range
        elif cursor:
            if git(path, "merge-base", "--is-ancestor", cursor, head)[0] != 0:
                work["skipped"][slug] = SKIP_NOT_ANCESTOR
                continue
            span = f"{cursor}..{head}"
        else:
            bootstrapped = True
            cursor = baseline_before(path, ref, args.baseline_days) if args.baseline_days else None
            cursor = cursor or head
            span = f"{cursor}..{head}"

        rows = first_parent(path, span)
        remaining = max(0, len(rows) - args.max_merges)
        rows = rows[: args.max_merges]
        for row in rows:
            extract_diff(path, slug, row, out_dir / slug)

        work["repos"][slug] = {
            "domain": info.get("domain"),
            "path": path,
            "branch": branch,
            "ref": ref,
            "head": head,
            "cursor": cursor,
            "bootstrapped": bootstrapped,
            "commits": rows,
            "remaining": remaining,
            "notes": notes,
        }

    work_path = out_dir / "work.json"
    work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for slug, reason in sorted(work["skipped"].items()):
        print(f"건너뜀  {slug}: {reason}")
    for slug, entry in sorted(work["repos"].items()):
        tail = f" · 예산 밖 {entry['remaining']}건" if entry["remaining"] else ""
        mark = " · 부트스트랩" if entry["bootstrapped"] else ""
        print(f"{slug}: 머지 {len(entry['commits'])}건{tail}{mark}")

    if not any(entry["commits"] or entry["bootstrapped"] for entry in work["repos"].values()):
        print("(미처리 없음)")
        print(work_path)
        return 10
    print(work_path)
    return 0


def cmd_advance(args) -> int:
    wiki = Path(args.wiki).expanduser()
    registry = load_json(wiki / "registry.json", {})
    info = (registry.get("repos", {}) if isinstance(registry, dict) else {}).get(args.slug)
    if info is None:
        print(f"# 등록되지 않은 레포: {args.slug}", file=sys.stderr)
        return 1

    paths = load_json(wiki / ".local" / "paths.json", {})
    path = paths.get(args.slug)
    branch = info.get("branch") or "main"
    if path and Path(path).is_dir():
        ref = target_ref(path, branch)
        if git(path, "merge-base", "--is-ancestor", args.sha, ref)[0] != 0:
            print(f"# {args.sha[:7]}는 {ref}의 조상이 아님 — 커서를 전진시키지 않음", file=sys.stderr)
            return 1
        args.sha = git(path, "rev-parse", args.sha)[1]

    state_path = wiki / "state" / f"{args.slug}.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    # 커서 파일은 cursor·at 2키만 둔다. 머지·문서 건수는 커밋 메시지가 말하고 branch는
    # registry.json이 정본이라 여기 복제하면 두 값이 어긋날 자리만 생긴다.
    state_path.write_text(json.dumps({
        "cursor": args.sha,
        "at": date.today().isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.slug} 커서 {args.sha[:7]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="등록 레포의 미반영 머지를 찾아 diff를 꺼낸다.")
    # --wiki는 하위 명령 뒤에 와야 자연스러워서 공통 부모로 둔다.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--wiki", metavar="PATH", default=DEFAULT_WIKI,
                        help=f"위키 저장소 (기본값: {DEFAULT_WIKI})")
    sub = parser.add_subparsers(dest="command", required=True)

    pending = sub.add_parser("pending", parents=[common], help="커서 이후 머지 목록과 diff 파일을 만든다")
    pending.add_argument("--out", metavar="DIR", required=True, help="diff와 work.json을 쓸 디렉터리")
    pending.add_argument("--repo", metavar="SLUG", action="append", help="대상 레포 한정 (반복 가능)")
    pending.add_argument("--range", metavar="REV", help="지목 범위. 이 실행은 커서를 전진시키지 않는다")
    pending.add_argument("--max-merges", metavar="N", type=int, default=DEFAULT_MAX_MERGES,
                         help=f"레포별 머지 예산 (기본값: {DEFAULT_MAX_MERGES})")
    pending.add_argument("--baseline-days", metavar="N", type=int,
                         help="커서 없는 레포를 며칠 전부터 소급할지")
    pending.set_defaults(func=cmd_pending)

    advance = sub.add_parser("advance", parents=[common], help="레포 커서를 전진시킨다")
    advance.add_argument("slug")
    advance.add_argument("sha")
    advance.set_defaults(func=cmd_advance)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
