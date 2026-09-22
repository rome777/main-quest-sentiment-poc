# PoC 비교 결과

검증셋 20건 (C:\aiffel_work\main-quest\poc\data\eval_set.csv), 모델을 돌리기 전에 확정했다.

> **주의 — 아래 '일치율'은 정확도가 아니다.** 참조 라벨(`reference_label` 칸)은 사람이 아니라 Claude 가 Gemini 라벨을 본 상태에서 매긴 것이고, 사람 검수를 거치지 않았다. 20건 중 15건이 Gemini 라벨과 같아 기준선이 자기를 보고 만든 기준으로 채점받는 구조다. 자세한 것은 ANALYSIS.md 의 한계 절.

| 후보 | 일치율 | 방향 반전 오류(POS↔NEG) | 평균 처리시간(건당) | 외부 전송 |
|---|---|---|---|---|
| 지금 쓰는 방식 (Gemini 2.5 Flash API) | 13/20 (65%) | 0건 | 6.246초 | 예 (Google) |
| 규칙 기반 키워드 매칭 | 7/20 (35%) | 0건 | 0.000초 | 아니오 |
| KcELECTRA-base-v2022 파인튜닝 (로컬) — 뉴스 댓글(구어체) 사전학습, MIT | 12/20 (60%) | 3건 | 0.078초 | 아니오 |
| klue/roberta-base 파인튜닝 (로컬) — 위키·뉴스(격식체) 사전학습, 라이선스 미확인 | 8/20 (40%) | 6건 | 0.095초 | 아니오 |
| KoELECTRA-v3 파인튜닝 (로컬) — 뉴스·위키·블로그 사전학습, Apache-2.0 | 9/20 (45%) | 6건 | 0.083초 | 아니오 |
| KR-FinBert-SC 파인튜닝 (로컬) — 경제뉴스·증권사 리포트(금융 도메인) 사전학습, 라이선스 미확인 | 11/20 (55%) | 3건 | 0.081초 | 아니오 |

성공 기준: 14/20(70%) 이상 + 방향 반전 오류 2건 이하 (PROBLEM.md).

## 지금 쓰는 방식 (Gemini 2.5 Flash API) — 혼동행렬

참조라벨\예측 | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 기타(실패등)
---|---|---|---|---|
![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 5 | 1 | 0 | 1
![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 1 | 2 | 3 | 1
![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 0 | 0 | 6 | 0

## 규칙 기반 키워드 매칭 — 혼동행렬

참조라벨\예측 | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 기타(실패등)
---|---|---|---|---|
![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 1 | 6 | 0 | 0
![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 1 | 6 | 0 | 0
![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 0 | 6 | 0 | 0

## KcELECTRA-base-v2022 파인튜닝 (로컬) — 뉴스 댓글(구어체) 사전학습, MIT — 혼동행렬

참조라벨\예측 | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 기타(실패등)
---|---|---|---|---|
![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 5 | 0 | 2 | 0
![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 1 | 3 | 3 | 0
![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 1 | 1 | 4 | 0

## klue/roberta-base 파인튜닝 (로컬) — 위키·뉴스(격식체) 사전학습, 라이선스 미확인 — 혼동행렬

참조라벨\예측 | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 기타(실패등)
---|---|---|---|---|
![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 4 | 0 | 3 | 0
![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 3 | 3 | 1 | 0
![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 3 | 2 | 1 | 0

## KoELECTRA-v3 파인튜닝 (로컬) — 뉴스·위키·블로그 사전학습, Apache-2.0 — 혼동행렬

참조라벨\예측 | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 기타(실패등)
---|---|---|---|---|
![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 3 | 1 | 3 | 0
![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 1 | 4 | 2 | 0
![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 3 | 1 | 2 | 0

## KR-FinBert-SC 파인튜닝 (로컬) — 경제뉴스·증권사 리포트(금융 도메인) 사전학습, 라이선스 미확인 — 혼동행렬

참조라벨\예측 | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 기타(실패등)
---|---|---|---|---|
![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 4 | 2 | 1 | 0
![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 2 | 5 | 0 | 0
![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 2 | 2 | 2 | 0

## 오분류 상세 (모든 후보 나열)

| idx | 제목 | 참조 | Gemini | 규칙 기반 | KcELECTRA | klue/roberta | KoELECTRA | KR-FinBert | 비고 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 이더파이 내 숏 청산가 딱 찍고 내려가네 ㅋㅋㅋㅋ | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 어려운 사례 |
| 2 | 숏충이 손절했네 바로 내릴께 | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 어려운 사례 |
| 3 | 너가 숏잡아서 한번더올릴께 ㅇㅇ | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) |  |
| 4 | 푸틴형 미사일싸줘요 빵야빵야 | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![파싱실패](https://img.shields.io/badge/%ED%8C%8C%EC%8B%B1%EC%8B%A4%ED%8C%A8-red) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | 어려운 사례 |
| 5 | 스토리지 잘가세요~~ | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) |  |
| 7 | 아래에서 탄 새끼들 지금 좆도 안쫄리면서 ㅅㅂ | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) |  |
| 8 | 이제 크립토로 싸이클 전환임 | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) |  |
| 9 | 진입못하고 포모오던 관망단들 개추 ㅋㅋㅋㅋ | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) |  |
| 10 | 비트 방금 말아올린거보고 롱으로 정했다 | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) |  |
| 11 | 억단위 익절 얼마만이노 ㅋㅋㅋㅋㅋ | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) |  |
| 12 | 이더 7월 저점에 샀으면 +50%네 | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 어려운 사례 |
| 13 | 매매할게 없다… | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) |  |
| 14 | 대운지 ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 어려운 사례 |
| 15 | 설거지장 냄새 존나나네...튀어야겠노 ㄷㄷ | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) |  |
| 16 | 랍스터 숏 치다가 목 돌아 가겠다.. | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) |  |
| 17 | 기분좋게 점심먹으려하는데 | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | 어려운 사례 |
| 19 | 코인턴 왔냐 ㅋㅋㅋㅋ | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![파싱실패](https://img.shields.io/badge/%ED%8C%8C%EC%8B%B1%EC%8B%A4%ED%8C%A8-red) | ![중립](https://img.shields.io/badge/%EC%A4%91%EB%A6%BD-yellow) | ![긍정](https://img.shields.io/badge/%EA%B8%8D%EC%A0%95-green) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | ![부정](https://img.shields.io/badge/%EB%B6%80%EC%A0%95-orange) | 어려운 사례 |