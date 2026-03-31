"""
골드키 CRM - 음성 상담 분석 블록
Gemini 1.5 Pro를 활용한 STT 및 쟁점 분석 UI

작성일: 2026-03-30
"""

import streamlit as st
import os
import tempfile
from typing import Optional
from engines.voice_analyzer import VoiceAnalyzer


def render_crm_voice_consultation_block(
    sel_pid: str,
    user_id: str,
    customer_name: str = "고객"
):
    """
    음성 상담 분석 블록 렌더링
    
    Args:
        sel_pid: 선택된 고객 person_id
        user_id: 현재 사용자(설계사) ID
        customer_name: 고객 이름
    """
    
    # 세션 초기화
    if f"voice_analysis_{sel_pid}" not in st.session_state:
        st.session_state[f"voice_analysis_{sel_pid}"] = {
            "analyzed": False,
            "result": None,
            "audio_file_name": None
        }
    
    # 헤더
    st.markdown("""
    <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 50%,#fcd34d 100%);
      border-radius:14px;padding:18px 22px 14px 22px;margin-bottom:16px;border-left:4px solid #f59e0b;'>
      <div style='color:#92400e;font-size:1.15rem;font-weight:900;letter-spacing:0.04em;'>
    🎙️ 음성 상담 분석 (STT & 쟁점 요약)
      </div>
      <div style='color:#78350f;font-size:0.80rem;margin-top:5px;'>
    통화 녹음 파일을 업로드하면 AI가 대화 내용을 분석하여 핵심 쟁점과 다음 할 일을 도출합니다
      </div>
    </div>""", unsafe_allow_html=True)
    
    # 파일 업로드
    st.markdown("### 📁 통화 녹음 파일 업로드")
    
    uploaded_file = st.file_uploader(
        "MP3, M4A, WAV 등의 오디오 파일을 선택하세요",
        type=["mp3", "m4a", "wav", "ogg", "flac", "aac"],
        key=f"voice_upload_{sel_pid}",
        help="고객과의 통화 녹음 파일을 업로드하세요. Gemini 1.5 Pro가 자동으로 분석합니다."
    )
    
    if uploaded_file is not None:
        # 파일 정보 표시
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"📎 **업로드된 파일**: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        # 분석 버튼
        col1, col2 = st.columns([1, 3])
        
        with col1:
            analyze_btn = st.button(
                "🎯 AI 분석 시작",
                type="primary",
                use_container_width=True,
                key=f"analyze_voice_{sel_pid}"
            )
        
        if analyze_btn:
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_file_path = tmp_file.name
            
            try:
                with st.spinner("🎙️ Gemini 1.5 Pro가 음성 파일을 분석하고 있습니다... (1-2분 소요)"):
                    # Gemini API 키 가져오기
                    try:
                        from modules.auth import get_env_secret
                        gemini_api_key = get_env_secret("GEMINI_API_KEY")
                    except:
                        gemini_api_key = os.getenv("GEMINI_API_KEY")
                    
                    if not gemini_api_key:
                        st.error("❌ Gemini API 키가 설정되지 않았습니다. 환경변수 GEMINI_API_KEY를 설정하세요.")
                        return
                    
                    # VoiceAnalyzer 초기화 및 분석
                    analyzer = VoiceAnalyzer(gemini_api_key=gemini_api_key)
                    result = analyzer.analyze_voice_consultation(
                        audio_file_path=tmp_file_path,
                        customer_name=customer_name
                    )
                    
                    # 결과 저장
                    st.session_state[f"voice_analysis_{sel_pid}"]["analyzed"] = True
                    st.session_state[f"voice_analysis_{sel_pid}"]["result"] = result
                    st.session_state[f"voice_analysis_{sel_pid}"]["audio_file_name"] = uploaded_file.name
                
                # 임시 파일 삭제
                os.unlink(tmp_file_path)
                
                if result["success"]:
                    st.success("✅ 음성 분석 완료!")
                    st.rerun()
                else:
                    st.error(f"❌ 분석 실패: {result['error']}")
            
            except Exception as e:
                st.error(f"❌ 분석 중 오류 발생: {e}")
                # 임시 파일 삭제
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    
    # 분석 결과 표시
    if st.session_state[f"voice_analysis_{sel_pid}"]["analyzed"]:
        result = st.session_state[f"voice_analysis_{sel_pid}"]["result"]
        audio_file_name = st.session_state[f"voice_analysis_{sel_pid}"]["audio_file_name"]
        
        if result and result["success"]:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            
            # 분석 완료 알림
            st.markdown(f"""
            <div style='background:#dcfce7;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #16a34a;'>
              <div style='color:#166534;font-size:0.95rem;font-weight:700;'>
            ✅ 분석 완료: {audio_file_name}
              </div>
            </div>""", unsafe_allow_html=True)
            
            # ═══ 1. 전체 대화 스크립트 ═══
            st.markdown("""
            <div style='background:#f0f9ff;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #0284c7;'>
              <div style='color:#075985;font-size:1rem;font-weight:700;margin-bottom:8px;'>
            📝 전체 대화 스크립트 (STT)
              </div>
            </div>""", unsafe_allow_html=True)
            
            with st.expander("📄 전체 대화 내용 보기", expanded=True):
                st.text_area(
                    "대화 스크립트",
                    value=result["transcript"],
                    height=300,
                    key=f"transcript_{sel_pid}",
                    label_visibility="collapsed"
                )
            
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
            
            # ═══ 2. 핵심 쟁점 3줄 요약 ═══
            st.markdown("""
            <div style='background:#fef3c7;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #f59e0b;'>
              <div style='color:#92400e;font-size:1rem;font-weight:700;margin-bottom:8px;'>
            💡 핵심 쟁점 3줄 요약
              </div>
            </div>""", unsafe_allow_html=True)
            
            if result["key_issues"]:
                for i, issue in enumerate(result["key_issues"], 1):
                    st.markdown(f"**{i}.** {issue}")
            else:
                st.warning("⚠️ 핵심 쟁점을 도출할 수 없습니다.")
            
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
            
            # ═══ 3. Next Action Items ═══
            st.markdown("""
            <div style='background:#dcfce7;border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid #16a34a;'>
              <div style='color:#166534;font-size:1rem;font-weight:700;margin-bottom:8px;'>
            ✅ Next Action Items (다음 할 일)
              </div>
            </div>""", unsafe_allow_html=True)
            
            if result["action_items"]:
                for i, action in enumerate(result["action_items"], 1):
                    st.checkbox(
                        action,
                        key=f"action_{sel_pid}_{i}",
                        value=False
                    )
            else:
                st.warning("⚠️ 액션 아이템을 도출할 수 없습니다.")
            
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
            
            # ═══ 4. 원본 결과 (디버깅용) ═══
            with st.expander("🔍 원본 분석 결과 (전체)", expanded=False):
                st.text_area(
                    "Gemini 원본 출력",
                    value=result.get("raw_result", ""),
                    height=400,
                    key=f"raw_result_{sel_pid}",
                    label_visibility="collapsed"
                )
            
            # ═══ 5. 재분석 버튼 ═══
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
            
            if st.button("🔄 다시 분석하기", key=f"reanalyze_{sel_pid}"):
                st.session_state[f"voice_analysis_{sel_pid}"]["analyzed"] = False
                st.session_state[f"voice_analysis_{sel_pid}"]["result"] = None
                st.session_state[f"voice_analysis_{sel_pid}"]["audio_file_name"] = None
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 테스트 코드
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    st.set_page_config(page_title="음성 상담 분석 블록 테스트", layout="wide")
    
    st.title("🎙️ 음성 상담 분석 블록 테스트")
    
    # 테스트용 더미 데이터
    render_crm_voice_consultation_block(
        sel_pid="test_person_id",
        user_id="test_user_id",
        customer_name="홍길동"
    )
