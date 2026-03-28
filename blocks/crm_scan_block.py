# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_scan_block.py
# CRM 증권 스캔 센터 - 보험증권 OCR 분석 및 자동 저장
# 원본: HQ scan_hub 탭 로직 CRM 버전 최적화
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import base64
from typing import Optional


def render_crm_scan_block(
    sel_pid: str,
    user_id: str,
    customer_name: str = "",
) -> None:
    """CRM 증권 스캔 센터 블록.
    
    Args:
        sel_pid: person_id (선택된 고객)
        user_id: 로그인 설계사 user_id
        customer_name: 고객 이름 (선택사항)
    """
    
    st.markdown("""
    <div style='background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 50%,#bbf7d0 100%);
      border-radius:14px;padding:18px 22px 14px 22px;margin-bottom:16px;border-left:4px solid #16a34a;'>
      <div style='color:#065f46;font-size:1.15rem;font-weight:900;letter-spacing:0.04em;'>
    📸 증권 스캔 센터 (CRM)
      </div>
      <div style='color:#047857;font-size:0.80rem;margin-top:5px;'>
    보험증권을 촬영하면 AI가 자동으로 보험사·상품명·가입일을 추출하여 DB에 저장합니다.
      </div>
    </div>""", unsafe_allow_html=True)
    
    # 세션 초기화
    if "_crm_scan_img" not in st.session_state:
        st.session_state["_crm_scan_img"] = None
    if "_crm_scan_result" not in st.session_state:
        st.session_state["_crm_scan_result"] = None
    if "_crm_scan_analyzing" not in st.session_state:
        st.session_state["_crm_scan_analyzing"] = False
    
    _scan_img = st.session_state.get("_crm_scan_img")
    _scan_result = st.session_state.get("_crm_scan_result")
    
    if _scan_img is None:
        # ── 1단계: 이미지 업로드 ─────────────────────────────────────
        st.markdown("""
    <div style='border:3px dashed #3b82f6;border-radius:20px;background:#EEF2FF;
      padding:32px 20px;text-align:center;margin-bottom:12px;cursor:pointer;'>
      <div style='font-size:3rem;margin-bottom:8px;'>📷</div>
      <div style='color:#60a5fa;font-size:1rem;font-weight:700;'>증권 사진 촬영 또는 업로드</div>
      <div style='color:#475569;font-size:0.75rem;margin-top:6px;'>
    스마트폰 카메라 또는 파일 선택 · JPG / PNG / PDF
      </div>
    </div>""", unsafe_allow_html=True)
        
        _scan_upload = st.file_uploader(
            "📷 증권 사진 선택",
            type=["jpg", "jpeg", "png", "pdf"],
            key=f"crm_scan_uploader_{sel_pid}",
            label_visibility="collapsed",
            help="모바일에서는 후면 카메라가 자동 실행됩니다",
        )
        
        # 모바일 후면 카메라 capture 속성 주입
        st.markdown("""
    <script>
    (function(){
      var inp = document.querySelector('input[data-testid="stFileUploaderInput"]');
      if(inp){ inp.setAttribute('capture','environment'); inp.setAttribute('accept','image/*'); }
    })();
    </script>""", unsafe_allow_html=True)
        
        if _scan_upload:
            st.session_state["_crm_scan_img"] = _scan_upload.getvalue()
            st.session_state["_crm_scan_result"] = None
            st.rerun()
    
    else:
        # ── 2단계: 이미지 미리보기 ────────────────────────────────────
        _img_b64 = base64.b64encode(_scan_img).decode()
        
        _prev_col, _btn_col = st.columns([3, 2])
        with _prev_col:
            st.markdown(
                f"<img src='data:image/jpeg;base64,{_img_b64}' "
                f"style='width:100%;border-radius:16px;box-shadow:0 4px 24px #0008;'/>",
                unsafe_allow_html=True,
            )
        with _btn_col:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if st.button("🔍 AI 증권 분석 시작", key=f"crm_scan_analyze_{sel_pid}",
                         use_container_width=True, type="primary"):
                st.session_state["_crm_scan_analyzing"] = True
                st.session_state["_crm_scan_result"] = None
            if st.button("🔄 다른 사진 선택", key=f"crm_scan_reset_{sel_pid}",
                         use_container_width=True):
                st.session_state["_crm_scan_img"] = None
                st.session_state["_crm_scan_result"] = None
                st.session_state["_crm_scan_analyzing"] = False
                st.rerun()
        
        # ── 3단계: AI 분석 실행 ──────────────────────────────────────
        if st.session_state.get("_crm_scan_analyzing") and _scan_result is None:
            st.markdown("""
    <div style='background:#EEF2FF;border-radius:14px;padding:20px;text-align:center;
      margin-top:12px;border:1px solid #22d3ee;'>
      <div style='font-size:2rem;margin-bottom:8px;animation:spin 1s linear infinite;'>⚙️</div>
      <div style='color:#22d3ee;font-weight:800;font-size:1rem;'>AI가 증권 정보를 분석 중입니다...</div>
      <div style='color:#64748b;font-size:0.78rem;margin-top:6px;'>보험사·상품명·가입일 자동 추출</div>
      <div style='background:linear-gradient(90deg,#0ea5e9,#22d3ee,#0ea5e9);height:3px;
    border-radius:2px;margin-top:14px;animation:scanbar 2s ease-in-out infinite;'></div>
    </div>
    <style>
    @keyframes scanbar{0%{transform:scaleX(0.1);opacity:0.5}50%{transform:scaleX(1);opacity:1}100%{transform:scaleX(0.1);opacity:0.5}}
    @keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
    </style>""", unsafe_allow_html=True)
            
            try:
                # Gemini Vision API로 증권 분석
                from shared_components import get_master_model
                _cl_scan, _ = get_master_model()
                
                _img_part = {"mime_type": "image/jpeg", "data": _scan_img}
                _scan_prompt = (
                    "이 이미지는 보험증권입니다.\n"
                    "다음을 JSON 형식으로 추출하세요:\n"
                    "1. insurance_company: 보험사명 (예: 삼성화재, KB손해보험)\n"
                    "2. product_name: 상품명 (예: 다이렉트 자동차보험)\n"
                    "3. join_date: 가입일 (YYYY-MM-DD 형식)\n"
                    "4. policy_number: 증권번호 (있는 경우)\n"
                    "5. confidence: 추출 신뢰도 0~100\n"
                    "JSON만 반환하고 설명 없이 출력하세요."
                )
                
                _scan_response = _cl_scan.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[_scan_prompt, _img_part],
                )
                _scan_text = _scan_response.text.strip()
                
                # JSON 파싱
                import json, re
                _jm = re.search(r'\{.*\}', _scan_text, re.DOTALL)
                if _jm:
                    _scan_parsed = json.loads(_jm.group())
                else:
                    _scan_parsed = {"confidence": 50}
                
                # insurance_scan 모듈로 추가 정규화
                try:
                    from insurance_scan import normalize_company
                    if "insurance_company" in _scan_parsed:
                        _scan_parsed["insurance_company"] = normalize_company(
                            _scan_parsed["insurance_company"]
                        )
                except ImportError:
                    pass
                
                st.session_state["_crm_scan_result"] = _scan_parsed
            except Exception as _e_scan:
                st.session_state["_crm_scan_result"] = {
                    "error": f"분석 오류: {str(_e_scan)[:100]}",
                    "confidence": 0,
                }
            
            st.session_state["_crm_scan_analyzing"] = False
            st.rerun()
        
        # ── 4단계: 분석 결과 표시 및 저장 ──────────────────────────────
        if _scan_result is not None:
            _conf = _scan_result.get("confidence", 0)
            _conf_color = "#22c55e" if _conf >= 80 else "#f59e0b" if _conf >= 50 else "#ef4444"
            _company = _scan_result.get("insurance_company", "미확인")
            _product = _scan_result.get("product_name", "미확인")
            _join_date = _scan_result.get("join_date", "")
            _policy_num = _scan_result.get("policy_number", "")
            
            st.markdown(f"""
    <div style='background:#EEF2FF;border-radius:14px;padding:16px 18px;margin-top:12px;
      border:1px solid {_conf_color};'>
      <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>
    <div style='color:#1e3a8a;font-weight:800;font-size:1rem;'>📋 AI 분석 결과</div>
    <div style='background:{_conf_color};color:#fff;font-size:0.72rem;font-weight:800;
      padding:2px 10px;border-radius:20px;'>신뢰도 {_conf}%</div>
      </div>
      <div style='color:#64748b;font-size:0.75rem;margin-bottom:4px;'>보험사</div>
      <div style='color:#1e3a8a;font-weight:700;font-size:0.95rem;margin-bottom:10px;'>{_company}</div>
      <div style='color:#64748b;font-size:0.75rem;margin-bottom:4px;'>상품명</div>
      <div style='color:#1e3a8a;font-weight:700;font-size:0.95rem;margin-bottom:10px;'>{_product}</div>
      {"<div style='color:#64748b;font-size:0.75rem;margin-bottom:4px;'>가입일</div><div style='color:#1e3a8a;font-weight:700;font-size:0.95rem;margin-bottom:10px;'>" + _join_date + "</div>" if _join_date else ""}
      {"<div style='color:#64748b;font-size:0.75rem;margin-bottom:4px;'>증권번호</div><div style='color:#1e3a8a;font-weight:700;font-size:0.95rem;'>" + _policy_num + "</div>" if _policy_num else ""}
    </div>""", unsafe_allow_html=True)
            
            # 수동 수정 옵션
            with st.expander("✏️ 정보 수정 (필요시)", expanded=False):
                _edit_company = st.text_input("보험사", value=_company, key=f"edit_company_{sel_pid}")
                _edit_product = st.text_input("상품명", value=_product, key=f"edit_product_{sel_pid}")
                _edit_date = st.text_input("가입일 (YYYY-MM-DD)", value=_join_date, key=f"edit_date_{sel_pid}")
                _edit_policy_num = st.text_input("증권번호", value=_policy_num, key=f"edit_policy_num_{sel_pid}")
            
            # DB 저장 버튼
            if st.button("💾 증권 정보 DB 저장", key=f"crm_scan_save_{sel_pid}", type="primary"):
                try:
                    from crm_fortress import upsert_policy, link_policy_role
                    from db_utils import get_supabase_client
                    import uuid
                    from datetime import datetime
                    
                    _final_company = st.session_state.get(f"edit_company_{sel_pid}", _company)
                    _final_product = st.session_state.get(f"edit_product_{sel_pid}", _product)
                    _final_date = st.session_state.get(f"edit_date_{sel_pid}", _join_date)
                    _final_policy_num = st.session_state.get(f"edit_policy_num_{sel_pid}", _policy_num)
                    
                    # Supabase policies 테이블에 저장
                    _policy_id = str(uuid.uuid4())
                    _sb = get_supabase_client()
                    
                    _policy_data = {
                        "id": _policy_id,
                        "policy_number": _final_policy_num or f"SCAN_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "insurance_company": _final_company,
                        "product_name": _final_product,
                        "contract_date": _final_date or None,
                        "agent_id": user_id,
                        "is_deleted": False,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                    
                    _sb.table("policies").insert(_policy_data).execute()
                    
                    # policy_roles 테이블에 피보험자 연결
                    _role_data = {
                        "id": str(uuid.uuid4()),
                        "policy_id": _policy_id,
                        "person_id": sel_pid,
                        "role": "피보험자",
                        "agent_id": user_id,
                        "is_deleted": False,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    _sb.table("policy_roles").insert(_role_data).execute()
                    
                    # GCS에 원본 이미지 암호화 저장
                    _gcs_path = ""
                    try:
                        from utils.crypto_utils import encrypt_data
                        from shared_components import get_env_secret
                        from google.cloud import storage
                        
                        _enc_key = get_env_secret("ENCRYPTION_KEY", "")
                        _enc_img = encrypt_data(_scan_img, _enc_key)
                        
                        _gcs_client = storage.Client()
                        _bucket_name = "goldkey-customer-profiles"
                        _bucket = _gcs_client.bucket(_bucket_name)
                        _blob_path = f"scanned_policies/{user_id}/{sel_pid}_scan_{datetime.now().strftime('%Y%m%d%H%M%S')}.enc"
                        _blob = _bucket.blob(_blob_path)
                        _blob.upload_from_string(_enc_img)
                        _gcs_path = f"gs://{_bucket_name}/{_blob_path}"
                    except Exception as _gcs_e:
                        st.warning(f"GCS 백업 실패 (DB는 저장됨): {_gcs_e}")
                    
                    # [GP-PHASE3] gk_scan_files 테이블에 메타데이터 저장
                    if _gcs_path:
                        try:
                            import db_utils as du
                            du.save_scan_file(
                                person_id=sel_pid,
                                agent_id=user_id,
                                file_type="policy",
                                gcs_path=_gcs_path,
                                file_name=f"scan_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg",
                                gcs_bucket=_bucket_name,
                                file_size_bytes=len(_scan_img),
                                mime_type="image/jpeg",
                                tags=["증권스캔", _final_company, _final_product],
                                category="policy_scan",
                                extracted_fields={
                                    "insurance_company": _final_company,
                                    "product_name": _final_product,
                                    "join_date": _final_date,
                                    "policy_number": _final_policy_num,
                                    "confidence": _conf,
                                },
                            )
                        except Exception:
                            pass
                    
                    st.success(f"✅ 증권 정보가 저장되었습니다!\n\n보험사: {_final_company}\n상품명: {_final_product}")
                    st.balloons()
                    
                    # 초기화
                    st.session_state["_crm_scan_img"] = None
                    st.session_state["_crm_scan_result"] = None
                    st.session_state["_crm_scan_analyzing"] = False
                    
                except Exception as _save_e:
                    st.error(f"❌ 저장 실패: {str(_save_e)}")
            
            if st.button("🔄 새로운 증권 스캔", key=f"crm_scan_new_{sel_pid}"):
                st.session_state["_crm_scan_img"] = None
                st.session_state["_crm_scan_result"] = None
                st.session_state["_crm_scan_analyzing"] = False
                st.rerun()
