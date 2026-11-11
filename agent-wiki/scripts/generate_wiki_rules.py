#!/usr/bin/env python3
# 세션 주입의 첫 블록(위키 제목·도입 문장·행동 규칙, 색인 경로)을 출력한다.
# 인자는 현재 레포의 {domain}/{slug}와 문서 색인·레포 책임 색인 경로이며 위키 파일은 읽지 않는다. 색인을 쓰지 못한 세션은 경로 없이 호출한다.
import sys

RULES = """# 위키 — {key}

이 레포는 MSA 환경의 한 서비스입니다. 개발·코드 리뷰 전에 아래 문서와 레포 목록으로 요청과 관련된 사실과 영향 범위를 확인하세요.

- {doc_rule}
- 문서끼리 또는 문서와 코드가 다르면 한쪽을 고르지 말고 두 값을 함께 알리세요.
- 위키 폴더는 세션 시작마다 원격 기준으로 초기화되므로 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리고 `agent-wiki의 add 스킬`로 반영을 제안하세요."""

DOC_RULE = "요청이 이 도메인의 업무 사실(정책, 코드값, 상태, 절차, 레포 사이 계약)과 관련되면 문서 폴더를 `^description:`으로 grep해 문서별 용도를 보고 맞는 문서를 골라 읽으세요. 찾을 수 없으면 본문까지 grep합니다."
INDEX_DOC_RULE = "요청이 이 도메인의 업무 사실(정책, 코드값, 상태, 절차, 레포 사이 계약)과 관련되면 문서 색인을 읽고 description으로 맞는 문서를 골라 읽으세요. 색인에서 찾을 수 없으면 문서 폴더를 grep해 본문까지 찾습니다."
INDEX = "\n\n- 문서 색인: `{docs}` — 문서별 이름과 description\n- 레포 책임: `{repos}` — 레포별 책임 전체"

if __name__ == "__main__":
    if len(sys.argv) not in (2, 4):
        raise SystemExit("usage: generate_wiki_rules.py <domain>/<slug> [<docs_index_path> <repos_index_path>]")
    indexed = len(sys.argv) == 4
    print(RULES.format(key=sys.argv[1], doc_rule=INDEX_DOC_RULE if indexed else DOC_RULE)
          + (INDEX.format(docs=sys.argv[2], repos=sys.argv[3]) if indexed else ""))
