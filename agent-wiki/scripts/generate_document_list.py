#!/usr/bin/env python3
# 세션 주입의 문서 목록 블록(도메인 공유 문서, 레포 전용 문서, 다른 도메인)을 출력한다.
# 문서 행은 frontmatter의 description 한 줄만 읽고, 문서가 없는 블록은 제목째 생략한다.
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
            return line[len("description:"):].strip()
    return ""


def block(title, path_line, rows):
    return f"## {title}\n\n`{path_line}`\n\n" + "\n".join(rows) if rows else ""


def doc_rows(folder):
    files = sorted(folder.glob("*.md")) if folder.is_dir() else []
    return [f"- {f.stem}" + (f" — {d}" if (d := description(f)) else "") for f in files if f.is_file()]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate_document_list.py <baseRoot> <domain>/<slug>")
    base = Path(sys.argv[1]).expanduser()
    domain, slug = sys.argv[2].split("/", 1)
    domains = json.loads((base / "registry.json").read_text())["domains"]
    others = [f"- {d}" + (f" — {g['description']}" if g.get("description") else "")
              for d, g in domains.items() if d != domain]
    blocks = [
        block("도메인 공유 문서", f"{base}/knowledge/{domain}/{{name}}.md", doc_rows(base / "knowledge" / domain)),
        block(f"{slug} 전용 문서", f"{base}/knowledge/{domain}/{slug}/{{name}}.md", doc_rows(base / "knowledge" / domain / slug)),
        block("다른 도메인 문서", f"{base}/knowledge/{{domain}}/", others),
    ]
    print("\n\n".join(b for b in blocks if b))
