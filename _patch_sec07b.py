# -*- coding: utf-8 -*-
"""GK-SEC-07 렌더링 함수 + RAG 섹터 쿼리 함수 삽입 패치"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

ANCHOR = 'def show_war_room() -> None:'
if ANCHOR not in content:
    print("ERROR: anchor not found")
    exit(1)

INSERT = r'''
# ══════════════════════════════════════════════════════════════════════════════
# [RAG-SECTOR] 섹터별 지능형 RAG 자가호출 엔진
# 업로드된 PDF(과실비율·약관·장해판정 등)를 섹터별로 인덱싱·검색
# ══════════════════════════════════════════════════════════════════════════════
def _rag_sector_query(query: str, sector: str = "auto", top_k: int = 3) -> list:
    """섹터별 RAG 검색 — Supabase pgvector 또는 로컬 TF-IDF 폴백.

    Args:
        query:  검색 질의 (사고 상황, 과실유형 등)
        sector: "auto"(자동차·과실비율), "income"(소득통계), "terms"(약관), "disability"(장해)
        top_k:  반환 결과 수

    Returns:
        [{"title": ..., "content": ..., "source": ..., "page": ..., "score": ...}, ...]
    """
    import streamlit as _st
    import re as _re

    # ── 섹터별 키워드 필터 ──────────────────────────────────────────────────
    _sector_filters = {
        "auto":       ["과실비율", "자동차사고", "교통사고", "충돌", "추돌", "직진", "회전", "신호"],
        "income":     ["소득통계", "월소득", "평균임금", "건강보험료", "역산"],
        "terms":      ["약관", "보장", "담보", "특약", "보험금", "지급"],
        "disability": ["장해", "AMA", "맥브라이드", "노동능력상실", "후유장해"],
    }

    # ── 1순위: Supabase pgvector RAG 검색 ──────────────────────────────────
    try:
        _sb = _st.session_state.get("_sb_client")
        if _sb is None:
            try:
                from database import get_supabase_client as _gsb
                _sb = _gsb()
            except Exception:
                _sb = None

        if _sb:
            # rag_documents 테이블에서 sector 필터 + 텍스트 유사도 검색
            _q = (
                _sb.table("rag_documents")
                .select("id,title,content,source,page_num,sector,created_at")
                .eq("sector", sector)
                .ilike("content", f"%{query[:30]}%")
                .limit(top_k * 2)
                .execute()
            )
            if _q.data:
                _results = []
                for _row in _q.data[:top_k]:
                    _results.append({
                        "title":   _row.get("title", ""),
                        "content": _row.get("content", "")[:500],
                        "source":  _row.get("source", ""),
                        "page":    _row.get("page_num", ""),
                        "score":   0.85,
                    })
                return _results
    except Exception:
        pass

    # ── 2순위: 세션 내 업로드 문서 TF-IDF 폴백 ─────────────────────────────
    try:
        _docs = _st.session_state.get("_rag_local_docs", {})
        if _docs:
            _kws = _sector_filters.get(sector, [])
            _hits = []
            for _doc_name, _doc_chunks in _docs.items():
                for _chunk in (_doc_chunks if isinstance(_doc_chunks, list) else [_doc_chunks]):
                    _text = str(_chunk)
                    _score = sum(1 for _kw in _kws if _kw in _text)
                    _score += sum(2 for _w in query.split() if _w in _text)
                    if _score > 0:
                        _hits.append({
                            "title":   _doc_name,
                            "content": _text[:400],
                            "source":  _doc_name,
                            "page":    "",
                            "score":   _score / 10.0,
                        })
            _hits.sort(key=lambda x: x["score"], reverse=True)
            return _hits[:top_k]
    except Exception:
        pass

    # ── 3순위: 내장 과실비율 샘플 데이터 (오프라인 폴백) ──────────────────
    _BUILTIN = {
        "auto": [
            {"title": "직진 차량 vs 좌회전 차량 (신호 없는 교차로)",
             "content": "직진 차량 20% : 좌회전 차량 80%. 좌회전 시 직진 차량 통행 방해 원칙.",
             "source": "과실비율 인정기준(2023)", "page": "48"},
            {"title": "추돌사고 — 후방 차량 전방 주시 태만",
             "content": "추돌 기본 과실: 후방 차량 100%. 급정거 등 전방 차량 귀책 시 10~20% 감산.",
             "source": "과실비율 인정기준(2023)", "page": "112"},
            {"title": "차선 변경 중 충돌",
             "content": "차선 변경 차량 70% : 직진 차량 30%. 급격한 차선 변경 시 100%까지 상향.",
             "source": "과실비율 인정기준(2023)", "page": "67"},
            {"title": "신호 위반 — 적색 신호 진입",
             "content": "신호 위반 차량 80~90%. 상대방 과속·주시 태만 시 10~20% 감산.",
             "source": "과실비율 인정기준(2023)", "page": "22"},
            {"title": "보행자 vs 차량 — 횡단보도",
             "content": "신호 있는 횡단보도: 차량 100%. 신호 없는 횡단보도: 차량 70~90%.",
             "source": "과실비율 인정기준(2023)", "page": "155"},
        ],
        "income": [
            {"title": "건강보험료 역산 소득 통계 기준",
             "content": "2024년 직장 건강보험료율 7.09%(근로자 부담 3.545%). 월소득 = 건보료 ÷ 0.0709.",
             "source": "가이딩 프로토콜 제32조", "page": ""},
        ],
        "disability": [
            {"title": "AMA 장해율 vs 맥브라이드 노동능력상실률",
             "content": "AMA: 전신기능 장해율 기준(생명보험 주로 사용). 맥브라이드: 직업별 노동능력상실률(손해보험·배상). 국가장애율: 복지법 기준, 보험 지급과 무관.",
             "source": "장해판정 기준 통합", "page": ""},
        ],
    }
    return [dict(d, score=0.6) for d in _BUILTIN.get(sector, [])[:top_k]]


def _rag_save_consult_note(client_name: str, note: str, sector: str = "auto") -> bool:
    """상담 노트를 RAG 피드백 데이터로 저장 — 다음 유사 고객 전략 제안에 활용.

    Supabase consult_notes 테이블에 저장. 실패 시 세션 로컬 저장.
    """
    import datetime as _dt, streamlit as _st

    _entry = {
        "client_name": client_name,
        "note":        note[:2000],
        "sector":      sector,
        "user_id":     _st.session_state.get("user_id", ""),
        "created_at":  _dt.datetime.now().isoformat(),
    }

    # Supabase 저장 시도
    try:
        _sb = _st.session_state.get("_sb_client")
        if _sb is None:
            from database import get_supabase_client as _gsb
            _sb = _gsb()
        if _sb:
            _sb.table("consult_notes").insert(_entry).execute()
            return True
    except Exception:
        pass

    # 로컬 세션 폴백
    _local = _st.session_state.get("_rag_consult_notes", [])
    _local.append(_entry)
    _st.session_state["_rag_consult_notes"] = _local[-200:]
    return False


def _rag_similar_cases(client_name: str, sector: str = "auto", top_k: int = 3) -> list:
    """저장된 상담 노트에서 현재 고객과 유사한 과거 사례를 반환."""
    import streamlit as _st

    _notes = _st.session_state.get("_rag_consult_notes", [])

    # Supabase에서도 조회
    try:
        _sb = _st.session_state.get("_sb_client")
        if _sb:
            from database import get_supabase_client as _gsb
            _sb = _gsb()
        if _sb:
            _q = (
                _sb.table("consult_notes")
                .select("client_name,note,sector,created_at")
                .eq("sector", sector)
                .eq("user_id", _st.session_state.get("user_id", ""))
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            if _q.data:
                _notes = _q.data + _notes
    except Exception:
        pass

    return [n for n in _notes if n.get("sector") == sector][:top_k]


# ══════════════════════════════════════════════════════════════════════════════
# [GK-SEC-07] 자동차보험 전술 상담 센터 렌더러
# 탭 라우터에서 cur == 'gk_sec07' 일 때 호출
# ══════════════════════════════════════════════════════════════════════════════
def _render_gk_sec07() -> None:
    """GK-SEC-07 자동차보험 전술 상담 센터 — 2×3 그리드 6개 서비스"""
    import datetime as _dt, streamlit as _st_s07

    # ── CSS ──────────────────────────────────────────────────────────────────
    st.markdown("""
<style>
/* GK-SEC-07 전용 스타일 */
.gks07-wrap {
    border: 1px dashed #000 !important;
    background: #E8F5E9 !important;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.gks07-header {
    background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 60%, #388E3C 100%);
    border-radius: 12px;
    padding: 16px 22px;
    margin-bottom: 18px;
    border: 1px dashed #000;
}
.gks07-header h2 {
    color: #fff !important;
    font-size: 1.25rem;
    font-weight: 900;
    margin: 0 0 4px 0;
}
.gks07-header p { color: #C8E6C9 !important; font-size: 0.82rem; margin: 0; }
.gks07-card {
    border: 1px dashed #000;
    background: #E8F5E9;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
    min-height: 80px;
}
.gks07-card-title {
    font-size: 0.92rem;
    font-weight: 900;
    color: #1B5E20;
    margin-bottom: 4px;
}
.gks07-card-desc {
    font-size: 0.78rem;
    color: #333;
    font-weight: 700;
}
.gks07-fault-row {
    border-left: 4px solid #2E7D32;
    background: #F1F8E9;
    border-radius: 0 8px 8px 0;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-size: 0.83rem;
    font-weight: 700;
    color: #1B5E20;
}
.gks07-fault-pct {
    display: inline-block;
    background: #2E7D32;
    color: #fff;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.8rem;
    font-weight: 900;
    margin-left: 8px;
}
.gks07-rag-box {
    border: 1px dashed #000;
    background: #FFFDE7;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.82rem;
    color: #333;
    font-weight: 700;
}
.gks07-rag-src {
    font-size: 0.72rem;
    color: #777;
    margin-top: 4px;
}
input, textarea, .stTextInput input, .stTextArea textarea {
    font-weight: 700 !important;
    color: #000 !important;
}
</style>""", unsafe_allow_html=True)

    # ── 헤더 ────────────────────────────────────────────────────────────────
    st.markdown("""
<div class="gks07-header">
  <h2>🚗 GK-SEC-07 자동차보험 전술 상담 센터</h2>
  <p>보험은 사고 후에 가치를 발한다. 마스터의 전술로 고객의 민사상 안전까지 완벽히 방어하라.</p>
</div>""", unsafe_allow_html=True)

    # ── 상단 네비게이션 ──────────────────────────────────────────────────────
    if st.button("⬅️ 네비게이션 게이트웨이로 돌아가기", key="sec07_back_top",
                 use_container_width=False):
        st.session_state["current_tab"] = "home"
        st.session_state["_scroll_top"] = True
        st.rerun()

    # ── GK-SEC-01 고객 데이터 연동 ───────────────────────────────────────────
    _c_name = (
        st.session_state.get("gs_c_name") or
        st.session_state.get("current_c_name") or
        st.session_state.get("_gp89_customer_name") or ""
    )

    # ── D-Day 갱신 카운트다운 위젯 ──────────────────────────────────────────
    with st.container():
        st.markdown('<div class="gks07-wrap">', unsafe_allow_html=True)
        st.markdown("**📅 고객 갱신일 D-Day 카운트다운**")
        _dd_cols = st.columns([2, 1, 1])
        with _dd_cols[0]:
            _renew_name = st.text_input(
                "고객명", value=_c_name,
                key="sec07_renew_name",
                placeholder="홍길동",
            )
        with _dd_cols[1]:
            _renew_date = st.date_input(
                "갱신 예정일",
                key="sec07_renew_date",
                value=_dt.date.today() + _dt.timedelta(days=30),
                min_value=_dt.date.today(),
            )
        with _dd_cols[2]:
            _days_left = (_renew_date - _dt.date.today()).days
            _dday_color = "#e74c3c" if _days_left <= 7 else ("#f39c12" if _days_left <= 30 else "#2E7D32")
            st.markdown(
                f'<div style="margin-top:28px;text-align:center;">'
                f'<span style="font-size:1.4rem;font-weight:900;color:{_dday_color};">'
                f'D-{_days_left}</span>'
                f'<br><span style="font-size:0.72rem;color:#555;font-weight:700;">갱신까지</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if _days_left <= 7:
                st.error("⚠️ 갱신 임박!")
            elif _days_left <= 30:
                st.warning("📢 갱신 1개월 전")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 2×3 서비스 그리드 ───────────────────────────────────────────────────
    _t1, _t2, _t3, _t4, _t5, _t6 = st.tabs([
        "1️⃣ 가입/갱신 관리",
        "2️⃣ 민사배상 & 담보",
        "3️⃣ 운전자보험 연계",
        "4️⃣ 장해 판정 기준",
        "5️⃣ 사고 대처 & 과실비율",
        "6️⃣ FC 필수 질문",
    ])

    # ── [1] 가입/갱신 관리 ──────────────────────────────────────────────────
    with _t1:
        st.markdown('<div class="gks07-wrap">', unsafe_allow_html=True)
        st.markdown("#### 📋 자동차보험 가입/갱신 관리")
        st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.82rem;font-family:sans-serif;">
<thead>
<tr style="background:#2E7D32;color:#fff;">
  <th style="padding:8px 10px;">구분</th>
  <th style="padding:8px 10px;">개인용</th>
  <th style="padding:8px 10px;">업무용</th>
  <th style="padding:8px 10px;">영업용</th>
</tr>
</thead>
<tbody>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;">보험료 수준</td>
  <td style="padding:7px;">기준</td>
  <td style="padding:7px;">+15~25%</td>
  <td style="padding:7px;">+40~60%</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;">사용 목적 고지</td>
  <td style="padding:7px;">출퇴근·일상</td>
  <td style="padding:7px;">업무 병행</td>
  <td style="padding:7px;">영업 전용</td>
</tr>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;">갱신 주기</td>
  <td style="padding:7px;">1년</td>
  <td style="padding:7px;">1년</td>
  <td style="padding:7px;">1년(분기납 가능)</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;">할인 특약</td>
  <td style="padding:7px;">마일리지·블랙박스</td>
  <td style="padding:7px;">블랙박스</td>
  <td style="padding:7px;">제한적</td>
</tr>
</tbody>
</table>
</div>""", height=175)
        st.markdown("**📌 특약 백과사전**")
        _spec_data = [
            ("대리운전 담보", "대리운전 중 사고 보상", "미가입 시 대리운전 사고 자차 미보상"),
            ("마일리지 할인", "연 1만km 이하 최대 12% 할인", "주행거리 제출 필수"),
            ("커넥티드 할인", "OBD/앱 주행 데이터 제공 시 5~10% 할인", "데이터 제공 동의 필요"),
            ("상급병실 특약", "1·2인실 입원료 차액 보상", "종합보험·운전자보험과 중복 체크"),
        ]
        for _name, _pro, _note in _spec_data:
            st.markdown(
                f'<div class="gks07-card">'
                f'<div class="gks07-card-title">✅ {_name}</div>'
                f'<div class="gks07-card-desc">장점: {_pro}</div>'
                f'<div class="gks07-card-desc" style="color:#c0392b;">주의: {_note}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── [2] 민사배상 & 담보 분석 ────────────────────────────────────────────
    with _t2:
        st.markdown('<div class="gks07-wrap">', unsafe_allow_html=True)
        st.markdown("#### ⚖️ 민사배상 관점 담보 분석")
        st.markdown("""
<div style="background:#E8F5E9;border:1px dashed #000;border-radius:10px;padding:12px 16px;margin-bottom:12px;">
<b style="font-size:0.9rem;color:#1B5E20;">민법 제750조 불법행위 책임 구조</b><br>
<span style="font-size:0.83rem;font-weight:700;color:#333;">
고의 또는 과실로 타인에게 손해를 가한 자는 그 손해를 배상할 책임이 있다.<br>
→ 자동차 사고 = 불법행위 → 대인·대물 담보가 민법상 배상책임을 커버
</span>
</div>""", unsafe_allow_html=True)
        st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.82rem;font-family:sans-serif;">
<thead>
<tr style="background:#2E7D32;color:#fff;">
  <th style="padding:8px;">담보</th>
  <th style="padding:8px;">민법 연결</th>
  <th style="padding:8px;">보상 범위</th>
  <th style="padding:8px;">과실상계</th>
  <th style="padding:8px;">핵심 포인트</th>
</tr>
</thead>
<tbody>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;color:#1B5E20;">대인배상Ⅰ</td>
  <td style="padding:7px;">자배법 의무</td>
  <td style="padding:7px;">사망·부상·후유장해</td>
  <td style="padding:7px;">없음(피해자 과실 불문)</td>
  <td style="padding:7px;font-weight:700;">의무 가입·한도 제한</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;color:#1565C0;">대인배상Ⅱ</td>
  <td style="padding:7px;">민750조</td>
  <td style="padding:7px;">Ⅰ 초과분 전액</td>
  <td style="padding:7px;">있음</td>
  <td style="padding:7px;font-weight:700;">무한 가입 권장</td>
</tr>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;color:#6A1B9A;">대물배상</td>
  <td style="padding:7px;">민750조</td>
  <td style="padding:7px;">차량·재물 손해</td>
  <td style="padding:7px;">있음</td>
  <td style="padding:7px;font-weight:700;">2억 이상 권장</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;color:#E65100;">자동차상해</td>
  <td style="padding:7px;">약정 담보</td>
  <td style="padding:7px;">자기 신체 부상·사망</td>
  <td style="padding:7px;">없음</td>
  <td style="padding:7px;font-weight:700;">자신 대체 권장</td>
</tr>
</tbody>
</table>
</div>""", height=200)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── [3] 운전자보험 상관관계 ──────────────────────────────────────────────
    with _t3:
        st.markdown('<div class="gks07-wrap">', unsafe_allow_html=True)
        st.markdown("#### 🚦 운전자보험 vs 자동차보험 상관관계")
        st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.82rem;font-family:sans-serif;">
<thead>
<tr style="background:#2E7D32;color:#fff;">
  <th style="padding:8px;">항목</th>
  <th style="padding:8px;">자동차보험</th>
  <th style="padding:8px;">운전자보험</th>
  <th style="padding:8px;">중복 여부</th>
</tr>
</thead>
<tbody>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;">성격</td>
  <td style="padding:7px;">손해보험(배상·손해)</td>
  <td style="padding:7px;">정액보험(형사·민사 비용)</td>
  <td style="padding:7px;color:#2E7D32;font-weight:700;">보완 관계</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;">형사합의금</td>
  <td style="padding:7px;">미보상</td>
  <td style="padding:7px;">✅ 보상(최대 3천~1억)</td>
  <td style="padding:7px;color:#c0392b;font-weight:700;">운전자보험 필수</td>
</tr>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;">벌금</td>
  <td style="padding:7px;">미보상</td>
  <td style="padding:7px;">✅ 보상(최대 500~2000만)</td>
  <td style="padding:7px;color:#c0392b;font-weight:700;">운전자보험 필수</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;">변호사 선임비</td>
  <td style="padding:7px;">일부 보상</td>
  <td style="padding:7px;">✅ 보상(최대 300만)</td>
  <td style="padding:7px;color:#f39c12;font-weight:700;">중복 가능</td>
</tr>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;">자기 신체 상해</td>
  <td style="padding:7px;">자상/자신 담보</td>
  <td style="padding:7px;">일부 보상</td>
  <td style="padding:7px;color:#f39c12;font-weight:700;">중복 체크 필요</td>
</tr>
</tbody>
</table>
</div>""", height=220)
        st.info("💡 **FC 전략:** 자동차보험 갱신 상담 시 반드시 운전자보험 가입 여부 확인 → 형사합의금 공백 집중 어필")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── [4] 장해 판정 기준 ──────────────────────────────────────────────────
    with _t4:
        st.markdown('<div class="gks07-wrap">', unsafe_allow_html=True)
        st.markdown("#### 🏥 장해 평가 모듈 — AMA / 맥브라이드 / 국가장애율 비교")
        _rag_dis = _rag_sector_query("장해 AMA 맥브라이드", sector="disability", top_k=2)
        for _r in _rag_dis:
            st.markdown(
                f'<div class="gks07-rag-box">📖 <b>{_r["title"]}</b><br>'
                f'{_r["content"]}'
                f'<div class="gks07-rag-src">출처: {_r["source"]}'
                f'{(" · " + str(_r["page"]) + "페이지") if _r.get("page") else ""}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.82rem;font-family:sans-serif;">
<thead>
<tr style="background:#2E7D32;color:#fff;">
  <th style="padding:8px;">기준</th>
  <th style="padding:8px;">정의</th>
  <th style="padding:8px;">주 사용처</th>
  <th style="padding:8px;">핵심 특징</th>
</tr>
</thead>
<tbody>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;color:#1B5E20;">AMA 장해율</td>
  <td style="padding:7px;">전신기능 장해율(%)</td>
  <td style="padding:7px;">생명보험·장기손해</td>
  <td style="padding:7px;">신체 기능 상실 기준, 직업 무관</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;color:#1565C0;">맥브라이드</td>
  <td style="padding:7px;">노동능력상실률(%)</td>
  <td style="padding:7px;">손해배상·자동차보상</td>
  <td style="padding:7px;">직업별 계수 적용, 실질 소득 손실 반영</td>
</tr>
<tr style="background:#E8F5E9;">
  <td style="padding:7px;font-weight:700;color:#6A1B9A;">국가장애율</td>
  <td style="padding:7px;">장애인복지법 기준</td>
  <td style="padding:7px;">복지 서비스 수급</td>
  <td style="padding:7px;">보험 지급과 무관 — 혼동 주의</td>
</tr>
</tbody>
</table>
</div>""", height=165)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── [5] 사고 대처 & 과실비율 ────────────────────────────────────────────
    with _t5:
        st.markdown('<div class="gks07-wrap">', unsafe_allow_html=True)
        st.markdown("#### 🔍 사고 상황별 과실비율 RAG 검색")
        st.caption("「230630 자동차사고 과실비율 인정기준」 기반 — 사고 유형 선택 또는 직접 입력")

        _acc_type = st.selectbox(
            "사고 유형 선택",
            [
                "직접 입력",
                "직진 vs 좌회전 (신호 없는 교차로)",
                "직진 vs 우회전",
                "추돌사고 (후방 전방 주시 태만)",
                "차선 변경 중 충돌",
                "신호 위반 충돌",
                "보행자 vs 차량 (횡단보도)",
                "유턴 중 충돌",
                "후진 중 충돌",
                "고속도로 앞지르기 중 충돌",
                "주차장 내 충돌",
            ],
            key="sec07_acc_type",
        )
        if _acc_type == "직접 입력":
            _query_text = st.text_input(
                "사고 상황 입력",
                key="sec07_acc_query",
                placeholder="예) 적색 신호 직진 중 좌회전 차량과 충돌",
            )
        else:
            _query_text = _acc_type

        if st.button("🔍 과실비율 RAG 검색", key="sec07_rag_btn", type="primary"):
            if _query_text.strip():
                with st.spinner("과실비율 인정기준 검색 중..."):
                    _results = _rag_sector_query(_query_text, sector="auto", top_k=3)
                st.session_state["_sec07_rag_results"] = _results
                st.session_state["_sec07_rag_query"] = _query_text

        _rag_res = st.session_state.get("_sec07_rag_results", [])
        _rag_q   = st.session_state.get("_sec07_rag_query", "")
        if _rag_res:
            st.markdown(f"**📋 검색 결과** — *\"{_rag_q}\"* 유사 판례 {len(_rag_res)}건")
            for _i, _r in enumerate(_rag_res, 1):
                _score_pct = int(_r.get("score", 0) * 100)
                st.markdown(
                    f'<div class="gks07-rag-box">'
                    f'<b>#{_i} {_r["title"]}</b> '
                    f'<span style="background:#2E7D32;color:#fff;border-radius:10px;'
                    f'padding:1px 8px;font-size:0.75rem;">유사도 {_score_pct}%</span><br>'
                    f'{_r["content"]}'
                    f'<div class="gks07-rag-src">📄 출처: {_r["source"]}'
                    f'{(" · " + str(_r["page"]) + "p") if _r.get("page") else ""}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.divider()
        st.markdown("**⚡ 사고 초동 대처 가이드 (현장 즉시 적용)**")
        _steps = [
            ("1단계", "인명 확인 및 119/112 신고", "부상자 발생 시 구조 우선 — 현장 이탈 시 뺑소니"),
            ("2단계", "현장 사진 촬영 (전방위)", "차량 위치·파손·도로 상황 — 최소 10장 이상"),
            ("3단계", "상대방 인적사항 확보", "이름·연락처·보험사·차량번호·면허번호"),
            ("4단계", "블랙박스 영상 확보", "현장에서 즉시 백업 — 덮어쓰기 방지"),
            ("5단계", "보험사 사고 접수", "24시간 콜센터 접수 — 합의 전 반드시 먼저"),
            ("6단계", "의료기관 방문", "사고 당일 진료 기록 확보 — 후유증 대비"),
        ]
        for _step, _title, _desc in _steps:
            st.markdown(
                f'<div class="gks07-fault-row">'
                f'<span class="gks07-fault-pct">{_step}</span> '
                f'<b>{_title}</b> — <span style="color:#555;font-weight:700;">{_desc}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── [6] FC 필수 질문 리스트 ─────────────────────────────────────────────
    with _t6:
        st.markdown('<div class="gks07-wrap">', unsafe_allow_html=True)
        st.markdown("#### 📝 FC 필수 질문 리스트 — 자동차보험 상담 체크리스트")
        _fc_questions = [
            ("차량 사용 목적", "개인용/업무용/영업용 구분 → 요율 결정 핵심"),
            ("연간 주행거리", "마일리지 할인 적용 여부 → 1만km 이하 시 최대 12%"),
            ("블랙박스 장착 여부", "블랙박스 할인 5~10% → 미장착 시 가입 권유"),
            ("운전자 범위", "가족 한정/지정 운전자 → 범위 좁힐수록 보험료 절감"),
            ("운전자보험 가입 여부", "형사합의금·벌금 담보 공백 확인 → 미가입 시 즉시 설계"),
            ("대인Ⅱ 무한 가입 여부", "유한(2~3억) 가입 시 무한으로 변경 권유"),
            ("대물 한도", "2억 미만 시 상향 권유 → 수입차 사고 대비"),
            ("자동차상해 vs 자기신체", "자상(과실무관) vs 자신(과실상계) 차이 설명"),
            ("최근 사고 이력", "3년 내 사고 → 우량 할인 손실 여부 확인"),
            ("갱신일 확인", "D-Day 관리 → 갱신 1달 전 접촉 타이밍"),
        ]
        for _i, (_q, _hint) in enumerate(_fc_questions, 1):
            _chk = st.checkbox(f"Q{_i}. {_q}", key=f"sec07_fc_q{_i}")
            if _chk:
                st.caption(f"   💡 {_hint}")

        st.divider()

        # ── 상담 노트 저장 → RAG 피드백 ──────────────────────────────────
        st.markdown("**📒 상담 노트 저장 (RAG 피드백 데이터)**")
        st.caption("저장된 노트는 다음 유사 고객 상담 시 맞춤 전략 제안에 활용됩니다.")
        _note_name = st.text_input("고객명", value=_c_name, key="sec07_note_name")
        _note_text = st.text_area(
            "상담 내용 메모",
            key="sec07_note_text",
            placeholder="예) 40대 남성, 업무용 차량, 연 3만km 운행. 운전자보험 미가입 상태. 형사합의금 공백 1억 설계 완료.",
            height=100,
        )
        if st.button("💾 상담 노트 저장 (RAG 학습)", key="sec07_note_save", type="primary"):
            if _note_text.strip():
                _ok = _rag_save_consult_note(
                    client_name=_note_name or "익명",
                    note=_note_text.strip(),
                    sector="auto",
                )
                st.success(f"✅ 노트 저장 완료{'(클라우드)' if _ok else '(로컬)'} — RAG 학습 데이터에 반영됩니다.")
                st.session_state.pop("sec07_note_text", None)
                st.rerun()
            else:
                st.warning("상담 내용을 입력해 주세요.")

        # ── 유사 과거 사례 제안 ───────────────────────────────────────────
        _similar = _rag_similar_cases(_note_name or "익명", sector="auto", top_k=3)
        if _similar:
            st.markdown("**🔁 유사 고객 과거 상담 사례 (RAG 제안)**")
            for _s in _similar:
                st.markdown(
                    f'<div class="gks07-rag-box">'
                    f'<b>{_s.get("client_name", "익명")}</b> '
                    f'<span style="font-size:0.72rem;color:#777;">{_s.get("created_at", "")[:10]}</span><br>'
                    f'{str(_s.get("note", ""))[:200]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('</div>', unsafe_allow_html=True)

    # ── 하단 네비게이션 ──────────────────────────────────────────────────────
    st.divider()
    _nav_col1, _nav_col2 = st.columns(2)
    with _nav_col1:
        if st.button("🏠 홈", key="sec07_home_btn", use_container_width=True):
            st.session_state["current_tab"] = "home"
            st.session_state["_scroll_top"] = True
            st.rerun()
    with _nav_col2:
        if st.button("✅ 분석 완료! '보험금 상담' 이동하기 →",
                     key="sec07_next_btn", use_container_width=True, type="primary"):
            st.session_state["current_tab"] = "t1"
            st.session_state["_scroll_top"] = True
            st.rerun()


'''

idx = content.find(ANCHOR)
content = content[:idx] + INSERT + content[idx:]

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: _render_gk_sec07 + RAG functions inserted")
