"""모든 후보를 같은 20건 검증셋으로 비교한다.

- Gemini: poc/baseline_gemini.py 를 먼저 돌려서 나온 poc/data/pred_gemini.csv
  를 읽는다 (API 호출은 한 번만 하면 되니 분리했다).
- 규칙 기반: poc/baseline_rule.py 를 그 자리에서 돌린다.
- 파인튜닝 모델들: FINETUNED_MODELS 에 적힌 poc/model* 디렉터리마다 그
  자리에서 불러와 돌린다. 아직 파인튜닝을 안 돌린 모델은 건너뛰고 표시만
  남긴다 - 부분적으로만 완료된 상태에서도 지금까지 나온 결과를 볼 수 있게.

출력: results/comparison.md
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from urllib.parse import quote

# Windows 콘솔 기본 코드페이지(cp949)가 em dash 같은 일부 유니코드 문자를
# 못 받아 print() 가 죽는다. 파일 출력(comparison.md)은 항상 UTF-8 이라
# 영향 없다 - 이건 터미널에 상태를 찍는 print() 만의 문제다.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import baseline_rule

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT.parent / "results"
LABELS = ["NEGATIVE", "NEUTRAL", "POSITIVE"]

_BADGE_COLOR = {"NEGATIVE": "orange", "NEUTRAL": "yellow", "POSITIVE": "green", "PARSE_FAILED": "red"}
_BADGE_TEXT_KO = {"NEGATIVE": "부정", "NEUTRAL": "중립", "POSITIVE": "긍정", "PARSE_FAILED": "파싱실패"}


def badge(label: str) -> str:
    """라벨을 한글 텍스트 + 색깔 shields.io 배너 이미지로 바꾼다.
    세 라벨과 파싱실패 밖의 값은 그대로 텍스트로 둔다."""
    color = _BADGE_COLOR.get(label)
    if color is None:
        return label
    text = _BADGE_TEXT_KO[label]
    return f"![{text}](https://img.shields.io/badge/{quote(text)}-{color})"

# 짧은 이름, 전체 이름, 모델 디렉터리, 사전학습 성격 한 줄. finetune_*.py 로 만든
# 것만 여기 적으면 evaluate.py 가 자동으로 찾아서 비교한다 - 없으면 건너뛴다.
# 짧은 이름은 오분류 상세표의 열 머리글로 쓴다 - 거기 전체 이름을 넣으면 표가
# 가로로 터져서 못 읽는다. 전체 이름은 요약표와 혼동행렬 제목에만 쓴다.
FINETUNED_MODELS = [
    ("KcELECTRA", "KcELECTRA-base-v2022", ROOT / "model", "뉴스 댓글(구어체) 사전학습, MIT"),
    ("klue/roberta", "klue/roberta-base", ROOT / "model_klue_roberta", "위키·뉴스(격식체) 사전학습, 라이선스 미확인"),
    ("KoELECTRA", "KoELECTRA-v3", ROOT / "model_koelectra", "뉴스·위키·블로그 사전학습, Apache-2.0"),
    ("KR-FinBert", "KR-FinBert-SC", ROOT / "model_krfinbert", "경제뉴스·증권사 리포트(금융 도메인) 사전학습, 라이선스 미확인"),
]


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


def run_finetuned(rows: list[dict], model_dir: Path) -> list[tuple[str, float]]:
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
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
        key = (row["reference_label"], pred)
        cm[key] = cm.get(key, 0) + 1
    return cm


def directional_flips(rows: list[dict], preds: list[str]) -> int:
    """POSITIVE<->NEGATIVE 로 정반대가 되는 오류 수."""
    n = 0
    for row, pred in zip(rows, preds):
        h = row["reference_label"]
        if (h == "POSITIVE" and pred == "NEGATIVE") or (h == "NEGATIVE" and pred == "POSITIVE"):
            n += 1
    return n


def format_cm(cm: dict[tuple[str, str], int]) -> str:
    header = "참조라벨\\예측 | " + " | ".join(badge(l) for l in LABELS) + " | 기타(실패등)"
    lines = [header, "---|" + "---|" * (len(LABELS) + 1)]
    all_preds = set(p for _, p in cm) | set(LABELS)
    extra_preds = sorted(all_preds - set(LABELS))
    for h in LABELS:
        cells = [str(cm.get((h, p), 0)) for p in LABELS]
        extra_count = sum(cm.get((h, p), 0) for p in extra_preds)
        lines.append(f"{badge(h)} | " + " | ".join(cells) + f" | {extra_count}")
    return "\n".join(lines)


def main() -> None:
    rows = load_eval_set()
    n = len(rows)
    gemini_map = load_gemini_preds()

    # 키는 짧은 이름(표 머리글용), full_name 이 요약표·혼동행렬에 쓸 전체 이름.
    candidates: dict[str, tuple[list[str], list[float]]] = {}
    full_name: dict[str, str] = {}

    candidates["Gemini"] = (
        [gemini_map[row["idx"]][0] for row in rows],
        [gemini_map[row["idx"]][1] for row in rows],
    )
    full_name["Gemini"] = "지금 쓰는 방식 (Gemini 2.5 Flash API)"

    rule_results = run_rule_baseline(rows)
    candidates["규칙 기반"] = ([p for p, _ in rule_results], [t for _, t in rule_results])
    full_name["규칙 기반"] = "규칙 기반 키워드 매칭"

    skipped = []
    for short, name, model_dir, note in FINETUNED_MODELS:
        if not model_dir.exists():
            skipped.append(name)
            continue
        results = run_finetuned(rows, model_dir)
        candidates[short] = ([p for p, _ in results], [t for _, t in results])
        full_name[short] = f"{name} 파인튜닝 (로컬) — {note}"

    if skipped:
        print(f"아직 파인튜닝 안 됨, 건너뜀: {', '.join(skipped)}")

    RESULTS_DIR.mkdir(exist_ok=True)
    lines = [
        "# PoC 비교 결과",
        "",
        f"검증셋 20건 ({DATA_DIR / 'eval_set.csv'}), 모델을 돌리기 전에 확정했다.",
        "",
        "> **주의 — 아래 '일치율'은 정확도가 아니다.** 참조 라벨(`reference_label` 칸)은 "
        "사람이 아니라 Claude 가 Gemini 라벨을 본 상태에서 매긴 것이고, 사람 검수를 "
        "거치지 않았다. 20건 중 15건이 Gemini 라벨과 같아 기준선이 자기를 보고 만든 "
        "기준으로 채점받는 구조다. 자세한 것은 ANALYSIS.md 의 한계 절.",
        "",
    ]
    lines.append("| 후보 | 일치율 | 방향 반전 오류(POS↔NEG) | 평균 처리시간(건당) | 외부 전송 |")
    lines.append("|---|---|---|---|---|")

    summary = {}
    for short, (preds, latency) in candidates.items():
        correct = sum(1 for row, p in zip(rows, preds) if row["reference_label"] == p)
        acc = correct / n
        flips = directional_flips(rows, preds)
        avg_lat = sum(latency) / len(latency)
        external = "예 (Google)" if "Gemini" in short else "아니오"
        lines.append(
            f"| {full_name[short]} | {correct}/{n} ({acc:.0%}) | {flips}건 | {avg_lat:.3f}초 | {external} |"
        )
        summary[short] = {"acc": acc, "flips": flips, "correct": correct}

    lines.append("")
    lines.append("성공 기준: 14/20(70%) 이상 + 방향 반전 오류 2건 이하 (PROBLEM.md).")
    if skipped:
        lines.append(f"아직 파인튜닝 안 돼서 이번 표에는 없음: {', '.join(skipped)}")
    lines.append("")

    for short, (preds, _) in candidates.items():
        lines.append(f"## {full_name[short]} — 혼동행렬")
        lines.append("")
        lines.append(format_cm(confusion_matrix(rows, preds)))
        lines.append("")

    names = list(candidates.keys())  # 짧은 이름 - 열 머리글로 들어간다
    lines.append("## 오분류 상세 (모든 후보 나열)")
    lines.append("")
    lines.append("| idx | 제목 | 참조 | " + " | ".join(names) + " | 비고 |")
    lines.append("|---|---|---|" + "---|" * len(names) + "---|")
    for i, row in enumerate(rows):
        preds_here = {name: preds[i] for name, (preds, _) in candidates.items()}
        any_wrong = any(p != row["reference_label"] for p in preds_here.values())
        if not any_wrong:
            continue
        note = "어려운 사례" if row["is_hard"] == "1" else ""
        title_short = row["title"][:35]
        cells = " | ".join(badge(preds_here[name]) for name in names)
        lines.append(f"| {row['idx']} | {title_short} | {badge(row['reference_label'])} | {cells} | {note} |")

    out_path = RESULTS_DIR / "comparison.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"저장: {out_path}")
    for name, s in summary.items():
        print(f"{name}: {s['correct']}/{n} 일치, 방향반전 {s['flips']}건")


if __name__ == "__main__":
    main()
