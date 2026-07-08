from __future__ import annotations

import re
from collections import Counter

# Terms likely to appear in HK meeting materials / ASR confusion pairs.
_MAX_TERMS = 50
_TC_TOKEN = re.compile(r"[\u4e00-\u9fff]{2,8}")
_EN_TOKEN = re.compile(r"\b[A-Z][A-Za-z0-9]{1,15}\b")
_NUM_TOKEN = re.compile(r"\d+(?:\.\d+)?%?")

_STOP_TC = {
    "我哋",
    "佢哋",
    "係咪",
    "可以",
    "應該",
    "因為",
    "所以",
    "其實",
    "然後",
    "今日",
    "明日",
    "會議",
    "報告",
    "問題",
    "方面",
    "情況",
    "公司",
    "部門",
    "項目",
    "時間",
    "數據",
    "資料",
    "內容",
    "部分",
    "第一",
    "第二",
    "第三",
    "最後",
    "總結",
    "討論",
    "分享",
    "講返",
    "講下",
    "好似",
    "覺得",
    "認為",
    "希望",
    "需要",
    "已經",
    "仍然",
    "或者",
    "如果",
    "不過",
    "另外",
    "關於",
    "根據",
    "進行",
    "完成",
    "開始",
    "結束",
}


def extract_glossary_terms(texts: list[str], limit: int = _MAX_TERMS) -> list[str]:
    """Pull domain terms from uploaded PDF text for ASR keyword boosting."""
    counter: Counter[str] = Counter()
    for text in texts:
        for match in _TC_TOKEN.findall(text):
            if match not in _STOP_TC and len(match) >= 2:
                counter[match] += 1
        for match in _EN_TOKEN.findall(text):
            counter[match] += 2
        for match in _NUM_TOKEN.findall(text):
            counter[match] += 1

    ranked = [term for term, _ in counter.most_common(limit * 2)]
    # Prefer longer TC phrases and mixed tokens; dedupe case-insensitively for EN.
    seen: set[str] = set()
    result: list[str] = []
    for term in sorted(ranked, key=lambda t: (-len(t), -counter[t])):
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(term)
        if len(result) >= limit:
            break
    return result


def merge_glossary(existing: list[str], new_terms: list[str], limit: int = _MAX_TERMS) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for term in [*existing, *new_terms]:
        key = term.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(term.strip())
        if len(merged) >= limit:
            break
    return merged
