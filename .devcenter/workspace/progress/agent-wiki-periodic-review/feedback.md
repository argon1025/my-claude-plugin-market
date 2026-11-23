# agent-wiki 정기 점검 작업 기록

- `constraint` 모의 위키에서 신규 파일을 diff에 표시하려고 git add -N을 실행하면 삭제한 추적 파일이 인덱스에도 반영될 수 있다. 문서 병합의 원본 삭제까지 검증하려면 git diff HEAD로 작업 트리와 기준 판본을 대조한다.
  - evidence: tests/check_wiki_review_result.py, dry-run/combined.patch의 export-replay.md 삭제
