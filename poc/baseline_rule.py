"""후보 2 — 규칙 기반 키워드 매칭.

han-river 저장소의 `hanriver/llm/client.py` 의 `MockClassifier` 와 같은
키워드 목록을 그대로 옮겼다 (실제로 API 키가 없을 때 프로덕션이 쓰는
폴백 로직이다 — "이미 쓰는 것"에 해당). 비용 0, 로컬, 외부 전송 없음.
성능 하한선 참고용으로 넣는다.

출처: C:\\Project\\han-river-view-or-dive\\src\\hanriver\\llm\\client.py
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
