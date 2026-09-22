"""후보 3 — beomi/KcELECTRA-base-v2022 파인튜닝.

네이버 뉴스 댓글(구어체·신조어)로 사전학습된 모델. MIT 라이선스.
학습 로직은 poc/finetune_common.py 를 봐라 — 다른 후보 모델들과 같은
방법(강의 5강: 뒤쪽 층 + 분류 head만 학습, 나머지는 얼림)을 쓴다.
"""

from pathlib import Path

import finetune_common as common

MODEL_NAME = "beomi/KcELECTRA-base-v2022"
OUT_DIR = Path(__file__).parent / "model"

if __name__ == "__main__":
    common.run(MODEL_NAME, OUT_DIR)
