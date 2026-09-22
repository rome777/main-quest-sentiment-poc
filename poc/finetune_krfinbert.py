"""후보 6 — snunlp/KR-FinBert-SC 파인튜닝.

**금융 도메인 특화** 모델. 경제 뉴스·증권사 리포트 13.22GB 로 추가
사전학습됐다 - "단순 LLM이 아니라 특별한 분야에 쓰이는 모델"에 가장
가까운 후보다. 원래 2-클래스(긍정/부정) 분류기로 공개돼 있지만, 우리는
3-클래스(POSITIVE/NEGATIVE/NEUTRAL)가 필요해서 분류 head 는 새로
초기화하고 백본(금융 도메인 지식)만 물려받는다 - 강의 5강이 말하는
"보는 눈은 그대로 두고 판단층만 새로 배운다"를 그대로 적용한 것이다.

**라이선스가 모델 카드 어디에도 없다** (2026-09-22, HuggingFace API 로
확인 — README, 태그 둘 다). 경제 뉴스·증권사 리포트로 학습됐다는 점에서
원저작물(뉴스 기사) 저작권도 얽혀 있을 수 있다. 이 PoC 는 개인 실험이라
그대로 실행하지만, **상용 서비스에 쓸 거면 이 후보는 라이선스가 확인되기
전까지 제외 대상이다** (강의 3강: 조건에 걸리는 후보는 성능이 얼마든 뺀다).
"""

from pathlib import Path

import finetune_common as common

MODEL_NAME = "snunlp/KR-FinBert-SC"
OUT_DIR = Path(__file__).parent / "model_krfinbert"

if __name__ == "__main__":
    common.run(MODEL_NAME, OUT_DIR)
