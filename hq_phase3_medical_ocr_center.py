# ══════════════════════════════════════════════════════════════════════════════
# [MODULE] hq_phase3_medical_ocr_center.py
# HQ 의무기록 OCR 분석 센터 - Phase 3
# policy_ocr_engine.py 연동 + gk_medical_records 저장 + UI 렌더링
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
from typing import Optional


def render_medical_ocr_center(person_id: str, agent_id: str, key_prefix: str = "hq_ocr") -> None:
    """
    [GP-PHASE3] HQ 의무기록 OCR 분석 센터.
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
        key_prefix: 세션 키 접두사
    """
    
    if not person_id or not agent_id:
        st.info("💡 고객을 선택하면 의무기록 분석을 시작할 수 있습니다.")
        return
    
    st.markdown("""
    <div style='background:linear-gradient(135deg,#dbeafe 0%,#bfdbfe 50%,#93c5fd 100%);
      border-radius:14px;padding:18px 22px 14px 22px;margin-bottom:16px;border-left:4px solid #2563eb;'>
      <div style='color:#1e3a8a;font-size:1.15rem;font-weight:900;letter-spacing:0.04em;'>
    🩺 의무기록 OCR 분석 센터 (Phase 3)
      </div>
      <div style='color:#1e40af;font-size:0.80rem;margin-top:5px;'>
    의무기록 파일을 업로드하면 AI가 진단명, 처방 내역, 검사 결과를 자동 추출하여 DB에 저장합니다.
      </div>
    </div>""", unsafe_allow_html=True)
    
    # 세션 초기화
    _ocr_img_key = f"{key_prefix}_ocr_img"
    _ocr_result_key = f"{key_prefix}_ocr_result"
    _ocr_analyzing_key = f"{key_prefix}_ocr_analyzing"
    
    if _ocr_img_key not in st.session_state:
        st.session_state[_ocr_img_key] = None
    if _ocr_result_key not in st.session_state:
        st.session_state[_ocr_result_key] = None
    if _ocr_analyzing_key not in st.session_state:
        st.session_state[_ocr_analyzing_key] = False
    
    _ocr_img = st.session_state.get(_ocr_img_key)
    _ocr_result = st.session_state.get(_ocr_result_key)
    
    # ── 1단계: 파일 업로드 ─────────────────────────────────────────────
    if _ocr_img is None:
        st.markdown("""
        <div style='border:3px dashed #2563eb;border-radius:20px;background:#eff6ff;
          padding:32px 20px;text-align:center;margin-bottom:12px;cursor:pointer;'>
          <div style='font-size:3rem;margin-bottom:8px;'>🩺</div>
          <div style='color:#3b82f6;font-size:1rem;font-weight:700;'>의무기록 파일 업로드</div>
          <div style='color:#475569;font-size:0.75rem;margin-top:6px;'>
        진단서, 처방전, 검사 결과지 등 · JPG / PNG / PDF
          </div>
        </div>""", unsafe_allow_html=True)
        
        _ocr_upload = st.file_uploader(
            "🩺 의무기록 파일 선택",
            type=["jpg", "jpeg", "png", "pdf"],
            key=f"{key_prefix}_ocr_uploader",
            label_visibility="collapsed",
            help="의무기록 파일을 업로드하세요",
        )
        
        if _ocr_upload:
            st.session_state[_ocr_img_key] = _ocr_upload.getvalue()
            st.session_state[_ocr_result_key] = None
            st.rerun()
    
    else:
        # ── 2단계: 파일 미리보기 및 분석 시작 ────────────────────────────
        import base64
        _img_b64 = base64.b64encode(_ocr_img).decode()
        
        _prev_col, _btn_col = st.columns([3, 2])
        with _prev_col:
            st.markdown(
                f"<img src='data:image/jpeg;base64,{_img_b64}' "
                f"style='width:100%;border-radius:16px;box-shadow:0 4px 24px #0008;'/>",
                unsafe_allow_html=True,
            )
        with _btn_col:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if st.button("🔍 AI 의무기록 분석 시작", key=f"{key_prefix}_analyze",
                         use_container_width=True, type="primary"):
                st.session_state[_ocr_analyzing_key] = True
                st.session_state[_ocr_result_key] = None
            if st.button("🔄 다른 파일 선택", key=f"{key_prefix}_reset",
                         use_container_width=True):
                st.session_state[_ocr_img_key] = None
                st.session_state[_ocr_result_key] = None
                st.session_state[_ocr_analyzing_key] = False
                st.rerun()
        
        # ── 3단계: AI 분석 실행 (policy_ocr_engine.py 연동) ──────────────
        if st.session_state.get(_ocr_analyzing_key) and _ocr_result is None:
            st.markdown("""
            <div style='background:#eff6ff;border-radius:14px;padding:20px;text-align:center;
              margin-top:12px;border:1px solid #3b82f6;'>
              <div style='font-size:2rem;margin-bottom:8px;animation:spin 1s linear infinite;'>⚙️</div>
              <div style='color:#2563eb;font-weight:800;font-size:1rem;'>AI가 의무기록을 분석 중입니다...</div>
              <div style='color:#64748b;font-size:0.78rem;margin-top:6px;'>진단명·처방·검사결과 자동 추출</div>
              <div style='background:linear-gradient(90deg,#3b82f6,#60a5fa,#3b82f6);height:3px;
            border-radius:2px;margin-top:14px;animation:scanbar 2s ease-in-out infinite;'></div>
            </div>
            <style>
            @keyframes scanbar{0%{transform:scaleX(0.1);opacity:0.5}50%{transform:scaleX(1);opacity:1}100%{transform:scaleX(0.1);opacity:0.5}}
            @keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
            </style>""", unsafe_allow_html=True)
            
            try:
                # policy_ocr_engine.py 연동
                from engines.policy_ocr_engine import extract_medical_record_data
                
                _ocr_data = extract_medical_record_data(_ocr_img)
                
                # 결과 파싱
                _parsed_result = {
                    "hospital_name": _ocr_data.get("hospital_name", ""),
                    "doctor_name": _ocr_data.get("doctor_name", ""),
                    "visit_date": _ocr_data.get("visit_date", ""),
                    "diagnosis_names": _ocr_data.get("diagnosis_names", []),
                    "diagnosis_codes": _ocr_data.get("diagnosis_codes", []),
                    "prescriptions": _ocr_data.get("prescriptions", {}),
                    "lab_results": _ocr_data.get("lab_results", {}),
                    "ocr_raw_text": _ocr_data.get("raw_text", ""),
                    "ocr_confidence": _ocr_data.get("confidence", 0.0),
                    "structured_data": _ocr_data,
                }
                
                st.session_state[_ocr_result_key] = _parsed_result
            except Exception as _e_ocr:
                st.session_state[_ocr_result_key] = {
                    "error": f"분석 오류: {str(_e_ocr)[:200]}",
                    "ocr_confidence": 0.0,
                }
            
            st.session_state[_ocr_analyzing_key] = False
            st.rerun()
        
        # ── 4단계: 분석 결과 표시 및 저장 ──────────────────────────────
        if _ocr_result is not None:
            if "error" in _ocr_result:
                st.error(f"❌ {_ocr_result['error']}")
            else:
                _conf = _ocr_result.get("ocr_confidence", 0.0)
                _conf_pct = int(_conf * 100)
                _conf_color = "#22c55e" if _conf_pct >= 80 else "#f59e0b" if _conf_pct >= 50 else "#ef4444"
                
                _hospital = _ocr_result.get("hospital_name", "미확인")
                _doctor = _ocr_result.get("doctor_name", "미확인")
                _visit_date = _ocr_result.get("visit_date", "")
                _diagnosis_names = _ocr_result.get("diagnosis_names", [])
                _prescriptions = _ocr_result.get("prescriptions", {})
                
                st.markdown(f"""
                <div style='background:#eff6ff;border-radius:14px;padding:16px 18px;margin-top:12px;
                  border:1px solid {_conf_color};'>
                  <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>
                <div style='color:#1e3a8a;font-weight:800;font-size:1rem;'>📋 AI 분석 결과</div>
                <div style='background:{_conf_color};color:#fff;font-size:0.72rem;font-weight:800;
                  padding:2px 10px;border-radius:20px;'>신뢰도 {_conf_pct}%</div>
                  </div>
                  <div style='color:#64748b;font-size:0.75rem;margin-bottom:4px;'>병원명</div>
                  <div style='color:#1e3a8a;font-weight:700;font-size:0.95rem;margin-bottom:10px;'>{_hospital}</div>
                  <div style='color:#64748b;font-size:0.75rem;margin-bottom:4px;'>의사명</div>
                  <div style='color:#1e3a8a;font-weight:700;font-size:0.95rem;margin-bottom:10px;'>{_doctor}</div>
                  {"<div style='color:#64748b;font-size:0.75rem;margin-bottom:4px;'>진료일</div><div style='color:#1e3a8a;font-weight:700;font-size:0.95rem;margin-bottom:10px;'>" + _visit_date + "</div>" if _visit_date else ""}
                </div>""", unsafe_allow_html=True)
                
                # 진단명 표시
                if _diagnosis_names:
                    st.markdown("**🩺 진단명**")
                    for diag in _diagnosis_names:
                        st.markdown(f"- {diag}")
                
                # 처방 내역 표시
                if _prescriptions:
                    st.markdown("**💊 처방 내역**")
                    st.json(_prescriptions)
                
                # 원문 텍스트 (expander)
                _raw_text = _ocr_result.get("ocr_raw_text", "")
                if _raw_text:
                    with st.expander("📄 OCR 추출 원문", expanded=False):
                        st.text_area("원문", value=_raw_text, height=200, key=f"{key_prefix}_raw_text")
                
                # DB 저장 버튼
                if st.button("💾 의무기록 DB 저장", key=f"{key_prefix}_save", type="primary"):
                    try:
                        import db_utils as du
                        from datetime import datetime
                        
                        # 먼저 gk_scan_files에 저장
                        _scan_id = du.save_scan_file(
                            person_id=person_id,
                            agent_id=agent_id,
                            file_type="medical",
                            gcs_path=f"temp://medical_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            file_name=f"medical_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg",
                            file_size_bytes=len(_ocr_img),
                            mime_type="image/jpeg",
                            tags=["의무기록", _hospital, *_diagnosis_names[:3]],
                            category="medical_record",
                            extracted_text=_raw_text,
                            extracted_fields=_ocr_result.get("structured_data", {}),
                        )
                        
                        # gk_medical_records에 저장
                        if _scan_id:
                            _record_id = du.save_medical_record(
                                scan_id=_scan_id,
                                person_id=person_id,
                                agent_id=agent_id,
                                record_type="diagnosis",
                                hospital_name=_hospital,
                                doctor_name=_doctor,
                                visit_date=_visit_date or None,
                                diagnosis_codes=_ocr_result.get("diagnosis_codes", []),
                                diagnosis_names=_diagnosis_names,
                                prescriptions=_prescriptions,
                                lab_results=_ocr_result.get("lab_results", {}),
                                ocr_raw_text=_raw_text,
                                ocr_confidence=_conf,
                                structured_data=_ocr_result.get("structured_data", {}),
                                ai_summary="",
                                risk_flags=[],
                                insurance_relevance_score=0.0,
                            )
                            
                            if _record_id:
                                st.success(f"✅ 의무기록이 저장되었습니다!\n\n병원: {_hospital}\n진단명: {', '.join(_diagnosis_names[:3])}")
                                st.balloons()
                            else:
                                st.warning("⚠️ 의무기록 저장 실패 (스캔 파일은 저장됨)")
                        else:
                            st.error("❌ 스캔 파일 저장 실패")
                        
                        # 초기화
                        st.session_state[_ocr_img_key] = None
                        st.session_state[_ocr_result_key] = None
                        st.session_state[_ocr_analyzing_key] = False
                        
                    except Exception as _save_e:
                        st.error(f"❌ 저장 실패: {str(_save_e)}")
                
                if st.button("🔄 새로운 의무기록 분석", key=f"{key_prefix}_new"):
                    st.session_state[_ocr_img_key] = None
                    st.session_state[_ocr_result_key] = None
                    st.session_state[_ocr_analyzing_key] = False
                    st.rerun()


def render_medical_records_history(person_id: str, agent_id: str, key_prefix: str = "hq_med_hist") -> None:
    """
    [GP-PHASE3] 의무기록 분석 이력 조회.
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
        key_prefix: 세션 키 접두사
    """
    
    if not person_id or not agent_id:
        return
    
    try:
        import db_utils as du
        
        medical_records = du.get_medical_records(person_id=person_id, agent_id=agent_id, limit=20)
        
        if not medical_records:
            st.info("📭 아직 분석된 의무기록이 없습니다.")
            return
        
        st.markdown(f"""
        <div style='background:#dbeafe;border:1px solid #3b82f6;border-radius:10px;padding:12px;
          margin-bottom:12px;'>
          <div style='color:#1e3a8a;font-size:0.85rem;font-weight:800;'>
        🩺 의무기록 분석 이력 (총 {len(medical_records)}건)
          </div>
        </div>""", unsafe_allow_html=True)
        
        for idx, mr in enumerate(medical_records):
            _hospital = mr.get("hospital_name", "미확인")
            _visit_date = mr.get("visit_date", "")
            _diagnosis_names = mr.get("diagnosis_names", [])
            _processed_at = mr.get("processed_at", "")
            
            with st.expander(f"🩺 {_hospital} · {_visit_date or '날짜 미확인'} · {_processed_at[:10] if _processed_at else ''}", expanded=False):
                st.markdown(f"**병원명**: {_hospital}")
                st.markdown(f"**의사명**: {mr.get('doctor_name', '미확인')}")
                st.markdown(f"**진료일**: {_visit_date or '미확인'}")
                
                if _diagnosis_names:
                    st.markdown("**진단명**:")
                    for diag in _diagnosis_names:
                        st.markdown(f"- {diag}")
                
                _prescriptions = mr.get("prescriptions")
                if _prescriptions:
                    st.markdown("**처방 내역**:")
                    st.json(_prescriptions)
                
                _ai_summary = mr.get("ai_summary", "")
                if _ai_summary:
                    st.markdown(f"**AI 요약**: {_ai_summary}")
        
    except Exception as e:
        st.error(f"❌ 의무기록 조회 오류: {e}")
