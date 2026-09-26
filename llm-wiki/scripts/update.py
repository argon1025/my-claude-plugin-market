#!/usr/bin/env python3
"""무인 갱신의 범위 계산 — 등록 레포를 커서부터 훑어 머지별 diff를 파일로 꺼낸다.

스킬이 이 스크립트를 쓰는 이유는 재현성이다. 레포 N개 순회·미러 확보·부트스트랩·
force-push 검사·diff 절단·제외 pathspec을 에이전트가 bash 여러 번으로 하면 실행마다
결과가 달라진다. 판정과 문서 편집은 스킬이 하고, 여기서는 "무엇을 볼지"만 정한다.

`pending`은 전 등록 레포의 커서 이후 first-parent 머지를 모아 머지 시각 순으로 세우고, 전역
예산만큼 골라 그 diff를 {out}/{slug}/{sha7}.diff로 꺼낸 뒤 work.json 경로를 마지막 줄에 낸다.
work.json `order`가 선택된 머지의 전역 순서다. 종료 코드는 0(작업 있음 또는 부트스트랩),
10(미처리 없음), 1(오류)이다.

추출 묶음(batches)도 여기서 자른다 — 머지 5건 또는 diff 파일 합계 500KB 중 먼저 닿는 쪽.
diff의 실제 바이트는 파일을 쓴 뒤에만 알 수 있고, 스킬이 묶으면 실행마다 경계가 달라진다.
묶음은 레포 안에서만 만든다.

레포는 세션을 연 체크아웃이 아니라 위키 전용 bare 미러({wiki}/.local/mirrors/{slug}.git)로
읽는다 — 체크아웃 경로는 워크트리를 지우면 사라진다. `mirror`는 그 미러를 clone·fetch해 경로를
내고, 에이전트가 다른 레포 코드를 읽을 때도 이 출력을 쓴다.

`advance`는 state/{slug}.json의 커서를 전진시킨다. 커서 파일을 레포별로 나눈 것은 여러
사람과 여러 머신이 서로 다른 레포를 갱신할 때 같은 파일에서 충돌하지 않게 하려는 것이다.
레포별 상태 표는 여기 없다 — registry.json·state/*.json과 미러 폴더를 보면 되는 일이라
register 스킬이 직접 조립한다.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

# 노드 로드와 휴면 판정은 graph가 정본이다 — registry.json이 도메인 아래 중첩이라 평탄화가
# 필요하고, 같은 변환을 여기 한 벌 더 두면 스키마를 고칠 때 한쪽만 남는다.
import graph

DEFAULT_WIKI = os.environ.get("LLM_WIKI_ROOT", "~/.ai-docs/wiki")
DEFAULT_MAX_MERGES = 40
DIFF_MAX_BYTES = 400_000
# 추출 에이전트 1회가 읽는 묶음의 상한. 건수는 사실 병합의 품질, 바이트는 컨텍스트 예산이다.
DEFAULT_BATCH_MERGES = 5
DEFAULT_BATCH_BYTES = 500_000
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

# bare clone은 fetch refspec을 두지 않아 이후 fetch가 FETCH_HEAD만 갱신한다. heads만 받는 것은
# --mirror가 GitHub의 refs/pull/*까지 받아 무거워지기 때문이다.
MIRROR_REFSPEC = "+refs/heads/*:refs/heads/*"

SKIP_NOT_ANCESTOR = "커서가 HEAD 조상이 아님(force-push 의심) — advance로 재설정"
SKIP_DORMANT = "휴면 레포 — registry.json의 status가 dormant"


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


def mirror_path(wiki: Path, slug: str) -> Path:
    return wiki / ".local" / "mirrors" / f"{slug}.git"


def clone_url(remote: str) -> str:
    """노드 remote의 clone URL. 스킴이나 scp 꼴이면 그대로, 아니면 graph.py map의 `https://{remote}.git`."""
    return remote if "://" in remote or remote.startswith("git@") else f"https://{remote}.git"


def ensure_mirror(wiki: Path, slug: str, info: dict) -> tuple[str | None, str]:
    """(미러 경로 또는 None, 사유·노트). 없으면 clone, 있으면 fetch한다.

    blob 없는 부분 clone(--filter=blob:none)은 쓰지 않는다 — `git grep {rev}`가 blob을 지연
    다운로드해 느려진다. url과 refspec은 매번 다시 적어 register가 remote를 바꿔도 따라간다.
    """
    remote = str(info.get("remote") or "").strip()
    if not remote:
        return None, "remote 없음 — /llm-wiki:register"
    url = clone_url(remote)
    path = mirror_path(wiki, slug)
    if not path.is_dir():
        path.parent.mkdir(parents=True, exist_ok=True)
        code, out = git(path.parent, "clone", "--bare", "--quiet", url, str(path), timeout=600)
        if code != 0:
            shutil.rmtree(path, ignore_errors=True)
            first = out.splitlines()[0] if out else "원인 미상"
            return None, f"미러 clone 실패 — {first}"
    git(path, "config", "remote.origin.url", url)
    git(path, "config", "remote.origin.fetch", MIRROR_REFSPEC)
    if git(path, "fetch", "--prune", "--quiet", "origin", timeout=600)[0] != 0:
        return str(path), "fetch 실패 — 미러 기존 ref 기준"
    return str(path), ""


def first_parent(path: str, rev_range: str) -> list[dict]:
    code, out = git(path, "log", "--first-parent", "--reverse",
                    "--format=%H%x09%P%x09%cI%x09%s", rev_range)
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
    row["bytes"] = target.stat().st_size
    return row


def batches(rows: list[dict], max_merges: int, max_bytes: int) -> list[dict]:
    """rows를 순서대로 묶는다. 현재 묶음이 건수 상한에 닿았거나, 비어 있지 않은데 바이트 합계가
    상한을 넘게 되면 새 묶음을 연다 — 단독으로 상한을 넘는 diff도 묶음 하나는 차지한다."""
    result: list[dict] = []
    current: list[dict] = []
    total = 0
    for row in rows:
        if current and (len(current) >= max_merges or total + row["bytes"] > max_bytes):
            result.append({"id": f"b{len(result) + 1:02d}", "shas": [r["sha"][:7] for r in current], "bytes": total})
            current, total = [], 0
        current.append(row)
        total += row["bytes"]
    if current:
        result.append({"id": f"b{len(result) + 1:02d}", "shas": [r["sha"][:7] for r in current], "bytes": total})
    return result


def baseline_before(path: str, ref: str, days: int) -> str | None:
    """{days}일 전 시점의 first-parent 커밋. 커서 없는 레포를 소급 시작할 때 쓴다."""
    code, out = git(path, "rev-list", "--first-parent", "-1", f"--before={days} days ago", ref)
    return out.strip() if code == 0 and out.strip() else None


def cmd_pending(args) -> int:
    wiki = Path(args.wiki).expanduser()
    registry = graph.load_registry(wiki)
    repos = registry["repos"]
    if not repos:
        print(f"# 등록된 레포가 없음: {wiki}/registry.json — /llm-wiki:register", file=sys.stderr)
        return 1

    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = set(args.repo or [])
    work = {"wiki": str(wiki), "order": [], "repos": {}, "skipped": {}, "range_only": bool(args.range)}

    # 1단: 레포별 미처리 머지를 모아 한 리스트에 세운다. diff는 선택된 것만 꺼내므로 여기서는 부르지 않는다.
    pool: list[dict] = []
    spans: dict[str, list[dict]] = {}
    for slug, info in sorted(repos.items()):
        if selected and slug not in selected:
            continue
        if graph.is_dormant(info):
            work["skipped"][slug] = SKIP_DORMANT
            continue
        path, note = ensure_mirror(wiki, slug, info)
        if path is None:
            work["skipped"][slug] = note
            continue
        notes = [note] if note else []

        branch = info.get("defaultBranch") or "main"
        code, head = git(path, "rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}")
        if code != 0:
            work["skipped"][slug] = f"대상 ref를 찾지 못함 ({branch})"
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
            cursor = baseline_before(path, branch, args.baseline_days) if args.baseline_days else None
            cursor = cursor or head
            span = f"{cursor}..{head}"

        rows = first_parent(path, span)
        # 정렬 키는 레포 안 누적 최대 시각이다. fast-forward·rebase 커밋은 committer date가
        # first-parent 순서와 어긋날 수 있는데, 날짜만으로 자르면 한 레포의 선택이 앞부분이
        # 아니게 되고 커서가 선택되지 않은 머지를 넘어 전진해 그 머지가 영구 누락된다.
        # 시각은 타임존 오프셋이 레포마다 달라 문자열이 아니라 epoch로 비교한다.
        latest = 0.0
        for position, row in enumerate(rows):
            latest = max(latest, datetime.fromisoformat(row["date"]).timestamp())
            row["slug"], row["key"], row["position"] = slug, latest, position
        pool.extend(rows)
        spans[slug] = rows
        work["repos"][slug] = {
            "domain": info.get("domain"),
            "path": path,
            "branch": branch,
            "head": head,
            "cursor": cursor,
            "bootstrapped": bootstrapped,
            "commits": [],
            "batches": [],
            "remaining": 0,
            "notes": notes,
        }

    # 2단: 전 레포를 머지 시각 순으로 세워 전역 예산만큼 자르고, 선택된 머지만 diff를 꺼낸다.
    pool.sort(key=lambda row: (row["key"], row["slug"], row["position"]))
    chosen = pool[: args.max_merges]
    for row in chosen:
        entry = work["repos"][row["slug"]]
        extract_diff(entry["path"], row["slug"], row, out_dir / row["slug"])
        work["order"].append({"slug": row["slug"], "sha7": row["sha"][:7], "date": row["date"]})
    picked = {id(row) for row in chosen}
    for slug, rows in spans.items():
        entry = work["repos"][slug]
        entry["commits"] = [
            {key: value for key, value in row.items() if key not in ("slug", "key", "position")}
            for row in rows if id(row) in picked
        ]
        entry["remaining"] = len(rows) - len(entry["commits"])
        entry["batches"] = batches(entry["commits"], args.batch_merges, args.batch_bytes)

    work_path = out_dir / "work.json"
    work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for slug, reason in sorted(work["skipped"].items()):
        print(f"건너뜀  {slug}: {reason}")
    for slug, entry in sorted(work["repos"].items()):
        tail = f" · 예산 밖 {entry['remaining']}건" if entry["remaining"] else ""
        mark = " · 부트스트랩" if entry["bootstrapped"] else ""
        print(f"{slug}: 머지 {len(entry['commits'])}건 · 묶음 {len(entry['batches'])}개{tail}{mark}")

    if not any(entry["commits"] or entry["bootstrapped"] for entry in work["repos"].values()):
        print("(미처리 없음)")
        print(work_path)
        return 10
    print(work_path)
    return 0


def cmd_advance(args) -> int:
    wiki = Path(args.wiki).expanduser()
    info = graph.load_registry(wiki)["repos"].get(args.slug)
    if info is None:
        print(f"# 등록되지 않은 레포: {args.slug}", file=sys.stderr)
        return 1

    # 검증 없이 적은 커서는 다음 pending의 조상 판정을 깨므로, 미러가 없으면 거부한다.
    path = mirror_path(wiki, args.slug)
    branch = info.get("defaultBranch") or "main"
    if not path.is_dir():
        print(f"# 미러 없음 — update.py mirror --repo {args.slug} 먼저", file=sys.stderr)
        return 1
    if git(path, "merge-base", "--is-ancestor", args.sha, branch)[0] != 0:
        print(f"# {args.sha[:7]}는 {branch}의 조상이 아님 — 커서를 전진시키지 않음", file=sys.stderr)
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


def cmd_mirror(args) -> int:
    wiki = Path(args.wiki).expanduser()
    repos = graph.load_registry(wiki)["repos"]
    # 지목하지 않으면 휴면을 뺀다 — 휴면 레포 코드는 update가 읽지 않는다. 지목은 휴면도 받는다.
    slugs = args.repo or [slug for slug, info in sorted(repos.items()) if not graph.is_dormant(info)]
    for slug in slugs:
        info = repos.get(slug)
        if info is None:
            print(f"{slug} 없음 — 등록되지 않은 레포")
            continue
        path, note = ensure_mirror(wiki, slug, info)
        if path is None:
            print(f"{slug} 없음 — {note}")
            continue
        branch = info.get("defaultBranch") or "main"
        print(f"{slug} {path}@{branch}" + (f" · {note}" if note else ""))
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
                         help=f"전역 머지 예산 (기본값: {DEFAULT_MAX_MERGES})")
    pending.add_argument("--baseline-days", metavar="N", type=int,
                         help="커서 없는 레포를 며칠 전부터 소급할지")
    pending.add_argument("--batch-merges", metavar="N", type=int, default=DEFAULT_BATCH_MERGES,
                         help=f"추출 묶음 하나의 머지 상한 (기본값: {DEFAULT_BATCH_MERGES})")
    pending.add_argument("--batch-bytes", metavar="N", type=int, default=DEFAULT_BATCH_BYTES,
                         help=f"추출 묶음 하나의 diff 파일 합계 상한 (기본값: {DEFAULT_BATCH_BYTES})")
    pending.set_defaults(func=cmd_pending)

    mirror = sub.add_parser("mirror", parents=[common], help="등록 레포의 bare 미러를 clone·fetch한다")
    mirror.add_argument("--repo", metavar="SLUG", action="append", help="대상 레포 한정 (반복 가능, 휴면 포함)")
    mirror.set_defaults(func=cmd_mirror)

    advance = sub.add_parser("advance", parents=[common], help="레포 커서를 전진시킨다")
    advance.add_argument("slug")
    advance.add_argument("sha")
    advance.set_defaults(func=cmd_advance)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
