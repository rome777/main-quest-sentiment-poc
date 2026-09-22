"""KcELECTRA-base-v2022 를 우리 데이터로 파인튜닝한다.

강의 5강의 방법을 그대로 따른다: 사전학습된 모델의 앞쪽 층(보편적인 한국어
구어체 패턴)은 얼리고, 뒤쪽 판단 부분만 우리 데이터로 다시 학습시킨다.

입력: poc/data/silver_labels.csv (Gemini 가 매긴 라벨 = silver label)
- 한국어 글만 쓴다 (이 PoC는 한국어로 범위를 좁혔다, PROBLEM.md 참고)
- 검증셋(poc/data/eval_set.csv)과 제목이 겹치는 행은 학습에서 제외한다
  (안 그러면 파인튜닝 모델이 정답을 이미 본 채로 시험을 보게 된다)

실행 위치: 이 컴퓨터, CPU. 외부로 아무것도 보내지 않는다.
출력: poc/model/ 에 파인튜닝된 가중치 저장. 다시 돌려도 같은 결과가 나오도록
시드를 고정한다.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

SEED = 42
MODEL_NAME = "beomi/KcELECTRA-base-v2022"
DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "model"
MAX_LEN = 64
BATCH_SIZE = 16
EPOCHS = 4
LR = 2e-5
# 뒤에서부터 몇 개 트랜스포머 층을 학습시킬지. 나머지는 얼린다(freeze).
UNFROZEN_LAYERS = 2

LABELS = ["NEGATIVE", "NEUTRAL", "POSITIVE"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}

_HANGUL = re.compile(r"[가-힣]")


def has_korean(text: str) -> bool:
    return bool(_HANGUL.search(text))


def load_training_rows() -> list[tuple[str, str]]:
    """(title, label) 목록. 한국어만, 검증셋과 겹치는 제목은 뺀다."""
    with open(DATA_DIR / "eval_set.csv", encoding="utf-8-sig") as f:
        eval_titles = {row["title"].strip() for row in csv.DictReader(f)}

    rows: list[tuple[str, str]] = []
    with open(DATA_DIR / "silver_labels.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            title = row["title"].strip()
            if not title or not has_korean(title):
                continue
            if title in eval_titles:
                continue  # 검증셋 유출 방지
            rows.append((title, row["label"]))
    return rows


class TitleDataset(Dataset):
    def __init__(self, rows, tokenizer):
        self.rows = rows
        self.tok = tokenizer

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        title, label = self.rows[idx]
        enc = self.tok(
            title,
            truncation=True,
            max_length=MAX_LEN,
            padding="max_length",
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(LABEL2ID[label], dtype=torch.long)
        return item


def freeze_backbone(model, unfrozen_layers: int) -> None:
    """뒤쪽 unfrozen_layers 개 트랜스포머 층 + 분류 head 만 학습 대상으로 남긴다."""
    for p in model.parameters():
        p.requires_grad = False

    # KcELECTRA(ELECTRA discriminator) 구조: model.electra.encoder.layer[i]
    encoder_layers = model.electra.encoder.layer
    n = len(encoder_layers)
    for layer in encoder_layers[n - unfrozen_layers :]:
        for p in layer.parameters():
            p.requires_grad = True

    # 분류 head 는 항상 새로 학습한다.
    for p in model.classifier.parameters():
        p.requires_grad = True

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"학습 대상 파라미터: {trainable:,} / 전체 {total:,} ({trainable/total:.1%})")


def main() -> None:
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    rows = load_training_rows()
    print(f"학습 자료 {len(rows)}건 (한국어, 검증셋 제외)")
    rng = np.random.RandomState(SEED)
    idx = rng.permutation(len(rows))
    split = int(len(rows) * 0.9)
    train_rows = [rows[i] for i in idx[:split]]
    val_rows = [rows[i] for i in idx[split:]]
    print(f"train={len(train_rows)} val={len(val_rows)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL2ID
    )
    freeze_backbone(model, UNFROZEN_LAYERS)

    train_ds = TitleDataset(train_rows, tokenizer)
    val_ds = TitleDataset(val_rows, tokenizer)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=LR
    )
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(0.1 * total_steps), num_training_steps=total_steps
    )

    device = torch.device("cpu")
    model.to(device)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            out = model(**batch)
            out.loss.backward()
            optimizer.step()
            scheduler.step()
            total_loss += out.loss.item()
        avg_loss = total_loss / len(train_loader)

        model.eval()
        correct = 0
        with torch.no_grad():
            for batch in val_loader:
                labels = batch.pop("labels").to(device)
                batch = {k: v.to(device) for k, v in batch.items()}
                logits = model(**batch).logits
                pred = logits.argmax(dim=-1)
                correct += (pred == labels).sum().item()
        val_acc = correct / len(val_ds) if val_ds else float("nan")
        print(f"epoch {epoch}/{EPOCHS} train_loss={avg_loss:.4f} val_acc={val_acc:.3f}")

    OUT_DIR.mkdir(exist_ok=True)
    model.save_pretrained(OUT_DIR)
    tokenizer.save_pretrained(OUT_DIR)
    print(f"모델 저장: {OUT_DIR}")


if __name__ == "__main__":
    main()
