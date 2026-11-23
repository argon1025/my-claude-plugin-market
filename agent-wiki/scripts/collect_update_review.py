#!/usr/bin/env python3
"""위키 한 사본에서 독립 수집 범위와 검토를 마친 뒤 기록할 커서를 계산한다."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

from collect_update_merges import checked_git, first_line, git, main as collect_merges, prepare

ROUTES = ("merges", "decisions", "wiki", "code", "docs")
# 생성물·의존 트리는 건너뛰고 제품·빌드·DB 진입점을 실제 기본 브랜치의 경로에서 찾는다.
EXCLUDED_DIRS = {".git", "node_modules", "vendor", "dist", "build", "target", "__pycache__", ".gradle", ".next", "generated", "coverage"}
CODE_SUFFIXES = {".py", ".java", ".kt", ".kts", ".scala", ".groovy", ".js", ".jsx", ".ts", ".tsx",
                 ".mjs", ".cjs", ".vue", ".svelte", ".go", ".rs", ".c", ".h", ".cpp", ".cc", ".hpp",
                 ".cs", ".swift", ".rb", ".php", ".sql", ".sh", ".bash", ".proto", ".graphql", ".dart",
                 ".lua", ".ex", ".exs", ".erl", ".clj", ".r", ".xml", ".yml", ".yaml", ".tf"}


def code_path(path):
    name = Path(path)
    return (not EXCLUDED_DIRS.intersection(name.parts)
            and not name.name.endswith((".min.js", ".d.ts", "lock.yaml"))
            and (name.suffix.lower() in CODE_SUFFIXES or name.name in {"Makefile", "Dockerfile", "Jenkinsfile"}))


def product_entry(path):
    name = Path(path)
    support_dirs = {"test", "tests", "__tests__", "spec", "specs", "fixture", "fixtures", "__fixtures__",
                    "testfixtures", "testdata", "mocks", "__mocks__", "androidtest"}
    parts = {part.lower() for part in name.parts[:-1]}
    stem = name.stem.lower()
    return (code_path(path) and not support_dirs.intersection(parts)
            and not stem.startswith(("test_", "fixture_"))
            and not name.stem.endswith(("Test", "Tests", "Spec"))
            and not stem.endswith(("_test", ".test", "_spec", ".spec", ".fixture", ".generated")))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def component(value):
    if not isinstance(value, str) or value in {"", ".", ".."} or Path(value).name != value:
        raise ValueError(f"잘못된 경로 이름: {value!r}")
    return value


def state_path(wiki, domain):
    return wiki / "state" / "review" / (component(domain) + ".json")


def state_at(path):
    try:
        data = read_json(path)
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: JSON 객체 필요")
    return data


def collect_merge_route(args, result, proposed):
    cmd = ["--wiki", str(args.wiki), "--workspace", str(args.workspace), "--out", str(args.out),
           "--domain", args.domain, "--max-merges", str(args.max_merges)]
    for start in args.start:
        cmd.extend(["--start", start])
    status = collect_merges(cmd)
    work = read_json(args.out / "work.json")
    result["errors"].extend(f"{s}: {why}" for s, why in work["skipped"].items())
    if status == 20:
        result["errors"].append("머지 시작 지점 필요: " + ", ".join(work["unset"]))
        return work
    for slug, info in work["repos"].items():
        for batch in info["batches"]:
            result["items"].append({"slug": slug, "repo": info["path"], "batch": batch["id"],
                                    "shas": batch["shas"], "diffs": batch["diffs"]})
        if slug not in work["skipped"] and (info["commits"] or info["bootstrapped"]):
            proposed["merges:" + slug] = info["commits"][-1]["sha"] if info["commits"] else info["cursor"]
    return work


def collect_decisions(args, prior, result, proposed):
    config = read_json(args.config)
    sources = config.get("decisionSources", {}).get(args.domain)
    if not isinstance(sources, dict) or not sources:
        raise ValueError(f"도메인 {args.domain}의 decisionSources 미등록")
    if args.decision_feed is None:
        raise ValueError("등록 출처의 --decision-feed가 없음")
    feed = read_json(args.decision_feed)
    if not isinstance(feed, dict):
        raise ValueError("결정 조회 결과는 출처별 JSON 객체여야 함")
    for name, query in sources.items():
        key = "decisions:" + name
        try:
            row = feed.get(name)
            if not query or not isinstance(row, dict):
                raise ValueError("등록 조회 범위 또는 조회 결과가 없음")
            if row.get("error"):
                raise ValueError(str(row["error"]))
            if row.get("scope") != query:
                raise ValueError("실제 조회 범위가 등록한 결정 출처와 다름")
            if row.get("complete") is not True or row.get("next") is not None:
                raise ValueError("마지막 페이지까지 조회하지 못함")
            checkpoint = prior.get(key)
            if checkpoint is not None and (not isinstance(checkpoint, dict) or checkpoint.get("scope") != query):
                raise ValueError("저장된 결정 조회 범위와 다름 — 새 출처 이름과 최초 조회 범위 필요")
            previous_end = checkpoint["through"] if checkpoint else None
            if "from" not in row or row["from"] != previous_end:
                raise ValueError("조회 시작점이 기준 브랜치의 커서와 다름")
            if not isinstance(row.get("through"), str) or not row["through"].strip():
                raise ValueError("조회 종료 시점·판본이 없음")
            records = row.get("records")
            if not isinstance(records, list) or not all(
                isinstance(rec, dict) and all(isinstance(rec.get(k), str) and rec[k].strip()
                                              for k in ("id", "revision", "url", "text")) for rec in records
            ):
                raise ValueError("원문 기록에 id·revision·url·text가 필요함")
            # 결정권과 대상, 판본의 선후는 URL의 원문과 대조해 검토 단계에서 판정한다.
            result["items"].extend({**rec, "source": name} for rec in records)
            if row["through"] != previous_end:
                proposed[key] = {"scope": query, "through": row["through"]}
        except ValueError as e:
            result["errors"].append(f"{name}: {e}")


def collect_wiki(args, base, prior, result, proposed):
    folder = "knowledge/" + args.domain
    cursor = prior.get("wiki")
    if cursor:
        checked_git(args.wiki, "merge-base", "--is-ancestor", cursor, base)
        interval = [cursor + ".." + base]
    else:
        interval = ["--since=7.days.ago", base]
    revs = checked_git(args.wiki, "log", "--first-parent", "--reverse", "--format=%H", *interval, "--", folder)
    if not cursor and not revs:
        # 첫 조회의 상한을 한 번 기록해야 다음 실행이 늦어져도 7일 사이의 변경을 놓치지 않는다.
        proposed["wiki"] = base
    for rev in revs.splitlines():
        parents = checked_git(args.wiki, "rev-list", "--parents", "-1", rev).split()[1:]
        # 머지에서도 정확히 기준 브랜치에 들어온 변경을 남긴다. 삭제·이름 변경은 이전 텍스트까지 필요하다.
        diff = (["diff", "--find-renames", parents[0], rev] if parents else
                ["show", "--format=", "--find-renames", rev])
        patch = checked_git(args.wiki, *diff, "--", folder)
        target = args.out / "wiki-diffs" / (rev + ".diff")
        target.parent.mkdir(exist_ok=True)
        target.write_text(patch + "\n", encoding="utf-8")
        result["items"].append({"revision": rev, "parent": parents[0] if parents else None, "diff": str(target)})
        proposed["wiki"] = rev


def tree_paths(repo, rev, *paths):
    out = checked_git(repo, "ls-tree", "-rz", "--name-only", rev, "--", *paths)
    return sorted(filter(None, out.split("\0")))


def wiki_docs(args, base):
    prefix = "knowledge/" + args.domain + "/"
    return [p.removeprefix(prefix) for p in tree_paths(args.wiki, base, prefix)
            if p.endswith(".md") and p.startswith(prefix)]


def doc_item(args, base, path):
    return {"doc": path, "repo": str(args.wiki), "revision": base, "path": f"knowledge/{args.domain}/{path}"}


def collect_docs(args, base, prior, result, proposed):
    docs = wiki_docs(args, base)
    cursor = prior.get("docs", "")
    chosen = ([d for d in docs if d > cursor] + [d for d in docs if d <= cursor])[:args.max_docs]
    result["items"].extend(doc_item(args, base, d) for d in chosen)
    if chosen and chosen[-1] != cursor:
        proposed["docs"] = chosen[-1]


def repo_snapshot(args, slug, node, merges):
    known = merges.get("repos", {}).get(slug)
    if known:
        return Path(known["path"]), known["head"]
    repo = args.workspace / component(slug)
    branch = node.get("defaultBranch") or "main"
    if not node.get("remote"):
        raise ValueError(f"{slug}: remote 없음")
    if reason := prepare(repo, node["remote"], branch):
        raise ValueError(f"{slug}: {reason}")
    return repo, checked_git(repo, "rev-parse", "--verify", "origin/" + branch + "^{commit}")


def collect_code(args, repos, merges, prior, result, proposed):
    cursor = prior.get("code", "")
    start_slug, _, start_file = cursor.partition("/")
    # 커서 레포의 나머지 파일 → 다음 레포들 → 한 바퀴 뒤 처음 경로. 경로 목록도 필요한 레포만 읽는다.
    slugs = sorted(repos)
    order = [s for s in slugs if s >= start_slug] + [s for s in slugs if s < start_slug]
    if start_slug in repos:
        order.append(start_slug)
    snapshots = {}
    for i, slug in enumerate(order):
        if slug not in snapshots:
            repo, rev = repo_snapshot(args, slug, repos[slug], merges)
            snapshots[slug] = (repo, rev, [p for p in tree_paths(repo, rev) if product_entry(p)])
        repo, rev, paths = snapshots[slug]
        for path in paths:
            if slug == start_slug and ((i == 0 and path <= start_file) or (i != 0 and path > start_file)):
                continue
            result["items"].append({"slug": slug, "repo": str(repo), "revision": rev, "path": path})
            if len(result["items"]) == args.max_code:
                break
        if len(result["items"]) == args.max_code:
            break
    if result["items"]:
        item = result["items"][-1]
        last = item["slug"] + "/" + item["path"]
        if last != cursor:
            proposed["code"] = last


def matches(repo, rev, text, *paths):
    status, out = git(repo, "grep", "-Iilz", "-F", "-e", text, rev, "--", *paths)
    if status not in (0, 1):
        raise ValueError(f"git grep 실패 — {first_line(out)}")
    return {p.removeprefix(rev + ":") for p in out.split("\0") if p}


def collect_topic(args, base, repos, result):
    folder = "knowledge/" + args.domain + "/"
    query = args.topic
    docs = wiki_docs(args, base)
    hits = matches(args.wiki, base, query, folder)
    # 사용자가 결과의 Git 경로·도메인 상대 경로·파일명을 그대로 넘길 수 있다.
    needle = query.removeprefix(str(args.wiki) + "/").removeprefix(folder).casefold()
    selected = [d for d in docs if folder + d in hits or needle in d.casefold()]
    # 문서 검색 결과에서 코드 대상을 좁힌다. 공통 문서의 적용 대상도 대상 레포에 포함한다.
    relevant = set()
    for doc in selected:
        item = doc_item(args, base, doc)
        result["items"].append(item)
        content = checked_git(args.wiki, "show", base + ":" + item["path"])
        relevant.update(s for s in repos if doc.startswith(s + "/") or s in content)
    service_path = query.removeprefix(str(args.workspace) + "/")
    named_slug, sep, subpath = service_path.partition("/")
    targets = {named_slug} if sep and named_slug in repos and not selected else relevant or repos
    for slug in sorted(targets):
        try:
            repo, rev = repo_snapshot(args, slug, repos[slug], {})
            matching = matches(repo, rev, query)
            term = subpath if sep and named_slug == slug else query
            files = [p for p in tree_paths(repo, rev) if code_path(p)
                     and (p in matching or term.casefold() in p.casefold())]
            result["items"].extend({"slug": slug, "repo": str(repo), "revision": rev, "path": p}
                                   for p in files[:args.max_code])
            if len(files) > args.max_code:
                result.setdefault("remaining", {})[slug] = len(files) - args.max_code
        except (ValueError, OSError) as e:
            result["errors"].append(str(e))


def finalize(args):
    report = read_json(args.out / "review.json")
    if report["domain"] != args.domain or str(args.wiki) != report["wiki"]:
        raise ValueError("수집한 위키·도메인과 완료 대상이 다름")
    checked_git(args.wiki, "merge-base", "--is-ancestor", report["base"], "HEAD")
    keys = set(args.finalize.split(","))
    unknown = keys - report["proposed"].keys()
    if unknown:
        raise ValueError("검토 위치를 기록할 수 없는 범위: " + ", ".join(sorted(unknown)))
    progress = state_path(args.wiki, args.domain)
    current = state_at(progress)
    updates = {}
    for key in sorted(keys):
        value = report["proposed"][key]
        if key.startswith("merges:"):
            path = args.wiki / "state" / (component(key.removeprefix("merges:")) + ".json")
            old = state_at(path)
            cursor = old.get("cursor") or None
            if cursor == value:
                continue
            if cursor != report["previous"].get(key):
                raise ValueError(f"{key} 머지 위치가 수집 이후 바뀜")
            updates[path] = {**old, "cursor": value, "at": date.today().isoformat()}
        else:
            if current.get(key) not in (report["previous"].get(key), value):
                raise ValueError(f"{key} 위치가 수집 이후 바뀜")
            if current.get(key) != value:
                current[key] = value
                updates[progress] = current
    for path, data in updates.items():
        write_json(path, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--out", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--paths", default=",".join(ROUTES))
    mode.add_argument("--topic")
    mode.add_argument("--finalize", help="완전히 검토한 proposed 키를 쉼표로 구분")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "config.json")
    parser.add_argument("--decision-feed", type=Path)
    parser.add_argument("--max-code", type=int, default=1)
    parser.add_argument("--max-docs", type=int, default=1)
    parser.add_argument("--max-merges", type=int, default=10)
    parser.add_argument("--start", action="append", default=[])
    args = parser.parse_args()
    args.wiki, args.out = (p.expanduser().resolve() for p in (args.wiki, args.out))
    component(args.domain)
    if args.finalize is not None:
        finalize(args)
        return 0
    if args.workspace is None or min(args.max_code, args.max_docs, args.max_merges) < 1:
        parser.error("--workspace 및 양의 수집 예산이 필요함")
    args.workspace = args.workspace.expanduser().resolve()
    selected = set(args.paths.split(","))
    if selected - set(ROUTES) or (args.topic is not None and not args.topic.strip()):
        parser.error("알 수 없는 --paths 또는 빈 주제")
    args.out.mkdir(parents=True, exist_ok=True)
    base = checked_git(args.wiki, "rev-parse", "--verify", "HEAD^{commit}")
    repos = read_json(args.wiki / "registry.json")["domains"][args.domain]["repos"]
    for slug in repos:
        component(slug)
    prior = state_at(state_path(args.wiki, args.domain))
    proposed, sources, merges = {}, {}, {}
    for route in (["topic"] if args.topic is not None else ROUTES):
        if route != "topic" and route not in selected:
            continue
        result = sources[route] = {"items": [], "errors": []}
        try:
            if route == "merges":
                merges = collect_merge_route(args, result, proposed)
                for slug, info in merges["repos"].items():
                    if "merges:" + slug in proposed:
                        prior["merges:" + slug] = None if info["bootstrapped"] else info["cursor"]
            elif route == "decisions":
                collect_decisions(args, prior, result, proposed)
            elif route == "wiki":
                collect_wiki(args, base, prior, result, proposed)
            elif route == "code":
                collect_code(args, repos, merges, prior, result, proposed)
            elif route == "docs":
                collect_docs(args, base, prior, result, proposed)
            else:
                collect_topic(args, base, repos, result)
        except (ValueError, OSError, KeyError, TypeError, AttributeError) as e:
            result["errors"].append(str(e))
            proposed.pop(route, None)
    path = args.out / "review.json"
    write_json(path, {"domain": args.domain, "wiki": str(args.wiki), "base": base, "sources": sources,
                      "previous": prior, "proposed": proposed})
    print(path)
    return int(any(source["errors"] for source in sources.values()))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, KeyError, ValueError, TypeError) as error:
        sys.exit(str(error))
