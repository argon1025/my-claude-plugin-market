#!/usr/bin/env python3
# 등록 레포(와 --current로 받은 현재 레포)를 워크스페이스에 clone하고 원격 defaultBranch로 강제 정리한다.
# 워크스페이스는 읽기 전용 사본이므로 로컬 변경·커밋·다른 브랜치는 버린다.
import argparse
import json
import os
import subprocess
from pathlib import Path


def git(*args):
    r = subprocess.run(["git", *args], env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, capture_output=True, text=True)
    if r.returncode != 0:
        lines = (r.stderr or r.stdout).strip().splitlines() or [f"git exit {r.returncode}"]
        raise RuntimeError(next((l for l in lines if l.startswith(("error:", "fatal:"))), lines[-1]))


def sync(path, node):
    if node is None or not all(isinstance(v, str) and v for v in node):
        raise RuntimeError("not in registry" if node is None else "missing remote or defaultBranch")
    remote, branch = node
    if not path.exists():
        git("clone", remote, str(path))
    for args in (("remote", "set-url", "origin", remote), ("fetch", "origin", branch),
                 ("checkout", "-f", "-B", branch, f"origin/{branch}"), ("clean", "-fd")):
        git("-C", str(path), *args)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="slug를 생략하면 전체 등록 레포, --current가 있으면 나열한 slug만")
    ap.add_argument("registry")
    ap.add_argument("root")
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--current", nargs=3, metavar=("SLUG", "REMOTE", "BRANCH"))
    a = ap.parse_args()
    (root := Path(a.root).expanduser()).mkdir(parents=True, exist_ok=True)
    nodes = {s: (n.get("remote"), n.get("defaultBranch"))
             for g in json.loads(Path(a.registry).expanduser().read_text()).get("domains", {}).values()
             for s, n in g.get("repos", {}).items()}
    targets = {s: nodes.get(s) for s in (a.slugs or ([] if a.current else nodes))}
    targets |= {a.current[0]: tuple(a.current[1:])} if a.current else {}
    bad = False
    for slug, node in targets.items():
        try:
            sync(root / slug, node)
            print(f"ok {slug}")
        except RuntimeError as e:
            bad = True
            print(f"fail {slug} {e}")
    raise SystemExit(1 if bad else 0)
