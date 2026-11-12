#!/usr/bin/env python3
# 세션 주입의 문서 위치 블록(레포 전용 문서·도메인 공유 문서의 장 수와 경로, 다른 도메인)을 출력하고, --full이면 문서 색인(문서별 이름과 description)을 출력한다.
# 주입에는 문서 이름을 싣지 않는다 — 이름 목록은 문서 수에 비례해 늘어 훅 주입 한도를 넘는다. 문서 행은 frontmatter의 description 한 줄만 읽는다.
import json
import sys
from pathlib import Path


def description(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("description:"):
            return line[len("description:"):].strip().strip("\"'")
    return ""


def block(title, path_line, rows):
    return f"## {title}\n\n`{path_line}`\n\n" + "\n".join(rows) if rows else ""


def docs(folder):
    return [f for f in (sorted(folder.glob("*.md")) if folder.is_dir() else []) if f.is_file()]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--full"]
    if len(args) != 2:
        raise SystemExit("usage: generate_document_list.py <baseRoot> <domain>/<slug> [--full]")
    base = Path(args[0]).expanduser()
    domain, slug = args[1].split("/", 1)
    shared, own = docs(base / "knowledge" / domain), docs(base / "knowledge" / domain / slug)
    shared_path, own_path = f"{base}/knowledge/{domain}/{{name}}.md", f"{base}/knowledge/{domain}/{slug}/{{name}}.md"
    if len(args) < len(sys.argv) - 1:
        rows = lambda files: [f"- {f.stem}" + (f" — {d}" if (d := description(f)) else "") for f in files]
        blocks = [block(f"{slug} 전용 문서", own_path, rows(own)), block("도메인 공유 문서", shared_path, rows(shared))]
    else:
        domains = json.loads((base / "registry.json").read_text())["domains"]
        others = [f"- {d}" + (f" — {g['description']}" if g.get("description") else "")
                  for d, g in domains.items() if d != domain]
        places = ([f"- {slug} 전용 문서 {len(own)}건: `{own_path}`"] if own else []) \
            + ([f"- 도메인 공유 문서 {len(shared)}건: `{shared_path}`"] if shared else [])
        blocks = [
            "## 문서 위치\n\n" + "\n".join(places) if places else "",
            block("다른 도메인 문서", f"{base}/knowledge/{{domain}}/", others),
        ]
    print("\n\n".join(b for b in blocks if b))
