"""후보 5 — monologg/koelectra-base-v3-discriminator 파인튜닝.

KcELECTRA 와 같은 ELECTRA 계열이지만 사전학습 자료가 다르다(뉴스·위키·
블로그 등 더 정제된 자료 위주). Apache-2.0 라이선스, 상업적 사용 가능
(HuggingFace 태그로 확인, 2026-09-22).
"""

from pathlib import Path

import finetune_common as common

MODEL_NAME = "monologg/koelectra-base-v3-discriminator"
OUT_DIR = Path(__file__).parent / "model_koelectra"

if __name__ == "__main__":
    common.run(MODEL_NAME, OUT_DIR)
