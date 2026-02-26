# ==========================================================================
# customer_mgmt.py  — 고객 관리 탭 (Phase 1)
# 기능:
#   1. 고객 등록 / 프로필 보기
#   2. 상담 메모 입력 → PII Masking → Gemini NER 추출 → 프로필 누적
#   3. 미팅 전 브리핑 버튼 (Phase 2 준비 — 현재는 섹터만)
# ==========================================================================

import os
import re
import json
import hashlib
from datetime import datetime, date
from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# 암호화 헬퍼 — modules/auth.py의 encrypt_val/decrypt_val 재사용
# ---------------------------------------------------------------------------
def _get_enc_key() -> bytes:
    """암호화 키 조회 — 환경변수 우선, 없으면 secrets, 없으면 기본값."""
    key = os.environ.get("ENCRYPTION_KEY", "")
    if not key:
        try:
            import streamlit as _st
            key = _st.secrets.get("ENCRYPTION_KEY", "") or ""
        except Exception:
            key = ""
    if not key:
        return b"temporary_fixed_key_for_dev_only_12345="
    return key.encode() if isinstance(key, str) else key


def _enc(text: str) -> str:
    """실명 등 민감 정보 암호화. 실패 시 원문 반환 (가용성 우선)."""
    if not text:
        return text
    try:
        from cryptography.fernet import Fernet
        return Fernet(_get_enc_key()).encrypt(text.encode()).decode()
    except Exception:
        return text


def _dec(text: str) -> str:
    """암호화된 실명 복호화. 실패 시 원문 반환 (평문 저장 레거시 호환)."""
    if not text:
        return text
    try:
        from cryptography.fernet import Fernet
        return Fernet(_get_enc_key()).decrypt(text.encode()).decode()
    except Exception:
        return text  # 복호화 실패 시 원문(평문) 그대로 반환 — 레거시 호환

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
TABLE_CUSTOMERS  = "gk_customers"
TABLE_CONSULT    = "gk_consultation_logs"
TABLE_PII        = "gk_pii_mapping"

_RELATION_OPTIONS = ["본인", "배우자", "자녀1", "자녀2", "자녀3", "부모(부)", "부모(모)", "기타"]

# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _agent_uid() -> str:
    """현재 로그인 설계사 UID — session_state.user_id 기반"""
    return st.session_state.get("user_id", "GUEST")


def _make_code_name(agent_uid: str, sb) -> str:
    """고객 코드명 자동 생성: 고객0001, 고객0002 ..."""
    if not sb:
        return f"고객{hashlib.md5(os.urandom(4)).hexdigest()[:4].upper()}"
    try:
        r = (sb.table(TABLE_CUSTOMERS)
             .select("id")
             .eq("agent_uid", agent_uid)
             .execute())
        seq = len(r.data or []) + 1
        return f"고객{seq:04d}"
    except Exception:
        return f"고객{hashlib.md5(os.urandom(4)).hexdigest()[:4].upper()}"


# ---------------------------------------------------------------------------
# PII Masking / Unmasking
# ---------------------------------------------------------------------------

def build_pii_map(agent_uid: str, customer_id: int, sb) -> dict:
    """DB에서 실명→코드명 매핑 딕셔너리 반환 {복호화된 실명: 코드명}"""
    if not sb:
        return {}
    try:
        r = (sb.table(TABLE_PII)
             .select("real_name, code_name")
             .eq("agent_uid", agent_uid)
             .eq("customer_id", customer_id)
             .execute())
        return {_dec(row["real_name"]): row["code_name"] for row in (r.data or [])}
    except Exception:
        return {}


def mask_text(text: str, pii_map: dict) -> str:
    """실명 → 코드명 치환 (긴 이름 우선)"""
    for real, code in sorted(pii_map.items(), key=lambda x: -len(x[0])):
        text = text.replace(real, code)
    return text


def unmask_text(text: str, pii_map: dict) -> str:
    """코드명 → 실명 복원"""
    reverse = {v: k for k, v in pii_map.items()}
    for code, real in sorted(reverse.items(), key=lambda x: -len(x[0])):
        text = text.replace(code, real)
    return text


def save_pii_entry(agent_uid: str, customer_id: int,
                   real_name: str, code_name: str, relation: str, sb) -> bool:
    if not sb or not real_name.strip():
        return False
    try:
        _enc_name = _enc(real_name.strip())
        # unique 충돌 키는 암호화 전 해시로 관리
        _name_hash = hashlib.sha256(real_name.strip().encode()).hexdigest()[:32]
        sb.table(TABLE_PII).upsert(
            {"agent_uid": agent_uid, "customer_id": customer_id,
             "real_name": _enc_name,
             "name_hash": _name_hash,
             "code_name": code_name,
             "relation": relation},
            on_conflict="agent_uid,name_hash",
        ).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Supabase CRUD
# ---------------------------------------------------------------------------

def load_customers(agent_uid: str, sb) -> list:
    """고객 목록 반환 — name/phone 복호화 후 반환 (설계사에게 실명 표시)"""
    if not sb:
        return []
    try:
        r = (sb.table(TABLE_CUSTOMERS)
             .select("*")
             .eq("agent_uid", agent_uid)
             .order("created_at", desc=True)
             .execute())
        rows = r.data or []
        for row in rows:
            row["name"]  = _dec(row.get("name", ""))
            row["phone"] = _dec(row.get("phone", ""))
        return rows
    except Exception:
        return []


def save_customer(agent_uid: str, name: str, phone: str, sb) -> Optional[int]:
    """고객 등록 → 신규 id 반환 (name/phone 암호화 저장)"""
    if not sb:
        return None
    code_name = _make_code_name(agent_uid, sb)
    try:
        r = sb.table(TABLE_CUSTOMERS).insert({
            "agent_uid": agent_uid,
            "name":      _enc(name.strip()),
            "code_name": code_name,
            "phone":     _enc(phone.strip()) if phone.strip() else "",
            "profile":   {},
        }).execute()
        new_id = (r.data or [{}])[0].get("id")
        return new_id
    except Exception:
        return None


def update_profile(customer_id: int, profile_patch: dict, sb) -> bool:
    """고객 프로필 JSONB 누적 업데이트"""
    if not sb:
        return False
    try:
        cur = (sb.table(TABLE_CUSTOMERS)
               .select("profile")
               .eq("id", customer_id)
               .single()
               .execute())
        existing = (cur.data or {}).get("profile", {}) or {}
        # 배열 필드는 extend, 나머지는 덮어쓰기
        for k, v in profile_patch.items():
            if isinstance(v, list) and isinstance(existing.get(k), list):
                seen = {json.dumps(i, ensure_ascii=False) for i in existing[k]}
                for item in v:
                    if json.dumps(item, ensure_ascii=False) not in seen:
                        existing[k].append(item)
                        seen.add(json.dumps(item, ensure_ascii=False))
            else:
                existing[k] = v
        sb.table(TABLE_CUSTOMERS).update(
            {"profile": existing, "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", customer_id).execute()
        return True
    except Exception:
        return False


def save_consultation(agent_uid: str, customer_id: int,
                      memo_raw: str, memo_masked: str,
                      ner_result: dict, consult_date: str, sb) -> bool:
    if not sb:
        return False
    try:
        sb.table(TABLE_CONSULT).insert({
            "agent_uid": agent_uid,
            "customer_id": customer_id,
            "memo_raw": memo_raw,
            "memo_masked": memo_masked,
            "ner_result": ner_result,
            "consult_date": consult_date,
        }).execute()
        return True
    except Exception:
        return False


def load_consultations(customer_id: int, sb, limit: int = 10) -> list:
    if not sb:
        return []
    try:
        r = (sb.table(TABLE_CONSULT)
             .select("*")
             .eq("customer_id", customer_id)
             .order("consult_date", desc=True)
             .limit(limit)
             .execute())
        return r.data or []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Gemini NER 추출
# ---------------------------------------------------------------------------

_NER_SYSTEM = """당신은 보험 설계사를 돕는 초개인화 인텔리전스 비서입니다.
상담 메모(이미 실명이 코드명으로 치환된 상태)에서 아래 항목을 JSON으로 추출하세요.
출력은 반드시 아래 키만 포함한 순수 JSON이어야 합니다 (마크다운 금지).

{
  "family": [{"name":"코드명","relation":"관계","note":"메모"}],
  "health": [{"person":"코드명","condition":"질병/수술명","date":"언급날짜(YYYY-MM 또는 미상)"}],
  "life_events": [{"event":"이벤트명","person":"코드명","date":"날짜","note":""}],
  "interests": ["관심사1","관심사2"],
  "financial_concerns": ["경제적 고민1"],
  "icebreakers": ["다음 상담 시 아이스브레이킹 질문 1","질문 2","질문 3"]
}

없는 항목은 빈 배열로 두세요. icebreakers는 반드시 3개, 매우 자연스럽고 공감적인 톤으로."""


def run_ner_extraction(masked_memo: str, gemini_client) -> dict:
    """Gemini로 NER 추출 → dict 반환"""
    if not gemini_client or not masked_memo.strip():
        return {}
    try:
        from google.genai import types
        resp = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[masked_memo],
            config=types.GenerateContentConfig(
                system_instruction=_NER_SYSTEM,
                temperature=0.2,
            ),
        )
        raw = (resp.text or "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# 메인 렌더 함수 (app.py에서 호출)
# ---------------------------------------------------------------------------

def render_customer_tab(sb, gemini_client):
    """고객 관리 탭 전체 UI"""

    agent_uid = _agent_uid()

    st.markdown(
        "<h3 style='margin-bottom:0'>👥 고객 관리</h3>"
        "<p style='color:#94a3b8;font-size:0.85rem;margin-top:2px'>"
        "보험 설계사의 초개인화 인텔리전스 비서 — 고객을 기억하고, 다음 만남을 준비합니다.</p>",
        unsafe_allow_html=True,
    )

    tab_list, tab_new, tab_memo, tab_brief = st.tabs(
        ["📋 고객 목록", "➕ 고객 등록", "📝 상담 메모", "🎯 미팅 브리핑"]
    )

    # ── 탭 1: 고객 목록 ────────────────────────────────────────────────────
    with tab_list:
        customers = load_customers(agent_uid, sb)
        if not customers:
            st.info("등록된 고객이 없습니다. '➕ 고객 등록' 탭에서 추가하세요.")
        else:
            st.caption(f"총 {len(customers)}명 등록")
            for c in customers:
                with st.expander(
                    f"**{c['name']}** ({c['code_name']})  "
                    f"— {c.get('phone','') or '연락처 미등록'}",
                    expanded=False,
                ):
                    prof = c.get("profile") or {}
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**가족관계**")
                        for f in prof.get("family", []):
                            st.markdown(f"- {f.get('name','')} ({f.get('relation','')})"
                                        + (f": {f['note']}" if f.get('note') else ""))
                        st.markdown("**건강 이벤트**")
                        for h in prof.get("health", []):
                            st.markdown(f"- {h.get('person','')} / {h.get('condition','')} ({h.get('date','')})")
                    with col_b:
                        st.markdown("**라이프 이벤트**")
                        for e in prof.get("life_events", []):
                            st.markdown(f"- {e.get('event','')} ({e.get('person','')})")
                        st.markdown("**관심사**")
                        interests = prof.get("interests", [])
                        st.markdown(", ".join(interests) if interests else "—")
                        st.markdown("**경제적 고민**")
                        for fc in prof.get("financial_concerns", []):
                            st.markdown(f"- {fc}")
                    # 최근 상담 로그
                    logs = load_consultations(c["id"], sb, limit=3)
                    if logs:
                        st.markdown("**최근 상담 메모**")
                        for lg in logs:
                            st.markdown(
                                f"<div style='background:#1e293b;padding:8px 12px;"
                                f"border-radius:6px;font-size:0.82rem;margin-bottom:4px'>"
                                f"<span style='color:#94a3b8'>{lg['consult_date']}</span>　"
                                f"{lg.get('memo_raw','')[:120]}{'...' if len(lg.get('memo_raw',''))>120 else ''}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                            ner = lg.get("ner_result") or {}
                            icebreakers = ner.get("icebreakers", [])
                            if icebreakers:
                                st.markdown("💬 **아이스브레이킹 제안**")
                                for q in icebreakers:
                                    st.markdown(f"  - {q}")

    # ── 탭 2: 고객 등록 ────────────────────────────────────────────────────
    with tab_new:
        st.markdown("#### 신규 고객 등록")
        with st.form("form_new_customer", clear_on_submit=True):
            n_name  = st.text_input("고객 실명 *", placeholder="홍길동")
            n_phone = st.text_input("연락처", placeholder="010-0000-0000")
            st.markdown("**가족 구성원 PII 등록** (실명 → AI 전송 시 코드명으로 자동 치환)")
            st.caption("본인은 자동 등록됩니다. 가족이 있으면 추가하세요.")
            n_fam_cols = st.columns([2, 2, 2])
            n_fam1_name = n_fam_cols[0].text_input("가족1 이름", key="nf1n")
            n_fam1_rel  = n_fam_cols[1].selectbox("관계1", _RELATION_OPTIONS, key="nf1r")
            n_fam2_name = n_fam_cols[2].text_input("가족2 이름", key="nf2n")
            n_fam2_rel  = st.columns([2, 2, 2])[1].selectbox("관계2", _RELATION_OPTIONS, key="nf2r")

            submitted = st.form_submit_button("✅ 등록", type="primary", use_container_width=True)

        if submitted:
            if not n_name.strip():
                st.error("고객 실명을 입력하세요.")
            elif not sb:
                st.error("Supabase 연결 필요")
            else:
                cid = save_customer(agent_uid, n_name, n_phone, sb)
                if cid:
                    # 본인 PII 등록
                    code = (sb.table(TABLE_CUSTOMERS)
                            .select("code_name")
                            .eq("id", cid).single().execute()
                            .data or {}).get("code_name", "고객")
                    save_pii_entry(agent_uid, cid, n_name.strip(), code, "본인", sb)
                    # 가족 PII 등록
                    for fname, frel, fcode_suffix in [
                        (n_fam1_name, n_fam1_rel, "가족1"),
                        (n_fam2_name, n_fam2_rel, "가족2"),
                    ]:
                        if fname.strip():
                            save_pii_entry(agent_uid, cid, fname.strip(),
                                           f"{code}_{fcode_suffix}", frel, sb)
                    st.success(f"✅ {n_name} 고객 등록 완료 (코드명: {code})")
                    st.rerun()
                else:
                    st.error("등록 실패. Supabase 연결 상태를 확인하세요.")

    # ── 탭 3: 상담 메모 입력 ──────────────────────────────────────────────
    with tab_memo:
        st.markdown("#### 상담 메모 입력 → AI 인사이트 추출")
        customers = load_customers(agent_uid, sb)
        if not customers:
            st.info("먼저 고객을 등록하세요.")
        else:
            c_options = {f"{c['name']} ({c['code_name']})": c for c in customers}
            selected_label = st.selectbox("고객 선택", list(c_options.keys()),
                                          key="memo_customer_sel")
            sel_customer = c_options[selected_label]

            memo_date = st.date_input("상담 날짜", value=date.today(), key="memo_date")
            memo_text = st.text_area(
                "상담 메모 (자유 입력)",
                height=160,
                placeholder="오늘 상담에서 나눈 이야기를 자유롭게 입력하세요.\n"
                            "예: 딸 지민이가 독감으로 고생했다고 함. 어린이보험 보장 강화에 관심.",
                key="memo_text_input",
            )

            col_run, col_clr = st.columns([3, 1])
            run_btn = col_run.button("🔍 AI 인사이트 추출", type="primary",
                                     use_container_width=True, key="btn_run_ner")

            if run_btn:
                if not memo_text.strip():
                    st.error("메모를 입력하세요.")
                else:
                    pii_map = build_pii_map(agent_uid, sel_customer["id"], sb)
                    masked = mask_text(memo_text, pii_map)

                    with st.spinner("🤖 AI가 인사이트를 추출하는 중..."):
                        ner = run_ner_extraction(masked, gemini_client)

                    if not ner:
                        st.warning("추출 결과가 없습니다. 메모를 더 구체적으로 작성해 보세요.")
                    else:
                        # 코드명 → 실명 복원하여 표시
                        ner_display = json.loads(
                            unmask_text(json.dumps(ner, ensure_ascii=False), pii_map)
                        )

                        st.markdown("---")
                        st.markdown("#### 📊 추출된 인사이트")
                        col1, col2 = st.columns(2)
                        with col1:
                            if ner_display.get("family"):
                                st.markdown("**👨‍👩‍👧 가족관계**")
                                for f in ner_display["family"]:
                                    st.markdown(f"- {f.get('name','')} ({f.get('relation','')})"
                                                + (f": {f['note']}" if f.get("note") else ""))
                            if ner_display.get("health"):
                                st.markdown("**🏥 건강 이벤트**")
                                for h in ner_display["health"]:
                                    st.markdown(f"- {h.get('person','')} / {h.get('condition','')} ({h.get('date','')})")
                            if ner_display.get("life_events"):
                                st.markdown("**🎉 라이프 이벤트**")
                                for e in ner_display["life_events"]:
                                    st.markdown(f"- {e.get('event','')} ({e.get('person','')})")
                        with col2:
                            if ner_display.get("interests"):
                                st.markdown("**💡 관심사**")
                                for i in ner_display["interests"]:
                                    st.markdown(f"- {i}")
                            if ner_display.get("financial_concerns"):
                                st.markdown("**💰 경제적 고민**")
                                for fc in ner_display["financial_concerns"]:
                                    st.markdown(f"- {fc}")

                        if ner_display.get("icebreakers"):
                            st.markdown("---")
                            st.markdown("**💬 다음 상담 아이스브레이킹 제안**")
                            for idx, q in enumerate(ner_display["icebreakers"], 1):
                                st.markdown(
                                    f"<div style='background:#1e3a5f;padding:10px 14px;"
                                    f"border-left:3px solid #3b82f6;border-radius:4px;"
                                    f"margin-bottom:6px;font-size:0.88rem'>"
                                    f"{idx}. {q}</div>",
                                    unsafe_allow_html=True,
                                )

                        # 저장
                        saved_ok = save_consultation(
                            agent_uid, sel_customer["id"],
                            memo_text, masked, ner,
                            str(memo_date), sb,
                        )
                        if saved_ok:
                            update_profile(sel_customer["id"], ner, sb)
                            st.success("✅ 메모 저장 및 고객 프로필 업데이트 완료")
                        else:
                            st.warning("⚠️ Supabase 저장 실패 (연결 확인 필요). 인사이트는 위에 표시됩니다.")

    # ── 탭 4: 미팅 브리핑 (Phase 2 준비) ──────────────────────────────────
    with tab_brief:
        st.markdown("#### 🎯 미팅 전 브리핑")
        st.info(
            "**준비 중 (Phase 2)**\n\n"
            "고객 데이터가 충분히 쌓이면 활성화됩니다.\n"
            "미팅 1시간 전, 해당 고객의 감성 데이터를 기반으로 "
            "AI가 맞춤 브리핑을 생성합니다.",
            icon="⏳",
        )
        customers = load_customers(agent_uid, sb)
        if customers:
            st.markdown("---")
            st.caption("미리 보기 — 고객을 선택하면 현재까지 쌓인 프로필을 요약합니다.")
            b_options = {f"{c['name']} ({c['code_name']})": c for c in customers}
            b_label = st.selectbox("고객 선택", list(b_options.keys()), key="brief_sel")
            b_cust  = b_options[b_label]
            if st.button("📋 현재 프로필 요약 보기", key="btn_brief_preview"):
                prof = b_cust.get("profile") or {}
                logs = load_consultations(b_cust["id"], sb, limit=5)
                summary_parts = []
                if prof.get("health"):
                    summary_parts.append(
                        "건강: " + ", ".join(
                            f"{h['person']} {h['condition']}" for h in prof["health"]
                        )
                    )
                if prof.get("life_events"):
                    summary_parts.append(
                        "이벤트: " + ", ".join(e["event"] for e in prof["life_events"])
                    )
                if prof.get("interests"):
                    summary_parts.append("관심사: " + ", ".join(prof["interests"]))
                if summary_parts:
                    st.markdown(
                        f"<div style='background:#1e293b;padding:14px 18px;"
                        f"border-radius:8px;font-size:0.9rem;line-height:1.7'>"
                        + "<br>".join(f"• {p}" for p in summary_parts)
                        + f"</div>",
                        unsafe_allow_html=True,
                    )
                    last_icebreakers = []
                    for lg in logs:
                        icebreakers = (lg.get("ner_result") or {}).get("icebreakers", [])
                        if icebreakers:
                            last_icebreakers = icebreakers
                            break
                    if last_icebreakers:
                        st.markdown("**💬 최근 추천 아이스브레이킹**")
                        for q in last_icebreakers:
                            st.markdown(f"- {q}")
                else:
                    st.info("아직 쌓인 프로필 데이터가 없습니다. 상담 메모를 입력하면 채워집니다.")

    # ── 긴급 데이터 파기 섹터 (본인 데이터 전용) ──────────────────────────
    _my_name = st.session_state.get("user_name", agent_uid)
    st.markdown("---")
    st.markdown(
        "<div style='background:#1a0000;border:2px solid #ef4444;border-radius:10px;"
        "padding:12px 16px;margin-top:8px'>"
        "<span style='color:#ef4444;font-weight:900;font-size:0.9rem;'>🚨 긴급 데이터 파기</span>"
        f"<span style='color:#fca5a5;font-size:0.78rem;margin-left:10px;'>"
        f"보안 위협 감지 시 — <b>{_my_name}</b> 본인의 고객 데이터만 삭제됩니다. "
        f"다른 설계사 데이터에는 영향 없음.</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    with st.expander("⚠️ 긴급 파기 실행 (클릭하여 열기)", expanded=False):
        st.warning(
            "**이 작업은 되돌릴 수 없습니다.**\n\n"
            "현재 로그인된 설계사의 **모든 고객 정보, 상담 메모, PII 매핑**이 "
            "Supabase DB에서 영구 삭제됩니다.\n\n"
            "보안 위협이 확실한 경우에만 실행하세요."
        )
        _confirm_text = st.text_input(
            "확인 문구 입력 (정확히 입력: **파기확인**)",
            key="emergency_purge_confirm",
            placeholder="파기확인",
        )
        _purge_btn = st.button(
            "🔴 지금 즉시 모든 고객 데이터 파기",
            key="btn_emergency_purge",
            type="primary",
            use_container_width=True,
        )
        if _purge_btn:
            if _confirm_text.strip() != "파기확인":
                st.error("❌ 확인 문구가 다릅니다. '파기확인'을 정확히 입력하세요.")
            elif not sb:
                st.error("Supabase 연결 필요")
            else:
                # ── 최종 경고 확인 단계 ──
                if not st.session_state.get("_purge_step2"):
                    st.session_state["_purge_step2"] = True
                    st.rerun()

                st.markdown(
                    "<div style='background:#7f1d1d;border:2px solid #ef4444;"
                    "border-radius:10px;padding:16px 18px;margin:10px 0'>"
                    "<div style='color:#fca5a5;font-size:1rem;font-weight:900;"
                    "margin-bottom:8px;'>⚠️ 최종 확인</div>"
                    "<div style='color:#fecaca;font-size:0.88rem;line-height:1.7;'>"
                    "파기 버튼 실행이 맞습니까?<br>"
                    "<b>고객 정보는 완전 파기되며 회복 불가능합니다.</b><br>"
                    f"대상: {agent_uid} 의 전체 고객 데이터"
                    "</div></div>",
                    unsafe_allow_html=True,
                )
                _col_yes, _col_no = st.columns(2)
                with _col_yes:
                    if st.button("🔴 예, 즉시 파기합니다", key="btn_purge_yes",
                                 type="primary", use_container_width=True):
                        try:
                            _del_uid = agent_uid
                            sb.table(TABLE_PII).delete().eq("agent_uid", _del_uid).execute()
                            sb.table(TABLE_CONSULT).delete().eq("agent_uid", _del_uid).execute()
                            sb.table(TABLE_CUSTOMERS).delete().eq("agent_uid", _del_uid).execute()
                            st.session_state.pop("_purge_step2", None)
                            st.session_state.pop("memo_customer_sel", None)
                            st.session_state.pop("brief_sel", None)
                            st.success(
                                f"✅ 파기 완료\n\n"
                                f"삭제 시각: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
                                "모든 고객 데이터가 영구 삭제되었습니다. 복구 불가능합니다."
                            )
                        except Exception as _pe:
                            st.error(f"파기 중 오류: {_pe}")
                with _col_no:
                    if st.button("⬅️ 취소", key="btn_purge_no",
                                 use_container_width=True):
                        st.session_state.pop("_purge_step2", None)
                        st.rerun()
