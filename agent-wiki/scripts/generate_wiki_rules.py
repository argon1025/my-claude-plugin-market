#!/usr/bin/env python3
# 세션 주입의 첫 블록(위키 제목·도입 문장·행동 규칙)을 출력한다.
# 인자는 현재 레포의 {domain}/{slug}이며 위키 파일은 읽지 않는다.
import sys

RULES = """# 위키 — {key}

이 레포는 MSA 환경의 한 서비스입니다. 개발·코드 리뷰 전에 아래 문서와 레포 목록으로 요청과 관련된 사실과 영향 범위를 확인하세요.

- 사용자 요청에 맞는 문서를 아래 목록에서 먼저 찾아 읽으세요. 목록에서 찾을 수 없으면 마지막으로 문서 폴더를 grep해 본문까지 찾습니다.
- 문서끼리 또는 문서와 코드가 다르면 한쪽을 고르지 말고 두 값을 함께 알리세요.
- 위키는 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리세요."""

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_wiki_rules.py <domain>/<slug>")
    print(RULES.format(key=sys.argv[1]))
