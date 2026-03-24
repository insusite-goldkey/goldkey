"""
voice_engine.py — 아나운서급 심리 맞춤형 보이스 엔진
+ SSML 수치 강조 정밀 제어 (설득의 기술)
[GP-VOICE] Goldkey AI Masters 2026

Architecture:
  [1] 텍스트 전처리  — SSML 강조 패턴 마킹 (수치·핵심 용어 자동 감지)
  [2] SSML 청크 빌더 — Logical/Emotional 성향별 프로소디 동적 변환
  [3] 다국어 감지    — 언어 자동 판별 → 해당 보이스 자동 전환
  [4] 보이스 플레이어 — JavaScript SpeechSynthesis 기반 브라우저 TTS
  [5] 모닝 브리핑   — 앱 기동 시 음성 오프닝 자동 트리거
  [6] STT 보이스 검색 — Web Speech API 기반 음성 인식 + 의도 파서
"""
from __future__ import annotations
import re, json, datetime, html as _html, os, random
import streamlit as st
import streamlit.components.v1 as _cv1

# ══════════════════════════════════════════════════════════════════════════════
# [GP-VOICE-2026] Zephyr 아나운서 톤 표준 산식
# 전역 TTS 기준 — 이 상수를 기준으로 모든 음성 수정 진행 (임의 변경 금지)
# Voice  : Zephyr (Gemini TTS 공식 보이스명 — ko-KR 아나운서 톤)
# Rate   : 1.1x (명징한 아나운서 속도)
# Pitch  : high (약간 높은 피치 — 전달력 극대화)
# Break  : 0.3s (SSML 문장 간 호흡)
# Model  : gemini-2.0-flash-preview-tts (Gemini 2.0 Flash TTS 전용 모델)
# ══════════════════════════════════════════════════════════════════════════════
_ZEPHYR_VOICE  = "Zephyr"            # Gemini TTS 공식 보이스명
_ZEPHYR_MODEL  = "gemini-2.0-flash-exp"  # 검증된 TTS 지원 모델 (exp)
_ZEPHYR_MODEL2 = "gemini-2.0-flash"      # 2차 폴백
_ZEPHYR_MODEL3 = "gemini-2.0-flash-preview-tts"  # 3차 폴백 (전용 모델)
_ZEPHYR_RATE  = 1.1            # 아나운서 속도 (1.1x)
_ZEPHYR_PITCH = "high"         # 약간 높은 피치 — 명징한 전달
_ZEPHYR_LANG  = "ko-KR"        # 한국어 표준
_ZEPHYR_BREAK = "0.3s"         # 문장 간 호흡 (SSML)


def _build_zephyr_ssml(text: str) -> str:
    """[GP-VOICE-2026] 아나운서 SSML 빌더.
    <speak> 래핑 + 문장 사이 <break time="0.3s"/> 삽입.
    수치·핵심 용어는 <emphasis level="strong"> 자동 마킹.
    """
    clean = re.sub(r"#{1,6}\s*", "", text)
    clean = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", clean)
    clean = re.sub(r"`([^`]+)`", r"\1", clean)
    clean = re.sub(r">\s*", "", clean)
    sentences = re.split(r"(?<=[.!?。])\s+", clean.strip())
    parts = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # 수치/핵심 용어 emphasis 마킹
        s = re.sub(
            r"(\d[\d,]*\s*(억\s*원?|만\s*원?|원|%)|트리니티|보장\s*공백|가처분)",
            r'<emphasis level="strong">\1</emphasis>', s,
        )
        parts.append(f'{s}<break time="{_ZEPHYR_BREAK}"/>')
    inner = "".join(parts)
    return f'<speak><prosody rate="110%" pitch="high">{inner}</prosody></speak>'


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000) -> bytes:
    """Raw PCM(16-bit mono 24kHz) → WAV 헤더 래핑 (Gemini TTS 출력 포맷)."""
    import struct as _st, io as _bio
    channels, bit_depth = 1, 16
    byte_rate   = sample_rate * channels * (bit_depth // 8)
    block_align = channels * (bit_depth // 8)
    data_size   = len(pcm_data)
    buf = _bio.BytesIO()
    buf.write(b"RIFF")
    buf.write(_st.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(_st.pack("<I", 16))           # subchunk1 size
    buf.write(_st.pack("<H", 1))            # PCM format
    buf.write(_st.pack("<H", channels))
    buf.write(_st.pack("<I", sample_rate))
    buf.write(_st.pack("<I", byte_rate))
    buf.write(_st.pack("<H", block_align))
    buf.write(_st.pack("<H", bit_depth))
    buf.write(b"data")
    buf.write(_st.pack("<I", data_size))
    buf.write(pcm_data)
    return buf.getvalue()


def synthesize_zephyr(text: str, api_key: str) -> bytes | None:
    """[GP-VOICE-2026] Gemini TTS — Zephyr 아나운서 보이스 합성.
    성공 시 WAV 바이트. 실패 시 None + st.session_state["_zephyr_err"]= 오류 메시지.
    모델 시도 순서: gemini-2.0-flash-exp → gemini-2.0-flash → gemini-2.0-flash-preview-tts
    """
    if not api_key or api_key == "여기에_발급받은_API_키를_넣어주세요":
        return None

    import base64 as _b64s
    # plain text 사용 (SSML 거부 이슈 회피)
    _plain = re.sub(r"[#*`>]+", "", text).strip()
    _errs: list[str] = []

    def _try_model(model_name: str) -> bytes | None:
        try:
            from google import genai as _gnai
            from google.genai import types as _gt
            _c = _gnai.Client(api_key=api_key)
            _r = _c.models.generate_content(
                model=model_name,
                contents=_plain,
                config=_gt.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=_gt.SpeechConfig(
                        voice_config=_gt.VoiceConfig(
                            prebuilt_voice_config=_gt.PrebuiltVoiceConfig(
                                voice_name=_ZEPHYR_VOICE
                            )
                        )
                    ),
                ),
            )
            if _r.candidates:
                _raw = _r.candidates[0].content.parts[0].inline_data.data
                if isinstance(_raw, str):
                    _raw = _b64s.b64decode(_raw)
                return _pcm_to_wav(_raw)
            _errs.append(f"{model_name}: candidates 없음")
        except Exception as _e:
            _errs.append(f"{model_name}: {type(_e).__name__}({_e})")
        return None

    for _m in [_ZEPHYR_MODEL, _ZEPHYR_MODEL2, _ZEPHYR_MODEL3]:
        _result = _try_model(_m)
        if _result:
            try:
                import streamlit as _st_tts
                _st_tts.session_state["_zephyr_err"] = None
                _st_tts.session_state["_zephyr_model_ok"] = _m
            except Exception:
                pass
            return _result

    _err_msg = " | ".join(_errs)
    try:
        import streamlit as _st_tts
        _st_tts.session_state["_zephyr_err"] = _err_msg
    except Exception:
        pass
    return None


# ── [Fix] 직함 이중 출력 방지 헬퍼 ────────────────────────────────────────────────
def _clean_agent_name(name: str) -> str:
    """'설계사님', '설계사', '님' 등 직함 접미사 제거 → 순수 이름 반환 (이중 호칭 방지)."""
    for _sfx in ("설계사님", "설계사", "선생님", "선생", "님"):
        name = name.replace(_sfx, "")
    return name.strip()

# ── STT Custom Component 등록 ──────────────────────────────────────────────────
_STT_COMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_stt_component")
try:
    _stt_component = _cv1.declare_component("gk_voice_stt", path=_STT_COMP_DIR)
except Exception:
    _stt_component = None

# ══════════════════════════════════════════════════════════════════════════════
# [1] 상수 & 보이스 프로필
# ══════════════════════════════════════════════════════════════════════════════

# 성향별 보이스 프로필
_VOICE_PROFILES = {
    "Logical": {
        "pitch":    -1.0,    # 단호하고 지적인 앵커 톤 (SSML -1st)
        "rate":      0.80,   # 전역 기본 속도
        "volume":    1.0,
        "lang":     "ko-KR",
        "icon":     "⚖️",
        "label":    "논리형 — 지적 앵커 톤",
        "desc":     "데이터와 수치 중심. 단호하고 신뢰감 있는 앵커 보이스.",
    },
    "Emotional": {
        "pitch":    +1.0,    # 부드럽고 따뜻한 큐레이터 톤 (SSML +1st)
        "rate":      0.85,
        "volume":    1.0,
        "lang":     "ko-KR",
        "icon":     "❤️",
        "label":    "감성형 — 따뜻한 큐레이터 톤",
        "desc":     "가치와 안심 중심. 부드럽고 공감적인 큐레이터 보이스.",
    },
}

# 다국어 보이스 이름 매핑
_LANG_VOICE_MAP = {
    "ko": "ko-KR",
    "en": "en-US",
    "ja": "ja-JP",
    "zh": "zh-CN",
    "vi": "vi-VN",
}

# SSML 강조 패턴 — (정규식, 속도배수, 음량증가)
_EMPHASIS_RULES: list[tuple] = [
    (r"\d+\.?\d*%",                  0.60, 1.2),   # 퍼센트 수치 (7.19% 등)
    (r"\d+억\s*원?",                 0.60, 1.2),   # 억원
    (r"\d[\d,]*만\s*원?",            0.70, 1.1),   # 만원
    (r"\d[\d,]*\s*원",               0.75, 1.0),   # 원
    (r"가처분\s*소득",               0.70, 1.1),   # 핵심 용어
    (r"보장\s*공백",                 0.65, 1.2),   # 핵심 용어
    (r"필요\s*자금",                 0.70, 1.1),   # 핵심 용어
    (r"트리니티",                    0.75, 1.0),   # 브랜드 용어
    (r"명목\s*연봉",                 0.72, 1.0),   # 계산 용어
]

# ── [EQ v2] 요일별 감성 스크립트 풀 ────────────────────────────────────────────
_EQ_MORNING_GREETS: dict[int, list[str]] = {
    0: [  # 월요일
        "활기찬 월요일 아침입니다! 이번 주도 설계사님의 열정을 곁에서 응원할게요.",
        "새로운 한 주가 시작됐어요! 오늘 첫 단추를 잘 끼우면 일주일이 달라집니다.",
        "월요일 아침, 커피 한 잔과 함께 시작해 보세요! 오늘의 목표를 함께 이뤄봅시다.",
    ],
    1: [  # 화요일
        "화요일입니다! 어제의 시작이 오늘의 결실로 이어지는 날이에요.",
        "화요일 아침, 어제보다 한 발짝 더 나아가는 하루 만들어 보세요!",
        "월요일을 잘 넘기셨군요! 화요일은 탄력이 붙는 날이에요. 오늘도 파이팅입니다!",
    ],
    2: [  # 수요일
        "어느덧 수요일, 한 주의 반환점입니다! 지금까지 정말 잘해오셨어요.",
        "수요일 아침이에요! 이번 주 절반을 지나가는 중요한 날이에요. 함께 달려봐요.",
        "수요일, 고지가 바로 눈앞입니다! 조금만 더 힘내세요.",
    ],
    3: [  # 목요일
        "목요일 아침입니다! 주말이 코앞이에요. 오늘 하루만 더 달려봐요!",
        "거의 다 왔어요! 목요일, 이번 주의 마지막 전력질주를 시작해볼까요?",
        "목요일이에요! 오늘 만나는 고객 한 분 한 분이 소중한 인연이 되길 바랍니다.",
    ],
    4: [  # 금요일
        "드디어 금요일입니다! 한 주 동안 정말 고생 많으셨어요. 기분 좋게 마무리해 볼까요?",
        "금요일 아침, 이번 주 마지막 날이에요! 오늘도 밝게 마무리해봐요.",
        "TGIF! 금요일입니다. 이번 주를 멋지게 마무리하면 주말이 더 달콤해질 거예요!",
    ],
    5: [  # 토요일
        "토요일인데도 열심히 하시는 설계사님, 진심으로 존경스러워요!",
        "주말에도 고객을 위해 힘써주시는군요. 덕분에 고객분들도 든든하실 거예요.",
        "토요일 아침, 주말에도 현장에 계신 설계사님을 Goldkey AI가 응원합니다!",
    ],
    6: [  # 일요일
        "일요일이에요! 잠깐의 확인이라도 함께해서 영광이에요. 충분한 휴식도 잊지 마세요.",
        "주말에도 고객 챙기시는 설계사님, 오늘만큼은 조금 쉬어가셔도 괜찮아요.",
        "일요일 아침입니다. 오늘 하루는 재충전하는 날로 쓰세요. 내일을 위한 에너지가 될 거예요!",
    ],
}

def _ev_empathy(ev_count: int) -> str:
    """일정 수에 따라 공감 추임새 반환."""
    if ev_count >= 5:
        return random.choice([
            "오늘 정말 바쁘시겠어요! 식사 꼭 챙기시고 안전하게 이동하세요.",
            "일정이 빽빽하네요! 혹시 잠깐이라도 쉬어가는 시간을 만드세요.",
            "오늘 하루 정말 치열하실 것 같아요. 중간중간 물도 꼭 챙겨드세요!",
        ])
    elif ev_count >= 1:
        return random.choice([
            "오늘도 일정을 꼭 확인하고 준비된 자세로 출발하세요!",
            "만남이 있는 하루, 작은 준비 하나하나가 큰 인상을 남길 거예요.",
            "고객과의 만남 전 메모 한 번 더 확인해보세요. 디테일이 신뢰를 만들어요.",
        ])
    else:
        return random.choice([
            "오늘은 차분히 기존 고객님들께 안부 인사를 건네보기 좋은 날이네요.",
            "일정이 없는 날도 기회입니다! 오랫동안 연락 못 한 고객께 전화 한 통 어떨까요?",
            "오늘은 새로운 전략을 세워보기 좋은 날이에요. 여유롭게 시작해 보세요!",
        ])

# ══════════════════════════════════════════════════════════════════════════════
# [2] 텍스트 전처리 & SSML 청크 빌더
# ══════════════════════════════════════════════════════════════════════════════

def inject_emphasis_markers(text: str) -> str:
    """
    핵심 수치·용어에 [[EMPH:rate:vol:텍스트]] 마커 삽입.
    이후 _chunks_to_js()에서 JavaScript SpeechSynthesis 청크로 변환.
    """
    out = text
    for pattern, rate_mul, vol_mul in _EMPHASIS_RULES:
        def _replace(m, r=rate_mul, v=vol_mul):
            return f"[[EMPH:{r}:{v}:{m.group(0)}]]"
        out = re.sub(pattern, _replace, out)
    return out


def build_ssml_chunks(text: str, personality_type: str) -> list[dict]:
    """
    텍스트를 읽기 청크 배열로 변환.
    각 청크: {text, rate, pitch, volume}
    JS SpeechSynthesis에서 청크별로 다른 파라미터로 발화.
    """
    prof     = _VOICE_PROFILES.get(personality_type, _VOICE_PROFILES["Emotional"])
    base_r   = prof["rate"]
    base_p   = prof["pitch"]
    base_v   = prof["volume"]

    # 마크업 제거 후 강조 마킹
    clean = re.sub(r"#{1,6}\s*", "", text)    # 마크다운 헤더
    clean = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", clean)  # bold/italic
    clean = re.sub(r"`([^`]+)`", r"\1", clean)              # code
    clean = re.sub(r">\s*", "", clean)                       # blockquote
    clean = inject_emphasis_markers(clean)

    # 마커를 기준으로 청크 분리
    parts   = re.split(r"(\[\[EMPH:[^\]]+\]\])", clean)
    chunks  = []
    for part in parts:
        if not part.strip():
            continue
        emph_m = re.match(r"\[\[EMPH:([^:]+):([^:]+):(.+)\]\]", part, re.DOTALL)
        if emph_m:
            rate_mul = float(emph_m.group(1))
            vol_mul  = float(emph_m.group(2))
            word     = emph_m.group(3).strip()
            chunks.append({
                "text":   word,
                "rate":   round(base_r * rate_mul, 2),
                "pitch":  base_p,
                "volume": min(base_v * vol_mul, 1.0),
                "emph":   True,
            })
        else:
            # 일반 텍스트 — 문장 단위로 분할
            sentences = re.split(r"(?<=[.!?。])\s+", part)
            for s in sentences:
                s = s.strip()
                if s:
                    chunks.append({
                        "text":   s,
                        "rate":   base_r,
                        "pitch":  base_p,
                        "volume": base_v,
                        "emph":   False,
                    })
    return chunks


def detect_language(text: str) -> str:
    """
    언어 자동 감지 (간단한 휴리스틱).
    한글 비율로 판단 — 미래에 langdetect 라이브러리로 교체 가능.
    """
    if not text:
        return "ko"
    total = len(text)
    ko_cnt = len(re.findall(r"[가-힣]", text))
    en_cnt = len(re.findall(r"[a-zA-Z]", text))
    ja_cnt = len(re.findall(r"[\u3040-\u30ff]", text))
    zh_cnt = len(re.findall(r"[\u4e00-\u9fff]", text))
    scores = {"ko": ko_cnt, "en": en_cnt, "ja": ja_cnt, "zh": zh_cnt}
    dominant = max(scores, key=scores.get)
    return dominant if scores[dominant] > total * 0.05 else "ko"


# ══════════════════════════════════════════════════════════════════════════════
# [3] 모닝 브리핑 텍스트 빌더
# ══════════════════════════════════════════════════════════════════════════════

def build_morning_briefing(
    agent_name: str = "",
    today_evs: list | None = None,
    nba_count: int = 0,
) -> str:
    """
    [EQ v2] 요일별·상황별 감성 스크립트 풀 기반 모닝 브리핑.
    random.choice()로 매일 다른 인사말 + 일정 수 공감 추임새 삽입.
    """
    today    = datetime.date.today()
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    wd_str   = weekdays[today.weekday()]
    today_s  = f"{today.year}년 {today.month}월 {today.day}일 {wd_str}"
    _name    = _clean_agent_name(agent_name)

    try:
        from shared_components import get_time_aware_greeting as _gtag
        _greet_base = _gtag()
    except Exception:
        _greet_pool = _EQ_MORNING_GREETS.get(today.weekday(), [])
        _greet_base = random.choice(_greet_pool) if _greet_pool else "안녕하세요! 좋은 하루 되세요."
    _greet = (f"{_name} 설계사님, {_greet_base}" if _name else _greet_base) + " "

    intro    = f"오늘은 {today_s}입니다. "

    ev_count = len(today_evs) if today_evs else 0
    ev_part  = ""
    if ev_count > 0:
        first   = today_evs[0].get("title", "") if today_evs else ""
        ev_part = (
            f"오늘 예정된 일정은 총 {ev_count}건이며, "
            f"첫 번째 일정은 '{first}'입니다. "
        )
    ev_part += _ev_empathy(ev_count) + " "

    nba_part = ""
    if nba_count > 0:
        nba_part = (
            f"AI 비서가 오늘의 우선순위 고객 {nba_count}명을 선별했습니다. "
            "만기 임박, 휴면 재접촉, 보장 공백 고객을 확인해 보세요. "
        )

    closing = random.choice([
        "오늘도 최고의 하루 되시길 바랍니다! Goldkey AI 마스터가 함께합니다.",
        "오늘 하루도 빛나는 성과를 거두세요! 언제나 응원하고 있어요.",
        "설계사님의 오늘이 환하게 빛나길 바랍니다. Goldkey가 함께하겠습니다.",
        "작은 한 걸음이 큰 변화를 만들어요. 오늘도 믿고 응원합니다!",
    ])
    return _greet + intro + ev_part + nba_part + closing


def build_morning_briefing_compact(
    agent_name: str = "",
    today_evs: list | None = None,
    nba_count: int = 0,
) -> str:
    """
    [EQ Compact Mode] 짧고 따뜻한 한마디 + 핵심 수치 즉시 나열.
    설정 탭 [브리핑 간소화] (gk_brief_compact) ON 시 자동 전환.
    예: "이세윤 설계사님, 좋은 아침입니다! 오늘 일정 3건, 우선순위 고객 2명. 첫 일정: 10시 김철수님. 오늘도 파이팅!"
    """
    _name    = _clean_agent_name(agent_name)
    ev_count = len(today_evs) if today_evs else 0
    first_ev = today_evs[0].get("title", "없음") if today_evs else "없음"

    try:
        from shared_components import get_time_aware_greeting as _gtag
        _warm = _gtag()
    except Exception:
        _warm = random.choice([
            "좋은 아침입니다!",
            "오늘도 파이팅입니다!",
            "밝은 하루 시작하세요!",
            "활기차게 시작해볼까요!",
        ])
    _greet = (f"{_name} 설계사님, {_warm}" if _name else _warm)

    _stats = f"오늘 일정 {ev_count}건"
    if nba_count > 0:
        _stats += f", 우선순위 고객 {nba_count}명"
    if ev_count > 0:
        _stats += f". 첫 일정: {first_ev}"
    _stats += "."

    _closing = random.choice(["오늘도 화이팅!", "응원합니다!", "멋진 하루 되세요!"])
    return f"{_greet} {_stats} {_closing}"


def build_customer_briefing(
    customer: dict,
    personality_type: str,
    person_id: str = "",
) -> str:
    """
    고객 상세 화면 진입 시 — 성향별 맞춤 AI 브리핑 텍스트.
    [EQ Skip Logic] 당일 동일 고객 2회차부터는 감성 인사 생략, 핵심 메모만 요약.
    """
    name   = customer.get("name", "고객")
    memo   = customer.get("memo", "")
    status = customer.get("status", "")
    tier   = customer.get("management_tier", 3)
    _memo_s = memo[:30] + "..." if len(memo) > 30 else (memo or "특이사항 없음")

    # ── Skip 로직: 당일 이미 브리핑된 고객 → 핵심만 요약 ────────────────────
    _skip_key = (
        f"_cust_briefed_{person_id}_{datetime.date.today().strftime('%Y%m%d')}"
        if person_id else ""
    )
    _already = bool(_skip_key and st.session_state.get(_skip_key))
    if _skip_key:
        st.session_state[_skip_key] = True

    if _already:
        return random.choice([
            f"{name}님 다시 확인하셨군요. 추가로 확인하실 메모 내용은 {_memo_s}입니다. "
            f"현재 상태는 '{status}', {tier}등급으로 관리 중입니다.",
            f"{name}님을 또 만났네요! 메모: {_memo_s}. 상태: '{status}'. 언제든 함께하겠습니다.",
        ])

    # ── 1회차: 전체 브리핑 ────────────────────────────────────────────────────
    if personality_type == "Logical":
        return (
            f"{name}님 고객 분석 브리핑입니다. "
            f"관리 등급 {tier}등급이며, 상태는 '{status}'입니다. "
            f"2026 트리니티 역산 기준으로 보장 공백 정밀 진단을 권장합니다. "
            f"건강보험료 납입 내역이 있다면 가처분 소득을 즉시 역산할 수 있습니다."
        )
    else:
        return (
            f"{name}님에 대한 맞춤 브리핑을 시작하겠습니다. "
            f"{name}님은 소중한 {tier}등급 고객이십니다. "
            f"상담 메모를 살펴보면 {_memo_s}이라고 되어 있습니다. "
            f"오늘 상담에서 {name}님의 가족을 위한 최선의 솔루션을 찾아드릴 수 있습니다."
        )


# ══════════════════════════════════════════════════════════════════════════════
# [GP-NEWS] 실시간 정보 수집 엔진 — 네이버 뉴스 + 날씨
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_naver_insurance_news(n: int = 3) -> list:
    """[GP-NEWS] 네이버 뉴스 API: '금감원 보험' 키워드 최신 n건 수집."""
    try:
        from shared_components import get_env_secret as _genv_n
        _cid  = _genv_n("NAVER_CLIENT_ID", "")
        _csec = _genv_n("NAVER_CLIENT_SECRET", "")
        if not _cid or not _csec:
            return []
        import requests as _req_n
        _resp = _req_n.get(
            "https://openapi.naver.com/v1/search/news.json",
            params={"query": "금감원 보험", "display": n, "sort": "date"},
            headers={
                "X-Naver-Client-Id":     _cid,
                "X-Naver-Client-Secret": _csec,
            },
            timeout=5,
        )
        if _resp.status_code == 200:
            _result = []
            for _it in _resp.json().get("items", []):
                import html as _html_nv
                _title = _html_nv.unescape(
                    re.sub(r"<[^>]+>", "", _it.get("title", ""))
                ).strip()
                _result.append({
                    "title":   _title,
                    "link":    _it.get("originallink") or _it.get("link", ""),
                    "pubDate": _it.get("pubDate", ""),
                })
            return _result
    except Exception:
        pass
    return []


def _fetch_seoul_weather() -> str:
    """[GP-NEWS] 서울 현재 날씨 텍스트 (wttr.in — 무료, API 키 불필요)."""
    try:
        import requests as _req_w
        _resp = _req_w.get(
            "https://wttr.in/Seoul?format=%C+%t+습도%h&lang=ko",
            timeout=5,
            headers={"User-Agent": "GoldkeyAI/2026"},
        )
        if _resp.status_code == 200:
            return _resp.text.strip()
    except Exception:
        pass
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# [4] 보이스 플레이어 UI (JavaScript SpeechSynthesis)
# ══════════════════════════════════════════════════════════════════════════════

def render_voice_player(
    text: str,
    personality_type: str = "Emotional",
    key: str = "vp_default",
    auto_play: bool = False,
    compact: bool = False,
) -> None:
    """
    심리 맞춤형 보이스 플레이어 위젯.
    - SSML 수치 강조 자동 적용
    - 성향 아이콘 표시 + 수동 전환 버튼
    - 텍스트 하이라이트 동기화
    """
    prof    = _VOICE_PROFILES.get(personality_type, _VOICE_PROFILES["Emotional"])
    chunks  = build_ssml_chunks(text, personality_type)
    lang    = detect_language(text)
    bcp_lang = _LANG_VOICE_MAP.get(lang, "ko-KR")
    chunks_json = json.dumps(chunks, ensure_ascii=False)
    auto_js = "true" if auto_play else "false"

    # 성향 전환 — Python 버튼으로 처리
    if not compact:
        _pv1, _pv2, _pv3 = st.columns([1, 1, 4])
        with _pv1:
            if st.button(f"⚖️ 논리형", key=f"{key}_logical",
                         help="논리형(지적 앵커) 모드로 전환"):
                st.session_state[f"{key}_ptype"] = "Logical"
                st.rerun()
        with _pv2:
            if st.button(f"❤️ 감성형", key=f"{key}_emotional",
                         help="감성형(따뜻한 큐레이터) 모드로 전환"):
                st.session_state[f"{key}_ptype"] = "Emotional"
                st.rerun()
        with _pv3:
            st.markdown(
                f"<div style='padding:6px 0;font-size:.78rem;color:#64748b;'>"
                f"{prof['icon']} <b>{prof['label']}</b> — {prof['desc']}</div>",
                unsafe_allow_html=True,
            )
        # 세션 전환 반영
        if f"{key}_ptype" in st.session_state:
            personality_type = st.session_state[f"{key}_ptype"]
            prof   = _VOICE_PROFILES.get(personality_type, _VOICE_PROFILES["Emotional"])
            chunks = build_ssml_chunks(text, personality_type)
            chunks_json = json.dumps(chunks, ensure_ascii=False)

    _cv1.html(
        _build_player_html(chunks_json, bcp_lang, prof, key, auto_js),
        height=90 if compact else 110,
        scrolling=False,
    )


def render_voice_player_bar(
    text: str,
    personality_type: str = "Emotional",
    key: str = "vp_bar",
) -> None:
    """
    HQ 앱 상단 고정형 미니 플레이어 바.
    """
    prof        = _VOICE_PROFILES.get(personality_type, _VOICE_PROFILES["Emotional"])
    chunks      = build_ssml_chunks(text, personality_type)
    lang        = detect_language(text)
    bcp_lang    = _LANG_VOICE_MAP.get(lang, "ko-KR")
    chunks_json = json.dumps(chunks, ensure_ascii=False)

    _cv1.html(
        _build_player_html(chunks_json, bcp_lang, prof, key, "false", mini=True),
        height=60,
        scrolling=False,
    )


def _build_player_html(
    chunks_json: str,
    lang: str,
    prof: dict,
    key: str,
    auto_js: str,
    mini: bool = False,
) -> str:
    icon  = _html.escape(prof["icon"])
    label = _html.escape(prof.get("label", ""))
    btn_h = "44px" if mini else "52px"

    return f"""<!DOCTYPE html><html lang="ko"><head>
<meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Malgun Gothic',sans-serif;}}
body{{background:transparent;padding:4px 0;}}
.vp{{display:flex;align-items:center;gap:8px;background:#f8fafc;
  border:1.5px solid #e2e8f0;border-radius:12px;padding:6px 12px;}}
.vp-btn{{width:{btn_h};height:{btn_h};border:none;border-radius:50%;
  background:#1e5ba4;color:#fff;font-size:1.2rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
  transition:background .15s;}}
.vp-btn:hover{{background:#154a8a;}}
.vp-btn:disabled{{background:#94a3b8;cursor:not-allowed;}}
.vp-progress{{flex:1;height:4px;background:#e2e8f0;border-radius:2px;overflow:hidden;}}
.vp-bar{{height:100%;background:#1e5ba4;width:0%;transition:width .3s;}}
.vp-label{{font-size:.72rem;color:#64748b;white-space:nowrap;}}
.vp-word{{font-size:.78rem;color:#1e5ba4;font-weight:700;max-width:160px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.vp-stop{{width:36px;height:36px;border:1.5px solid #e2e8f0;border-radius:8px;
  background:#fff;cursor:pointer;font-size:.9rem;}}
</style></head><body>
<div class="vp">
  <button class="vp-btn" id="playBtn" onclick="togglePlay()" title="재생/일시정지">▶</button>
  <button class="vp-stop" onclick="stopAll()" title="정지">⏹</button>
  <div style="flex:1;display:flex;flex-direction:column;gap:4px;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span class="vp-word" id="curWord">{icon} {label if not mini else '🔊 AI 브리핑'}</span>
      <span class="vp-label" id="progLabel">0 / 0</span>
    </div>
    <div class="vp-progress"><div class="vp-bar" id="progBar"></div></div>
  </div>
</div>
<script>
var chunks = {chunks_json};
var lang   = "{lang}";
var idx    = 0;
var playing= false;
var synth  = window.speechSynthesis;

function getVoice(l) {{
  var vs = synth.getVoices();
  for(var i=0;i<vs.length;i++) {{ if(vs[i].lang.startsWith(l.split('-')[0])) return vs[i]; }}
  return null;
}}

function speakChunk(i) {{
  if(i >= chunks.length) {{ stopAll(); return; }}
  var c  = chunks[i];
  var u  = new SpeechSynthesisUtterance(c.text);
  u.lang   = lang;
  u.rate   = c.rate || 0.85;
  u.pitch  = 1 + (c.pitch || 0) * 0.1;
  u.volume = c.volume || 1.0;
  var v = getVoice(lang); if(v) u.voice = v;
  var pct  = Math.round((i / chunks.length) * 100);
  document.getElementById('progBar').style.width = pct + '%';
  document.getElementById('progLabel').textContent = (i+1) + ' / ' + chunks.length;
  document.getElementById('curWord').textContent = c.emph ? '🔴 ' + c.text : c.text;
  u.onend = function() {{ if(playing) speakChunk(i+1); }};
  u.onerror = function() {{ if(playing) speakChunk(i+1); }};
  synth.speak(u);
}}

function togglePlay() {{
  var btn = document.getElementById('playBtn');
  if(playing) {{
    synth.pause();
    playing = false;
    btn.textContent = '▶';
  }} else {{
    if(synth.paused) {{
      synth.resume();
    }} else {{
      synth.cancel();
      idx = 0;
      speakChunk(0);
    }}
    playing = true;
    btn.textContent = '⏸';
  }}
}}

function stopAll() {{
  synth.cancel();
  playing = false;
  idx = 0;
  document.getElementById('playBtn').textContent = '▶';
  document.getElementById('progBar').style.width = '0%';
  document.getElementById('curWord').textContent = '{icon} {label if not mini else "AI 브리핑"}';
  document.getElementById('progLabel').textContent = '0 / 0';
}}

// [Fix] 자동 재생 — 더블 플레이백 + 메아리 현상 원천 차단
if({auto_js}) {{
  var _gkFlag = '_gk_played_{key}';
  var _alreadyPlayed = false;
  try {{ _alreadyPlayed = !!sessionStorage.getItem(_gkFlag); }} catch(e) {{ _alreadyPlayed = !!window[_gkFlag]; }}
  if (!_alreadyPlayed) {{
    try {{ sessionStorage.setItem(_gkFlag, '1'); }} catch(e) {{ window[_gkFlag] = true; }}
    synth.cancel();
    function _doAutoPlay() {{
      if(chunks.length > 0 && !playing) {{
        playing = true;
        document.getElementById('playBtn').textContent = '⏸';
        speakChunk(0);
      }}
    }}
    if(synth.getVoices().length > 0) {{
      _doAutoPlay();
    }} else {{
      window.speechSynthesis.onvoiceschanged = function() {{
        window.speechSynthesis.onvoiceschanged = null;
        _doAutoPlay();
      }};
    }}
  }}
}}
</script></body></html>"""


def render_voice_player_zephyr(
    text: str,
    key: str = "vp_zephyr",
    auto_play: bool = False,
    compact: bool = False,
) -> None:
    """[GP-VOICE-2026] Zephyr 아나운서 TTS 플레이어.
    우선순위: Gemini TTS(Zephyr) → Web Speech API(폴백)
    Gemini GOOGLE_API_KEY 없거나 합성 실패 시 자동으로 기존 Web Speech API 사용.
    """
    try:
        from shared_components import get_env_secret as _genv_v
        _api_key = (_genv_v("GEMINI_API_KEY", "")
                    or _genv_v("GOOGLE_API_KEY", ""))
    except Exception:
        _api_key = (os.environ.get("GEMINI_API_KEY", "")
                    or os.environ.get("GOOGLE_API_KEY", ""))

    _audio_bytes = None
    if _api_key and _api_key != "여기에_발급받은_API_키를_넣어주세요":
        _audio_bytes = synthesize_zephyr(text, _api_key)

    if _audio_bytes:
        # ── Gemini Zephyr TTS 성공 — st.audio 재생 ─────────────────────
        _ok_model = st.session_state.get("_zephyr_model_ok", _ZEPHYR_MODEL)
        st.markdown(
            "<div style='background:rgba(30,91,164,0.08);border:1px dashed #1e5ba4;"
            "border-radius:10px;padding:6px 14px;font-size:clamp(11px,1.8vw,13px);color:#1e5ba4;"
            "margin-bottom:6px;'>"
            "🎙️ <b>Text-to-Speech AI</b> · <b>Gemini Pro TTS</b> · "
            f"Language: Korean (South Korea) · Voice: {_ZEPHYR_VOICE} · Model: {_ok_model}<br>"
            "📱 <b>모바일:</b> 아래 ▶ 버튼을 눌러 재생하세요</div>",
            unsafe_allow_html=True,
        )
        import io as _io
        st.audio(_io.BytesIO(_audio_bytes), format="audio/wav")
    else:
        # ── 폴백 — 기존 Web Speech API ─────────────────────────────────
        _tts_err = st.session_state.get("_zephyr_err", "")
        if not compact:
            if _tts_err:
                st.caption(f"⚠️ Gemini TTS 오류 → Web Speech 폴백 | 원인: {_tts_err[:120]}")
            elif not _api_key:
                st.caption("⚠️ GEMINI_API_KEY 미설정 → Web Speech 폴백")
            else:
                st.caption("🔊 Web Speech API (Gemini TTS 폴백)")
        render_voice_player(
            text,
            personality_type="Emotional",
            key=key,
            auto_play=auto_play,
            compact=compact,
        )


def render_voice_player_bar_zephyr(text: str, key: str = "vp_bar_zephyr") -> None:
    """HQ 홈 미니 재생 바 — Gemini Pro TTS (Zephyr) 우선, Web Speech 폴백."""
    try:
        from shared_components import get_env_secret as _genv_v
        _api_key = (_genv_v("GEMINI_API_KEY", "") or _genv_v("GOOGLE_API_KEY", ""))
    except Exception:
        _api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

    if _api_key and _api_key != "여기에_발급받은_API_키를_넣어주세요":
        _audio_bytes = synthesize_zephyr(text, _api_key)
        if _audio_bytes:
            import io as _io
            st.markdown(
                "<div style='font-size:clamp(11px,1.8vw,13px);color:#475569;margin-bottom:4px;'>"
                "🔊 Text-to-Speech AI · Gemini Pro TTS · Korean (South Korea) · Zephyr</div>",
                unsafe_allow_html=True,
            )
            st.audio(_io.BytesIO(_audio_bytes), format="audio/wav")
            return

    render_voice_player_bar(
        text=text,
        personality_type="Emotional",
        key=key,
    )


# ══════════════════════════════════════════════════════════════════════════════
# [5] 실시간 모닝 뉴스 브리핑 엔진 (GP-RT 2026)
# pytz KST · 네이버 뉴스 · 날씨 · AI 아나운서 · 중지 버튼 · 보안 카드
# ══════════════════════════════════════════════════════════════════════════════

def render_time_aware_briefing(
    agent_id: str,
    agent_name: str = "",
) -> None:
    """
    [GP-RT §5] 실시간 모닝 뉴스 브리핑 엔진 — 로그인 시 1회 자동 재생.
    브리핑 순서: [현재 시각(KST)] → [오늘의 날씨] → [주요 보험 뉴스 3건] → [스케줄 요약]
    - pytz Asia/Seoul 기준 서울 정확 시각
    - 네이버 뉴스 API: '금감원 보험' 최신 3건
    - AI 아나운서: 'GoldkeyAimasters2026의 AI 상담 코치'
    - [🛑 브리핑 중지] Compact 버튼
    - 보안 카드: 마이크 수집 없음 안내
    당일 1회 자동 재생. st.session_state["_morning_briefed_YYYYMMDD"] 중복 방지.
    """
    today_key = f"_morning_briefed_{datetime.date.today().strftime('%Y%m%d')}"
    if st.session_state.get(today_key):
        return

    # ── [GP-RT §1] 서울 시각 (pytz Asia/Seoul) ───────────────────────────────
    try:
        import pytz as _pytz_rt
        _kst = _pytz_rt.timezone("Asia/Seoul")
        _now = datetime.datetime.now(_kst)
    except Exception:
        _now = datetime.datetime.now()
    _h        = _now.hour
    _time_str = _now.strftime("%H:%M")
    _date_str = _now.strftime("%Y년 %m월 %d일")
    _weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    _wd_str   = _weekdays[_now.weekday()]
    if 5 <= _h < 12:
        _time_emoji, _time_label, _time_sub = "🌅", "모닝 브리핑", "활기찬 하루의 시작을 함께합니다"
    elif 12 <= _h < 18:
        _time_emoji, _time_label, _time_sub = "☀️", "오후 브리핑", "오늘의 오후 일정과 우선순위를 안내해 드립니다"
    elif 18 <= _h < 22:
        _time_emoji, _time_label, _time_sub = "🌆", "저녁 브리핑", "수고 많으셨습니다. 남은 일정을 마무리해 드리겠습니다"
    else:
        _time_emoji, _time_label, _time_sub = "🌙", "심야 브리핑", "늦은 시간까지 열정적인 설계사님을 응원합니다"

    # ── [GP-RT §2] 실시간 정보 수집 (세션 캐시 — 당일 1회) ──────────────────
    _today_s     = _now.strftime("%Y%m%d")
    _news_key    = f"_brief_news_{_today_s}"
    _weather_key = f"_brief_weather_{_today_s}"
    _news_items  = st.session_state.get(_news_key)
    _weather_txt = st.session_state.get(_weather_key)
    if _news_items is None:
        _news_items = _fetch_naver_insurance_news(3)
        st.session_state[_news_key] = _news_items
    if _weather_txt is None:
        _weather_txt = _fetch_seoul_weather()
        st.session_state[_weather_key] = _weather_txt

    # ── [GP-RT §3] 오늘 일정 + NBA 로드 ─────────────────────────────────────
    today_evs = []
    try:
        from calendar_engine import cal_load_today
        today_evs = cal_load_today(agent_id)
    except Exception:
        pass
    nba_count = 0
    try:
        from nba_engine import get_all_nba_actions
        nba_count = len(get_all_nba_actions(agent_id))
    except Exception:
        pass

    _name = _clean_agent_name(agent_name)

    # ── [GP-RT §4] Gemini AI 브리핑 텍스트 (아나운서 페르소나) ──────────────
    _compact_mode = st.session_state.get("gk_brief_compact", False)
    briefing_text = ""
    try:
        from shared_components import get_env_secret as _genv_b
        _api_key_b = _genv_b("GOOGLE_API_KEY", "")
        if _api_key_b and _api_key_b != "여기에_발급받은_API_키를_넣어주세요":
            import google.genai as _genai_b
            import google.genai.types as _gtypes_b
            _cli_b   = _genai_b.Client(api_key=_api_key_b)
            _ev_sum  = f"{len(today_evs)}건" if today_evs else "없음"
            _first   = today_evs[0].get("title", "") if today_evs else ""
            _nba_s   = f"{nba_count}명" if nba_count > 0 else "없음"
            _news_s  = "\n".join(
                [f"  {i+1}. {nw['title']}" for i, nw in enumerate(_news_items[:3])]
            ) if _news_items else "  (뉴스 없음)"
            _wx_s    = f"서울 날씨: {_weather_txt}" if _weather_txt else ""
            _brief_prompt = (
                "너는 GoldkeyAimasters2026의 AI 상담 코치다. "
                "반드시 첫 문장은 정확히 이렇게 시작하라: "
                "'안녕하세요, GoldkeyAimasters2026의 AI 상담 코치입니다.' "
                f"현재 서울 시각은 {_date_str} {_wd_str} {_time_str}이며 {_time_label}입니다. "
                f"{_wx_s} "
                f"오늘의 주요 보험 뉴스:\n{_news_s}\n"
                f"{_name + ' 설계사님,' if _name else ''} "
                f"오늘 일정 {_ev_sum}{'(첫 일정: ' + _first + ')' if _first else ''}, "
                f"우선순위 고객 {_nba_s}. "
                "신뢰감 있고 지적인 아나운서 톤으로 문장 간 연결이 자연스럽게 "
                f"{'2~3문장으로 간결하게' if _compact_mode else '5~6문장으로'} "
                "브리핑하라. 반드시 한국어. 뉴스는 핵심 키워드만 언급."
            )
            _resp_b = _cli_b.models.generate_content(
                model="gemini-1.5-flash",
                contents=_brief_prompt,
                config=_gtypes_b.GenerateContentConfig(
                    max_output_tokens=380, temperature=0.7,
                ),
            )
            briefing_text = (_resp_b.text or "").strip()
    except Exception:
        pass

    # ── 폴백: 정적 브리핑 텍스트 ─────────────────────────────────────────────
    if not briefing_text:
        _news_part = ""
        if _news_items:
            _news_part = " 오늘의 주요 보험 뉴스: " + ", ".join(
                [(nw["title"][:30] + "…" if len(nw["title"]) > 30 else nw["title"])
                 for nw in _news_items[:3]]
            ) + "."
        _wx_part = f" 서울 날씨는 {_weather_txt}입니다." if _weather_txt else ""
        if _compact_mode:
            briefing_text = build_morning_briefing_compact(agent_name, today_evs, nba_count)
        else:
            briefing_text = (
                "안녕하세요, GoldkeyAimasters2026의 AI 상담 코치입니다. "
                f"현재 서울 시각은 {_date_str} {_wd_str} {_time_str}입니다."
                f"{_wx_part}{_news_part} "
            ) + build_morning_briefing(agent_name, today_evs, nba_count)

    st.session_state["_morning_briefing_text"] = briefing_text

    # ══════════════════════════════════════════════════════════════════════════
    # [GP-RT §5] 브리핑 UI 렌더링
    # ══════════════════════════════════════════════════════════════════════════

    # ── 중지 상태 확인 ────────────────────────────────────────────────────────
    _stop_key = f"_brief_stopped_{_today_s}"
    if st.session_state.get(_stop_key):
        return

    # ── 헤더 배너 + [🛑 브리핑 중지] 버튼 (Compact) ─────────────────────────
    _hdr_c1, _hdr_c2 = st.columns([9, 1])
    with _hdr_c1:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#eff6ff,#dbeafe);"
            f"border:1.5px dashed #93c5fd;border-radius:10px;"
            f"padding:8px 14px;"
            f"display:flex;align-items:center;gap:10px;'>"
            f"<span style='font-size:1.3rem;'>{_time_emoji}</span>"
            f"<div>"
            f"<div style='color:#1e40af;font-size:.88rem;font-weight:900;'>"
            f"{_time_label}"
            f"<span style='color:#3b82f6;font-size:.70rem;font-weight:500;margin-left:8px;'>"
            f"서울 {_time_str} · {_date_str} {_wd_str}</span></div>"
            f"<div style='color:#4b5563;font-size:.72rem;margin-top:1px;'>{_time_sub}</div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with _hdr_c2:
        st.markdown("<div style='height:2px;'></div>", unsafe_allow_html=True)
        if st.button(
            "🛑", key=f"_brief_stop_btn_{_today_s}",
            help="브리핑 중지", use_container_width=True,
        ):
            st.session_state[_stop_key] = True
            st.rerun()

    # ── 날씨 + 뉴스 인포 카드 ────────────────────────────────────────────────
    if _weather_txt or _news_items:
        _card = (
            "<div style='background:#fffbeb;border:1px dashed #000;"
            "border-radius:10px;padding:8px 14px;margin:6px 0;font-size:0.82rem;'>"
        )
        if _weather_txt:
            _card += (
                "<div style='font-weight:700;color:#78350f;margin-bottom:5px;'>"
                f"🌤️ 오늘의 날씨&nbsp;&nbsp;"
                f"<span style='font-weight:500;color:#555;'>{_weather_txt}</span></div>"
            )
        if _news_items:
            _card += (
                "<div style='font-weight:700;color:#1e3a8a;margin-bottom:3px;'>"
                "📰 주요 보험 뉴스 (금감원)</div>"
            )
            for _ni, _nw in enumerate(_news_items[:3]):
                _nt   = _nw.get("title", "")
                _nd   = (_nt[:52] + "…") if len(_nt) > 52 else _nt
                _link = _nw.get("link", "")
                _num  = f"<span style='color:#6b7280;font-weight:700;'>{_ni+1}.</span> "
                if _link:
                    _card += (
                        f"<div style='color:#374151;line-height:1.65;font-size:0.79rem;"
                        f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%;'>"
                        f"{_num}<a href='{_link}' target='_blank' "
                        f"style='color:#1e40af;text-decoration:none;'>{_nd}</a></div>"
                    )
                else:
                    _card += (
                        f"<div style='color:#374151;line-height:1.65;font-size:0.79rem;"
                        f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%;'>"
                        f"{_num}{_nd}</div>"
                    )
        _card += "</div>"
        st.markdown(_card, unsafe_allow_html=True)

    # ── [GP-VOICE-2026] Zephyr 아나운서 TTS ─────────────────────────────────
    render_voice_player_zephyr(
        briefing_text,
        key="morning_briefing",
        auto_play=True,
        compact=True,
    )

    # ── [GP-COMPLIANCE] 면책 고지 + 피드백 ───────────────────────────────────
    try:
        from compliance import render_ai_disclaimer as _rd, render_feedback_button as _rfb
        _rd(margin_top=4)
        _rfb(key="morning_briefing_fb", context="morning_briefing", compact=True)
    except Exception:
        pass

    # ── [GP-RT §6] 보안 카드 ─────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.76rem;color:#374151;padding:5px 12px;"
        "background:#f9fafb;border:1px dashed #000;border-radius:8px;"
        "margin-top:6px;'>"
        "<b>🎙️ AI 아나운서 브리핑: 마이크 수집 없이 스피커 출력 전용으로 작동하여 "
        "사생활을 보호합니다.</b>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.session_state[today_key] = True


render_morning_briefing_auto = render_time_aware_briefing


# ══════════════════════════════════════════════════════════════════════════════
# [6] STT 보이스 검색 — Web Speech API + 의도 파서
# ══════════════════════════════════════════════════════════════════════════════

_INTENT_RULES: list[tuple] = [
    (r"VVIP|VIP|일등급|1\s*등급|최우선",              "management_tier", 1),
    (r"핵심|이등급|2\s*등급",                          "management_tier", 2),
    (r"일반|잠재|삼등급|3\s*등급",                     "management_tier", 3),
    (r"즐겨찾기|중요고객|단골|중점관리",               "is_favorite",     True),
    (r"계약|계약완료|성공|클로징",                     "status",          "contracted"),
    (r"진행|상담중|진행중",                             "status",          "active"),
    (r"가망|리드|잠재|미계약",                         "status",          "potential"),
    (r"자동차|차량|자동차보험",                        "renewal_type",    "auto"),
    (r"화재|집|주택|화재보험",                         "renewal_type",    "fire"),
]
_KEYWORD_PATTERNS: list[str] = [
    r"치매", r"암\b", r"뇌졸중", r"뇌경색", r"심장", r"입원", r"수술",
    r"어린이", r"태아", r"운전자", r"실손", r"종신", r"연금",
]


def parse_voice_intent(text: str) -> dict:
    """
    음성 인식 텍스트에서 CRM 검색 의도를 추출.

    Returns: {
        "query":   str,         # 이름 키워드
        "filters": {
            "management_tier": int | None,
            "status":          str | None,
            "renewal_month":   int | None,
            "renewal_type":    str | None,  # "auto" | "fire"
            "is_favorite":     bool | None,
            "keyword":         str | None,  # 보험 종류 키워드
        }
    }
    """
    filters: dict = {}
    text = text.strip()

    for pattern, key, val in _INTENT_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            filters[key] = val

    mo_m = re.search(r"(\d{1,2})\s*월\s*(만기|갱신|도래)", text)
    if mo_m:
        filters["renewal_month"] = int(mo_m.group(1))

    for kp in _KEYWORD_PATTERNS:
        if re.search(kp, text):
            filters["keyword"] = re.search(kp, text).group(0)
            break

    name_m = re.search(r"([가-힣]{2,4})\s*(고객|씨|님|씨네)?", text)
    query = ""
    if name_m:
        candidate = name_m.group(1)
        _excluded = {"고객", "치매", "암보험", "뇌경색", "심장", "일반", "핵심", "잠재",
                     "진행", "계약", "가망", "자동", "화재", "중요", "즐겨", "만기"}
        if candidate not in _excluded:
            query = candidate

    return {"query": query, "filters": filters}


def render_voice_search(
    session_key: str = "crm_voice_q",
    key: str = "voice_search_main",
) -> str | None:
    """
    [GP-VOICE §6] Web Speech API 기반 음성 고객 검색 위젯.

    - 브라우저 SpeechRecognition API로 STT 처리 (서버 rerun 없음)
    - 인식 완료 후 [✔ 검색] 클릭 → session_state[session_key]에 저장 → 1회 rerun
    - 반환: 인식된 음성 텍스트 (없으면 None)

    미리 parse_voice_intent(result) 호출하여 filters 추출 가능.
    """
    result = None
    if _stt_component is not None:
        result = _stt_component(key=key, default=None)
    else:
        result = _cv1.html(
            "<div style='padding:8px;background:#fff3cd;border:1px dashed #f59e0b;"
            "border-radius:8px;font-size:0.78rem;color:#92400e;'>"
            "⚠️ 음성 검색 컴포넌트 로드 실패 — 텍스트 검색을 사용하세요.</div>",
            height=50,
        )
        return st.session_state.get(session_key)

    if result and isinstance(result, str) and result.strip():
        prev = st.session_state.get(session_key, "")
        st.session_state[session_key] = result.strip()
        if result.strip() != prev:
            st.rerun()
        return result.strip()
    return st.session_state.get(session_key)
