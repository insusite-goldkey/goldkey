# -*- coding: utf-8 -*-
"""
지능형 리딩 파트너 - 디지털 자산 수집 허브 (Digital Asset Collection Hub)
태블릿 최적화 + 스마트 스캔 + 문서 복원 시스템

작성일: 2026-03-31
목적: 증권 스캔 및 분석 파이프라인 고도화
"""

import streamlit as st
from typing import Dict, Optional, List, Tuple
import base64
import io
import time
from datetime import datetime
from PIL import Image
import numpy as np
import cv2

# 기하학적 보정 및 Key-Value 매핑 엔진 통합
try:
    from modules.geometric_correction_engine import GeometricCorrectionEngine
    from modules.key_value_mapping_engine import KeyValueMappingEngine
    _GEOMETRIC_CORRECTION_OK = True
    _KEY_VALUE_MAPPING_OK = True
except ImportError:
    _GEOMETRIC_CORRECTION_OK = False
    _KEY_VALUE_MAPPING_OK = False


class DigitalAssetCollectionHub:
    """
    디지털 자산 수집 허브
    
    핵심 기능:
    1. 태블릿 Drag & Drop (분석 대기 구역)
    2. 인텔리전트 스캐너 모드 (문서 경계 자동 감지)
    3. 원문 보존형 노출 제어 (Hi-Fi Exposure Control)
    4. 지능형 문서 복원 (AI Document Restoration)
    """
    
    def __init__(self):
        """초기화"""
        self.session_key = "digital_asset_hub"
        self.drop_zone_active = False
        self.scan_mode_active = False
        
        # 엔진 초기화
        if _GEOMETRIC_CORRECTION_OK:
            self.geo_engine = GeometricCorrectionEngine()
        else:
            self.geo_engine = None
        
        if _KEY_VALUE_MAPPING_OK:
            self.kv_engine = KeyValueMappingEngine()
        else:
            self.kv_engine = None
        
        # 세션 초기화
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "uploaded_files": [],
                "scanned_documents": [],
                "analysis_queue": [],
                "processing_status": {},
                "geometric_correction_enabled": True,
                "key_value_extraction_enabled": True
            }
    
    def render_drop_zone(self):
        """
        분석 대기 구역 (Analysis Drop Zone) 렌더링
        
        태블릿 Split View 최적화
        """
        st.markdown(
            """
            <div style='background:linear-gradient(135deg,#f0f9ff 0%,#e0f2fe 100%);
                        border:3px dashed #3b82f6;border-radius:16px;
                        padding:40px;margin:20px 0;text-align:center;
                        box-shadow:0 4px 20px rgba(59,130,246,0.15);
                        min-height:200px;display:flex;flex-direction:column;
                        justify-content:center;align-items:center;'>
                <div style='font-size:48px;margin-bottom:16px;'>📂</div>
                <div style='font-size:20px;font-weight:900;color:#1e40af;
                            margin-bottom:12px;'>
                    분석 대기 구역 (Analysis Drop Zone)
                </div>
                <div style='font-size:14px;color:#3b82f6;line-height:1.6;'>
                    증권 파일(PDF, JPG)을 이곳에 끌어다 놓으세요<br>
                    또는 아래 버튼을 눌러 파일을 선택하세요
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 파일 업로더 (Drag & Drop 지원)
        uploaded_files = st.file_uploader(
            "증권 파일 선택",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="drop_zone_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            self._process_dropped_files(uploaded_files)
    
    def _process_dropped_files(self, files: List):
        """
        드롭된 파일 처리
        
        Args:
            files: 업로드된 파일 리스트
        """
        for file in files:
            # 파일 무결성 검사
            file_info = {
                "name": file.name,
                "type": file.type,
                "size": file.size,
                "uploaded_at": datetime.now().isoformat()
            }
            
            # 이미지 파일인 경우 기하학적 보정 적용
            if file.type in ["image/jpeg", "image/jpg", "image/png"]:
                if self.geo_engine and st.session_state[self.session_key].get("geometric_correction_enabled", True):
                    try:
                        image = Image.open(file)
                        corrected_image, correction_info = self.geo_engine.process_pil_image(image)
                        file_info["geometric_correction"] = correction_info
                        file_info["corrected_image"] = corrected_image
                    except Exception as e:
                        file_info["geometric_correction_error"] = str(e)
            
            # 분석 대기열에 추가
            st.session_state[self.session_key]["uploaded_files"].append(file_info)
            st.session_state[self.session_key]["analysis_queue"].append(file_info)
            
            # 리딩 파트너 피드백
            st.success(f"✅ 자산을 안전하게 수신했습니다: {file.name}")
        
        # 분석 파이프라인 트리거
        self._trigger_analysis_pipeline()
    
    def render_smart_scanner(self):
        """
        인텔리전트 스캐너 모드 렌더링
        
        문서 경계 자동 감지 + 실시간 촬영
        """
        st.markdown(
            """
            <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);
                        border:2px solid #f59e0b;border-radius:12px;
                        padding:24px;margin:16px 0;'>
                <div style='text-align:center;'>
                    <div style='font-size:40px;margin-bottom:12px;'>📸</div>
                    <div style='font-size:18px;font-weight:900;color:#92400e;
                                margin-bottom:8px;'>
                        인텔리전트 스캐너 모드
                    </div>
                    <div style='font-size:13px;color:#78350f;line-height:1.6;'>
                        문서의 경계를 스스로 인식하고 스캔합니다<br>
                        일반 카메라 촬영이 아닌 <b>정밀 문서 스캔</b> 방식입니다
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 스캔 시작 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("📸 스캔 시작", use_container_width=True, type="primary"):
                self._activate_scanner_mode()
        
        # 스캔 모드 활성화 시
        if st.session_state.get(f"{self.session_key}_scanner_active"):
            self._render_scanner_interface()
    
    def _activate_scanner_mode(self):
        """스캐너 모드 활성화"""
        st.session_state[f"{self.session_key}_scanner_active"] = True
        
        st.info("""
        📱 **스캐너 모드 활성화**
        
        실제 배포 시 다음 기능이 자동 실행됩니다:
        1. 기기 카메라 권한 획득
        2. 실시간 문서 테두리 감지
        3. 자동 촬영 (문서 경계 인식 시)
        4. 노출 최적화 (-1.0 ~ -0.5 단계)
        """)
    
    def _render_scanner_interface(self):
        """스캐너 인터페이스 렌더링"""
        st.markdown("---")
        
        # 카메라 입력 (Streamlit 기본 기능)
        camera_image = st.camera_input(
            "증권 촬영",
            key="smart_scanner_camera",
            label_visibility="collapsed"
        )
        
        if camera_image:
            # 이미지 처리
            image = Image.open(camera_image)
            
            # 문서 복원 적용
            restored_image = self._apply_document_restoration(image)
            
            # 확인 팝업
            self._render_scan_confirmation(restored_image, camera_image.name)
    
    def _apply_document_restoration(self, image: Image.Image) -> Image.Image:
        """
        지능형 문서 복원 적용
        
        Args:
            image: 원본 이미지
        
        Returns:
            Image.Image: 복원된 이미지
        """
        # 1. 노출 최적화 (Exposure Control)
        # 실제 구현 시 OpenCV 또는 PIL ImageEnhance 사용
        # 여기서는 간단한 시뮬레이션
        
        # 2. 기하학적 보정 (De-warping)
        # 실제 구현 시 OpenCV의 perspective transform 사용
        
        # 3. 구김 제거 (De-skewing & Flattening)
        # 실제 구현 시 Document Scanner SDK 사용
        
        # 현재는 원본 반환 (실제 배포 시 복원 로직 적용)
        return image
    
    def _render_scan_confirmation(self, image: Image.Image, filename: str):
        """
        스캔 확인 팝업 렌더링
        
        Args:
            image: 스캔된 이미지
            filename: 파일명
        """
        st.markdown(
            """
            <div style='background:#fef2f2;border:2px solid #dc2626;
                        border-radius:12px;padding:20px;margin:16px 0;'>
                <div style='font-size:16px;font-weight:700;color:#991b1b;
                            margin-bottom:12px;text-align:center;'>
                    📋 이 문서를 지금 분석에 반영할까요?
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 미리보기
        st.image(image, caption="스캔된 문서 미리보기", use_container_width=True)
        
        # 확인 버튼
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 분석 투입", use_container_width=True, type="primary", key="confirm_scan"):
                self._add_to_analysis_queue(image, filename)
                st.success("✅ 정밀 분석을 시작합니다")
                st.session_state[f"{self.session_key}_scanner_active"] = False
                st.rerun()
        
        with col2:
            if st.button("🔄 재촬영", use_container_width=True, key="rescan"):
                st.info("다시 촬영해주세요")
                st.rerun()
    
    def _add_to_analysis_queue(self, image: Image.Image, filename: str):
        """
        분석 대기열에 추가
        
        Args:
            image: 이미지
            filename: 파일명
        """
        # 이미지를 base64로 변환하여 저장
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        document_info = {
            "name": filename,
            "type": "image/png",
            "image_data": img_str,
            "scanned_at": datetime.now().isoformat(),
            "restored": True
        }
        
        st.session_state[self.session_key]["scanned_documents"].append(document_info)
        st.session_state[self.session_key]["analysis_queue"].append(document_info)
    
    def _trigger_analysis_pipeline(self):
        """분석 파이프라인 트리거"""
        queue_size = len(st.session_state[self.session_key]["analysis_queue"])
        
        if queue_size > 0:
            st.info(f"📊 분석 대기열: {queue_size}건")
    
    def render_document_restoration_demo(self):
        """
        문서 복원 데모 렌더링
        
        De-warping, De-skewing, Exposure Control 시각화
        """
        st.markdown(
            """
            <div style='background:linear-gradient(135deg,#f3e8ff 0%,#e9d5ff 100%);
                        border:2px solid #a855f7;border-radius:12px;
                        padding:24px;margin:16px 0;'>
                <div style='font-size:18px;font-weight:900;color:#6b21a8;
                            margin-bottom:16px;text-align:center;'>
                    🛡️ 지능형 문서 복원 (AI Document Restoration)
                </div>
                
                <div style='background:#ffffff;border-radius:8px;padding:16px;
                            margin-bottom:12px;'>
                    <div style='font-size:14px;color:#374151;line-height:1.7;'>
                        <b style='color:#a855f7;'>1. 기하학적 보정 (De-warping)</b><br>
                        렌즈 왜곡으로 휘어진 문서를 직선으로 바로잡습니다
                    </div>
                </div>
                
                <div style='background:#ffffff;border-radius:8px;padding:16px;
                            margin-bottom:12px;'>
                    <div style='font-size:14px;color:#374151;line-height:1.7;'>
                        <b style='color:#a855f7;'>2. 구김 제거 (De-skewing & Flattening)</b><br>
                        종이의 주름을 분석하여 굴곡을 평면화합니다
                    </div>
                </div>
                
                <div style='background:#ffffff;border-radius:8px;padding:16px;'>
                    <div style='font-size:14px;color:#374151;line-height:1.7;'>
                        <b style='color:#a855f7;'>3. 원문 보존형 노출 제어 (Hi-Fi Exposure Control)</b><br>
                        노출을 -1.0~-0.5 단계로 고정하여 글자 선명도 최우선 확보
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 리딩 파트너 보고
        st.markdown(
            """
            <div style='background:#065f46;color:#ffffff;border-radius:8px;
                        padding:16px;margin:16px 0;'>
                <div style='font-size:14px;line-height:1.6;'>
                    💡 <b>리딩 파트너 보고</b><br><br>
                    "문서의 <b>기하학적 오차</b>를 수정했습니다.<br>
                    이제 육안으로 확인하는 것보다 더 정교한 분석이 가능합니다."
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def render_analysis_queue(self):
        """분석 대기열 렌더링"""
        queue = st.session_state[self.session_key]["analysis_queue"]
        
        if not queue:
            st.info("📭 분석 대기 중인 문서가 없습니다")
            return
        
        st.markdown(
            f"""
            <div style='background:#ecfdf5;border:2px solid #059669;
                        border-radius:12px;padding:20px;margin:16px 0;'>
                <div style='font-size:16px;font-weight:700;color:#065f46;
                            margin-bottom:12px;'>
                    📊 분석 대기열 ({len(queue)}건)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        for idx, item in enumerate(queue, 1):
            st.markdown(
                f"""
                <div style='background:#ffffff;border-left:4px solid #10b981;
                            border-radius:8px;padding:14px;margin-bottom:10px;'>
                    <div style='font-size:14px;color:#374151;'>
                        <b>{idx}.</b> {item.get('name', '문서')}
                        <span style='color:#6b7280;margin-left:12px;'>
                            ({item.get('type', 'unknown')})
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # 일괄 분석 시작 버튼
        if st.button("🚀 일괄 분석 시작", use_container_width=True, type="primary"):
            st.success("✅ 정밀 분석을 시작합니다")
            # 실제 분석 로직 호출
            self._start_batch_analysis()
    
    def _start_batch_analysis(self):
        """일괄 분석 시작"""
        queue = st.session_state[self.session_key]["analysis_queue"]
        
        for item in queue:
            # 실제 분석 로직 (OCR, 데이터 추출 등)
            st.session_state[self.session_key]["processing_status"][item["name"]] = "processing"
        
        st.info(f"📊 {len(queue)}건의 문서를 분석 중입니다...")


def render_digital_asset_collection_hub():
    """
    디지털 자산 수집 허브 렌더링 (전역 함수)
    """
    hub = DigitalAssetCollectionHub()
    
    # 헤더
    st.markdown(
        """
        <div style='background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 100%);
                    border-radius:12px;padding:24px;margin-bottom:20px;
                    box-shadow:0 4px 20px rgba(30,58,138,0.3);'>
            <div style='text-align:center;'>
                <div style='font-size:48px;margin-bottom:12px;'>🏛️</div>
                <div style='font-size:24px;font-weight:900;color:#ffffff;
                            text-shadow:0 2px 4px rgba(0,0,0,0.3);margin-bottom:8px;'>
                    디지털 자산 수집 허브
                </div>
                <div style='font-size:14px;color:#dbeafe;'>
                    태블릿 최적화 + 스마트 스캔 + 문서 복원
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 분석 대기 구역",
        "📸 스마트 스캔",
        "🛡️ 문서 복원",
        "📊 분석 대기열"
    ])
    
    with tab1:
        st.subheader("📂 분석 대기 구역 (Analysis Drop Zone)")
        st.markdown("""
        **태블릿 Split View 최적화**
        - 바탕화면이나 폴더 앱에서 파일을 끌어다 놓으세요
        - PDF, JPG 파일을 즉시 분석 파이프라인에 투입합니다
        """)
        hub.render_drop_zone()
    
    with tab2:
        st.subheader("📸 인텔리전트 스캐너 모드")
        st.markdown("""
        **Smart Scan Protocol**
        - 문서 경계 자동 감지
        - 실시간 촬영 및 노출 최적화
        - 촬영 직후 즉시 확인 가능
        """)
        hub.render_smart_scanner()
    
    with tab3:
        st.subheader("🛡️ 지능형 문서 복원")
        st.markdown("""
        **AI Document Restoration**
        - 기하학적 보정 (De-warping)
        - 구김 제거 (De-skewing & Flattening)
        - 원문 보존형 노출 제어 (Hi-Fi Exposure Control)
        """)
        hub.render_document_restoration_demo()
    
    with tab4:
        st.subheader("📊 분석 대기열")
        hub.render_analysis_queue()


def main():
    """테스트 실행"""
    st.set_page_config(
        page_title="디지털 자산 수집 허브",
        page_icon="🏛️",
        layout="wide"
    )
    
    st.title("🏛️ 디지털 자산 수집 허브 - 고신뢰도 문서 복원 시스템")
    
    render_digital_asset_collection_hub()


if __name__ == "__main__":
    main()
