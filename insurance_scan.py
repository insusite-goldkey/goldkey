# ==========================================================================
# insurance_scan.py
# [보험증권 스캔 → 상품 구조화 추출] 모듈
#
# 역할: 보험증권 OCR/Vision 텍스트에서 보험사명·상품명·가입일을 구조화하여
#       disclosure_crawler의 JIT 약관 크롤링 입력값으로 변환.
#
# 사용처: scan_hub 탭 → 보험증권 스캔 완료 후 약관 크롤링 자동 연동
# ==========================================================================

import re
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# 1. 보험사명 정규화 테이블
# ---------------------------------------------------------------------------
_COMPANY_ALIASES: list[tuple[list[str], str]] = [
    (["삼성화재", "삼성 화재"],                     "삼성화재"),
    (["현대해상", "현대 해상"],                     "현대해상"),
    (["DB손해", "DB손보", "동부화재", "동부 화재"],  "DB손해보험"),
    (["KB손해", "KB손보", "LIG"],                    "KB손해보험"),
    (["메리츠화재", "메리츠 화재"],                 "메리츠화재"),
    (["롯데손해", "롯데손보"],                       "롯데손해보험"),
    (["한화손해", "한화손보"],                       "한화손해보험"),
    (["흥국화재", "흥국 화재"],                     "흥국화재"),
    (["MG손해", "새마을손보"],                      "MG손해보험"),
    (["삼성생명", "삼성 생명"],                     "삼성생명"),
    (["한화생명", "한화 생명"],                     "한화생명"),
    (["교보생명", "교보 생명"],                     "교보생명"),
    (["신한라이프", "신한 라이프", "오렌지라이프"], "신한라이프"),
    (["NH농협생명", "농협생명"],                    "NH농협생명"),
    (["미래에셋생명", "미래에셋 생명"],             "미래에셋생명"),
    (["DB생명", "DB 생명"],                         "DB생명"),
    (["KDB생명", "KDB 생명"],                       "KDB생명"),
    (["라이나생명", "라이나 생명", "LINA"],         "라이나생명"),
    (["KB라이프", "KB생명", "KB Life"],             "KB라이프생명"),
    (["MetLife", "메트라이프", "메트 라이프"],      "MetLife생명"),
    (["iM라이프", "iM생명", "IM라이프"],            "iM라이프생명"),
    (["푸본현대생명", "푸본 현대"],                 "푸본현대생명"),
    (["흥국생명", "흥국 생명"],                     "흥국생명"),
    (["동양생명", "동양 생명"],                     "동양생명"),
    (["ABL생명", "ABL 생명"],                       "ABL생명"),
    (["하나생명", "하나 생명"],                     "하나생명"),
    (["처브라이프", "라이나손보", "Chubb"],         "라이나손보(Chubb)"),
]


def normalize_company(raw: str) -> str:
    """원문 텍스트에서 표준 보험사명으로 정규화."""
    raw = raw.strip()
    for aliases, standard in _COMPANY_ALIASES:
        for alias in aliases:
            if alias in raw:
                return standard
    return raw  # 매칭 없으면 원문 반환


# ---------------------------------------------------------------------------
# 2. 날짜 파싱 헬퍼
# ---------------------------------------------------------------------------
_DATE_PATTERNS = [
    r"(\d{4})[.\-/년\s](\d{1,2})[.\-/월\s](\d{1,2})[일]?",  # 2023.01.15 / 2023년 1월 15일
    r"(\d{4})(\d{2})(\d{2})",                                   # 20230115
    r"(\d{2})[.\-/](\d{2})[.\-/](\d{2})",                      # 23.01.15 (YY.MM.DD)
]

def parse_date(raw: str) -> Optional[str]:
    """날짜 문자열을 YYYY-MM-DD로 정규화. 파싱 실패 시 None 반환."""
    for pat in _DATE_PATTERNS:
        m = re.search(pat, raw)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            # 2자리 연도 처리 (YY → YYYY)
            if len(y) == 2:
                y = ("20" + y) if int(y) <= 50 else ("19" + y)
            try:
                dt = datetime(int(y), int(mo), int(d))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# 3. 증권 텍스트에서 상품 정보 구조화 추출
# ---------------------------------------------------------------------------
_PRODUCT_NAME_PATTERNS = [
    r"(?:상품명|보험명|상품\s*:\s*|보험\s*:\s*)[\s:：]*([^\n\r,;]+)",
    r"(?:무배당|유배당|갱신형|비갱신형|저축성|보장성)[^\n\r,;]{2,40}(?:보험|보장|플랜|종신|정기)",
    r"[가-힣A-Za-z\s]{3,30}(?:보험|보장|플랜|종신|정기|암보험|실손|간병|치매)",
]

_JOIN_DATE_PATTERNS = [
    r"(?:가입일|계약일|보험개시일|효력발생일|개시일)[^\d]*(\d{4}[.\-/년\s]\d{1,2}[.\-/월\s]\d{1,2}[일]?)",
    r"(?:가입일자|계약일자)[^\d]*(\d{4}[.\-/년\s]\d{1,2}[.\-/월\s]\d{1,2}[일]?)",
    r"(?:가입일|계약일)[^\d]*(\d{8})",
]

_COMPANY_PATTERNS = [
    r"(?:보험사|회사명|보험회사)[^\n\r:：]*[:\s：]+([가-힣A-Za-z\s]+(?:화재|해상|손보|손해보험|생명|라이프|보험))",
    r"^([가-힣A-Za-z\s]{2,15}(?:화재|해상|손보|손해보험|생명|라이프))",
]


def extract_policy_info(text: str) -> dict:
    """
    보험증권 OCR 텍스트에서 보험사·상품명·가입일 추출.

    반환:
        {
            "company":    "삼성화재",           # 정규화된 보험사명
            "product":    "삼성화재 암보험 3.0", # 상품명
            "join_date":  "2019-03-15",          # YYYY-MM-DD
            "confidence": 85,                    # 추출 신뢰도 (0~100)
            "raw_matches": {...}                 # 원문 매칭 내용
        }
    """
    result = {
        "company": "",
        "product": "",
        "join_date": "",
        "confidence": 0,
        "raw_matches": {},
    }
    score = 0

    # ── 보험사 추출 ──────────────────────────────────────────────────
    company_raw = ""
    for pat in _COMPANY_PATTERNS:
        m = re.search(pat, text[:1000], re.MULTILINE)
        if m:
            company_raw = m.group(1).strip()
            break
    # 전체 텍스트에서 알리아스 매칭 (패턴 미탐지 시 백업)
    if not company_raw:
        for aliases, standard in _COMPANY_ALIASES:
            for alias in aliases:
                if alias in text[:2000]:
                    company_raw = alias
                    break
            if company_raw:
                break

    if company_raw:
        result["company"] = normalize_company(company_raw)
        result["raw_matches"]["company_raw"] = company_raw
        score += 35

    # ── 상품명 추출 ──────────────────────────────────────────────────
    product_raw = ""
    for pat in _PRODUCT_NAME_PATTERNS:
        m = re.search(pat, text[:3000])
        if m:
            product_raw = m.group(0 if m.lastindex is None else 1).strip()
            product_raw = product_raw[:60]  # 최대 60자
            break

    if product_raw:
        result["product"] = product_raw
        result["raw_matches"]["product_raw"] = product_raw
        score += 35

    # ── 가입일 추출 ──────────────────────────────────────────────────
    join_date_raw = ""
    for pat in _JOIN_DATE_PATTERNS:
        m = re.search(pat, text[:3000])
        if m:
            join_date_raw = m.group(1)
            parsed = parse_date(join_date_raw)
            if parsed:
                result["join_date"] = parsed
                result["raw_matches"]["join_date_raw"] = join_date_raw
                score += 30
                break

    result["confidence"] = min(score, 100)
    return result


# ---------------------------------------------------------------------------
# 4. 복수 증권 텍스트 일괄 처리
# ---------------------------------------------------------------------------
def extract_policies_from_scan(ssot_scan_data: list) -> list:
    """
    scan_hub의 ssot_scan_data 리스트에서 보험증권(type=policy) 항목만 처리.

    반환: [
        {
            "source_file": "hong_samsung.pdf",
            "company":     "삼성화재",
            "product":     "무배당 삼성화재 암보험",
            "join_date":   "2019-03-15",
            "confidence":  85,
            "already_indexed": False,  # disclosure_crawler 캐시 여부 (호출 전 False)
        },
        ...
    ]
    """
    results = []
    for item in ssot_scan_data:
        if item.get("type") != "policy":
            continue
        text = item.get("text", "")
        if not text.strip():
            continue
        info = extract_policy_info(text)
        results.append({
            "source_file":      item.get("file", ""),
            "company":          info["company"],
            "product":          info["product"],
            "join_date":        info["join_date"],
            "confidence":       info["confidence"],
            "already_indexed":  False,
        })
    return results


# ---------------------------------------------------------------------------
# 5. Gemini 보조 추출 (신뢰도 낮을 때 LLM으로 재시도)
# ---------------------------------------------------------------------------
_EXTRACT_PROMPT = """아래 보험증권 텍스트에서 다음 3가지 정보를 JSON으로 추출하세요.

[추출 항목]
1. company: 보험사명 (예: 삼성화재, 현대해상, 교보생명)
2. product: 상품명 전체 (예: 무배당 삼성화재 New암보험 3.0)
3. join_date: 가입일 또는 계약일 (YYYY-MM-DD 형식)

[출력 형식]
```json
{"company": "...", "product": "...", "join_date": "YYYY-MM-DD"}
```

찾을 수 없는 항목은 빈 문자열("")로 처리하세요.

[증권 텍스트]
{text}
"""

def extract_with_llm(text: str, gemini_client, model_name: str) -> dict:
    """
    규칙 기반 추출 신뢰도가 낮을 때 Gemini LLM으로 보조 추출.
    신뢰도 50 미만인 경우 호출 권장.
    """
    import json, re as _re
    try:
        prompt = _EXTRACT_PROMPT.format(text=text[:3000])
        resp = gemini_client.models.generate_content(
            model=model_name,
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        raw = (resp.text or "").strip()
        raw = _re.sub(r"^```(?:json)?", "", raw).strip()
        raw = _re.sub(r"```$", "", raw).strip()
        parsed = json.loads(raw)
        return {
            "company":   normalize_company(parsed.get("company", "")),
            "product":   parsed.get("product", "")[:60],
            "join_date": parsed.get("join_date", ""),
            "confidence": 90,  # LLM 추출은 높은 신뢰도
            "raw_matches": {"llm_result": parsed},
        }
    except Exception:
        return {"company": "", "product": "", "join_date": "", "confidence": 0, "raw_matches": {}}
