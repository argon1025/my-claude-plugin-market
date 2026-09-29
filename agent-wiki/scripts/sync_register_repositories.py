#!/usr/bin/env python3
# registry.json의 등록 레포를 워크스페이스에 clone하고 defaultBranch로 checkout·pull --ff-only한다.
# 위키 트리와 registry.json은 읽기만 하며, 워크스페이스 clone 밖의 브랜치는 건드리지 않는다.
import json
import os
import subprocess
import sys
from pathlib import Path

ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


def git(*args):
    r = subprocess.run(["git", *args], env=ENV, capture_output=True, text=True)
    if r.returncode != 0:
        lines = (r.stderr or r.stdout).strip().splitlines() or [f"git exit {r.returncode}"]
        raise RuntimeError(next((l for l in lines if l.startswith(("error:", "fatal:"))), lines[-1]))


def sync(root, slug, node):
    path = root / slug
    if not path.exists():
        git("clone", node["remote"], str(path))
    git("-C", str(path), "checkout", node["defaultBranch"])
    git("-C", str(path), "pull", "--ff-only", "origin", node["defaultBranch"])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: sync_register_repositories.py <registry.json> <workspace-root> [slug ...]")
    registry = json.loads(Path(sys.argv[1]).expanduser().read_text())
    root = Path(sys.argv[2]).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[3:])
    failed = False
    for group in registry.get("domains", {}).values():
        for slug, node in group.get("repos", {}).items():
            if only and slug not in only:
                continue
            try:
                sync(root, slug, node)
                print(f"ok {slug}")
            except (RuntimeError, KeyError) as e:
                failed = True
                print(f"fail {slug} {e}")
    sys.exit(1 if failed else 0)
