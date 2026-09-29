#!/usr/bin/env python3
# 등록 레포(와 --current로 받은 현재 레포)를 워크스페이스에 clone하고 원격 defaultBranch 최신으로 맞춘다.
# 기존 clone에 미커밋 변경·로컬 커밋·다른 브랜치가 있으면 dirty로 보고만 하고, --force일 때만 버리고 맞춘다.
import argparse
import json
import os
import subprocess
from pathlib import Path

ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


def git(*args):
    r = subprocess.run(["git", *args], env=ENV, capture_output=True, text=True)
    if r.returncode != 0:
        lines = (r.stderr or r.stdout).strip().splitlines() or [f"git exit {r.returncode}"]
        raise RuntimeError(next((l for l in lines if l.startswith(("error:", "fatal:"))), lines[-1]))
    return r.stdout.strip()


def sync(path, remote, branch, force):
    fresh = not path.exists()
    if fresh:
        git("clone", remote, str(path))
    p = str(path)
    git("-C", p, "fetch", "origin", branch)
    current = git("-C", p, "branch", "--show-current")
    changes = git("-C", p, "status", "--porcelain")
    ahead = git("-C", p, "rev-list", "--count", f"origin/{branch}..HEAD")
    if not (force or fresh) and (current != branch or changes or ahead != "0"):
        return f"dirty branch={current} changes={len(changes.splitlines())} ahead={ahead}"
    git("-C", p, "checkout", "-f", "-B", branch, f"origin/{branch}")
    git("-C", p, "clean", "-fd")
    return "ok"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="slug를 생략하면 전체 등록 레포, --current가 있으면 나열한 slug만")
    ap.add_argument("registry")
    ap.add_argument("root")
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--current", nargs=3, metavar=("SLUG", "REMOTE", "BRANCH"))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    nodes = {s: (n.get("remote"), n.get("defaultBranch"))
             for g in json.loads(Path(a.registry).expanduser().read_text()).get("domains", {}).values()
             for s, n in g.get("repos", {}).items()}
    targets = {s: nodes[s] for s in (a.slugs or ([] if a.current else nodes)) if s in nodes}
    if a.current:
        targets[a.current[0]] = tuple(a.current[1:])
    bad = False
    for slug in sorted(set(a.slugs) - nodes.keys()):
        bad = True
        print(f"fail {slug} not in registry")
    for slug, (remote, branch) in targets.items():
        try:
            result = sync(root / slug, remote, branch, a.force)
        except (RuntimeError, TypeError) as e:
            result = f"fail {e}"
        bad |= result != "ok"
        print(f"{result.split()[0]} {slug} {' '.join(result.split()[1:])}".rstrip())
    raise SystemExit(1 if bad else 0)
