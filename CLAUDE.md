# science-class-assistant

- `app.py`: 과학 탐구 수업 설계 Streamlit 앱 (Gemini).
- `생기부/`: 생활기록부(세특·자율·행동특성) 작성 비서. 작업 전 `생기부/작성규칙.md`와 `생기부/사용법.md`를 읽는다.
  - 비서: `.claude/agents/sgb-reader`(판독) → `sgb-writer`(작성) → `sgb-reviewer`(검수) → `sgb-speller`(맞춤법). 반별로 병렬 실행.
  - 학생 데이터는 `생기부/작업/`에만 두고 커밋하지 않는다. 학생 이름은 어디에도 쓰지 않는다.
