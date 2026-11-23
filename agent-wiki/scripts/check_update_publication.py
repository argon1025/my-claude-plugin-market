#!/usr/bin/env python3
"""Decide whether an update can start or publish using the host's complete list of open PRs."""
import argparse
import json
from pathlib import Path
import sys

from collect_update_merges import checked_git


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("--open-prs", type=Path, required=True)
    parser.add_argument("--base", required=True, help="SHA of the wiki used to collect and review")
    parser.add_argument("--base-branch", required=True)
    parser.add_argument("--ready", action="store_true", help="Check the final committed proposal")
    parser.add_argument("--compared", type=Path, help="Ready-stage comparison with other open PR heads")
    args = parser.parse_args()
    response = json.loads(args.open_prs.read_text(encoding="utf-8"))
    if isinstance(response, list):
        # gh api --paginate --slurp가 성공하면 마지막 페이지까지의 배열이 온다.
        if not response or not all(isinstance(page, list) for page in response):
            raise ValueError("GitHub PR 페이지 목록이 비었거나 형식이 잘못됨")
        pulls = [{"head": pr["head"]["ref"], "sha": pr["head"]["sha"],
                  "base": pr["base"]["ref"], "url": pr["html_url"]} for page in response for pr in page]
    elif response["complete"] is True and isinstance(response["pulls"], list):
        pulls = response["pulls"]
    else:
        raise ValueError("열린 PR 전체 목록을 확인하지 못함")
    others = []
    for row in pulls:
        if not all(isinstance(row[k], str) and row[k] for k in ("head", "base", "url")):
            raise ValueError("열린 PR의 브랜치 또는 링크가 없음")
        if row["base"] != args.base_branch:
            continue
        if row["head"].startswith("wiki-update/"):
            print(row["url"])
            return 10
        others.append(row)
    current = checked_git(args.wiki, "rev-parse", "--verify", f"refs/remotes/origin/{args.base_branch}^{{commit}}")
    if current != args.base:
        raise ValueError("위키 기준 브랜치가 바뀜 — 최신 사본에서 다시 수집")
    checked_git(args.wiki, "merge-base", "--is-ancestor", args.base, "HEAD")
    if args.ready:
        if checked_git(args.wiki, "status", "--porcelain"):
            raise ValueError("검토 후 커밋하지 않은 변경이 있음")
        if not checked_git(args.wiki, "diff", "--name-only", args.base, "HEAD"):
            print("게시할 변경 없음")
            return 10
        if others:
            if args.compared is None:
                raise ValueError("열린 기여 PR과 이번 변경의 대상·주장 대조 필요")
            compared = json.loads(args.compared.read_text(encoding="utf-8"))
            for pr in others:
                check = compared[pr["url"]]
                if not pr.get("sha") or check["sha"] != pr["sha"] or not check.get("reason"):
                    raise ValueError("열린 기여 PR 판본·대조 근거 미확인")
                if check["overlap"] is True:
                    print(pr["url"], check["reason"])
                    return 10
                if check["overlap"] is not False:
                    raise ValueError("열린 기여 PR 중복 여부 미확인")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.exit(str(error))
