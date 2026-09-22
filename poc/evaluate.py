"""세 후보를 같은 20건 검증셋으로 비교한다.

- 후보 1 (Gemini): poc/baseline_gemini.py 를 먼저 돌려서 나온
  poc/data/pred_gemini.csv 를 읽는다 (API 호출은 한 번만 하면 되니 분리했다).
- 후보 2 (규칙 기반): poc/baseline_rule.py 를 그 자리에서 돌린다.
- 후보 3 (파인튜닝 KcELECTRA): poc/model/ 에서 불러와 그 자리에서 돌린다.

출력: results/comparison.md, results/confusion_*.csv, results/errors.md
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import baseline_rule

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "model"
RESULTS_DIR = ROOT.parent / "results"
LABELS = ["NEGATIVE", "NEUTRAL", "POSITIVE"]


def load_eval_set() -> list[dict]:
    with open(DATA_DIR / "eval_set.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_gemini_preds() -> dict[str, tuple[str, float]]:
    """idx -> (pred_label, latency_sec). poc/baseline_gemini.py 를 먼저 실행해야 한다."""
    path = DATA_DIR / "pred_gemini.csv"
    if not path.exists():
        raise SystemExit(
            "poc/data/pred_gemini.csv 가 없다. 먼저 `python poc/baseline_gemini.py` 를 실행하라."
        )
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            out[row["idx"]] = (row["pred_label"], float(row["latency_sec"]))
    return out


def run_rule_baseline(rows: list[dict]) -> list[tuple[str, float]]:
    preds = []
    for row in rows:
        t0 = time.perf_counter()
        label = baseline_rule.classify(row["title"])
        dt = time.perf_counter() - t0
        preds.append((label, dt))
    return preds


def run_finetuned(rows: list[dict]) -> list[tuple[str, float]]:
    if not MODEL_DIR.exists():
        raise SystemExit(
            "poc/model/ 이 없다. 먼저 `python poc/finetune_kcelectra.py` 를 실행하라."
        )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()

    preds = []
    with torch.no_grad():
        for row in rows:
            t0 = time.perf_counter()
            enc = tokenizer(row["title"], truncation=True, max_length=64, return_tensors="pt")
            logits = model(**enc).logits
            pred_id = logits.argmax(dim=-1).item()
            label = model.config.id2label[pred_id]
            dt = time.perf_counter() - t0
            preds.append((label, dt))
    return preds


def confusion_matrix(rows: list[dict], preds: list[str]) -> dict[tuple[str, str], int]:
    cm: dict[tuple[str, str], int] = {}
    for row, pred in zip(rows, preds):
        key = (row["human_label"], pred)
        cm[key] = cm.get(key, 0) + 1
    return cm


def directional_flips(rows: list[dict], preds: list[str]) -> int:
    """POSITIVE<->NEGATIVE 로 정반대가 되는 오류 수."""
    n = 0
    for row, pred in zip(rows, preds):
        h = row["human_label"]
        if (h == "POSITIVE" and pred == "NEGATIVE") or (h == "NEGATIVE" and pred == "POSITIVE"):
            n += 1
    return n


def format_cm(cm: dict[tuple[str, str], int]) -> str:
    header = "human\\pred | " + " | ".join(LABELS + ["기타(실패등)"])
    lines = [header, "---|" + "---|" * (len(LABELS) + 1)]
    all_preds = set(p for _, p in cm) | set(LABELS)
    extra_preds = sorted(all_preds - set(LABELS))
    for h in LABELS:
        cells = [str(cm.get((h, p), 0)) for p in LABELS]
        extra_count = sum(cm.get((h, p), 0) for p in extra_preds)
        lines.append(f"{h} | " + " | ".join(cells) + f" | {extra_count}")
    return "\n".join(lines)


def main() -> None:
    rows = load_eval_set()
    n = len(rows)
    gemini_map = load_gemini_preds()

    gemini_preds = [gemini_map[row["idx"]][0] for row in rows]
    gemini_latency = [gemini_map[row["idx"]][1] for row in rows]

    rule_results = run_rule_baseline(rows)
    rule_preds = [p for p, _ in rule_results]
    rule_latency = [t for _, t in rule_results]

    ft_results = run_finetuned(rows)
    ft_preds = [p for p, _ in ft_results]
    ft_latency = [t for _, t in ft_results]

    candidates = {
        "1. 지금 쓰는 방식 (Gemini 2.5 Flash API)": (gemini_preds, gemini_latency),
        "2. 규칙 기반 키워드 매칭": (rule_preds, rule_latency),
        "3. KcELECTRA 파인튜닝 (로컬)": (ft_preds, ft_latency),
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    lines = ["# PoC 비교 결과", "", f"검증셋 20건 ({DATA_DIR / 'eval_set.csv'}), 정답은 모델을 돌리기 전에 확정했다.", ""]
    lines.append("| 후보 | 정확도 | 방향 반전 오류(POS↔NEG) | 평균 처리시간(건당) | 외부 전송 |")
    lines.append("|---|---|---|---|---|")

    summary = {}
    for name, (preds, latency) in candidates.items():
        correct = sum(1 for row, p in zip(rows, preds) if row["human_label"] == p)
        acc = correct / n
        flips = directional_flips(rows, preds)
        avg_lat = sum(latency) / len(latency)
        external = "예 (Google)" if "Gemini" in name else "아니오"
        lines.append(f"| {name} | {correct}/{n} ({acc:.0%}) | {flips}건 | {avg_lat:.3f}초 | {external} |")
        summary[name] = {"acc": acc, "flips": flips, "correct": correct}

    lines.append("")
    lines.append(f"성공 기준: 14/20(70%) 이상 + 방향 반전 오류 2건 이하 (PROBLEM.md).")
    lines.append("")

    for name, (preds, _) in candidates.items():
        lines.append(f"## {name} — 혼동행렬")
        lines.append("")
        lines.append(format_cm(confusion_matrix(rows, preds)))
        lines.append("")

    lines.append("## 오분류 상세 (모든 후보 나열)")
    lines.append("")
    lines.append("| idx | 제목 | 정답 | Gemini | 규칙기반 | 파인튜닝 | 비고 |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, row in enumerate(rows):
        preds_here = {name: preds[i] for name, (preds, _) in candidates.items()}
        any_wrong = any(p != row["human_label"] for p in preds_here.values())
        if not any_wrong:
            continue
        g = preds_here["1. 지금 쓰는 방식 (Gemini 2.5 Flash API)"]
        r = preds_here["2. 규칙 기반 키워드 매칭"]
        f = preds_here["3. KcELECTRA 파인튜닝 (로컬)"]
        note = "어려운 사례" if row["is_hard"] == "1" else ""
        title_short = row["title"][:35]
        lines.append(f"| {row['idx']} | {title_short} | {row['human_label']} | {g} | {r} | {f} | {note} |")

    out_path = RESULTS_DIR / "comparison.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"저장: {out_path}")
    for name, s in summary.items():
        print(f"{name}: {s['correct']}/{n} 정확도, 방향반전 {s['flips']}건")


if __name__ == "__main__":
    main()
