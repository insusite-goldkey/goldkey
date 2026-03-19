# sim_trainer.py — Goldkey AI Masters 2026
"""
[AI 상담 시뮬레이션 엔진]
설계사 교육용 롤플레이 시뮬레이터:
  - 5가지 고객 페르소나 랜덤 생성
  - LLM 기반 AI 고객 응대 (st.chat_message)
  - 트리니티 핵심 키워드 채점 (Scorecard)
  - 마스터의 힌트 (closing_engine 연계)

exports:
  render_simulation_dashboard() — Streamlit 렌더링 진입점
"""
from __future__ import annotations

import random
import streamlit as st

# ── 고객 페르소나 5종 ─────────────────────────────────────────────────────────
_PERSONAS: list[dict] = [
    {
        "type": "회의적",
        "emoji": "😒",
        "desc": "보험은 돈 낭비라고 생각하며, 이미 충분하다고 믿음",
        "system": (
            "당신은 보험에 회의적인 45세 직장인입니다. "
            "국가 의료보험이면 충분하고 추가 보험은 낭비라고 생각합니다. "
            "설계사의 말에 즉각 반박하되, 정확한 숫자 근거에는 서서히 설득됩니다. "
            "한 번에 넘어가지 말고 1~2가지 반박 질문을 던지세요. "
            "답변은 2~3문장 이내로 고객 역할만 하세요."
        ),
        "opener": "'아, 저 보험 이미 있는데요. 굳이 더 들 필요 있나요?'",
        "nhi": 185_000,
        "cancer_amt": "3천만 원",
    },
    {
        "type": "걱정인형",
        "emoji": "😟",
        "desc": "불안하긴 한데 구체적으로 뭐가 부족한지 모름",
        "system": (
            "당신은 막연하게 불안한 35세 주부입니다. "
            "보험이 부족한 것 같긴 한데 구체적으로 뭐가 부족한지 모릅니다. "
            "'그래서 얼마면 돼요?', '제일 급한 게 뭐예요?'라는 구체적 질문을 합니다. "
            "감정적으로 공감해주면 마음이 열립니다. "
            "답변은 2~3문장 이내로 고객 역할만 하세요."
        ),
        "opener": "'솔직히 보험이 부족한 것 같긴 한데... 뭐가 부족한 건지 잘 모르겠어요.'",
        "nhi": 120_000,
        "cancer_amt": "2천만 원",
    },
    {
        "type": "논리파",
        "emoji": "🧐",
        "desc": "가성비와 수치를 중시하며, 정확한 근거를 요구함",
        "system": (
            "당신은 수치와 근거를 중시하는 35세 IT 개발자입니다. "
            "설계사가 막연하게 말하면 즉각 '근거가 뭔가요?', '통계 출처가 있나요?'라고 반박합니다. "
            "건보료 역산 공식이나 KOSIS 통계를 제시하면 신뢰합니다. "
            "답변은 2~3문장 이내로 고객 역할만 하세요."
        ),
        "opener": "'3천만 원이 부족하다고 하셨는데, 그 기준이 뭔가요? 정확한 근거가 있나요?'",
        "nhi": 210_000,
        "cancer_amt": "3천만 원",
    },
    {
        "type": "가격 민감형",
        "emoji": "💸",
        "desc": "매달 보험료 부담이 크다고 느끼며, 추가 가입에 저항감 강함",
        "system": (
            "당신은 보험료 부담을 크게 느끼는 38세 자영업자입니다. "
            "'매달 이것저것 빠져나가는 게 너무 많아요'라며 추가 비용에 강하게 저항합니다. "
            "하지만 '꼭 필요한 것만, 1순위만' 이라는 논리에는 마음이 열립니다. "
            "답변은 2~3문장 이내로 고객 역할만 하세요."
        ),
        "opener": "'보험료가 이미 너무 많아요. 솔직히 더 드는 건 좀 부담스럽고요.'",
        "nhi": 95_000,
        "cancer_amt": "5천만 원",
    },
    {
        "type": "가족 걱정형",
        "emoji": "👨‍👩‍👧",
        "desc": "본인보다 가족(배우자·자녀)을 위한 보험을 더 걱정함",
        "system": (
            "당신은 42세 가장으로, 본인 보험보다 가족 보험에 더 신경씁니다. "
            "'저보다 아이들 거나 아내 거 먼저 챙겨야 하지 않나요?'라고 합니다. "
            "본인이 쓰러졌을 때 가족 생계 유지와 연결 지어 설명하면 강하게 공감합니다. "
            "답변은 2~3문장 이내로 고객 역할만 하세요."
        ),
        "opener": "'제 보험보다 아이들 거나 아내 거 먼저 챙겨야 할 것 같은데요.'",
        "nhi": 165_000,
        "cancer_amt": "4천만 원",
    },
]

# ── 채점 키워드 (트리니티 핵심 3대 포인트 + 신뢰) ─────────────────────────────
_SCORE_RULES: dict[str, dict] = {
    "논리 전달력": {
        "weight": 35,
        "keywords": ["건보료", "건강보험료", "역산", "월소득", "소득", "추정"],
        "hint": "건보료 역산 공식(건보료 ÷ 0.0719 = 월소득)을 언급해보세요.",
    },
    "위기 강조": {
        "weight": 35,
        "keywords": ["2년", "24개월", "18개월", "1년", "치료 기간", "소득 공백", "생활비", "생계"],
        "hint": "치료 기간(암 2년, 뇌졸중 2년)과 그 기간의 생활비·소득 공백을 강조하세요.",
    },
    "상해장해 함정": {
        "weight": 15,
        "keywords": ["10%", "장해", "실질", "수령액", "3억", "5억", "1천만"],
        "hint": "10% 장해 시 실질 수령액(1억의 10% = 1,000만 원)을 들어 3~5억의 필요성을 강조하세요.",
    },
    "신뢰 구축": {
        "weight": 15,
        "keywords": ["kosis", "통계", "신용정보원", "국가", "데이터", "근거", "공식"],
        "hint": "KOSIS 통계 또는 신용정보원 자료를 근거로 들어 권위를 확보하세요.",
    },
}


def get_ai_customer_persona() -> dict:
    """랜덤 고객 페르소나 반환"""
    return random.choice(_PERSONAS)


def score_consultant_pitch(pitch: str) -> dict[str, dict]:
    """설계사 멘트에서 핵심 키워드 포함 여부 채점"""
    p = pitch.lower()
    result = {}
    for cat, cfg in _SCORE_RULES.items():
        matched = [kw for kw in cfg["keywords"] if kw.lower() in p]
        ratio = min(len(matched) / max(len(cfg["keywords"]) * 0.35, 1), 1.0)
        score = min(int(ratio * 100), 100)
        result[cat] = {
            "score": score,
            "weight": cfg["weight"],
            "matched": matched,
            "hint": cfg["hint"],
            "passed": len(matched) >= 1,
        }
    return result


def _get_llm_response(persona: dict, history: list[dict], user_pitch: str) -> str:
    """LLM 기반 페르소나 응답 생성 (실패 시 폴백 응답)"""
    try:
        from shared_components import get_env_secret
        import openai

        api_key  = get_env_secret("OPENAI_API_KEY") or get_env_secret("GEMINI_API_KEY", "")
        base_url = get_env_secret(
            "OPENAI_API_BASE",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        messages = [
            {
                "role": "system",
                "content": (
                    persona["system"]
                    + "\n\n[상황 설정] 고객의 월 건강보험료는 "
                    + f"{persona['nhi']:,}원이며, 현재 암진단비는 {persona['cancer_amt']} 가입 중입니다."
                    + "\n설명 없이 오직 고객 역할만 수행하세요."
                ),
            },
            *[{"role": m["role"], "content": m["content"]} for m in history],
            {"role": "user", "content": user_pitch},
        ]
        resp = client.chat.completions.create(
            model=st.session_state.get("model_name", "gemini-2.0-flash"),
            messages=messages,
            max_tokens=250,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        _fallback = {
            "회의적":      "음... 그 말이 맞긴 한데, 솔직히 아직도 잘 모르겠어요. 좀 더 구체적으로 설명해주실 수 있나요?",
            "걱정인형":    "그렇군요... 그럼 제일 급하게 필요한 게 뭔가요? 순서대로 좀 알려주세요.",
            "논리파":      "흥미로운 수치네요. 그 계산의 전제 조건이 뭔가요? 검증된 자료가 있나요?",
            "가격 민감형": "이해는 해요. 그런데 매달 얼마나 더 나가는 건가요?",
            "가족 걱정형": "저는 그렇다 쳐도, 아내랑 아이들은 어떻게 해야 할까요?",
        }
        return _fallback.get(persona.get("type", ""), "조금 더 자세히 설명해주시겠어요?")


def render_simulation_dashboard(compact: bool = False) -> None:
    """
    AI 상담 시뮬레이션 대시보드.

    Args:
        compact: True 이면 제목 크기를 줄여 좁은 레이아웃에 맞춤 (CRM용)
    """
    # ── 헤더 ──────────────────────────────────────────────────────────────────
    title_size = "0.95rem" if compact else "1.08rem"
    st.markdown(
        f"<div style='font-size:{title_size};font-weight:900;color:#1e3a8a;"
        "border-bottom:2px solid #1e3a8a;padding-bottom:6px;margin-bottom:10px;'>"
        "🎮 AI 상담 시나리오 시뮬레이터</div>",
        unsafe_allow_html=True,
    )

    # ── 세션 초기화 ────────────────────────────────────────────────────────────
    if "sim_persona" not in st.session_state:
        st.session_state["sim_persona"] = get_ai_customer_persona()
        st.session_state["sim_history"] = []
        st.session_state["sim_scores"]  = None

    persona = st.session_state["sim_persona"]

    # ── 페르소나 카드 ──────────────────────────────────────────────────────────
    _pc1, _pc2 = st.columns([7, 3])
    with _pc1:
        st.markdown(
            f"<div style='background:#eff6ff;border:1px dashed #000;"
            f"border-radius:8px;padding:9px 13px;'>"
            f"<b>📋 오늘의 가상 고객: {persona['emoji']} {persona['type']}형</b><br>"
            f"<span style='font-size:0.80rem;color:#374151;'>{persona['desc']}</span><br>"
            f"<span style='font-size:0.76rem;color:#6b7280;'>"
            f"💬 첫마디: <em>{persona['opener']}</em><br>"
            f"📌 건보료 {persona['nhi']:,}원 납부 중 / 암진단비 {persona['cancer_amt']} 보유</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with _pc2:
        if st.button("🎲 새 고객 뽑기", use_container_width=True, key="sim_new_persona"):
            st.session_state["sim_persona"] = get_ai_customer_persona()
            st.session_state["sim_history"] = []
            st.session_state["sim_scores"]  = None
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── 대화 히스토리 ─────────────────────────────────────────────────────────
    if st.session_state["sim_history"]:
        for msg in st.session_state["sim_history"]:
            if msg["role"] == "user":
                st.chat_message("user", avatar="🙋").write(msg["content"])
            else:
                st.chat_message("assistant", avatar=persona["emoji"]).write(msg["content"])
    else:
        st.chat_message("assistant", avatar=persona["emoji"]).write(
            f"{persona['type']}형 고객: {persona['opener']}"
        )

    # ── 입력 영역 ─────────────────────────────────────────────────────────────
    _inp_c, _btn_c = st.columns([7, 3])
    with _inp_c:
        user_pitch = st.text_area(
            "✍️ 설계사님의 멘트를 입력하세요:",
            placeholder=(
                "예: 고객님, 현재 건보료를 기준으로 역산하면 월소득이 약 500만 원입니다.\n"
                "암 치료 기간 2년간의 소득 공백을 채우려면 최소 1억 2천만 원이 필요합니다."
            ),
            height=95,
            key="sim_pitch_input",
        )
    with _btn_c:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # 힌트 버튼
        if st.button("💡 마스터의 힌트", use_container_width=True, key="sim_hint_btn"):
            st.session_state["sim_show_hint"] = True

        # 채점 버튼 (대화 이력 있을 때만 활성)
        _has_history = bool(st.session_state["sim_history"])
        if st.button(
            "📊 채점 보기",
            use_container_width=True,
            key="sim_score_btn",
            disabled=not _has_history,
        ):
            st.session_state["sim_show_score"] = True

        # 초기화 버튼
        if _has_history:
            if st.button("🔄 다시 시작", use_container_width=True, key="sim_reset_btn"):
                st.session_state["sim_history"] = []
                st.session_state["sim_scores"]  = None
                st.rerun()

    # ── 힌트 팝업 ─────────────────────────────────────────────────────────────
    if st.session_state.get("sim_show_hint"):
        with st.expander("💡 마스터의 힌트 — 트리니티 3대 핵심 포인트", expanded=True):
            for cat, cfg in _SCORE_RULES.items():
                st.markdown(f"- **{cat}**: {cfg['hint']}")
            # closing_engine 연계 힌트
            try:
                from closing_engine import _SPECIAL_TACTICS  # type: ignore
                st.divider()
                st.caption("🎯 필살 멘트 스니펫:")
                for item, tactic in list(_SPECIAL_TACTICS.items())[:2]:
                    st.markdown(f"**[{item}]** _{tactic[:60]}..._")
            except Exception:
                pass
        st.session_state["sim_show_hint"] = False

    # ── 전송 버튼 ─────────────────────────────────────────────────────────────
    if st.button(
        "🎤 AI 고객 반응 보기",
        type="primary",
        use_container_width=True,
        key="sim_send_btn",
    ):
        if not (user_pitch and user_pitch.strip()):
            st.warning("멘트를 입력해 주세요.")
        else:
            with st.spinner(
                f"AI {persona['emoji']} {persona['type']} 고객이 답변을 생각 중입니다..."
            ):
                ai_resp = _get_llm_response(
                    persona=persona,
                    history=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["sim_history"]
                    ],
                    user_pitch=user_pitch.strip(),
                )
            st.session_state["sim_history"].append(
                {"role": "user",      "content": user_pitch.strip()}
            )
            st.session_state["sim_history"].append(
                {"role": "assistant", "content": ai_resp}
            )
            st.session_state["sim_scores"] = score_consultant_pitch(user_pitch)
            st.rerun()

    # ── 채점 리포트 ───────────────────────────────────────────────────────────
    if st.session_state.get("sim_scores") or st.session_state.get("sim_show_score"):
        scores = st.session_state.get("sim_scores") or {}
        if scores:
            st.divider()
            st.markdown(
                "<b style='font-size:0.88rem;'>📝 마스터의 실시간 코칭 리포트</b>",
                unsafe_allow_html=True,
            )
            _sc_cols = st.columns(len(scores))
            total_weighted = 0.0
            for i, (cat, data) in enumerate(scores.items()):
                s      = data["score"]
                delta  = ("✅ " + ", ".join(data["matched"][:2])) if data["matched"] else "❌ 미감지"
                _sc_cols[i].metric(cat, f"{s}%", delta)
                total_weighted += s * data["weight"] / 100

            total = int(total_weighted)
            grade = "S" if total >= 85 else ("A" if total >= 70 else ("B" if total >= 55 else "C"))
            g_color = {
                "S": "#059669", "A": "#2563eb", "B": "#f59e0b", "C": "#dc2626"
            }[grade]

            st.markdown(
                f"<div style='background:#f8fafc;border:1px dashed #000;border-radius:8px;"
                f"padding:8px 14px;text-align:center;margin-top:6px;'>"
                f"<span style='font-size:0.82rem;font-weight:700;'>종합 점수: </span>"
                f"<span style='font-size:1.3rem;font-weight:900;color:{g_color};'>"
                f"{total}점 ({grade}등급)</span></div>",
                unsafe_allow_html=True,
            )

            missing = [(cat, d["hint"]) for cat, d in scores.items() if not d["passed"]]
            if missing:
                with st.expander("📌 개선 포인트", expanded=False):
                    for cat, hint in missing:
                        st.markdown(f"- **{cat}**: {hint}")

        st.session_state["sim_show_score"] = False
