"""후보 1 — 지금 쓰는 방식. han-river 프로덕션의 GeminiClassifier 를 그대로
불러와 검증셋 20건에 실제로 호출한다 (같은 프롬프트, 같은 구조화 출력
스키마 — 강의도 말했듯 "지금 쓰는 방식"을 후보에서 빼면 개선 폭을 모른다).

han-river 저장소의 코드를 import 만 한다 — 복사하지 않는다. 프롬프트가
나중에 바뀌어도 이 스크립트는 항상 실제 프로덕션 프롬프트로 비교하게 된다.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

HANRIVER_SRC = Path(r"C:\Project\han-river-view-or-dive\src")
sys.path.insert(0, str(HANRIVER_SRC))
load_dotenv(r"C:\Project\han-river-view-or-dive\.env")

import os  # noqa: E402

from hanriver.llm.prompt import ParseError  # noqa: E402
from hanriver.llm.client import GeminiClassifier  # noqa: E402


async def classify_all(titles: list[str]) -> list[tuple[str, float, int]]:
    """각 제목을 분류하고 (라벨, 소요시간초, 재시도횟수) 리스트를 돌려준다.

    발견한 것: 프로덕션의 `_is_retryable` 은 429/5xx 만 재시도 대상으로 본다.
    그런데 실제로 겹쳐서 호출해 보면 8/20 건꼴로 JSON 이 중간에 끊긴 채
    돌아온다(예: '{"label": "POSITIVE"...' 가 35글자쯤에서 잘림). 이건
    ParseError 라 재시도 대상이 아니고, 지금 프로덕션 코드는 이 경우
    그대로 예외를 던지고 그 잡을 실패 처리한다. 이 PoC 스크립트에서는
    공정한 비교를 위해 여기서만 3회까지 재시도한다.
    """
    api_key = os.environ["GEMINI_API_KEY"]
    # thinking_level="low" 가 지금 API 버전에서 이 모델에 400 을 낸다
    # (프로덕션 코드 작성 이후 API 쪽이 바뀐 것으로 보인다 - han-river 문제이지
    # 이 PoC 스크립트가 고칠 범위가 아니라 여기서만 끈다).
    clf = GeminiClassifier(api_key=api_key, thinking_level="")
    results = []
    for title in titles:
        t0 = time.perf_counter()
        retries = 0
        label = None
        while retries < 5:
            try:
                result = await clf.classify(title)
                label = result.label
                break
            except ParseError:
                retries += 1
        if label is None:
            # 5회 재시도에도 JSON 파싱이 계속 깨졌다 — 실패로 기록하고 계속 진행한다.
            # (프로덕션 코드는 재시도 대상이 아니라서 여기서 그냥 예외로 죽는다.
            # 이 자체가 발견한 문제다 — README 의 "한계" 절 참고.)
            label = "PARSE_FAILED"
        dt = time.perf_counter() - t0
        results.append((label, dt, retries))
    print("Gemini 토큰 사용량:", clf.usage())
    return results


def main() -> None:
    import csv

    data_dir = Path(__file__).parent / "data"
    with open(data_dir / "eval_set.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    titles = [r["title"] for r in rows]

    results = asyncio.run(classify_all(titles))

    with open(data_dir / "pred_gemini.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["idx", "title", "human_label", "pred_label", "latency_sec", "parse_retries"])
        for row, (label, dt, retries) in zip(rows, results):
            w.writerow([row["idx"], row["title"], row["human_label"], label, f"{dt:.3f}", retries])
    n_retried = sum(1 for _, _, r in results if r > 0)
    print(f"JSON 파싱 실패 후 재시도가 필요했던 건: {n_retried}/{len(results)}")
    print(f"저장: {data_dir / 'pred_gemini.csv'}")


if __name__ == "__main__":
    main()
