"""여러 사전학습 모델을 같은 방법으로 파인튜닝하기 위한 공통 코드.

강의 5강 방법(뒤쪽 몇 개 층 + 분류 head만 학습, 앞쪽은 얼림)을 후보마다
독립된 스크립트(`finetune_*.py`)에서 반복하지 않으려고 뺐다. 모델
아키텍처(BERT/RoBERTa/ELECTRA)가 달라도 `encoder.layer` 구조는 같아서
속성 이름만 찾아내면 얼리는 로직은 그대로 쓸 수 있다.
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
DATA_DIR = Path(__file__).parent / "data"
MAX_LEN = 64
BATCH_SIZE = 16
EPOCHS = 4
LR = 2e-5
UNFROZEN_LAYERS = 2  # 뒤에서부터 몇 개 층을 학습시킬지. 나머지는 얼린다.

LABELS = ["NEGATIVE", "NEUTRAL", "POSITIVE"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}

_HANGUL = re.compile(r"[가-힣]")


def has_korean(text: str) -> bool:
    return bool(_HANGUL.search(text))


def load_training_rows() -> list[tuple[str, str]]:
    """(title, label) 목록. 검증 세트(poc/data/eval_set.csv)과 겹치는 제목은 뺀다."""
    with open(DATA_DIR / "eval_set.csv", encoding="utf-8-sig") as f:
        eval_titles = {row["title"].strip() for row in csv.DictReader(f)}

    rows: list[tuple[str, str]] = []
    with open(DATA_DIR / "silver_labels.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            title = row["title"].strip()
            if not title or not has_korean(title):
                continue
            if title in eval_titles:
                continue  # 검증 세트 유출 방지
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


# AutoModelForSequenceClassification 이 만드는 클래스들의 백본 속성 이름.
# BertForSequenceClassification.bert / RobertaForSequenceClassification.roberta /
# ElectraForSequenceClassification.electra 처럼 모델 클래스 이름 규칙을 따른다.
_BACKBONE_ATTRS = ("electra", "bert", "roberta", "deberta", "distilbert")


def get_encoder_layers(model):
    """모델 아키텍처와 무관하게 트랜스포머 층 리스트를 찾아 돌려준다."""
    for attr in _BACKBONE_ATTRS:
        base = getattr(model, attr, None)
        if base is not None and hasattr(base, "encoder") and hasattr(base.encoder, "layer"):
            return base.encoder.layer
    raise ValueError(
        f"{type(model).__name__} 에서 encoder.layer 를 못 찾았다 - "
        f"이 아키텍처는 finetune_common.py 에 백본 이름을 추가해야 한다."
    )


def freeze_backbone(model, unfrozen_layers: int = UNFROZEN_LAYERS) -> None:
    """뒤쪽 unfrozen_layers 개 트랜스포머 층 + 분류 head 만 학습 대상으로 남긴다."""
    for p in model.parameters():
        p.requires_grad = False

    encoder_layers = get_encoder_layers(model)
    n = len(encoder_layers)
    for layer in encoder_layers[n - unfrozen_layers :]:
        for p in layer.parameters():
            p.requires_grad = True

    for p in model.classifier.parameters():
        p.requires_grad = True

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"학습 대상 파라미터: {trainable:,} / 전체 {total:,} ({trainable/total:.1%})")


def run(model_name: str, out_dir: Path, unfrozen_layers: int = UNFROZEN_LAYERS) -> float:
    """모델 하나를 파인튜닝하고 저장한다. 마지막 에폭의 검증 정확도를 돌려준다."""
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    rows = load_training_rows()
    print(f"[{model_name}] 학습 자료 {len(rows)}건 (한국어, 검증 세트 제외)")
    rng = np.random.RandomState(SEED)
    idx = rng.permutation(len(rows))
    split = int(len(rows) * 0.9)
    train_rows = [rows[i] for i in idx[:split]]
    val_rows = [rows[i] for i in idx[split:]]
    print(f"train={len(train_rows)} val={len(val_rows)}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL2ID
    )
    freeze_backbone(model, unfrozen_layers)

    train_ds = TitleDataset(train_rows, tokenizer)
    val_ds = TitleDataset(val_rows, tokenizer)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(0.1 * total_steps), num_training_steps=total_steps
    )

    device = torch.device("cpu")
    model.to(device)

    val_acc = float("nan")
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
        print(f"[{model_name}] epoch {epoch}/{EPOCHS} train_loss={avg_loss:.4f} val_acc={val_acc:.3f}")

    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)
    print(f"[{model_name}] 모델 저장: {out_dir}")
    return val_acc
