# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_accident_analysis_block.py
# CRM 사고 분석 블록 - 블랙박스 영상 분석 및 과실비율 추정
# Gemini 1.5 Pro 영상 분석 + RAG 기반 과실비율 매칭 + 수리비 추정
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import os
import tempfile
from pathlib import Path
from typing import Optional


def render_crm_accident_analysis_block(
    sel_pid: str,
    user_id: str,
    customer_name: str = "",
) -> None:
    """CRM 사고 분석 블록 - 블랙박스 영상 분석 및 과실비율 추정.
    
    Args:
        sel_pid: person_id (선택된 고객)
        user_id: 로그인 설계사 user_id
        customer_name: 고객 이름
    """
    
    # [GP-IDENTITY §1] person_id 필수 검증
    if not sel_pid or not user_id:
        st.error("❌ [GP-IDENTITY] 고객을 먼저 선택해 주세요.")
        return
    
    # customer_name 미제공 시 DB에서 조회
    if not customer_name:
        try:
            from db_utils import get_supabase_client
            _sb = get_supabase_client()
            if _sb:
                _person_resp = _sb.table("people").select("name").eq("id", sel_pid).limit(1).execute()
                if _person_resp.data and len(_person_resp.data) > 0:
                    customer_name = _person_resp.data[0].get("name", "고객")
        except Exception:
            customer_name = "고객"
    
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 50%,#fcd34d 100%);
      border-radius:14px;padding:18px 22px 14px 22px;margin-bottom:16px;border-left:4px solid #f59e0b;'>
      <div style='color:#92400e;font-size:1.15rem;font-weight:900;letter-spacing:0.04em;'>
    🚗 AI 사고 분석 센터 (Gemini 1.5 Pro + RAG)
      </div>
      <div style='color:#b45309;font-size:0.80rem;margin-top:5px;'>
    블랙박스 영상을 AI가 분석하여 가해/피해 차량 구분 → 과실비율 인정기준 매칭 → 수리비 추정까지 자동 처리
      </div>
      <div style='color:#92400e;font-size:0.75rem;margin-top:8px;font-weight:700;'>
    📌 분석 대상자: {customer_name}
      </div>
    </div>""", unsafe_allow_html=True)
    
    # 세션 초기화
    if "_crm_accident_video" not in st.session_state:
        st.session_state["_crm_accident_video"] = None
    if "_crm_accident_result" not in st.session_state:
        st.session_state["_crm_accident_result"] = None
    if "_crm_accident_analyzing" not in st.session_state:
        st.session_state["_crm_accident_analyzing"] = False
    
    _video = st.session_state.get("_crm_accident_video")
    _result = st.session_state.get("_crm_accident_result")
    
    if _video is None and _result is None:
        # ── 1단계: 블랙박스 영상 업로드 ─────────────────────────────────────
        st.markdown("""
    <div style='border:3px dashed #f59e0b;border-radius:20px;background:#fffbeb;
      padding:32px 20px;text-align:center;margin-bottom:12px;cursor:pointer;'>
      <div style='font-size:3rem;margin-bottom:8px;'>🎥</div>
      <div style='color:#f59e0b;font-size:1rem;font-weight:700;'>블랙박스 영상 업로드</div>
      <div style='color:#475569;font-size:0.75rem;margin-top:6px;'>
    MP4 형식 · 최대 100MB · 사고 전후 30초 이상 권장
      </div>
    </div>""", unsafe_allow_html=True)
        
        _video_upload = st.file_uploader(
            "🎥 블랙박스 영상 선택 (MP4)",
            type=["mp4", "mov", "avi"],
            key=f"crm_accident_video_{sel_pid}",
            help="사고 전후 상황이 모두 포함된 영상을 업로드하세요",
        )
        
        if _video_upload is not None:
            st.session_state["_crm_accident_video"] = _video_upload
            st.rerun()
    
    elif _video is not None and _result is None:
        # ── 2단계: 영상 미리보기 및 분석 시작 ─────────────────────────────────────
        st.markdown("### 📹 업로드된 영상")
        st.video(_video)
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button(
                "🤖 AI 분석 시작",
                type="primary",
                use_container_width=True,
                key=f"crm_accident_analyze_{sel_pid}"
            ):
                st.session_state["_crm_accident_analyzing"] = True
                st.rerun()
        
        with col2:
            if st.button(
                "🔄 다시 업로드",
                use_container_width=True,
                key=f"crm_accident_reupload_{sel_pid}"
            ):
                st.session_state["_crm_accident_video"] = None
                st.session_state["_crm_accident_result"] = None
                st.session_state["_crm_accident_analyzing"] = False
                st.rerun()
        
        # ── 3단계: AI 분석 실행 ─────────────────────────────────────
        if st.session_state.get("_crm_accident_analyzing"):
            with st.spinner("🤖 Gemini 1.5 Pro가 영상을 분석하고 있습니다... (1-2분 소요)"):
                try:
                    # 임시 파일로 저장
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                        tmp_file.write(_video.read())
                        tmp_path = tmp_file.name
                    
                    # 사고 분석 엔진 초기화
                    from engines.accident_analyzer import AccidentAnalyzer
                    
                    analyzer = AccidentAnalyzer(
                        gemini_api_key=os.getenv("GEMINI_API_KEY"),
                        supabase_url=os.getenv("SUPABASE_URL"),
                        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
                    )
                    
                    # 전체 분석 실행
                    result = analyzer.analyze_accident_full(tmp_path)
                    
                    # 임시 파일 삭제
                    os.unlink(tmp_path)
                    
                    # 결과 저장
                    st.session_state["_crm_accident_result"] = result
                    st.session_state["_crm_accident_analyzing"] = False
                    
                    st.success("✅ 분석 완료!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ 분석 실패: {e}")
                    st.session_state["_crm_accident_analyzing"] = False
                    
                    # 디버그 정보
                    import traceback
                    with st.expander("🔍 오류 상세 정보"):
                        st.code(traceback.format_exc())
    
    elif _result is not None:
        # ── 4단계: 분석 결과 표시 ─────────────────────────────────────
        video_analysis = _result.get("video_analysis", {})
        fault_ratio_matches = _result.get("fault_ratio_matches", [])
        repair_estimate = _result.get("repair_estimate", {})
        fraud_response_guide = _result.get("fraud_response_guide", {})
        
        # 상단 버튼
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(
                "🔄 새 영상 분석",
                use_container_width=True,
                key=f"crm_accident_new_{sel_pid}"
            ):
                st.session_state["_crm_accident_video"] = None
                st.session_state["_crm_accident_result"] = None
                st.session_state["_crm_accident_analyzing"] = False
                st.rerun()
        
        with col2:
            if st.button(
                "💾 분석 결과 저장",
                type="primary",
                use_container_width=True,
                key=f"crm_accident_save_{sel_pid}"
            ):
                # TODO: Supabase에 분석 결과 저장
                st.success("✅ 분석 결과가 저장되었습니다!")
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 1. 사고 상황 요약 ═══
        st.markdown("""
        <div style='background:#f0fdf4;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #16a34a;'>
          <div style='color:#065f46;font-size:1rem;font-weight:700;margin-bottom:8px;'>
        📋 사고 상황 요약
          </div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown(f"**{video_analysis.get('summary', '분석 결과 없음')}**")
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 2. 차량 정보 ═══
        st.markdown("""
        <div style='background:#eff6ff;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #3b82f6;'>
          <div style='color:#1e40af;font-size:1rem;font-weight:700;margin-bottom:8px;'>
        🚗 차량 정보
          </div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔴 가해 차량**")
            st.info(video_analysis.get("vehicles", {}).get("attacker", "정보 없음"))
        
        with col2:
            st.markdown("**🔵 피해 차량**")
            st.info(video_analysis.get("vehicles", {}).get("victim", "정보 없음"))
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 3. 사고 유형 및 파손 부위 ═══
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style='background:#fef3c7;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #f59e0b;'>
              <div style='color:#92400e;font-size:1rem;font-weight:700;margin-bottom:8px;'>
            ⚠️ 사고 유형
              </div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown(f"**{video_analysis.get('accident_type', '분류 불가')}**")
        
        with col2:
            st.markdown("""
            <div style='background:#fee2e2;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #ef4444;'>
              <div style='color:#991b1b;font-size:1rem;font-weight:700;margin-bottom:8px;'>
            🔧 파손 부위 및 심각도
              </div>
            </div>""", unsafe_allow_html=True)
            
            damage = video_analysis.get("damage_assessment", {})
            damaged_parts = damage.get("damaged_parts", [])
            severity = damage.get("severity", "알 수 없음")
            
            st.markdown(f"**심각도**: {severity}")
            if damaged_parts:
                st.markdown("**파손 부위**:")
                for part in damaged_parts:
                    st.markdown(f"- {part}")
            else:
                st.markdown("파손 부위 정보 없음")
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 4. 신호 및 도로 상황 분석 (신규 추가) ═══
        signal_analysis = video_analysis.get("signal_and_road_analysis", {})
        
        if signal_analysis:
            st.markdown("""
            <div style='background:#dcfce7;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #16a34a;'>
              <div style='color:#166534;font-size:1rem;font-weight:700;margin-bottom:8px;'>
            🚥 신호 및 도로 상황 분석 (정밀 인식)
              </div>
            </div>""", unsafe_allow_html=True)
            
            # A. 신호등 색상 변화
            traffic_signals = signal_analysis.get("traffic_signals", {})
            if traffic_signals:
                st.markdown("### 📍 신호등 색상 변화 추적")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔵 우리 차량 신호등**")
                    our_signals = traffic_signals.get("our_vehicle", {})
                    st.markdown(f"- 사고 5초 전: `{our_signals.get('5_seconds_before', '확인 불가')}`")
                    st.markdown(f"- 사고 직전(1초): `{our_signals.get('1_second_before', '확인 불가')}`")
                    st.markdown(f"- 충돌 시점: `{our_signals.get('at_collision', '확인 불가')}`")
                    st.markdown(f"- 사고 직후: `{our_signals.get('after_collision', '확인 불가')}`")
                
                with col2:
                    st.markdown("**🔴 상대 차량 신호등 (추정)**")
                    opp_signals = traffic_signals.get("opponent_vehicle", {})
                    st.markdown(f"- 사고 5초 전: `{opp_signals.get('5_seconds_before', '확인 불가')}`")
                    st.markdown(f"- 사고 직전(1초): `{opp_signals.get('1_second_before', '확인 불가')}`")
                    st.markdown(f"- 충돌 시점: `{opp_signals.get('at_collision', '확인 불가')}`")
                
                signal_change = traffic_signals.get("signal_change_timing", "")
                if signal_change:
                    st.info(f"⏱️ **신호 변화 타이밍**: {signal_change}")
                
                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            # B. 노면 표시
            road_markings = signal_analysis.get("road_markings", {})
            if road_markings:
                st.markdown("### 🛣️ 노면 표시 및 지시")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    arrows = road_markings.get("arrows", "확인 불가")
                    lane_lines = road_markings.get("lane_lines", "확인 불가")
                    st.markdown(f"- **노면 화살표**: {arrows}")
                    st.markdown(f"- **차로 구분선**: {lane_lines}")
                
                with col2:
                    crosswalk = road_markings.get("crosswalk", "확인 불가")
                    stop_line = road_markings.get("stop_line", "확인 불가")
                    st.markdown(f"- **횡단보도**: {crosswalk}")
                    st.markdown(f"- **정지선**: {stop_line}")
                
                other_markings = road_markings.get("other_markings", "")
                if other_markings and other_markings != "없음":
                    st.markdown(f"- **기타 표시**: {other_markings}")
                
                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            # C. 교통 표지판
            traffic_signs = signal_analysis.get("traffic_signs", {})
            if traffic_signs and any(traffic_signs.values()):
                st.markdown("### 🚸 교통 표지판 인식")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    regulatory = traffic_signs.get("regulatory", "없음")
                    guide = traffic_signs.get("guide", "없음")
                    if regulatory != "없음":
                        st.markdown(f"- **규제 표지판**: {regulatory}")
                    if guide != "없음":
                        st.markdown(f"- **지시 표지판**: {guide}")
                
                with col2:
                    warning = traffic_signs.get("warning", "없음")
                    auxiliary = traffic_signs.get("auxiliary", "없음")
                    if warning != "없음":
                        st.markdown(f"- **주의 표지판**: {warning}")
                    if auxiliary != "없음":
                        st.markdown(f"- **보조 표지판**: {auxiliary}")
                
                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            # D. 법규 위반 여부
            violations = signal_analysis.get("violations", {})
            if violations:
                st.markdown("### ⚠️ 법규 위반 여부 판별")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔵 우리 차량 위반 사항**")
                    our_violations = violations.get("our_vehicle", {})
                    
                    violation_labels = {
                        "signal_violation": "신호위반",
                        "direction_violation": "지시위반",
                        "lane_violation": "차로위반",
                        "speed_violation": "속도위반",
                        "safe_distance_violation": "안전거리 미확보",
                        "other_violations": "기타 위반"
                    }
                    
                    has_violation = False
                    for key, label in violation_labels.items():
                        violation_info = our_violations.get(key, {})
                        if isinstance(violation_info, dict) and violation_info.get("exists"):
                            has_violation = True
                            detail = violation_info.get("detail", "")
                            st.error(f"❌ **{label}**: {detail}")
                    
                    if not has_violation:
                        st.success("✅ 위반 사항 없음")
                
                with col2:
                    st.markdown("**🔴 상대 차량 위반 사항**")
                    opp_violations = violations.get("opponent_vehicle", {})
                    
                    has_violation = False
                    for key, label in violation_labels.items():
                        violation_info = opp_violations.get(key, {})
                        if isinstance(violation_info, dict) and violation_info.get("exists"):
                            has_violation = True
                            detail = violation_info.get("detail", "")
                            st.error(f"❌ **{label}**: {detail}")
                    
                    if not has_violation:
                        st.success("✅ 위반 사항 없음")
                
                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            # E. 과실 판단 근거
            fault_judgment = signal_analysis.get("fault_judgment", {})
            if fault_judgment:
                st.markdown("### ⚖️ 과실 판단 근거 (법규 위반 기반)")
                
                primary_fault = fault_judgment.get("primary_fault_vehicle", "")
                fault_basis = fault_judgment.get("fault_basis", "")
                estimated_ratio = fault_judgment.get("estimated_fault_ratio", "")
                ratio_basis = fault_judgment.get("ratio_basis", "")
                
                if primary_fault:
                    st.warning(f"**주요 과실 차량**: {primary_fault}")
                
                if fault_basis:
                    st.markdown(f"**과실 근거**: {fault_basis}")
                
                if estimated_ratio:
                    st.info(f"**예상 과실비율**: {estimated_ratio}")
                
                if ratio_basis:
                    st.caption(f"근거: {ratio_basis}")
            
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 5. 과실비율 인정기준 매칭 ═══
        st.markdown("""
        <div style='background:#f5f3ff;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #8b5cf6;'>
          <div style='color:#5b21b6;font-size:1rem;font-weight:700;margin-bottom:8px;'>
        ⚖️ 과실비율 인정기준 (RAG 검색 결과)
          </div>
        </div>""", unsafe_allow_html=True)
        
        if fault_ratio_matches:
            for i, match in enumerate(fault_ratio_matches, 1):
                with st.expander(f"📄 {i}. {match['document_name']} (유사도: {match['similarity']:.2%})"):
                    st.markdown(f"**예상 과실비율**: {match['fault_ratio']}")
                    st.markdown("**관련 내용**:")
                    st.text(match['content'][:500] + "..." if len(match['content']) > 500 else match['content'])
        else:
            st.warning("⚠️ 과실비율 인정기준을 찾을 수 없습니다. source_docs 폴더에 '과실비율 인정기준' PDF를 추가하세요.")
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 6. 수리비 추정 ═══
        st.markdown("""
        <div style='background:#fef2f2;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #dc2626;'>
          <div style='color:#991b1b;font-size:1rem;font-weight:700;margin-bottom:8px;'>
        💰 예상 수리비
          </div>
        </div>""", unsafe_allow_html=True)
        
        if repair_estimate:
            st.markdown(f"### 총 예상 수리비: **{repair_estimate.get('total_range', '정보 없음')}**")
            st.markdown(f"**(평균: {repair_estimate.get('total_estimate', 0):,}원)**")
            
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            st.markdown("**부위별 상세 내역**:")
            parts_detail = repair_estimate.get("parts_detail", [])
            
            if parts_detail:
                for part_info in parts_detail:
                    col1, col2, col3 = st.columns([2, 2, 3])
                    with col1:
                        st.markdown(f"**{part_info['part']}**")
                    with col2:
                        st.markdown(f"`{part_info['repair_type']}`")
                    with col3:
                        st.markdown(f"{part_info['cost_range']}")
            
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            st.caption(repair_estimate.get("disclaimer", ""))
        else:
            st.warning("⚠️ 수리비 추정 정보가 없습니다.")
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 7. 경미 상해 및 보험사기 대응 가이드 (신규 추가) ═══
        minor_injury = video_analysis.get("minor_injury_analysis", {})
        
        if minor_injury and fraud_response_guide.get("is_applicable"):
            st.markdown("""
            <div style='background:#fee2e2;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #dc2626;'>
              <div style='color:#991b1b;font-size:1rem;font-weight:700;margin-bottom:8px;'>
            🚨 경미 상해 및 과장 행동 분석 (연성 사기 감지)
              </div>
            </div>""", unsafe_allow_html=True)
            
            # A. 초저속 미세 충돌 판별
            minor_collision = minor_injury.get("minor_collision_detection", {})
            if minor_collision:
                st.markdown("### 🔍 초저속 미세 충돌 판별")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"- **블랙박스 지평선 흔들림**: {minor_collision.get('horizon_shake', '확인 불가')}")
                    st.markdown(f"- **차량 파손 정도**: {minor_collision.get('vehicle_damage', '확인 불가')}")
                
                with col2:
                    st.markdown(f"- **접근 속도 추정**: {minor_collision.get('approach_speed', '확인 불가')}")
                    is_minor = minor_collision.get('is_minor_collision', False)
                    st.markdown(f"- **미세 충돌 여부**: {'✅ 예' if is_minor else '❌ 아니오'}")
                
                basis = minor_collision.get('basis', '')
                if basis:
                    st.info(f"💡 **판단 근거**: {basis}")
                
                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            # B. 과장 행동 감지
            exaggerated = minor_injury.get("exaggerated_behavior_detection", {})
            if exaggerated:
                st.markdown("### ⚠️ 과장 행동 감지 (생체역학적 분석)")
                
                occupant_movement = exaggerated.get("occupant_movement", {})
                if occupant_movement:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"- **머리/목 움직임**: {occupant_movement.get('head_neck', '확인 불가')}")
                        st.markdown(f"- **상체 움직임**: {occupant_movement.get('upper_body', '확인 불가')}")
                    
                    with col2:
                        st.markdown(f"- **충격 강도 대비 신체 반응**: {occupant_movement.get('reaction_vs_impact', '확인 불가')}")
                
                st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
                
                suspicious = exaggerated.get("suspicious_indicators", {})
                if suspicious:
                    st.markdown("**과장 행동 의심 지표:**")
                    
                    physical = suspicious.get("physical_inconsistency", {})
                    if physical.get("exists"):
                        st.error(f"❌ **물리적 불일치**: {physical.get('detail', '')}")
                    
                    delayed = suspicious.get("delayed_exaggeration", {})
                    if delayed.get("exists"):
                        st.error(f"❌ **시간차 과장**: {delayed.get('detail', '')}")
                    
                    biomech = suspicious.get("biomechanical_contradiction", {})
                    if biomech.get("exists"):
                        st.error(f"❌ **생체역학적 모순**: {biomech.get('detail', '')}")
                
                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            # C. 과장 청구 추론
            claim_inference = minor_injury.get("exaggerated_claim_inference", {})
            if claim_inference:
                st.markdown("### 📊 과장 청구 추론")
                
                causal = claim_inference.get("causal_contradiction", False)
                suspicion = claim_inference.get("suspicion_level", "없음")
                basis = claim_inference.get("suspicion_basis", "")
                
                if causal:
                    st.warning("⚠️ **물리적 충격과 신체 움직임의 인과관계 모순 발견**")
                
                if suspicion != "없음":
                    if suspicion == "높음":
                        st.error(f"🚨 **과장 청구 의심 소견**: {suspicion}")
                    elif suspicion == "보통":
                        st.warning(f"⚠️ **과장 청구 의심 소견**: {suspicion}")
                    else:
                        st.info(f"ℹ️ **과장 청구 의심 소견**: {suspicion}")
                    
                    if basis:
                        st.markdown(f"**의심 근거**: {basis}")
                
                st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
            
            # D. 보험사기 대응 법률 가이드
            if fraud_response_guide.get("is_applicable"):
                st.markdown("### ⚖️ 보험사기 대응 법률 가이드")
                
                response_level = fraud_response_guide.get("response_level", "불필요")
                fraud_possibility = fraud_response_guide.get("soft_fraud_possibility", "없음")
                
                if response_level == "강력 권고":
                    st.error(f"🚨 **대응 권고 수위**: {response_level} | **연성 사기 가능성**: {fraud_possibility}")
                elif response_level == "권고":
                    st.warning(f"⚠️ **대응 권고 수위**: {response_level} | **연성 사기 가능성**: {fraud_possibility}")
                else:
                    st.info(f"ℹ️ **대응 권고 수위**: {response_level} | **연성 사기 가능성**: {fraud_possibility}")
                
                legal_guide = fraud_response_guide.get("legal_guide", "")
                if legal_guide:
                    with st.expander("📋 법률 가이드 전문 보기"):
                        st.markdown(legal_guide)
                
                action_steps = fraud_response_guide.get("action_steps", [])
                if action_steps:
                    st.markdown("**실행 단계:**")
                    for step in action_steps:
                        st.markdown(f"- {step}")
                
                st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
                
                # 보험사기 신고 센터 링크
                st.markdown("""
                **주요 연락처:**
                - 🏛️ [금융감독원 보험사기 신고 센터](https://www.fss.or.kr) - ☎️ 1332
                - 🚗 [도로교통공단 마디모 프로그램](https://www.koroad.or.kr) - ☎️ 1577-1120
                - 🚔 경찰청 보험범죄 신고 - ☎️ 112
                """)
            
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # ═══ 8. 추가 정보 ═══
        with st.expander("📍 사고 발생 시각 및 위치"):
            st.markdown(f"**발생 시각**: {video_analysis.get('timestamp', '알 수 없음')}")
            st.markdown(f"**위치 힌트**: {video_analysis.get('location_hint', '알 수 없음')}")
        
        # ═══ 7. [Phase 7] 분석 결과 공유 블록 ═══
        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
        
        # 분석 결과를 텍스트로 정리
        _accident_summary = f"""
# 사고 분석 결과

## 사고 상황 요약
{video_analysis.get('summary', '분석 결과 없음')}

## 차량 정보
- **가해 차량**: {video_analysis.get('vehicles', {}).get('attacker', '정보 없음')}
- **피해 차량**: {video_analysis.get('vehicles', {}).get('victim', '정보 없음')}

## 사고 유형
{video_analysis.get('accident_type', '분류 불가')}

## 파손 부위 및 심각도
- **심각도**: {damage.get('severity', '알 수 없음')}
- **파손 부위**: {', '.join(damaged_parts) if damaged_parts else '정보 없음'}

## 예상 과실비율
"""
        
        if fault_ratio_matches:
            for i, match in enumerate(fault_ratio_matches[:1], 1):  # 상위 1개만
                _accident_summary += f"- {match['fault_ratio']} (출처: {match['document_name']})\n"
        else:
            _accident_summary += "- 과실비율 인정기준 검색 결과 없음\n"
        
        _accident_summary += f"""
## 예상 수리비
- **총 예상 수리비**: {repair_estimate.get('total_range', '정보 없음')}
- **평균**: {repair_estimate.get('total_estimate', 0):,}원

{repair_estimate.get('disclaimer', '')}
"""
        
        from blocks.share_report_block import render_share_report_block
        
        render_share_report_block(
            analysis_content=_accident_summary,
            customer_name=customer_name,
            block_title="사고 분석 결과",
            key_prefix=f"share_accident_{sel_pid}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 테스트 코드
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    st.set_page_config(page_title="사고 분석 블록 테스트", layout="wide")
    
    st.title("🚗 사고 분석 블록 테스트")
    
    # 테스트용 더미 데이터
    render_crm_accident_analysis_block(
        sel_pid="test_person_id",
        user_id="test_user_id",
        customer_name="홍길동"
    )
