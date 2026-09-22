"""han-river DB에서 감성분류용 실데이터를 뽑아 로컬 CSV로 저장한다.
읽기 전용. 운영 DB에 아무것도 쓰지 않는다.
"""
import asyncio
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Project\han-river-view-or-dive\src")))

import asyncpg
from dotenv import load_dotenv

load_dotenv(r"C:\Project\han-river-view-or-dive\.env")

OUT_DIR = Path(__file__).parent / "data"
OUT_DIR.mkdir(exist_ok=True)


async def main():
    db_url = os.environ["DATABASE_URL"]
    # asyncpg는 postgresql+asyncpg:// 스킴을 안 받는다 -> postgresql:// 로 변환
    conn_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(conn_url)

    # 1) 라벨 분포 확인
    rows = await conn.fetch(
        "SELECT label, count(*) FROM post_sentiment GROUP BY label ORDER BY 2 DESC"
    )
    print("=== post_sentiment 라벨 분포 ===")
    for r in rows:
        print(dict(r))

    total = await conn.fetchval("SELECT count(*) FROM post_sentiment")
    print(f"총 라벨 수: {total}")

    body_notnull = await conn.fetchval(
        "SELECT count(*) FROM raw_post rp JOIN post_sentiment ps ON ps.post_id = rp.id WHERE rp.body IS NOT NULL AND length(rp.body) > 0"
    )
    print(f"본문 있는 라벨 행 수: {body_notnull}")

    # 2) 학습용(대량, silver label = Gemini) 추출: 제목+본문+라벨+신뢰도+비꼬기여부
    rows = await conn.fetch(
        """
        SELECT rp.id, rp.source, rp.board, rp.title, rp.body,
               ps.label, ps.confidence, ps.intensity, ps.is_sarcasm, ps.model
        FROM post_sentiment ps
        JOIN raw_post rp ON rp.id = ps.post_id
        WHERE rp.title IS NOT NULL AND length(rp.title) > 0
        ORDER BY rp.posted_at DESC
        LIMIT 4000
        """
    )
    with open(OUT_DIR / "silver_labels.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "source", "board", "title", "body", "label", "confidence", "intensity", "is_sarcasm", "model"])
        for r in rows:
            w.writerow([r["id"], r["source"], r["board"], r["title"], r["body"], r["label"], r["confidence"], r["intensity"], r["is_sarcasm"], r["model"]])
    print(f"silver_labels.csv: {len(rows)}건 저장")

    # 3) 사람이 검증할 후보 풀 (다양성 확보용): 소스별/라벨별 최근 글 + is_sarcasm=true 글 + confidence 낮은 글
    diverse = await conn.fetch(
        """
        (SELECT rp.id, rp.source, rp.title, rp.body, ps.label, ps.confidence, ps.is_sarcasm
         FROM post_sentiment ps JOIN raw_post rp ON rp.id = ps.post_id
         WHERE ps.is_sarcasm = true AND rp.title IS NOT NULL
         ORDER BY rp.posted_at DESC LIMIT 15)
        UNION ALL
        (SELECT rp.id, rp.source, rp.title, rp.body, ps.label, ps.confidence, ps.is_sarcasm
         FROM post_sentiment ps JOIN raw_post rp ON rp.id = ps.post_id
         WHERE ps.confidence < 60 AND rp.title IS NOT NULL
         ORDER BY rp.posted_at DESC LIMIT 15)
        UNION ALL
        (SELECT rp.id, rp.source, rp.title, rp.body, ps.label, ps.confidence, ps.is_sarcasm
         FROM post_sentiment ps JOIN raw_post rp ON rp.id = ps.post_id
         WHERE ps.label='POSITIVE' AND rp.title IS NOT NULL
         ORDER BY random() LIMIT 15)
        UNION ALL
        (SELECT rp.id, rp.source, rp.title, rp.body, ps.label, ps.confidence, ps.is_sarcasm
         FROM post_sentiment ps JOIN raw_post rp ON rp.id = ps.post_id
         WHERE ps.label='NEGATIVE' AND rp.title IS NOT NULL
         ORDER BY random() LIMIT 15)
        UNION ALL
        (SELECT rp.id, rp.source, rp.title, rp.body, ps.label, ps.confidence, ps.is_sarcasm
         FROM post_sentiment ps JOIN raw_post rp ON rp.id = ps.post_id
         WHERE ps.label='NEUTRAL' AND rp.title IS NOT NULL
         ORDER BY random() LIMIT 15)
        """
    )
    with open(OUT_DIR / "eval_candidates.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "source", "title", "body", "gemini_label", "gemini_confidence", "gemini_is_sarcasm"])
        for r in dict.fromkeys([tuple(r.values()) for r in diverse]):
            w.writerow(r)
    print(f"eval_candidates.csv: {len(set(tuple(r.values()) for r in diverse))}건 저장 (사람 검증용 후보 풀)")

    await conn.close()


asyncio.run(main())
