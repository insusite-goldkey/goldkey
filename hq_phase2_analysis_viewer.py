"""
hq_phase2_analysis_viewer.py — [GP-PHASE2] HQ 앱 트리니티/KB 분석 이력 뷰어

HQ 앱 M-SECTION에서 사용하는 분석 이력 조회 UI.
CRM에서 수행한 트리니티/KB 분석 결과를 DB에서 불러와 시각화.
"""
import streamlit as st
import db_utils as du
from shared_components import decrypt_pii


def render_analysis_history_dashboard(person_id: str, agent_id: str, key_prefix: str = "_hq_analysis"):
    """
    [GP-PHASE2] HQ 앱 분석 이력 대시보드 (트리니티 + KB 통합).
    
    Args:
        person_id: 고객 UUID
        agent_id: 담당 설계사
        key_prefix: Streamlit 위젯 키 접두사
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    # 고객 정보 조회
    customer = du.get_customer(person_id, agent_id)
    if not customer:
        st.error("❌ 고객 정보를 찾을 수 없습니다.")
        return
    
    customer_name = decrypt_pii(customer.get("name", ""))
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);border:1px dashed #000;border-radius:12px;padding:16px;margin-bottom:20px;color:#fff;'>
        <div style='font-size:1.1rem;font-weight:700;margin-bottom:8px;'>
            📊 {customer_name}님의 분석 이력
        </div>
        <div style='font-size:0.85rem;opacity:0.9;'>
            CRM에서 수행한 트리니티/KB 분석 결과를 조회합니다. (세션 휘발 방지 완료)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 탭으로 분리
    tab1, tab2, tab3 = st.tabs(["🎯 트리니티 분석", "📋 KB 분석", "🔗 통합 분석"])
    
    with tab1:
        render_trinity_history(person_id, agent_id, key_prefix)
    
    with tab2:
        render_kb_history(person_id, agent_id, key_prefix)
    
    with tab3:
        render_integrated_history(person_id, agent_id, key_prefix)


def render_trinity_history(person_id: str, agent_id: str, key_prefix: str):
    """트리니티 분석 이력 렌더링"""
    st.markdown("### 🎯 트리니티 분석 이력")
    
    # 이력 조회
    history = du.get_trinity_analysis_history(person_id=person_id, agent_id=agent_id, limit=10)
    
    if not history:
        st.info("💡 트리니티 분석 이력이 없습니다. CRM 앱에서 분석을 수행하세요.")
        return
    
    st.markdown(f"**총 {len(history)}건의 분석 이력**")
    
    # 최신 분석 강조 표시
    latest = history[0]
    _render_trinity_card(latest, is_latest=True, key_prefix=key_prefix)
    
    # 나머지 이력
    if len(history) > 1:
        with st.expander(f"📜 이전 분석 이력 ({len(history)-1}건)", expanded=False):
            for idx, analysis in enumerate(history[1:], start=1):
                _render_trinity_card(analysis, is_latest=False, key_prefix=f"{key_prefix}_{idx}")


def _render_trinity_card(analysis: dict, is_latest: bool, key_prefix: str):
    """개별 트리니티 분석 카드 렌더링"""
    analysis_id = analysis.get("analysis_id", "")
    analyzed_at = analysis.get("analyzed_at", "")[:19].replace("T", " ")
    nhis_premium = analysis.get("nhis_premium", 0)
    monthly_required = analysis.get("monthly_required", 0)
    gross_monthly = analysis.get("gross_monthly", 0)
    net_annual = analysis.get("net_annual", 0)
    deduction_rate = analysis.get("deduction_rate", 0)
    analysis_data = analysis.get("analysis_data", {})
    income_breakdown = analysis.get("income_breakdown", {})
    coverage_needs = analysis.get("coverage_needs", {})
    report_summary = analysis.get("report_summary", "")
    ai_closing = analysis.get("ai_closing_comment", "")
    
    border_color = "#10b981" if is_latest else "#6b7280"
    bg_color = "#ecfdf5" if is_latest else "#f9fafb"
    
    st.markdown(f"""
    <div style='background:{bg_color};border:2px solid {border_color};border-radius:10px;padding:16px;margin-bottom:16px;'>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;'>
            {f"<span style='background:#10b981;color:#fff;padding:4px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;'>최신 분석</span>" if is_latest else ""}
            <span style='color:#6b7280;font-size:0.80rem;{f"margin-left:auto;" if is_latest else ""}'>{analyzed_at}</span>
        </div>
        <div style='font-size:0.90rem;color:#1a1a1a;margin-bottom:12px;'>
            <strong>건보료 역산 결과</strong>
        </div>
        <div style='display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:12px;'>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:10px;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>월 건강보험료</div>
                <div style='font-size:1.1rem;font-weight:700;color:#3b82f6;'>{nhis_premium:,.0f}원</div>
            </div>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:10px;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>역산 명목 월소득</div>
                <div style='font-size:1.1rem;font-weight:700;color:#10b981;'>{gross_monthly:,.0f}원</div>
            </div>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:10px;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>필요 월소득 (M_req)</div>
                <div style='font-size:1.1rem;font-weight:700;color:#f59e0b;'>{monthly_required:,.0f}원</div>
            </div>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:10px;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>합산 공제율</div>
                <div style='font-size:1.1rem;font-weight:700;color:#ec4899;'>{deduction_rate*100:.2f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 담보별 Gap 분석
    if analysis_data and isinstance(analysis_data, dict):
        with st.expander("📊 담보별 보장 Gap 분석", expanded=is_latest):
            _render_trinity_gap_table(analysis_data)
    
    # 소득 공제 상세
    if income_breakdown and isinstance(income_breakdown, dict):
        with st.expander("💰 소득 공제 상세", expanded=False):
            st.json(income_breakdown)
    
    # 리포트 요약
    if report_summary:
        with st.expander("📝 분석 요약", expanded=False):
            st.markdown(report_summary)
    
    if ai_closing:
        st.info(f"🤖 AI 멘트: {ai_closing}")


def _render_trinity_gap_table(analysis_data: dict):
    """트리니티 Gap 분석 테이블"""
    # _income_meta 제외
    items = {k: v for k, v in analysis_data.items() if not k.startswith("_")}
    
    if not items:
        st.info("담보 데이터가 없습니다.")
        return
    
    # 테이블 헤더
    st.markdown("""
    <div style='display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr;gap:8px;background:#f3f4f6;padding:10px;border-radius:6px;font-size:0.75rem;font-weight:600;color:#374151;margin-bottom:8px;'>
        <div>담보명</div>
        <div style='text-align:right;'>현재가입</div>
        <div style='text-align:right;'>표준KB</div>
        <div style='text-align:right;'>적정역산</div>
        <div style='text-align:right;'>부족분</div>
        <div style='text-align:center;'>충족여부</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 테이블 행
    for item_name, item_data in items.items():
        if not isinstance(item_data, dict):
            continue
        
        current = item_data.get("현재가입", 0)
        standard = item_data.get("표준_KB", 0)
        adequate = item_data.get("적정_역산", 0)
        gap = item_data.get("부족분", 0)
        status = item_data.get("충족여부", "")
        
        status_color = {
            "충족": "#10b981",
            "부족": "#f59e0b",
            "위험": "#ef4444"
        }.get(status, "#6b7280")
        
        st.markdown(f"""
        <div style='display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr;gap:8px;background:#ffffff;border:1px dashed #e5e7eb;padding:10px;border-radius:6px;font-size:0.75rem;margin-bottom:6px;'>
            <div style='font-weight:600;color:#1a1a1a;'>{item_name}</div>
            <div style='text-align:right;color:#6b7280;'>{current:,.0f}</div>
            <div style='text-align:right;color:#6b7280;'>{standard:,.0f}</div>
            <div style='text-align:right;color:#3b82f6;font-weight:600;'>{adequate:,.0f}</div>
            <div style='text-align:right;color:#ef4444;font-weight:600;'>{gap:,.0f}</div>
            <div style='text-align:center;'><span style='background:{status_color};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.70rem;font-weight:600;'>{status}</span></div>
        </div>
        """, unsafe_allow_html=True)


def render_kb_history(person_id: str, agent_id: str, key_prefix: str):
    """KB 분석 이력 렌더링"""
    st.markdown("### 📋 KB 7대 스탠다드 분석 이력")
    
    # 이력 조회
    history = du.get_kb_analysis_history(person_id=person_id, agent_id=agent_id, limit=10)
    
    if not history:
        st.info("💡 KB 분석 이력이 없습니다. CRM 앱에서 분석을 수행하세요.")
        return
    
    st.markdown(f"**총 {len(history)}건의 분석 이력**")
    
    # 최신 분석 강조 표시
    latest = history[0]
    _render_kb_card(latest, is_latest=True, key_prefix=key_prefix)
    
    # 나머지 이력
    if len(history) > 1:
        with st.expander(f"📜 이전 분석 이력 ({len(history)-1}건)", expanded=False):
            for idx, analysis in enumerate(history[1:], start=1):
                _render_kb_card(analysis, is_latest=False, key_prefix=f"{key_prefix}_{idx}")


def _render_kb_card(analysis: dict, is_latest: bool, key_prefix: str):
    """개별 KB 분석 카드 렌더링"""
    analysis_id = analysis.get("analysis_id", "")
    analyzed_at = analysis.get("analyzed_at", "")[:19].replace("T", " ")
    kb_total_score = analysis.get("kb_total_score", 0)
    kb_grade = analysis.get("kb_grade", "")
    customer_age = analysis.get("customer_age", 0)
    customer_gender = analysis.get("customer_gender", "")
    analysis_data = analysis.get("analysis_data", {})
    category_scores = analysis.get("category_scores", [])
    report_summary = analysis.get("report_summary", "")
    ai_summary = analysis.get("ai_summary", "")
    
    border_color = "#10b981" if is_latest else "#6b7280"
    bg_color = "#ecfdf5" if is_latest else "#f9fafb"
    
    grade_colors = {
        "S": "#10b981",
        "A": "#3b82f6",
        "B": "#f59e0b",
        "C": "#f97316",
        "D": "#ef4444",
        "F": "#991b1b"
    }
    grade_color = grade_colors.get(kb_grade, "#6b7280")
    
    st.markdown(f"""
    <div style='background:{bg_color};border:2px solid {border_color};border-radius:10px;padding:16px;margin-bottom:16px;'>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;'>
            {f"<span style='background:#10b981;color:#fff;padding:4px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;'>최신 분석</span>" if is_latest else ""}
            <span style='color:#6b7280;font-size:0.80rem;{f"margin-left:auto;" if is_latest else ""}'>{analyzed_at}</span>
        </div>
        <div style='display:flex;align-items:center;gap:16px;margin-bottom:12px;'>
            <div style='background:{grade_color};color:#fff;padding:16px 24px;border-radius:10px;text-align:center;'>
                <div style='font-size:0.70rem;opacity:0.9;margin-bottom:4px;'>KB 등급</div>
                <div style='font-size:2.5rem;font-weight:900;'>{kb_grade}</div>
            </div>
            <div style='flex:1;'>
                <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:12px;'>
                    <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>KB 종합 점수</div>
                    <div style='font-size:1.5rem;font-weight:700;color:{grade_color};'>{kb_total_score:.1f}점</div>
                </div>
            </div>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:12px;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>분석 대상</div>
                <div style='font-size:0.90rem;font-weight:600;color:#1a1a1a;'>{customer_age}세 / {customer_gender}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 카테고리별 점수
    if category_scores and isinstance(category_scores, list):
        with st.expander("📊 KB 7대 분류별 점수", expanded=is_latest):
            _render_kb_category_chart(category_scores)
    
    # 리포트 요약
    if report_summary:
        with st.expander("📝 분석 요약", expanded=False):
            st.markdown(report_summary)
    
    if ai_summary:
        st.info(f"🤖 AI 요약: {ai_summary}")


def _render_kb_category_chart(category_scores: list):
    """KB 카테고리별 점수 차트"""
    if not category_scores:
        st.info("카테고리 점수 데이터가 없습니다.")
        return
    
    for cat in category_scores:
        cat_name = cat.get("label", "")
        cat_score = cat.get("score", 0)
        cat_badge = cat.get("badge", "")
        
        badge_colors = {
            "충족": "#10b981",
            "양호": "#3b82f6",
            "보통": "#f59e0b",
            "부족": "#f97316",
            "위험": "#ef4444"
        }
        badge_color = badge_colors.get(cat_badge, "#6b7280")
        
        st.markdown(f"""
        <div style='background:#ffffff;border:1px dashed #e5e7eb;border-radius:6px;padding:12px;margin-bottom:8px;'>
            <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;'>
                <span style='font-size:0.85rem;font-weight:600;color:#1a1a1a;'>{cat_name}</span>
                <span style='background:{badge_color};color:#fff;padding:2px 10px;border-radius:4px;font-size:0.70rem;font-weight:600;'>{cat_badge}</span>
            </div>
            <div style='background:#f3f4f6;border-radius:4px;height:8px;overflow:hidden;'>
                <div style='background:{badge_color};height:100%;width:{cat_score}%;transition:width 0.3s;'></div>
            </div>
            <div style='text-align:right;font-size:0.75rem;color:#6b7280;margin-top:4px;'>{cat_score:.1f}점</div>
        </div>
        """, unsafe_allow_html=True)


def render_integrated_history(person_id: str, agent_id: str, key_prefix: str):
    """통합 분석 이력 렌더링"""
    st.markdown("### 🔗 통합 분석 이력 (트리니티 + KB + NIBO)")
    
    # 이력 조회
    history = du.get_integrated_analysis_history(person_id=person_id, agent_id=agent_id, limit=10)
    
    if not history:
        st.info("💡 통합 분석 이력이 없습니다. CRM 앱에서 통합 분석을 수행하세요.")
        return
    
    st.markdown(f"**총 {len(history)}건의 통합 분석 이력**")
    
    for idx, analysis in enumerate(history):
        _render_integrated_card(analysis, is_latest=(idx==0), key_prefix=f"{key_prefix}_{idx}")


def _render_integrated_card(analysis: dict, is_latest: bool, key_prefix: str):
    """개별 통합 분석 카드 렌더링"""
    analysis_id = analysis.get("analysis_id", "")
    analyzed_at = analysis.get("analyzed_at", "")[:19].replace("T", " ")
    analysis_type = analysis.get("analysis_type", "")
    trinity_id = analysis.get("trinity_analysis_id", "")
    kb_id = analysis.get("kb_analysis_id", "")
    integrated_score = analysis.get("integrated_score", 0)
    integrated_grade = analysis.get("integrated_grade", "")
    nibo_status = analysis.get("nibo_status", "")
    
    border_color = "#10b981" if is_latest else "#6b7280"
    bg_color = "#ecfdf5" if is_latest else "#f9fafb"
    
    type_labels = {
        "full": "전체 분석 (트리니티 + KB + NIBO)",
        "trinity_only": "트리니티 단독",
        "kb_only": "KB 단독"
    }
    type_label = type_labels.get(analysis_type, analysis_type)
    
    nibo_status_labels = {
        "pending": "대기중",
        "done": "완료",
        "failed": "실패"
    }
    nibo_label = nibo_status_labels.get(nibo_status, nibo_status)
    
    st.markdown(f"""
    <div style='background:{bg_color};border:2px solid {border_color};border-radius:10px;padding:16px;margin-bottom:16px;'>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;'>
            {f"<span style='background:#10b981;color:#fff;padding:4px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;'>최신 분석</span>" if is_latest else ""}
            <span style='background:#8b5cf6;color:#fff;padding:4px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;'>{type_label}</span>
            <span style='color:#6b7280;font-size:0.80rem;margin-left:auto;'>{analyzed_at}</span>
        </div>
        <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;'>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:10px;text-align:center;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>트리니티 분석</div>
                <div style='font-size:0.85rem;font-weight:600;color:{("#10b981" if trinity_id else "#d1d5db")};'>{"✓ 포함" if trinity_id else "미포함"}</div>
            </div>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:10px;text-align:center;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>KB 분석</div>
                <div style='font-size:0.85rem;font-weight:600;color:{("#10b981" if kb_id else "#d1d5db")};'>{"✓ 포함" if kb_id else "미포함"}</div>
            </div>
            <div style='background:#ffffff;border:1px dashed #d1d5db;border-radius:6px;padding:10px;text-align:center;'>
                <div style='font-size:0.70rem;color:#6b7280;margin-bottom:4px;'>NIBO 상태</div>
                <div style='font-size:0.85rem;font-weight:600;color:#3b82f6;'>{nibo_label}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_quick_analysis_summary(person_id: str, agent_id: str):
    """
    [GP-PHASE2] 빠른 분석 요약 위젯 (M-SECTION 상단 배치용).
    
    최신 트리니티/KB 분석 결과를 한눈에 표시.
    """
    if not person_id or not agent_id:
        return
    
    # 최신 분석 조회
    latest_trinity = du.get_latest_trinity_analysis(person_id, agent_id)
    latest_kb = du.get_latest_kb_analysis(person_id, agent_id)
    
    if not latest_trinity and not latest_kb:
        st.info("💡 분석 이력이 없습니다. CRM 앱에서 분석을 수행하세요.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if latest_trinity:
            analyzed_at = latest_trinity.get("analyzed_at", "")[:10]
            monthly_req = latest_trinity.get("monthly_required", 0)
            
            st.markdown(f"""
            <div style='background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:14px;'>
                <div style='font-size:0.75rem;color:#059669;margin-bottom:6px;'>🎯 최신 트리니티 분석</div>
                <div style='font-size:1.3rem;font-weight:700;color:#10b981;margin-bottom:4px;'>{monthly_req:,.0f}원</div>
                <div style='font-size:0.70rem;color:#6b7280;'>필요 월소득 · {analyzed_at}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#f9fafb;border:1px dashed #d1d5db;border-radius:8px;padding:14px;text-align:center;'>
                <div style='font-size:0.80rem;color:#9ca3af;'>트리니티 분석 없음</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if latest_kb:
            analyzed_at = latest_kb.get("analyzed_at", "")[:10]
            kb_grade = latest_kb.get("kb_grade", "")
            kb_score = latest_kb.get("kb_total_score", 0)
            
            grade_colors = {
                "S": "#10b981",
                "A": "#3b82f6",
                "B": "#f59e0b",
                "C": "#f97316",
                "D": "#ef4444",
                "F": "#991b1b"
            }
            grade_color = grade_colors.get(kb_grade, "#6b7280")
            
            st.markdown(f"""
            <div style='background:#eff6ff;border:2px solid #3b82f6;border-radius:8px;padding:14px;'>
                <div style='font-size:0.75rem;color:#1d4ed8;margin-bottom:6px;'>📋 최신 KB 분석</div>
                <div style='font-size:1.3rem;font-weight:700;color:{grade_color};margin-bottom:4px;'>{kb_grade}등급 ({kb_score:.1f}점)</div>
                <div style='font-size:0.70rem;color:#6b7280;'>{analyzed_at}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#f9fafb;border:1px dashed #d1d5db;border-radius:8px;padding:14px;text-align:center;'>
                <div style='font-size:0.80rem;color:#9ca3af;'>KB 분석 없음</div>
            </div>
            """, unsafe_allow_html=True)
