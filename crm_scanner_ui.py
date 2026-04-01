"""
crm_scanner_ui.py — 전문가용 빌딩급 AI 스캔 모듈 및 OCR 파이프라인
[GP-STEP6] Goldkey AI Masters 2026

빌딩급 OCR 파이프라인:
- AR 가이드 카메라 UI (수평/사각형 가이드)
- 비동기 OCR 처리 (GCS 업로드 + Cloud Run 엔진)
- 실시간 추출 피드 (Live Feed)
- 12단계 자동 전환 (3단계 → 4단계)
"""
from __future__ import annotations
import re, json, datetime, uuid, base64
from typing import Optional, Dict, Any, List
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] GCS 업로드 및 Cloud Run OCR 엔진 호출
# ══════════════════════════════════════════════════════════════════════════════

def _get_gcs_client():
    """Google Cloud Storage 클라이언트 가져오기"""
    try:
        from google.cloud import storage
        import os
        
        # 환경변수에서 GCS 인증 정보 로드
        credentials_json = os.environ.get("GCS_CREDENTIALS_JSON")
        if credentials_json:
            import json
            from google.oauth2 import service_account
            creds_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return storage.Client(credentials=credentials)
        else:
            # 로컬 개발 환경 (Application Default Credentials)
            return storage.Client()
    except Exception:
        return None


def upload_to_gcs(
    file_bytes: bytes,
    filename: str,
    agent_id: str,
    person_id: str,
    bucket_name: str = "goldkey-ai-scans"
) -> Optional[str]:
    """
    이미지를 GCS에 업로드
    
    Args:
        file_bytes: 이미지 바이트
        filename: 파일명
        agent_id: 설계사 ID
        person_id: 고객 UUID
        bucket_name: GCS 버킷명
    
    Returns:
        str: GCS 공개 URL 또는 None
    """
    try:
        client = _get_gcs_client()
        if not client:
            return None
        
        bucket = client.bucket(bucket_name)
        
        # 파일 경로: {agent_id}/{person_id}/{timestamp}_{filename}
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"{agent_id}/{person_id}/{timestamp}_{filename}"
        
        blob = bucket.blob(blob_name)
        blob.upload_from_string(file_bytes, content_type="image/jpeg")
        
        # 공개 URL 반환
        return f"gs://{bucket_name}/{blob_name}"
    except Exception:
        return None


def call_cloud_run_ocr(
    gcs_url: str,
    agent_id: str,
    person_id: str
) -> Optional[Dict[str, Any]]:
    """
    Cloud Run OCR 엔진 호출 (비동기)
    
    Args:
        gcs_url: GCS 파일 URL
        agent_id: 설계사 ID
        person_id: 고객 UUID
    
    Returns:
        dict: OCR 결과 또는 None
    """
    try:
        import requests
        import os
        
        cloud_run_url = os.environ.get("CLOUD_RUN_OCR_URL", "https://goldkey-ocr-xxxxxx.run.app/api/ocr")
        
        response = requests.post(
            cloud_run_url,
            json={
                "gcs_url": gcs_url,
                "agent_id": agent_id,
                "person_id": person_id
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('CLOUD_RUN_API_KEY', '')}"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# [2] AR 가이드 카메라 UI
# ══════════════════════════════════════════════════════════════════════════════

def render_ar_camera_guide():
    """
    AR 가이드 카메라 UI (수평/사각형 가이드 오버레이)
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:10px;'>"
        "📸 증권 스캔 (AR 가이드)</div>",
        unsafe_allow_html=True
    )
    
    # AR 가이드 CSS + HTML
    ar_guide_html = """
    <style>
    .ar-camera-container {
        position: relative;
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
        background: linear-gradient(135deg, #F3F4F6, #E0E7FF);
        border: 2px solid #93C5FD;
        border-radius: 12px;
        padding: 20px;
        min-height: 400px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    .ar-guide-frame {
        position: relative;
        width: 90%;
        max-width: 500px;
        aspect-ratio: 1.414;  /* A4 비율 */
        border: 3px dashed #3B82F6;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .ar-guide-corner {
        position: absolute;
        width: 30px;
        height: 30px;
        border: 3px solid #1E3A8A;
    }
    
    .ar-guide-corner.top-left {
        top: -3px;
        left: -3px;
        border-right: none;
        border-bottom: none;
        border-radius: 8px 0 0 0;
    }
    
    .ar-guide-corner.top-right {
        top: -3px;
        right: -3px;
        border-left: none;
        border-bottom: none;
        border-radius: 0 8px 0 0;
    }
    
    .ar-guide-corner.bottom-left {
        bottom: -3px;
        left: -3px;
        border-right: none;
        border-top: none;
        border-radius: 0 0 0 8px;
    }
    
    .ar-guide-corner.bottom-right {
        bottom: -3px;
        right: -3px;
        border-left: none;
        border-top: none;
        border-radius: 0 0 8px 0;
    }
    
    .ar-guide-text {
        font-size: 0.9rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        padding: 12px;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
    }
    
    .ar-level-indicator {
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: #E2E8F0;
        border-radius: 2px;
        overflow: hidden;
    }
    
    .ar-level-bubble {
        width: 20px;
        height: 4px;
        background: #22C55E;
        border-radius: 2px;
        position: absolute;
        left: 40px;  /* 중앙 위치 */
        animation: level-pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes level-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    </style>
    
    <div class='ar-camera-container'>
        <div class='ar-level-indicator'>
            <div class='ar-level-bubble'></div>
        </div>
        
        <div class='ar-guide-frame'>
            <div class='ar-guide-corner top-left'></div>
            <div class='ar-guide-corner top-right'></div>
            <div class='ar-guide-corner bottom-left'></div>
            <div class='ar-guide-corner bottom-right'></div>
            
            <div class='ar-guide-text'>
                증권을 가이드 프레임 안에<br>
                수평으로 맞춰주세요
            </div>
        </div>
    </div>
    """
    
    st.markdown(ar_guide_html, unsafe_allow_html=True)


def render_camera_controls():
    """
    카메라 컨트롤 버튼 (촬영/플래시/갤러리)
    """
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        camera_btn = st.button(
            "📸 촬영",
            key="scanner_camera_btn",
            use_container_width=True,
            help="카메라로 증권 촬영"
        )
    
    with col2:
        flash_btn = st.button(
            "💡 플래시",
            key="scanner_flash_btn",
            use_container_width=True,
            help="플래시 ON/OFF"
        )
    
    with col3:
        gallery_btn = st.button(
            "🖼️ 갤러리",
            key="scanner_gallery_btn",
            use_container_width=True,
            help="갤러리에서 이미지 불러오기"
        )
    
    return camera_btn, flash_btn, gallery_btn


# ══════════════════════════════════════════════════════════════════════════════
# [3] 파일 업로드 UI (갤러리 대체)
# ══════════════════════════════════════════════════════════════════════════════

def render_file_uploader(person_id: str, agent_id: str):
    """
    파일 업로드 UI (모바일 갤러리 대체)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    """
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "증권 이미지 업로드",
        type=["jpg", "jpeg", "png", "pdf"],
        key=f"scanner_uploader_{person_id}",
        help="증권 사진 또는 PDF를 업로드하세요",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        return uploaded_file
    
    return None


# ══════════════════════════════════════════════════════════════════════════════
# [4] 비동기 OCR 처리 프로세스 (loading_skeleton 활용)
# ══════════════════════════════════════════════════════════════════════════════

def process_ocr_async(
    file_bytes: bytes,
    filename: str,
    agent_id: str,
    person_id: str
) -> Optional[Dict[str, Any]]:
    """
    비동기 OCR 처리 파이프라인
    
    Args:
        file_bytes: 이미지 바이트
        filename: 파일명
        agent_id: 설계사 ID
        person_id: 고객 UUID
    
    Returns:
        dict: OCR 결과 또는 None
    """
    from loading_skeleton import render_loading_progress
    
    # 1단계: GCS 업로드
    with st.spinner(""):
        render_loading_progress(
            message="이미지를 클라우드에 업로드 중...",
            progress=20,
            hint="Google Cloud Storage 업로드"
        )
        
        gcs_url = upload_to_gcs(file_bytes, filename, agent_id, person_id)
        
        if not gcs_url:
            st.error("❌ 이미지 업로드에 실패했습니다.")
            return None
    
    # 2단계: Cloud Run OCR 엔진 호출
    with st.spinner(""):
        render_loading_progress(
            message="AI가 증권을 분석 중입니다...",
            progress=50,
            hint="보험사명, 상품명, 보험료 추출 중"
        )
        
        ocr_result = call_cloud_run_ocr(gcs_url, agent_id, person_id)
        
        if not ocr_result:
            st.error("❌ OCR 분석에 실패했습니다.")
            return None
    
    # 3단계: 데이터 파싱 및 저장
    with st.spinner(""):
        render_loading_progress(
            message="데이터를 정리하고 저장 중...",
            progress=80,
            hint="gk_policies 테이블 저장"
        )
        
        # gk_policies 테이블에 저장
        save_result = save_ocr_to_policies(ocr_result, agent_id, person_id, gcs_url)
        
        if not save_result:
            st.error("❌ 데이터 저장에 실패했습니다.")
            return None
    
    # 4단계: 12단계 전환 (3단계 → 4단계)
    with st.spinner(""):
        render_loading_progress(
            message="고객 단계를 업데이트 중...",
            progress=95,
            hint="3단계(정보 수집) → 4단계(분석 진행)"
        )
        
        update_customer_stage(person_id, agent_id, new_stage=4)
    
    # 완료
    render_loading_progress(
        message="✅ 스캔 완료!",
        progress=100,
        hint="분석 결과를 확인하세요"
    )
    
    return ocr_result


def render_loading_progress(message: str, progress: int, hint: str = ""):
    """
    로딩 진행률 표시 (배화 현상 차단)
    
    Args:
        message: 메인 메시지
        progress: 진행률 (0~100)
        hint: 힌트 텍스트
    """
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#EFF6FF,#DBEAFE);"
        f"border:1.5px solid #93C5FD;border-radius:10px;padding:16px;margin:12px 0;'>"
        f"<div style='font-size:.9rem;font-weight:700;color:#1E3A8A;margin-bottom:8px;'>{message}</div>"
        f"<div style='background:#E2E8F0;border-radius:8px;height:12px;overflow:hidden;margin-bottom:6px;'>"
        f"<div style='background:linear-gradient(90deg,#3B82F6,#60A5FA);width:{progress}%;"
        f"height:100%;transition:width .4s ease;'></div>"
        f"</div>"
        f"<div style='font-size:.75rem;color:#64748B;text-align:right;'>{hint}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [5] 데이터 매핑 및 12단계 전환
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    """Supabase 클라이언트 가져오기"""
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def save_ocr_to_policies(
    ocr_result: Dict[str, Any],
    agent_id: str,
    person_id: str,
    gcs_url: str
) -> bool:
    """
    OCR 결과를 gk_policies 테이블에 저장
    
    Args:
        ocr_result: OCR 결과
        agent_id: 설계사 ID
        person_id: 고객 UUID
        gcs_url: GCS 파일 URL
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        # OCR 결과에서 주요 필드 추출
        raw_text = ocr_result.get("raw_text", "")
        parsed_data = ocr_result.get("parsed_data", {})
        
        policy_data = {
            "policy_number": parsed_data.get("policy_number", ""),
            "insurance_company": parsed_data.get("insurance_company", ""),
            "product_name": parsed_data.get("product_name", ""),
            "product_type": parsed_data.get("product_type", ""),
            "contract_date": parsed_data.get("contract_date", ""),
            "expiry_date": parsed_data.get("expiry_date", ""),
            "premium": parsed_data.get("premium", 0),
            "payment_period": parsed_data.get("payment_period", ""),
            "coverage_period": parsed_data.get("coverage_period", ""),
            "raw_text": raw_text,
            "source": "ocr",
            "agent_id": agent_id
        }
        
        # gk_policies 테이블에 저장
        result = sb.table("gk_policies").insert(policy_data).execute()
        
        if not result.data:
            return False
        
        policy_id = result.data[0].get("id")
        
        # gk_policy_roles 테이블에 연결 (피보험자로 자동 연결)
        role_data = {
            "policy_id": policy_id,
            "person_id": person_id,
            "role": "피보험자",
            "agent_id": agent_id
        }
        
        sb.table("gk_policy_roles").insert(role_data).execute()
        
        return True
    except Exception:
        return False


def update_customer_stage(person_id: str, agent_id: str, new_stage: int) -> bool:
    """
    고객 세일즈 단계 업데이트
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        new_stage: 새로운 단계 (1~12)
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        # gk_people 테이블 업데이트
        result = (
            sb.table("gk_people")
            .update({"current_stage": new_stage})
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        
        return bool(result.data)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [6] 실시간 추출 피드 (Live Feed)
# ══════════════════════════════════════════════════════════════════════════════

def render_live_extraction_feed(ocr_result: Optional[Dict[str, Any]]):
    """
    실시간 추출 피드 (AI가 읽어내는 키워드 시각화)
    
    Args:
        ocr_result: OCR 결과
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin:16px 0 10px;'>"
        "🔍 실시간 추출 피드 (Live Feed)</div>",
        unsafe_allow_html=True
    )
    
    if not ocr_result:
        st.info("스캔을 시작하면 AI가 읽어내는 키워드가 실시간으로 표시됩니다.")
        return
    
    parsed_data = ocr_result.get("parsed_data", {})
    
    # 추출된 키워드 목록
    keywords = [
        ("보험사", parsed_data.get("insurance_company", "추출 중...")),
        ("상품명", parsed_data.get("product_name", "추출 중...")),
        ("증권번호", parsed_data.get("policy_number", "추출 중...")),
        ("월 보험료", f"{parsed_data.get('premium', 0):,}원" if parsed_data.get('premium') else "추출 중..."),
        ("계약일", parsed_data.get("contract_date", "추출 중...")),
        ("만기일", parsed_data.get("expiry_date", "추출 중..."))
    ]
    
    # 키워드 카드 렌더링
    for idx, (label, value) in enumerate(keywords):
        # 애니메이션 딜레이 (순차적으로 나타남)
        delay = idx * 0.1
        
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#F0FDF4,#DCFCE7);"
            f"border:1px solid #22C55E;border-radius:8px;padding:10px 12px;margin-bottom:8px;"
            f"animation:fade-in-up 0.5s ease-out {delay}s both;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<span style='font-size:.82rem;font-weight:700;color:#166534;'>{label}</span>"
            f"<span style='font-size:.85rem;color:#14532D;'>{value}</span>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # 애니메이션 CSS
    st.markdown("""
    <style>
    @keyframes fade-in-up {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [7] 메인 렌더링 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_scanner_module(person_id: str, agent_id: str, customer_name: str = ""):
    """
    전문가용 빌딩급 AI 스캔 모듈 메인 렌더링
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
    """
    st.markdown(
        f"<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        f"🏗️ 빌딩급 AI 스캔 모듈 — {customer_name}</div>",
        unsafe_allow_html=True
    )
    
    # 2분할 레이아웃 (좌측: 카메라, 우측: 실시간 피드)
    col1, col2 = st.columns([1.2, 1], gap="medium")
    
    with col1:
        # AR 가이드 카메라 UI
        render_ar_camera_guide()
        
        # 카메라 컨트롤 버튼
        camera_btn, flash_btn, gallery_btn = render_camera_controls()
        
        # 파일 업로더 (갤러리 대체)
        uploaded_file = render_file_uploader(person_id, agent_id)
        
        # 스캔 시작 버튼
        if uploaded_file:
            st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
            
            if st.button("🚀 스캔 시작", key=f"start_scan_{person_id}", use_container_width=True):
                # 파일 바이트 읽기
                file_bytes = uploaded_file.read()
                filename = uploaded_file.name
                
                # 비동기 OCR 처리
                ocr_result = process_ocr_async(file_bytes, filename, agent_id, person_id)
                
                if ocr_result:
                    st.session_state[f"ocr_result_{person_id}"] = ocr_result
                    st.success("✅ 스캔이 완료되었습니다!")
                    st.rerun()
    
    with col2:
        # 실시간 추출 피드
        ocr_result = st.session_state.get(f"ocr_result_{person_id}")
        render_live_extraction_feed(ocr_result)
        
        # OCR 결과 상세 보기
        if ocr_result:
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            
            with st.expander("📄 전체 추출 텍스트 보기", expanded=False):
                raw_text = ocr_result.get("raw_text", "")
                st.text_area(
                    "추출된 텍스트",
                    value=raw_text,
                    height=200,
                    key=f"raw_text_{person_id}",
                    label_visibility="collapsed"
                )


# ══════════════════════════════════════════════════════════════════════════════
# [8] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (crm_app_impl.py 통합)

```python
from crm_scanner_ui import render_scanner_module

# 고객 상세 페이지에서 스캔 모듈 렌더링
if st.session_state.get("crm_spa_screen") == "scanner":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    customer_name = st.session_state.get("crm_customer_name", "")
    
    if person_id and agent_id:
        render_scanner_module(person_id, agent_id, customer_name)
```

## Cloud Run OCR 엔진 API 스펙

### Endpoint
```
POST https://goldkey-ocr-xxxxxx.run.app/api/ocr
```

### Request Body
```json
{
    "gcs_url": "gs://goldkey-ai-scans/agent123/person456/20260401_120000_policy.jpg",
    "agent_id": "agent123",
    "person_id": "person456"
}
```

### Response Body
```json
{
    "status": "success",
    "raw_text": "삼성생명보험주식회사\\n증권번호: 1234567890\\n...",
    "parsed_data": {
        "insurance_company": "삼성생명",
        "product_name": "삼성생명 암보험",
        "policy_number": "1234567890",
        "premium": 150000,
        "contract_date": "2025-01-01",
        "expiry_date": "2045-01-01",
        "payment_period": "20년납",
        "coverage_period": "100세만기"
    }
}
```

## 환경변수 설정

### .streamlit/secrets.toml
```toml
[gcs]
credentials_json = '''
{
  "type": "service_account",
  "project_id": "goldkey-ai-masters",
  ...
}
'''

[cloud_run]
ocr_url = "https://goldkey-ocr-xxxxxx.run.app/api/ocr"
api_key = "your-api-key-here"
```
"""
