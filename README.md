# PoC — 커뮤니티 글 감성분류, Gemini API 탈출

비공개로 운영 중인 파이프라인이 암호화폐 커뮤니티 글의 감성분류를
Google Gemini 2.5 Flash API에 맡기고 있다. 그 자리에 **로컬에서 도는
한국어 특화 파인튜닝 모델**을 넣을 수 있는지 실측한 PoC다.

- 문제 정의·성공 기준(모델 실행 전 확정): [PROBLEM.md](PROBLEM.md)
- 결과 분석: [ANALYSIS.md](ANALYSIS.md)
- 원본 결과표: [results/comparison.md](results/comparison.md)

## 후보 6개를 실제 데이터로 비교했다

검증셋 20건, 2026-09-22 측정. **'일치율'은 정확도가 아니다** — 참조 라벨을
사람이 아니라 Claude 가 매겼고(사람 검수 없음) 그마저 Gemini 라벨을 본 상태에서
매겼다. 이 PoC 의 가장 큰 한계이고 [ANALYSIS.md](ANALYSIS.md) 에 정리했다.

| 후보 | 일치율 | 방향 반전 오류 | 건당 처리시간 | 외부 전송 |
|---|---|---|---|---|
| 1. 지금 쓰는 방식 — Gemini 2.5 Flash API | 65% | 0건 | 6.25초 | 예 |
| 2. 규칙 기반 키워드 매칭 (기존 폴백) | 35% | 0건 | 0초 | 아니오 |
| 3. KcELECTRA-base-v2022 파인튜닝 (로컬) | 60% | 3건 | 0.08초 | 아니오 |
| 4. klue/roberta-base 파인튜닝 (로컬) | 40% | 6건 | 0.08초 | 아니오 |
| 5. KoELECTRA-v3 파인튜닝 (로컬) | 45% | 6건 | 0.08초 | 아니오 |
| 6. KR-FinBert-SC 파인튜닝 (로컬) | 55% | 3건 | 0.08초 | 아니오 |

성공 기준(70% 이상 + 방향 반전 2건 이하)을 **파인튜닝 후보 네 개가 모두
넘지 못해 이번 구성으로는 채택하지 않는다.** 왜 그런지, 그리고 검증 중
찾은 Gemini 쪽 신뢰성 문제는 [ANALYSIS.md](ANALYSIS.md) 참고.

## 재현 방법

`poc/baseline_gemini.py`, `poc/extract_data.py` 는 비공개 운영 코드/DB에
접근해야 해서 이 저장소만 클론해서는 못 돌린다 (`.env.example` 을 `.env`
로 복사하고 본인 경로를 채워야 한다). 나머지(`finetune_*.py`,
`baseline_rule.py`, `evaluate.py`)는 이미 남겨둔 `poc/data/*.csv` 스냅샷
만으로 그대로 돌아간다.

```bash
uv venv .venv --python 3.12 --system-site-packages
uv pip install --python .venv/Scripts/python.exe -r requirements.txt

.venv/Scripts/python.exe poc/finetune_kcelectra.py     # 후보 3: 첫 실행 시 모델 다운로드
.venv/Scripts/python.exe poc/finetune_klue_roberta.py  # 후보 4
.venv/Scripts/python.exe poc/finetune_koelectra.py     # 후보 5
.venv/Scripts/python.exe poc/finetune_krfinbert.py     # 후보 6
.venv/Scripts/python.exe poc/evaluate.py               # 전체 비교 (학습 안 된 후보는 건너뛴다)
```
