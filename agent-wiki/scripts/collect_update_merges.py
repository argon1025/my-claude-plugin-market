#!/usr/bin/env python3
# update가 반영할 도메인 레포의 미처리 first-parent 머지를 커서부터 모아 시각 순으로 세우고, diff를 조각 파일로 꺼내 묶음으로 자른다.
# 워크스페이스 clone은 fetch만 하고 작업 트리는 건드리지 않으며 origin/{defaultBranch} ref만 읽는다.
# 문서·커서 파일 수정은 스킬이 하며, 여기서는 무엇을 볼지만 정해 work.json 경로를 마지막 줄에 낸다.
import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

# 추출 에이전트 1회가 읽는 묶음 상한 — 건수는 사실 병합 품질, 바이트는 컨텍스트 예산.
BATCH_MERGES = 5
BATCH_BYTES = 200_000
# diff 조각 상한 — Read 1회가 끝까지 담는 크기.
PART_BYTES = 120_000
# 머리말에 싣는 딸린 커밋 수 상한 — 대형 머지에서 머리말이 diff를 밀어내지 않게 함.
MESSAGE_MAX_COMMITS = 20
# 생성물·잠금 파일처럼 사실이 나올 수 없는 경로만 뺀다.
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
CANDIDATES = [("HEAD", 0), ("최근 10건 앞", 10), ("최근 30건 앞", 30)]


def git(cwd, *args, timeout=300):
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args], env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
                           capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return r.returncode, (r.stdout if r.returncode == 0 else r.stderr).strip()


def first_line(text):
    lines = text.splitlines()
    return next((l for l in lines if l.startswith(("error:", "fatal:"))), lines[-1] if lines else "원인 미상")


def prepare(path, remote, branch):
    """오류 사유 또는 None. 없으면 clone, 있으면 remote를 다시 적고 기본 브랜치만 fetch."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        code, out = git(path.parent, "clone", "--quiet", remote, str(path), timeout=600)
        return None if code == 0 else f"clone 실패 — {first_line(out)}"
    git(path, "remote", "set-url", "origin", remote)
    code, out = git(path, "fetch", "--quiet", "origin", branch, timeout=600)
    return None if code == 0 else f"fetch 실패 — {first_line(out)}"


def first_parent(path, span):
    code, out = git(path, "log", "--first-parent", "--reverse", "--format=%H%x09%P%x09%cI%x09%s", span)
    rows = []
    for line in out.splitlines() if code == 0 else []:
        parts = line.split("\t", 3)
        if len(parts) == 4:
            sha, parents, when, subject = parts
            rows.append({"sha": sha, "parents": len(parents.split()), "date": when, "subject": subject,
                         "_parent": parents.split()[0] if parents else ""})
    return rows


def cut(text):
    """PART_BYTES 이하 덩어리로 줄 경계에서 자른다 — 한 줄이 상한을 넘으면 그 줄만 한 덩어리."""
    chunks, current, size = [], [], 0
    for line in text.splitlines(keepends=True):
        n = len(line.encode("utf-8"))
        if current and size + n > PART_BYTES:
            chunks.append("".join(current))
            current, size = [], 0
        current.append(line)
        size += n
    return chunks + ["".join(current)] if current else chunks


def split(body, room):
    """diff 본문을 파일 경계로 나눠 조각마다 상한까지 이어 붙인다 — 첫 조각은 머리말 몫을 뺀 room까지."""
    files = [f if i == 0 else "diff --git " + f for i, f in enumerate(body.split("\ndiff --git "))]
    for i in range(len(files) - 1):
        files[i] += "\n"
    pieces, current, size = [], "", 0
    for chunk in (c for f in files for c in (cut(f) if len(f.encode("utf-8")) > PART_BYTES else [f])):
        n = len(chunk.encode("utf-8"))
        if current and size + n > (room if not pieces else PART_BYTES):
            pieces.append(current)
            current, size = "", 0
        current += chunk
        size += n
    return pieces + [current] if current else pieces or [""]


def extract_diff(path, slug, row, out_dir):
    # 머지는 sha^1...sha로 봐야 한다 — diff-tree는 머지에서 경로를 내놓지 않음.
    merge = row["parents"] >= 2
    head = ["diff"] if merge else ["show", "--format="]
    span = [f"{row['sha']}^1...{row['sha']}"] if merge else [row["sha"]]
    _, name_status = git(path, *head, "--name-status", *span)
    row["files_changed"] = sum(1 for l in name_status.splitlines() if l.strip())
    # 머지 커밋 메시지는 "Merged in ..." 한 줄뿐이라 결정 근거가 적히는 딸린 커밋 메시지를 싣는다.
    if merge:
        _, message = git(path, "log", f"--max-count={MESSAGE_MAX_COMMITS}", "--format=%h %s%n%b",
                         f"{row['sha']}^1..{row['sha']}")
    else:
        _, message = git(path, "log", "-1", "--format=%s%n%b", row["sha"])
    _, body = git(path, *head, *span, "--", ".", *EXCLUDE_PATHSPECS)
    sha7, title = row["sha"][:7], f"# {slug} {row['sha']} ({row['date']})\n# 제목: {row['subject']}\n"

    def header(n):
        return (
            title
            + f"# 변경 파일 {row['files_changed']}건 — diff 조각 {n}개\n"
            + ("# --- 딸린 커밋 메시지 ---\n" if merge else "# --- 커밋 메시지 ---\n")
            + "\n".join(f"# {l}" for l in message.splitlines())
            + "\n# --- 변경 파일 목록 (제외 규칙 미적용 전체) ---\n"
            + name_status
            + "\n# --- diff (제외 규칙 적용) ---\n"
        )

    pieces = split(body, PART_BYTES - len(header(1).encode("utf-8")))
    out_dir.mkdir(parents=True, exist_ok=True)
    row["parts"] = []
    for k, piece in enumerate(pieces, 1):
        target = out_dir / (f"{sha7}.diff" if k == 1 else f"{sha7}.{k}.diff")
        lead = header(len(pieces)) if k == 1 else (
            title + f"# 조각 {k}/{len(pieces)} — 같은 머지 앞 조각에 이어짐\n")
        target.write_text(lead + piece, encoding="utf-8")
        row["parts"].append({"path": str(target), "bytes": target.stat().st_size})


def batches(rows):
    # 머지 단위로 묶어 같은 머지의 조각은 한 묶음에 둔다 — 건수 상한에 닿았거나 바이트 합계가 상한을 넘게 되면
    # 새 묶음이고, 단독으로 상한을 넘는 머지도 묶음 하나를 차지.
    result, current, total = [], [], 0
    for row in rows + [None]:
        size = sum(p["bytes"] for p in row["parts"]) if row else 0
        if current and (row is None or len(current) >= BATCH_MERGES or total + size > BATCH_BYTES):
            result.append({"id": f"b{len(result) + 1:02d}", "shas": [r["sha"][:7] for r in current],
                           "diffs": [p["path"] for r in current for p in r["parts"]], "bytes": total})
            current, total = [], 0
        if row is not None:
            current.append(row)
            total += size
    return result


def main():
    ap = argparse.ArgumentParser(description="도메인 레포의 미처리 머지 diff를 꺼내 work.json을 쓴다")
    ap.add_argument("--wiki", required=True, help="위키 clone({tmp})")
    ap.add_argument("--workspace", required=True, help="workspace.root")
    ap.add_argument("--domain", required=True)
    ap.add_argument("--out", required=True, help="diff와 work.json을 쓸 디렉터리")
    ap.add_argument("--start", action="append", default=[], metavar="SLUG=REV", help="커서 없는 레포의 시작 지점(HEAD 또는 sha)")
    ap.add_argument("--max-merges", type=int, default=20)
    a = ap.parse_args()

    wiki, workspace, out = (Path(p).expanduser() for p in (a.wiki, a.workspace, a.out))
    try:
        registry = json.loads((wiki / "registry.json").read_text())
    except (OSError, ValueError) as e:
        raise SystemExit(f"registry.json 읽기 실패 — {e}")
    group = registry.get("domains", {}).get(a.domain)
    if not isinstance(group, dict):
        raise SystemExit(f"도메인 없음: {a.domain}")
    repos = group.get("repos", {})
    starts = dict(s.split("=", 1) for s in a.start if "=" in s)
    if len(starts) != len(a.start) or starts.keys() - repos.keys():
        raise SystemExit(f"--start는 SLUG=REV 형식이고 SLUG는 {a.domain} 레포여야 함: {a.start}")

    out.mkdir(parents=True, exist_ok=True)
    work = {"domain": a.domain, "order": [], "repos": {}, "skipped": {}, "unset": {}}
    pool, spans = [], {}
    for slug, node in sorted(repos.items()):
        path, remote, branch = workspace / slug, node.get("remote"), node.get("defaultBranch") or "main"
        if not remote:
            work["skipped"][slug] = "remote 없음 — /agent-wiki:register"
            continue
        if reason := prepare(path, remote, branch):
            work["skipped"][slug] = reason
            continue
        code, head = git(path, "rev-parse", "--verify", "--quiet", f"origin/{branch}^{{commit}}")
        if code != 0:
            work["skipped"][slug] = f"대상 ref 없음 (origin/{branch})"
            continue

        try:
            cursor = json.loads((wiki / "state" / f"{slug}.json").read_text()).get("cursor")
        except (OSError, ValueError, AttributeError):
            cursor = None
        bootstrapped = False
        if not cursor and slug in starts:
            rev = head if starts[slug] == "HEAD" else starts[slug]
            code, cursor = git(path, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
            if code != 0 or git(path, "merge-base", "--is-ancestor", cursor, head)[0] != 0:
                work["skipped"][slug] = f"시작 지점 {starts[slug]}이 origin/{branch} 조상이 아님"
                continue
            bootstrapped = True
        elif not cursor:
            candidates = []
            for label, back in CANDIDATES:
                code, sha = git(path, "rev-parse", "--verify", "--quiet", f"{head}~{back}^{{commit}}")
                if code == 0:
                    candidates.append({"label": label, "sha": sha})
            work["unset"][slug] = {"head": head[:7], "candidates": candidates}
            continue
        elif git(path, "merge-base", "--is-ancestor", cursor, head)[0] != 0:
            work["skipped"][slug] = f"커서 {cursor[:7]}가 origin/{branch} 조상이 아님(force-push 의심) — state/{slug}.json 재설정 필요"
            continue

        rows = first_parent(path, f"{cursor}..{head}")
        # 커서가 first-parent 위에 있으면 범위 첫 행의 첫 부모가 커서이고, 행이 없으면 커서가 head임.
        if rows and rows[0]["_parent"] != cursor:
            work["skipped"][slug] = f"커서 {cursor[:7]}가 origin/{branch} first-parent 밖 — registry defaultBranch 확인"
            continue
        # 정렬 키는 레포 안 누적 최대 시각 — committer date가 first-parent 순서와 어긋나도 레포 안 선택이
        # 앞부분이 되어 커서가 선택되지 않은 머지를 넘지 않음, 타임존이 달라 epoch로 비교.
        latest = 0.0
        for position, row in enumerate(rows):
            latest = max(latest, datetime.fromisoformat(row["date"]).timestamp())
            row["_key"] = (latest, slug, position)
        pool += rows
        spans[slug] = rows
        work["repos"][slug] = {"path": str(path), "branch": branch, "head": head, "cursor": cursor,
                               "bootstrapped": bootstrapped, "commits": [], "batches": [], "remaining": 0}

    work_path = out / "work.json"
    if work["unset"]:
        work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for slug, info in sorted(work["unset"].items()):
            print(f"커서 없음  {slug}: HEAD {info['head']} · 후보 {len(info['candidates'])}개")
        print(work_path)
        return 20

    pool.sort(key=lambda r: r["_key"])
    chosen = pool[: a.max_merges]
    for row in chosen:
        extract_diff(work["repos"][row["_key"][1]]["path"], row["_key"][1], row, out / row["_key"][1])
        work["order"].append({"slug": row["_key"][1], "sha7": row["sha"][:7], "date": row["date"]})
    picked = {id(r) for r in chosen}
    for slug, rows in spans.items():
        entry = work["repos"][slug]
        entry["commits"] = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows if id(r) in picked]
        entry["remaining"] = len(rows) - len(entry["commits"])
        entry["batches"] = batches(entry["commits"])
    work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for slug, reason in sorted(work["skipped"].items()):
        print(f"건너뜀  {slug}: {reason}")
    for slug, entry in sorted(work["repos"].items()):
        tail = f" · 예산 밖 {entry['remaining']}건" if entry["remaining"] else ""
        mark = " · 부트스트랩" if entry["bootstrapped"] else ""
        print(f"{slug}: 머지 {len(entry['commits'])}건 · 묶음 {len(entry['batches'])}개{tail}{mark}")
    busy = any(e["commits"] or e["bootstrapped"] for e in work["repos"].values())
    if not busy:
        print("(미처리 없음)")
    print(work_path)
    return 0 if busy else 10


if __name__ == "__main__":
    raise SystemExit(main())
