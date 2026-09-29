#!/usr/bin/env python3
# 위키 트리(baseRoot)를 clone하거나 원격 기준 브랜치로 강제 정리한다.
# baseRoot는 읽기 전용 사본이므로 origin을 remote로 맞추고 로컬 변경·커밋·다른 브랜치는 버린다.
import os
import subprocess
import sys
from pathlib import Path


def git(*args):
    r = subprocess.run(["git", *args], env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, capture_output=True, text=True)
    if r.returncode != 0:
        lines = (r.stderr or r.stdout).strip().splitlines() or [f"git exit {r.returncode}"]
        raise RuntimeError(next((l for l in lines if l.startswith(("error:", "fatal:"))), lines[-1]))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: sync_wiki.py <baseRoot> <remote> <baseBranch>")
    root, remote, branch = str(Path(sys.argv[1]).expanduser()), sys.argv[2], sys.argv[3]
    try:
        if not Path(root).exists():
            git("clone", remote, root)
        git("-C", root, "remote", "set-url", "origin", remote)
        git("-C", root, "fetch", "origin", branch)
        git("-C", root, "checkout", "-f", "-B", branch, f"origin/{branch}")
        git("-C", root, "clean", "-fd")
    except RuntimeError as e:
        print(f"fail {e}")
        raise SystemExit(1)
    print("ok")
