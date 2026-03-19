# ==========================================================
# external_gateway.py — 외부 격리 게이트웨이
# ==========================================================
# [설계 원칙]
#   - 이 파일만이 외부 세계(API, 환경변수, 파일I/O)와 접촉한다
#   - app.py는 이 모듈의 함수만 호출하며 외부와 직접 접촉하지 않는다
#   - 모든 입출력은 이 파일에서 surrogate 정제 후 내부로 전달된다
#   - 외부 오류는 이 파일 안에서 흡수하고 안전한 기본값을 반환한다
# ==========================================================

import os
import json
import unicodedata

# ── 내부 정제 함수 (app.py 의존 없이 독립 동작) ──────────────────────
def _clean(text) -> str:
    """surrogate 문자 완전 제거 — 외부 데이터가 내부로 들어오는 유일한 관문"""
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""
    try:
        import ftfy as _ftfy
        text = _ftfy.fix_text(text, normalization="NFC")
    except Exception:
        pass
    try:
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Cs")
    except Exception:
        pass
    try:
        text = text.encode("utf-8", errors="ignore").decode("utf-8")
    except Exception:
        pass
    return text


# ==========================================================
# [GATE 1] 환경변수 / Secrets 읽기
# ==========================================================
def get_secret(key: str, default: str = "") -> str:
    """secrets.toml → 환경변수 순으로 읽고, 결과를 정제하여 반환"""
    value = default
    # 1순위: Streamlit secrets
    try:
        import streamlit as st
        value = st.secrets.get(key, default) or default
    except Exception:
        pass
    # 2순위: 환경변수
    if not value or value == default:
        value = os.environ.get(key, default)
    # 외부에서 온 값 → 반드시 정제 후 반환
    return _clean(str(value))


# ==========================================================
# [GATE 2] Gemini API 호출
# ==========================================================
def call_gemini(client, model_name: str, prompt: str, config) -> str:
    """
    Gemini API 호출 격리 게이트.
    - 입력 prompt를 정제 후 전송
    - 응답을 정제 후 반환
    - 모든 예외를 흡수하고 안전한 오류 메시지 반환
    """
    # 입력 정제 — surrogate가 있으면 protobuf 직렬화 단계에서 터짐
    safe_prompt = _clean(prompt)
    try:
        resp = client.models.generate_content(
            model=model_name,
            contents=safe_prompt,
            config=config
        )
        raw = resp.text if resp and resp.text else ""
        # 응답 정제 — AI가 surrogate를 포함한 텍스트를 반환할 수 있음
        return _clean(raw)
    except UnicodeEncodeError as e:
        _pos = getattr(e, 'start', '?')
        return f"[인코딩 오류] AI 응답에 처리 불가 문자가 포함되었습니다. (위치: {_pos})"
    except Exception as e:
        err = _clean(str(e))
        if "quota" in err.lower() or "rate" in err.lower():
            return "[API 한도 초과] 잠시 후 다시 시도해주세요."
        if "api_key" in err.lower() or "auth" in err.lower():
            return "[인증 오류] API 키를 확인해주세요."
        return f"[AI 오류] {err[:200]}"


# ==========================================================
# [GATE 3] 파일 I/O
# ==========================================================
def read_json_file(path: str, default=None):
    """JSON 파일 읽기 — 오류 시 default 반환, 내용 정제 후 반환"""
    if default is None:
        default = []
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        # 파일 내용 정제
        safe_raw = _clean(raw)
        return json.loads(safe_raw)
    except Exception:
        return default


def write_json_file(path: str, data, ensure_ascii: bool = False) -> bool:
    """JSON 파일 쓰기 — 오류 시 False 반환"""
    try:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii)
        return True
    except Exception:
        return False


def read_text_file(path: str, default: str = "") -> str:
    """텍스트 파일 읽기 — 내용 정제 후 반환"""
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return _clean(f.read())
    except Exception:
        return default


# ==========================================================
# [GATE 4] 사용자 입력 정제
# ==========================================================
def sanitize_input(text) -> str:
    """사용자 입력(텍스트박스, 파일명 등) → 내부 진입 전 정제"""
    return _clean(text)


def sanitize_pdf_text(raw_text: str) -> str:
    """PDF/DOCX 추출 텍스트 → 내부 진입 전 정제 (surrogate 다수 발생 지점)"""
    return _clean(raw_text)


# ==========================================================
# [GATE 5] 외부 상태 진단
# ==========================================================
def check_gateway_health() -> dict:
    """게이트웨이 자가 진단 — 관리자 탭에서 호출 가능"""
    result = {
        "gemini_api_key": "설정됨" if get_secret("GEMINI_API_KEY") else "미설정",
        "admin_key":      "설정됨" if get_secret("ADMIN_KEY") else "기본값 사용",
        "ftfy_available": False,
        "locale":         os.environ.get("LANG", "미설정"),
    }
    try:
        import ftfy  # noqa
        result["ftfy_available"] = True
    except ImportError:
        pass
    return result
