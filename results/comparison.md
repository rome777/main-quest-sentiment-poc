# PoC 비교 결과

검증셋 20건 (C:\aiffel_work\main-quest\poc\data\eval_set.csv), 정답은 모델을 돌리기 전에 확정했다.

| 후보 | 정확도 | 방향 반전 오류(POS↔NEG) | 평균 처리시간(건당) | 외부 전송 |
|---|---|---|---|---|
| 1. 지금 쓰는 방식 (Gemini 2.5 Flash API) | 13/20 (65%) | 0건 | 6.246초 | 예 (Google) |
| 2. 규칙 기반 키워드 매칭 | 7/20 (35%) | 0건 | 0.000초 | 아니오 |
| 3. KcELECTRA 파인튜닝 (로컬) | 12/20 (60%) | 3건 | 0.071초 | 아니오 |

성공 기준: 14/20(70%) 이상 + 방향 반전 오류 2건 이하 (PROBLEM.md).

## 1. 지금 쓰는 방식 (Gemini 2.5 Flash API) — 혼동행렬

human\pred | NEGATIVE | NEUTRAL | POSITIVE | 기타(실패등)
---|---|---|---|---|
NEGATIVE | 5 | 1 | 0 | 1
NEUTRAL | 1 | 2 | 3 | 1
POSITIVE | 0 | 0 | 6 | 0

## 2. 규칙 기반 키워드 매칭 — 혼동행렬

human\pred | NEGATIVE | NEUTRAL | POSITIVE | 기타(실패등)
---|---|---|---|---|
NEGATIVE | 1 | 6 | 0 | 0
NEUTRAL | 1 | 6 | 0 | 0
POSITIVE | 0 | 6 | 0 | 0

## 3. KcELECTRA 파인튜닝 (로컬) — 혼동행렬

human\pred | NEGATIVE | NEUTRAL | POSITIVE | 기타(실패등)
---|---|---|---|---|
NEGATIVE | 5 | 0 | 2 | 0
NEUTRAL | 1 | 3 | 3 | 0
POSITIVE | 1 | 1 | 4 | 0

## 오분류 상세 (모든 후보 나열)

| idx | 제목 | 정답 | Gemini | 규칙기반 | 파인튜닝 | 비고 |
|---|---|---|---|---|---|---|
| 1 | 이더파이 내 숏 청산가 딱 찍고 내려가네 ㅋㅋㅋㅋ | NEGATIVE | NEGATIVE | NEUTRAL | NEGATIVE | 어려운 사례 |
| 2 | 숏충이 손절했네 바로 내릴께 | NEUTRAL | POSITIVE | NEGATIVE | POSITIVE | 어려운 사례 |
| 3 | 너가 숏잡아서 한번더올릴께 ㅇㅇ | POSITIVE | POSITIVE | NEUTRAL | POSITIVE |  |
| 4 | 푸틴형 미사일싸줘요 빵야빵야 | NEGATIVE | PARSE_FAILED | NEUTRAL | POSITIVE | 어려운 사례 |
| 5 | 스토리지 잘가세요~~ | NEGATIVE | NEGATIVE | NEUTRAL | POSITIVE |  |
| 7 | 아래에서 탄 새끼들 지금 좆도 안쫄리면서 ㅅㅂ | POSITIVE | POSITIVE | NEUTRAL | NEGATIVE |  |
| 8 | 이제 크립토로 싸이클 전환임 | POSITIVE | POSITIVE | NEUTRAL | NEUTRAL |  |
| 9 | 진입못하고 포모오던 관망단들 개추 ㅋㅋㅋㅋ | POSITIVE | POSITIVE | NEUTRAL | POSITIVE |  |
| 10 | 비트 방금 말아올린거보고 롱으로 정했다 | POSITIVE | POSITIVE | NEUTRAL | POSITIVE |  |
| 11 | 억단위 익절 얼마만이노 ㅋㅋㅋㅋㅋ | POSITIVE | POSITIVE | NEUTRAL | POSITIVE |  |
| 12 | 이더 7월 저점에 샀으면 +50%네 | NEUTRAL | POSITIVE | NEUTRAL | POSITIVE | 어려운 사례 |
| 13 | 매매할게 없다… | NEGATIVE | NEUTRAL | NEUTRAL | NEGATIVE |  |
| 14 | 대운지 ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ | NEUTRAL | NEGATIVE | NEUTRAL | NEGATIVE | 어려운 사례 |
| 15 | 설거지장 냄새 존나나네...튀어야겠노 ㄷㄷ | NEGATIVE | NEGATIVE | NEUTRAL | NEGATIVE |  |
| 16 | 랍스터 숏 치다가 목 돌아 가겠다.. | NEGATIVE | NEGATIVE | NEUTRAL | NEGATIVE |  |
| 17 | 기분좋게 점심먹으려하는데 | NEUTRAL | POSITIVE | NEUTRAL | NEUTRAL | 어려운 사례 |
| 19 | 코인턴 왔냐 ㅋㅋㅋㅋ | NEUTRAL | PARSE_FAILED | NEUTRAL | POSITIVE | 어려운 사례 |