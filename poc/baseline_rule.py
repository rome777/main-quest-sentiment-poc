"""후보 2 — 규칙 기반 키워드 매칭.

운영 코드(비공개 저장소)에 있는 API 키 없을 때의 폴백 분류기와 같은
키워드 목록을 그대로 옮겼다 ("이미 쓰는 것"에 해당). 비용 0, 로컬,
외부 전송 없음. 성능 하한선 참고용으로 넣는다.
"""

from __future__ import annotations

_POSITIVE = frozenset(
    {"가즈아", "떡상", "상승", "축하", "올라", "매수", "불장", "moon", "pump"}
)
_NEGATIVE = frozenset({"한강", "폭락", "손절", "하락", "망했", "공포", "떡락", "dump", "scam"})


def classify(title: str, body: str | None = None) -> str:
    text = (title + " " + (body or "")).lower()
    for kw in _POSITIVE:
        if kw in text:
            return "POSITIVE"
    for kw in _NEGATIVE:
        if kw in text:
            return "NEGATIVE"
    return "NEUTRAL"
