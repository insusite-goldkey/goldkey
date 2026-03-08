# modules/gp96_auto_learn.py
# ══════════════════════════════════════════════════════════════════════════════
# [GP-96 지능형 자산화 — 자율 학습 엔진]
# 가이딩 프로토콜 제96조: 3대 트리거 × 4대 커리큘럼 × 4단계 파이프라인
#
# 3대 트리거 조건 (Trigger Conditions):
#   T1. 신규 리플렛·약관 업로드 시 (OCR 기반)
#   T2. 의무기록·진단서 스캔 시 (실무 기반 — KCD 코드 + 처치명)
#   T3. 상담 중 미정의 용어 발생 시 (RAG 기반)
#
# 4대 커리큘럼 (Curriculum):
#   C1. 첨단 의료 및 고가 치료제 (Medical Tech)
#   C2. 인수 심사 및 상품 구조 (Underwriting)
#   C3. 보상 및 법률 쟁점 (Claim & Law)
#   C4. 표준 질병 분류 및 신체 부위 (KCD & Anatomy)
#
# 4단계 파이프라인 (Pipeline):
#   P1. 추출 (Extraction)    — 비정형 텍스트에서 용어 + 정의 분리
#   P2. 검증 (Validation)    — 최신 약관·법령 팩트 체크
#   P3. 1인칭 변환 (Tone-up) — "내가~" 화법으로 재작성 (제80조)
#   P4. 연동 (Mapping)       — 섹션(A~F) + 액션 버튼 자동 배치
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
import json
import datetime
from typing import Optional

# ── GP-96 커리큘럼 시그니처 (키워드 → 카테고리 매핑) ──────────────────────────
GP96_CURRICULUM: dict[str, dict] = {
    "C1": {
        "name": "첨단 의료 및 고가 치료제",
        "label": "Medical Tech",
        "color": "#ef4444",
        "icon": "🧬",
        "keywords": [
            "ADC", "엔허투", "CAR-T", "중입자", "표적항암", "면역항암", "NGS", "유전체",
            "양성자", "로봇수술", "다빈치", "이뮨세포", "세포치료", "유전자치료",
            "펨브롤리주맙", "키트루다", "면역관문", "PD-L1", "HER2", "BRCA",
        ],
        "section": "A",
        "action_buttons": ["암 질환 상담", "보험금 청구 상담"],
    },
    "C2": {
        "name": "인수 심사 및 상품 구조",
        "label": "Underwriting",
        "color": "#f97316",
        "icon": "📋",
        "keywords": [
            "3N5", "유병자", "계약전환", "납입면제", "체증형", "무해지", "환급형",
            "고지의무", "할증", "부담보", "인수거절", "역선택", "표준체", "우량체",
            "갱신형", "비갱신형", "순수보장형", "저해지",
        ],
        "section": "B",
        "action_buttons": ["신규보험 상담", "통합보험 설계"],
    },
    "C3": {
        "name": "보상 및 법률 쟁점",
        "label": "Claim & Law",
        "color": "#6366f1",
        "icon": "⚖️",
        "keywords": [
            "18개월", "유예기간", "면책기간", "기왕증", "지정대리청구", "부지급",
            "소멸시효", "분쟁조정", "판례", "약관해석", "통지의무", "고지위반",
            "청구거절", "손해사정", "보험금청구권", "금감원",
        ],
        "section": "C",
        "action_buttons": ["보험금 청구 상담", "나의 인생 방어 사령부"],
    },
    "C4": {
        "name": "표준 질병 분류 및 신체 부위",
        "label": "KCD & Anatomy",
        "color": "#0ea5e9",
        "icon": "🏥",
        "keywords": [
            "KCD", "상병코드", "C코드", "D코드", "I코드", "S코드", "M코드",
            "악성신생물", "경계성종양", "제자리암", "뇌혈관", "심근경색", "골절",
            "척추", "관절", "신경", "TNM", "병기",
        ],
        "section": "D",
        "action_buttons": ["KCD 상해 분석", "암 질환 상담"],
    },
}

# ── GP-96 섹션 → 탭 키 매핑 ────────────────────────────────────────────────
GP96_SECTION_TAB: dict[str, str] = {
    "A": "cancer",
    "B": "t0",
    "C": "claim_scanner",
    "D": "kcd_injury",
    "E": "ins_bot",
    "F": "know_pipe",
}

# ── 미정의 용어 판정용 최소 길이 ──────────────────────────────────────────────
_MIN_UNKNOWN_LEN = 2

# ── 커리큘럼 자동 분류 함수 ────────────────────────────────────────────────────

def detect_curriculum(text: str) -> list[str]:
    """
    텍스트에서 커리큘럼 카테고리 코드(C1~C4) 목록을 반환.
    매칭된 커리큘럼이 없으면 빈 리스트.
    """
    t = text.upper()
    matched = []
    for code, meta in GP96_CURRICULUM.items():
        for kw in meta["keywords"]:
            if kw.upper() in t:
                if code not in matched:
                    matched.append(code)
                break
    return matched


# ══════════════════════════════════════════════════════════════════════════════
# P1. 추출 (Extraction) — 비정형 텍스트에서 신규 용어 후보 분리
# ══════════════════════════════════════════════════════════════════════════════

# 특약명 추출 정규식 패턴 (리플렛·약관 공통)
_SPECIAL_CLAUSE_PATTERN = re.compile(
    r"([가-힣a-zA-Z0-9\s()·,\.]{3,30}(?:특약|담보|보장|급여|비용|치료비|수술비|일당|진단비|특별약관))",
    re.MULTILINE,
)
# KCD 코드 패턴
_KCD_PATTERN = re.compile(r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b")
# 의학적 처치명 패턴 (처치, 수술, 시술, 치료 등이 포함된 명사구)
_PROCEDURE_PATTERN = re.compile(
    r"([가-힣a-zA-Z0-9\s()·]{3,25}(?:수술|시술|치료|요법|검사|절제|이식|삽입|결찰))",
    re.MULTILINE,
)


def extract_candidates_from_leaflet(text: str) -> list[dict]:
    """
    T1 트리거: 리플렛·약관 텍스트에서 신규 특약명 후보 추출.
    반환: [{"raw": str, "trigger": "T1", "curriculum": [C코드]}]
    """
    candidates = []
    seen = set()
    for m in _SPECIAL_CLAUSE_PATTERN.finditer(text):
        raw = m.group(1).strip()
        if len(raw) >= 4 and raw not in seen:
            seen.add(raw)
            candidates.append({
                "raw": raw,
                "trigger": "T1",
                "curriculum": detect_curriculum(raw),
            })
    return candidates


def extract_candidates_from_medical(text: str) -> list[dict]:
    """
    T2 트리거: 의무기록·진단서 텍스트에서 KCD 코드 + 처치명 추출.
    반환: [{"raw": str, "kcd": str, "trigger": "T2", "curriculum": [C코드]}]
    """
    candidates = []
    seen = set()

    kcd_matches = _KCD_PATTERN.findall(text)
    for kcd in kcd_matches:
        if kcd not in seen:
            seen.add(kcd)
            candidates.append({
                "raw": kcd,
                "kcd": kcd,
                "trigger": "T2",
                "curriculum": ["C4"],
            })

    for m in _PROCEDURE_PATTERN.finditer(text):
        raw = m.group(1).strip()
        if len(raw) >= 4 and raw not in seen:
            seen.add(raw)
            candidates.append({
                "raw": raw,
                "kcd": "",
                "trigger": "T2",
                "curriculum": detect_curriculum(raw) or ["C4"],
            })
    return candidates


def detect_undefined_terms(query: str, dict_keys: list[str]) -> list[str]:
    """
    T3 트리거: 쿼리에서 기존 사전에 없는 잠재적 핵심 용어 반환.
    - 2음절 이상 한글/영문 단어가 사전에 없을 때 후보로 등록.
    """
    tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", query)
    lower_keys = {k.lower() for k in dict_keys}
    unknown = []
    for tok in tokens:
        if len(tok) >= _MIN_UNKNOWN_LEN and tok.lower() not in lower_keys:
            unknown.append(tok)
    return list(dict.fromkeys(unknown))


# ══════════════════════════════════════════════════════════════════════════════
# P2. 검증 (Validation) — 팩트 체크 프롬프트 생성
# ══════════════════════════════════════════════════════════════════════════════

_VALIDATION_SOURCES = [
    "금융감독원 분쟁조정 사례집",
    "대법원 보험 관련 판례",
    "보건복지부 한국 표준 질병 사인 분류(KCD)",
    "생명보험협회·손해보험협회 표준약관",
    "국민건강보험 급여기준",
]


def build_validation_prompt(raw_term: str, raw_definition: str = "") -> str:
    """P2: 검증용 AI 프롬프트 생성."""
    src_list = "\n".join(f"  - {s}" for s in _VALIDATION_SOURCES)
    return f"""당신은 보험 전문 AI입니다. 아래 용어에 대해 팩트 체크를 수행하십시오.

[검증 대상 용어]
용어: {raw_term}
{"초안 정의: " + raw_definition if raw_definition else ""}

[검증 기준 출처 (가이딩 프로토콜 제22·26조)]
{src_list}

[요청 사항]
1. 위 출처 기준으로 용어의 정의가 정확한지 확인하십시오.
2. 관련 KCD 코드가 있다면 병기하십시오.
3. 관련 판례·분쟁조정 사례 번호가 있다면 1~2건 제시하십시오.
4. 검증 결과를 아래 JSON 형식으로만 출력하십시오 (다른 텍스트 없음):

{{
  "term": "정확한 용어명",
  "definition": "검증된 정의 (2~4문장)",
  "kcd": ["관련 KCD 코드1", "관련 KCD 코드2"],
  "precedent": ["판례·분쟁 사례1", "판례·분쟁 사례2"],
  "validation_ok": true,
  "validation_note": "검증 메모 (이상 없음 또는 보류 사유)"
}}"""


def parse_validation_response(raw_json: str) -> Optional[dict]:
    """P2: AI JSON 응답 파싱. 실패 시 None 반환."""
    try:
        m = re.search(r"\{[\s\S]+\}", raw_json)
        if m:
            return json.loads(m.group(0))
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# P3. 1인칭 변환 (Tone-up) — 제80조 "내가~" 화법 재작성
# ══════════════════════════════════════════════════════════════════════════════

_TONEUP_TEMPLATES: dict[str, str] = {
    "C1": (
        "내가 이 최신 치료 기술을 제안하는 이유는, "
        "단 한 번의 치료에 수천만 원이 드는 현실에서 "
        "고객님의 재산을 지키는 유일한 방어선이 되기 때문입니다."
    ),
    "C2": (
        "내가 이 담보 구조를 설계에 반영하는 이유는, "
        "가입 조건이 까다로울수록 미리 준비해야 할 이유가 분명해지기 때문입니다. "
        "지금 이 순간이 가장 유리한 인수 조건입니다."
    ),
    "C3": (
        "내가 이 법적 쟁점을 먼저 설명드리는 이유는, "
        "모르고 지나치면 정당한 보험금을 받지 못하는 사례가 실제로 있기 때문입니다."
    ),
    "C4": (
        "내가 이 질병 코드를 파악하는 이유는, "
        "같은 병명이라도 코드에 따라 지급 여부가 달라지기 때문입니다. "
        "정확한 코드 확인이 보험금의 차이를 만듭니다."
    ),
}
_TONEUP_DEFAULT = (
    "내가 이 담보를 제안하는 이유는, "
    "고객님의 상황에서 가장 취약한 보장 공백을 메우는 핵심 항목이기 때문입니다."
)


def build_toneup_prompt(term: str, definition: str, curriculum_codes: list[str]) -> str:
    """P3: 1인칭 변환 AI 프롬프트 생성."""
    _code = curriculum_codes[0] if curriculum_codes else ""
    _template = _TONEUP_TEMPLATES.get(_code, _TONEUP_DEFAULT)
    return f"""당신은 보험 설계사 AI입니다. 아래 용어를 1인칭 상담 화법으로 변환하십시오.

[가이딩 프로토콜 제80조 — 1인칭 화법 규칙]
- 반드시 "내가~"로 시작하십시오.
- 고객의 감정(불안, 기대, 안도)을 자극하는 언어를 사용하십시오.
- 2~3문장으로 작성하십시오.
- 아래 화법 패턴을 참고하십시오: "{_template}"

[용어] {term}
[정의] {definition}

결과 화법만 출력하십시오 (다른 텍스트 없음):"""


# ══════════════════════════════════════════════════════════════════════════════
# P4. 연동 (Mapping) — 섹션(A~F) + 액션 버튼 자동 결정
# ══════════════════════════════════════════════════════════════════════════════

def map_to_section(curriculum_codes: list[str]) -> dict:
    """
    P4: 커리큘럼 코드 → 섹션 + 탭 키 + 액션 버튼 매핑.
    반환: {"section": "A", "tab_key": "cancer", "action_buttons": [...]}
    """
    if not curriculum_codes:
        return {
            "section": "E",
            "tab_key": GP96_SECTION_TAB["E"],
            "action_buttons": ["보험봇 전문용어 검색"],
        }
    code = curriculum_codes[0]
    meta = GP96_CURRICULUM.get(code, {})
    section = meta.get("section", "E")
    return {
        "section": section,
        "tab_key": GP96_SECTION_TAB.get(section, "ins_bot"),
        "action_buttons": meta.get("action_buttons", []),
        "curriculum_name": meta.get("name", ""),
        "curriculum_label": meta.get("label", ""),
        "curriculum_icon": meta.get("icon", "📚"),
        "curriculum_color": meta.get("color", "#475569"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 통합 파이프라인 실행 함수
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline_sync(
    raw_term: str,
    raw_definition: str = "",
    curriculum_codes: list[str] | None = None,
    trigger: str = "T3",
    ai_call_fn=None,
) -> dict:
    """
    GP-96 4단계 파이프라인 동기 실행.

    Args:
        raw_term: 추출된 원시 용어
        raw_definition: 초안 정의 (없으면 빈 문자열)
        curriculum_codes: 커리큘럼 코드 목록 (없으면 자동 감지)
        trigger: 트리거 코드 ("T1"|"T2"|"T3")
        ai_call_fn: AI 호출 함수 (prompt: str) -> str. None이면 AI 스킵.

    Returns:
        완성된 pending entry dict:
        {
            "key": str,
            "entry": {term, category, definition, kcd, precedent, voice, tags},
            "trigger": str,
            "curriculum": [C코드],
            "mapping": {section, tab_key, action_buttons, ...},
            "pipeline_log": [...],
            "created_at": ISO timestamp,
            "status": "pending",
        }
    """
    log = []

    # ── P1: 추출 완료 (raw_term이 이미 추출된 상태로 전달됨) ─────────────────
    log.append({"step": "P1", "status": "ok", "note": f"추출된 용어: {raw_term}"})

    # 커리큘럼 자동 감지 (미제공 시)
    if not curriculum_codes:
        curriculum_codes = detect_curriculum(raw_term + " " + raw_definition)
    if not curriculum_codes:
        curriculum_codes = ["C3"]  # 기본값: 보상·법률 쟁점

    # ── P2: 검증 (AI 호출) ───────────────────────────────────────────────────
    validated = {
        "term": raw_term,
        "definition": raw_definition or f"{raw_term}에 대한 정의가 검증 중입니다.",
        "kcd": [],
        "precedent": [],
        "validation_ok": False,
        "validation_note": "AI 미호출 — 수동 검증 필요",
    }
    if ai_call_fn:
        try:
            val_prompt = build_validation_prompt(raw_term, raw_definition)
            val_raw = ai_call_fn(val_prompt)
            parsed = parse_validation_response(val_raw)
            if parsed:
                validated.update(parsed)
                log.append({"step": "P2", "status": "ok",
                             "note": f"검증 완료: {parsed.get('validation_note', '')}"})
            else:
                log.append({"step": "P2", "status": "warn",
                             "note": "AI 응답 JSON 파싱 실패 — 원시 텍스트 보존"})
        except Exception as e:
            log.append({"step": "P2", "status": "error", "note": str(e)})
    else:
        log.append({"step": "P2", "status": "skip", "note": "AI 미연결 — 수동 검증 필요"})

    # ── P3: 1인칭 변환 ───────────────────────────────────────────────────────
    voice = ""
    if ai_call_fn:
        try:
            toneup_prompt = build_toneup_prompt(
                validated["term"], validated["definition"], curriculum_codes
            )
            voice = ai_call_fn(toneup_prompt).strip()
            log.append({"step": "P3", "status": "ok", "note": "1인칭 화법 변환 완료"})
        except Exception as e:
            log.append({"step": "P3", "status": "error", "note": str(e)})
    if not voice:
        _code = curriculum_codes[0] if curriculum_codes else ""
        voice = _TONEUP_TEMPLATES.get(_code, _TONEUP_DEFAULT)
        if not ai_call_fn:
            log.append({"step": "P3", "status": "skip", "note": "AI 미연결 — 템플릿 화법 적용"})

    # ── P4: 연동 ─────────────────────────────────────────────────────────────
    mapping = map_to_section(curriculum_codes)
    log.append({
        "step": "P4",
        "status": "ok",
        "note": f"섹션 {mapping['section']} → 탭: {mapping['tab_key']}",
    })

    # ── 카테고리 결정 ─────────────────────────────────────────────────────────
    _code = curriculum_codes[0] if curriculum_codes else "C3"
    _cat_map = {"C1": "암", "C2": "설계전략", "C3": "약관", "C4": "KCD"}
    category = _cat_map.get(_code, "약관")

    # ── 태그 자동 생성 ────────────────────────────────────────────────────────
    tags = [raw_term] + curriculum_codes + [trigger]
    kcd_in_tags = [k for k in validated.get("kcd", []) if k]
    tags.extend(kcd_in_tags[:2])

    return {
        "key": re.sub(r"\s+", "", raw_term)[:20],
        "entry": {
            "term": validated["term"],
            "category": category,
            "definition": validated["definition"],
            "kcd": validated.get("kcd", []),
            "precedent": validated.get("precedent", []),
            "voice": voice,
            "tags": list(dict.fromkeys(tags)),
            "gp96_trigger": trigger,
            "gp96_curriculum": curriculum_codes,
            "gp96_validation_ok": validated.get("validation_ok", False),
        },
        "trigger": trigger,
        "curriculum": curriculum_codes,
        "mapping": mapping,
        "pipeline_log": log,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "status": "pending",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 세션 큐 헬퍼 (Streamlit session_state 연동)
# ══════════════════════════════════════════════════════════════════════════════

def queue_pending_term(pending_entry: dict, session_state) -> None:
    """GP-96 결과를 session_state 승인 큐에 추가 (중복 방지)."""
    queue: list = session_state.get("dict_pending_queue", [])
    existing_keys = {item.get("key", "") for item in queue}
    if pending_entry["key"] not in existing_keys:
        queue.append(pending_entry)
        session_state["dict_pending_queue"] = queue


def get_pending_queue(session_state) -> list:
    """승인 대기 큐 반환."""
    return session_state.get("dict_pending_queue", [])


def approve_pending_term(key: str, session_state, insurance_dict: dict) -> bool:
    """
    승인 처리: 큐에서 key 해당 항목을 insurance_dict에 등록.
    반환: 성공 여부
    """
    queue: list = session_state.get("dict_pending_queue", [])
    for i, item in enumerate(queue):
        if item.get("key") == key:
            insurance_dict[key] = item["entry"]
            queue.pop(i)
            session_state["dict_pending_queue"] = queue
            return True
    return False


def reject_pending_term(key: str, session_state) -> bool:
    """큐에서 key 해당 항목 거절 삭제."""
    queue: list = session_state.get("dict_pending_queue", [])
    for i, item in enumerate(queue):
        if item.get("key") == key:
            queue.pop(i)
            session_state["dict_pending_queue"] = queue
            return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# T3 트리거: 상담 쿼리 자동 감지 헬퍼
# ══════════════════════════════════════════════════════════════════════════════

def check_t3_trigger(query: str, dict_keys: list[str]) -> list[dict]:
    """
    T3 트리거 실행: 쿼리에서 미정의 용어를 감지하고
    각 미정의 용어에 대한 기초 pending 후보 리스트 반환.
    반환: [{"raw": str, "trigger": "T3", "curriculum": [C코드]}]
    """
    undefined = detect_undefined_terms(query, dict_keys)
    candidates = []
    for tok in undefined:
        curr = detect_curriculum(tok)
        if curr:
            candidates.append({
                "raw": tok,
                "trigger": "T3",
                "curriculum": curr,
            })
    return candidates
