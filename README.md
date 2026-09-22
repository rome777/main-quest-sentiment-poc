# PoC — 커뮤니티 글 감성분류, Gemini API 탈출

개인 자동매매 시스템(비공개 저장소)이 암호화폐 커뮤니티 글의 감성분류를
Google Gemini 2.5 Flash API에 맡기고 있다. 그 자리에 **로컬에서 도는
한국어 특화 파인튜닝 모델**을 넣을 수 있는지 실측한 PoC다.

- 문제 정의·성공 기준(모델 실행 전 확정): [PROBLEM.md](PROBLEM.md)
- 결과 분석: [ANALYSIS.md](ANALYSIS.md)
- 원본 결과표: [results/comparison.md](results/comparison.md)

## 후보 3개를 실제 데이터로 비교했다

| 후보 | 정확도 | 방향 반전 오류 | 건당 처리시간 | 외부 전송 |
|---|---|---|---|---|
| 1. 지금 쓰는 방식 — Gemini 2.5 Flash API | 65% | 0건 | 6.25초 | 예 |
| 2. 규칙 기반 키워드 매칭 (기존 폴백) | 35% | 0건 | 0초 | 아니오 |
| 3. KcELECTRA-base-v2022 파인튜닝 (로컬) | 60% | 3건 | 0.07초 | 아니오 |

성공 기준(70% 이상 + 방향 반전 2건 이하)에 못 미쳐 **이번 파인튜닝 구성은
채택하지 않는다.** 왜 그런지, 그리고 검증 중 찾은 Gemini 쪽 신뢰성 문제는
[ANALYSIS.md](ANALYSIS.md) 참고.

## 재현 방법

```bash
uv venv .venv --python 3.12 --system-site-packages
uv pip install --python .venv/Scripts/python.exe -r requirements.txt

.venv/Scripts/python.exe poc/baseline_gemini.py      # 후보 1: 본인 GEMINI_API_KEY 필요
.venv/Scripts/python.exe poc/finetune_kcelectra.py   # 후보 3: 첫 실행 시 모델 다운로드
.venv/Scripts/python.exe poc/evaluate.py             # 셋을 한 번에 비교 (후보 2 포함)
```

원본 DB에서 데이터를 다시 뽑고 싶다면 `poc/extract_data.py` (로컬 PostgreSQL
필요, 보통은 건너뛰어도 된다 — 스냅샷이 `poc/data/*.csv` 에 이미 있다).
