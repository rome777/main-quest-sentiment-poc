"""후보 4 — klue/roberta-base 파인튜닝.

KcELECTRA(뉴스 댓글, 구어체)와 대조되는 격식체 자료(위키·뉴스 등)로
사전학습된 모델. **라이선스가 모델 카드·태그 어디에도 명시돼 있지 않다**
(2026-09-22, HuggingFace API 로 확인) — 강의 3강이 경고한 바로 그 경우다.
연구 공개물이라 개인 PoC 실험 용도로는 쓰지만, 상용으로 쓸 거면 이 후보는
라이선스가 확인되기 전까지 제외 대상이다.
"""

from pathlib import Path

import finetune_common as common

MODEL_NAME = "klue/roberta-base"
OUT_DIR = Path(__file__).parent / "model_klue_roberta"

if __name__ == "__main__":
    common.run(MODEL_NAME, OUT_DIR)
