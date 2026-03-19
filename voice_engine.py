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
"""
from __future__ import annotations
import re, json, datetime, html as _html
import streamlit as st
import streamlit.components.v1 as _cv1

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
    오늘 날짜 + 일정 요약 + NBA 요약을 담은 모닝 브리핑 텍스트.
    앱 기동 시 최초 1회 자동 발화.
    """
    today   = datetime.date.today()
    weekdays = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"]
    wd_str  = weekdays[today.weekday()]
    today_s = f"{today.year}년 {today.month}월 {today.day}일 {wd_str}"

    greet   = f"안녕하세요{', ' + agent_name + ' 설계사님' if agent_name else ''}! "
    intro   = f"오늘은 {today_s}입니다. "

    ev_part = ""
    if today_evs:
        cnt     = len(today_evs)
        first   = today_evs[0].get("title","") if today_evs else ""
        ev_part = f"오늘 예정된 일정은 총 {cnt}건이며, 첫 번째 일정은 '{first}'입니다. "

    nba_part = ""
    if nba_count > 0:
        nba_part = (
            f"AI 비서가 오늘의 우선순위 고객 {nba_count}명을 선별했습니다. "
            "만기 임박, 휴면 재접촉, 보장 공백 고객을 확인해 보세요. "
        )

    closing = "오늘도 최고의 하루 되시길 바랍니다. Goldkey AI 마스터가 함께합니다."
    return greet + intro + ev_part + nba_part + closing


def build_customer_briefing(customer: dict, personality_type: str) -> str:
    """고객 상세 화면 진입 시 — 성향별 맞춤 AI 브리핑 텍스트."""
    name    = customer.get("name", "고객")
    memo    = customer.get("memo", "")
    status  = customer.get("status", "")
    tier    = customer.get("management_tier", 3)

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
            f"상담 메모를 살펴보면 {memo[:30] + '...' if len(memo) > 30 else memo if memo else '특이사항 없음'} "
            f"이라고 되어 있습니다. "
            f"오늘 상담에서 {name}님의 가족을 위한 최선의 솔루션을 찾아드릴 수 있습니다."
        )


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

// 보이스 로드 후 자동 재생 (옵션)
if({auto_js}) {{
  window.speechSynthesis.onvoiceschanged = function() {{
    if(chunks.length > 0) {{ playing=true; document.getElementById('playBtn').textContent='⏸'; speakChunk(0); }}
  }};
  if(synth.getVoices().length > 0 && chunks.length > 0) {{
    playing=true; document.getElementById('playBtn').textContent='⏸'; speakChunk(0);
  }}
}}
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════════════════
# [5] 모닝 브리핑 자동 트리거 (앱 기동 시 1회)
# ══════════════════════════════════════════════════════════════════════════════

def render_morning_briefing_auto(
    agent_id: str,
    agent_name: str = "",
) -> None:
    """
    앱 기동 시 최초 1회 — 아나운서 모닝 브리핑 자동 재생.
    st.session_state["_morning_briefed_YYYYMMDD"] 로 당일 중복 방지.
    """
    today_key = f"_morning_briefed_{datetime.date.today().strftime('%Y%m%d')}"
    if st.session_state.get(today_key):
        return

    # 오늘 일정 로드 (calendar_engine 연동)
    today_evs = []
    try:
        from calendar_engine import cal_load_today
        today_evs = cal_load_today(agent_id)
    except Exception:
        pass

    # NBA 건수 로드 (nba_engine 연동)
    nba_count = 0
    try:
        from nba_engine import get_all_nba_actions
        nba_count = len(get_all_nba_actions(agent_id))
    except Exception:
        pass

    briefing_text = build_morning_briefing(agent_name, today_evs, nba_count)
    st.session_state["_morning_briefing_text"] = briefing_text

    st.markdown(
        "<div style='background:linear-gradient(90deg,#0f172a,#1e3a5c);border-radius:12px;"
        "padding:12px 18px;margin-bottom:10px;display:flex;align-items:center;gap:12px;'>"
        "<div style='font-size:1.5rem;'>🌅</div>"
        "<div>"
        "<div style='color:#fff;font-size:.88rem;font-weight:900;'>모닝 브리핑</div>"
        "<div style='color:#94c4f5;font-size:.74rem;margin-top:2px;'>오늘의 영업 일정과 우선순위 고객을 안내해 드리겠습니다</div>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    render_voice_player(
        briefing_text,
        personality_type="Emotional",
        key="morning_briefing",
        auto_play=True,
        compact=True,
    )

    st.session_state[today_key] = True
