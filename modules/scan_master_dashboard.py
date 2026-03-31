# -*- coding: utf-8 -*-
"""
스캔 마스터 대시보드 (Scan Master Dashboard)
5:5 전략 커맨드 센터 - The War Room

작성일: 2026-03-31
목적: 전문가급 스캔 및 분석 통합 대시보드
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
import base64
import io
import time
from datetime import datetime
from PIL import Image
import json
import cv2
import numpy as np


class ScanMasterDashboard:
    """
    스캔 마스터 대시보드
    
    핵심 구성:
    - 좌측 (5): Input & Ads (인벤토리 & 파워)
    - 우측 (5): Insight & Action (전략 리포트)
    """
    
    def __init__(self):
        """초기화"""
        self.session_key = "scan_master_dashboard"
        
        # 세션 초기화
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "recent_scans": [],
                "current_analysis": None,
                "feature_showcase": True,
                "dark_theme": True
            }
    
    def render(self):
        """
        5:5 마스터 대시보드 렌더링
        """
        # 다크 테마 CSS 주입
        self._inject_dark_theme()
        
        # 5:5 레이아웃
        col_left, col_right = st.columns([5, 5])
        
        with col_left:
            self._render_left_powerhouse()
        
        with col_right:
            self._render_right_insight()
    
    def _inject_dark_theme(self):
        """
        다크 테마 + 네온 블루/골드 CSS 주입
        """
        st.markdown(
            """
            <style>
                /* 다크 테마 기본 배경 */
                .stApp {
                    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
                }
                
                /* 네온 블루 포인트 */
                .neon-blue {
                    color: #00d4ff;
                    text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff;
                }
                
                /* 골드 포인트 */
                .gold-accent {
                    color: #ffd700;
                    text-shadow: 0 0 10px #ffd700;
                }
                
                /* 전문가 카드 스타일 */
                .pro-card {
                    background: rgba(26, 31, 58, 0.8);
                    border: 1px solid rgba(0, 212, 255, 0.3);
                    border-radius: 12px;
                    padding: 20px;
                    margin: 10px 0;
                    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1);
                    backdrop-filter: blur(10px);
                }
                
                /* 로딩 애니메이션 */
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                .loading-indicator {
                    animation: pulse 2s infinite;
                }
                
                /* 데이터 플로우 애니메이션 */
                @keyframes dataflow {
                    0% { transform: translateX(-100%); opacity: 0; }
                    50% { opacity: 1; }
                    100% { transform: translateX(100%); opacity: 0; }
                }
                
                .data-flow {
                    animation: dataflow 2s ease-in-out;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
    
    def _render_left_powerhouse(self):
        """
        좌측: 인벤토리 & 파워 (The Powerhouse)
        
        구성:
        1. Professional Drop Zone
        2. 최근 진단 목록
        3. Feature Ad-Box (전 기능 요약)
        """
        st.markdown("### 🎯 전술 장비 (Tactical Arsenal)")
        
        # 1. Professional Drop Zone
        self._render_professional_drop_zone()
        
        # 2. 최근 진단 목록
        self._render_recent_scans()
        
        # 3. Feature Ad-Box
        self._render_feature_ad_box()
    
    def _render_professional_drop_zone(self):
        """
        Professional Drop Zone (네이티브 HTML5)
        """
        st.markdown(
            """
            <div class='pro-card' style='min-height:200px;text-align:center;
                                        border:2px dashed #00d4ff;'>
                <div style='font-size:48px;margin:20px 0;'>📂</div>
                <div class='neon-blue' style='font-size:20px;font-weight:900;
                                              margin-bottom:12px;'>
                    Professional Drop Zone
                </div>
                <div style='color:#8b9dc3;font-size:14px;line-height:1.6;'>
                    증권·의무기록·재무제표·건축물대장을 이곳에 드롭하세요<br>
                    <span class='gold-accent'>최상의 조도와 비틀림 보정 엔진이 대기 중입니다</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # HTML5 네이티브 드래그 앤 드롭 (JavaScript)
        drop_zone_html = """
        <div id="native-drop-zone" style="display:none;">
            <input type="file" id="file-input" multiple accept=".pdf,.jpg,.jpeg,.png" 
                   style="display:none;">
        </div>
        
        <script>
            // 네이티브 드래그 앤 드롭 이벤트 핸들러
            const dropZone = document.querySelector('.pro-card');
            
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#ffd700';
                dropZone.style.backgroundColor = 'rgba(255, 215, 0, 0.1)';
            });
            
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#00d4ff';
                dropZone.style.backgroundColor = 'rgba(26, 31, 58, 0.8)';
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#00d4ff';
                dropZone.style.backgroundColor = 'rgba(26, 31, 58, 0.8)';
                
                const files = e.dataTransfer.files;
                console.log('Dropped files:', files);
                
                // Streamlit으로 파일 전달 (추후 구현)
                // window.parent.postMessage({type: 'file_drop', files: files}, '*');
            });
        </script>
        """
        
        st.components.v1.html(drop_zone_html, height=0)
        
        # Streamlit 파일 업로더 (폴백)
        uploaded_files = st.file_uploader(
            "또는 파일 선택",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="master_dashboard_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            self._process_uploaded_files(uploaded_files)
    
    def _render_recent_scans(self):
        """
        최근 진단 목록
        """
        st.markdown("#### 📋 최근 진단 목록")
        
        recent_scans = st.session_state[self.session_key].get("recent_scans", [])
        
        if not recent_scans:
            st.markdown(
                """
                <div class='pro-card' style='text-align:center;padding:30px;'>
                    <div style='color:#8b9dc3;font-size:14px;'>
                        아직 분석된 문서가 없습니다
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for scan in recent_scans[-5:]:  # 최근 5개만 표시
                status_color = "#00d4ff" if scan.get("status") == "completed" else "#ffd700"
                st.markdown(
                    f"""
                    <div class='pro-card' style='padding:15px;margin:5px 0;'>
                        <div style='display:flex;justify-content:space-between;align-items:center;'>
                            <div>
                                <div style='color:white;font-weight:700;font-size:14px;'>
                                    {scan.get('filename', '알 수 없음')}
                                </div>
                                <div style='color:#8b9dc3;font-size:12px;margin-top:4px;'>
                                    {scan.get('category', '일반 문서')} · {scan.get('timestamp', '')}
                                </div>
                            </div>
                            <div style='color:{status_color};font-weight:900;font-size:12px;'>
                                {scan.get('status_text', '진단 완료')}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    def _render_feature_ad_box(self):
        """
        Feature Ad-Box (전 기능 요약)
        
        스크롤 없이 모든 핵심 기능 노출
        """
        st.markdown("#### ⚡ 스캔 지능 요약")
        
        features = [
            {
                "icon": "🏢",
                "name": "건물 급수 판정",
                "desc": "건축물대장 + 사진 교차 분석",
                "color": "#00d4ff"
            },
            {
                "icon": "🏥",
                "name": "의무기록 인터프리터",
                "desc": "KCD-10 질병 코드 자동 추출",
                "color": "#ff6b6b"
            },
            {
                "icon": "📊",
                "name": "재무제표 주식평가",
                "desc": "비상장주식 가치 산출",
                "color": "#ffd700"
            },
            {
                "icon": "🎥",
                "name": "사고 영상 AI",
                "desc": "과실 비율 자동 분석",
                "color": "#a78bfa"
            },
            {
                "icon": "📄",
                "name": "공공 기록 매핑",
                "desc": "사업자등록증 자동 파싱",
                "color": "#34d399"
            },
            {
                "icon": "🔗",
                "name": "복합 RAG 분석",
                "desc": "재무+의료+보험 통합",
                "color": "#f472b6"
            }
        ]
        
        # 2x3 그리드
        for i in range(0, len(features), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(features):
                    feature = features[i + j]
                    with col:
                        st.markdown(
                            f"""
                            <div class='pro-card' style='text-align:center;padding:20px;
                                                        border-color:{feature['color']};
                                                        cursor:pointer;transition:all 0.3s;'>
                                <div style='font-size:36px;margin-bottom:8px;'>
                                    {feature['icon']}
                                </div>
                                <div style='color:{feature['color']};font-weight:900;
                                            font-size:14px;margin-bottom:6px;'>
                                    {feature['name']}
                                </div>
                                <div style='color:#8b9dc3;font-size:11px;line-height:1.4;'>
                                    {feature['desc']}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
    
    def _render_right_insight(self):
        """
        우측: 인사이트 & 액션 (Strategic Insight)
        
        구성:
        1. AI Insight Box (정밀 분석 요약)
        2. Strategic Solution Box (보험 전략 적용)
        """
        st.markdown("### 🎯 전략 리포트 (Strategic Insight)")
        
        current_analysis = st.session_state[self.session_key].get("current_analysis")
        
        if not current_analysis:
            self._render_empty_insight()
        else:
            # 1. AI Insight Box
            self._render_ai_insight_box(current_analysis)
            
            # 2. Strategic Solution Box
            self._render_strategic_solution_box(current_analysis)
    
    def _render_empty_insight(self):
        """
        분석 대기 상태 UI
        """
        st.markdown(
            """
            <div class='pro-card' style='min-height:400px;display:flex;
                                        flex-direction:column;justify-content:center;
                                        align-items:center;text-align:center;'>
                <div style='font-size:72px;margin-bottom:20px;opacity:0.3;'>
                    🎯
                </div>
                <div class='neon-blue' style='font-size:20px;font-weight:900;
                                              margin-bottom:12px;'>
                    분석 대기 중
                </div>
                <div style='color:#8b9dc3;font-size:14px;line-height:1.8;'>
                    좌측에서 문서를 업로드하면<br>
                    이곳에 <span class='gold-accent'>정밀 분석 결과</span>가 표시됩니다
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_ai_insight_box(self, analysis: Dict):
        """
        AI Insight Box (정밀 분석 요약)
        
        Args:
            analysis: 분석 결과 데이터
        """
        st.markdown("#### 🔍 AI 정밀 분석 요약")
        
        category = analysis.get("category", "일반")
        insights = analysis.get("insights", {})
        
        # 카테고리별 인사이트 렌더링
        if category == "건물":
            self._render_building_insight(insights)
        elif category == "의료":
            self._render_medical_insight(insights)
        elif category == "재무":
            self._render_financial_insight(insights)
        else:
            self._render_general_insight(insights)
    
    def _render_building_insight(self, insights: Dict):
        """건물 분석 인사이트"""
        st.markdown(
            f"""
            <div class='pro-card data-flow'>
                <div style='color:#00d4ff;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    🏢 건물 구조 분석
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    <b>구조:</b> {insights.get('structure', '철근콘크리트조')}<br>
                    <b>외벽:</b> {insights.get('wall', '샌드위치 패널 마감')}<br>
                    <b>지붕:</b> {insights.get('roof', '철근콘크리트')}<br>
                    <br>
                    <span style='color:#ffd700;font-weight:700;'>
                        ⚠️ {insights.get('warning', '가연성 마감재 혼용 확인')}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_medical_insight(self, insights: Dict):
        """의료 분석 인사이트"""
        st.markdown(
            f"""
            <div class='pro-card data-flow'>
                <div style='color:#ff6b6b;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    🏥 의무기록 판독
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    <b>질병 코드:</b> {insights.get('kcd_code', 'I63.9 (뇌경색)')}<br>
                    <b>진단명:</b> {insights.get('diagnosis', '뇌경색')}<br>
                    <b>진단일:</b> {insights.get('diagnosis_date', '2024-01-15')}<br>
                    <br>
                    <span style='color:#ffd700;font-weight:700;'>
                        ⚠️ 보장 공백 발생 가능성 {insights.get('gap_probability', '80')}%
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_financial_insight(self, insights: Dict):
        """재무 분석 인사이트"""
        st.markdown(
            f"""
            <div class='pro-card data-flow'>
                <div style='color:#ffd700;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    📊 재무제표 분석
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    <b>비상장주식 추정가:</b> {insights.get('stock_value', '45억 원')}<br>
                    <b>자산총계:</b> {insights.get('total_assets', '120억 원')}<br>
                    <b>부채비율:</b> {insights.get('debt_ratio', '35%')}<br>
                    <br>
                    <span style='color:#ffd700;font-weight:700;'>
                        ⚠️ {insights.get('warning', '자산 보전 구조 재설계 시급')}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_general_insight(self, insights: Dict):
        """일반 분석 인사이트"""
        st.markdown(
            f"""
            <div class='pro-card data-flow'>
                <div style='color:#00d4ff;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    📄 문서 분석
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    {insights.get('summary', '분석 결과가 여기에 표시됩니다')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_strategic_solution_box(self, analysis: Dict):
        """
        Strategic Solution Box (보험 전략 적용)
        
        Args:
            analysis: 분석 결과 데이터
        """
        st.markdown("#### 💼 보험 전략 적용")
        
        category = analysis.get("category", "일반")
        solutions = analysis.get("solutions", {})
        
        # 카테고리별 솔루션 렌더링
        if category == "건물":
            self._render_building_solution(solutions)
        elif category == "의료":
            self._render_medical_solution(solutions)
        elif category == "재무":
            self._render_financial_solution(solutions)
        else:
            self._render_general_solution(solutions)
    
    def _render_building_solution(self, solutions: Dict):
        """건물 급수 판정 솔루션"""
        st.markdown(
            f"""
            <div class='pro-card'>
                <div style='color:#00d4ff;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    🎯 화재보험 급수 판정
                </div>
                <div style='background:rgba(0,212,255,0.1);border-left:4px solid #00d4ff;
                            padding:16px;border-radius:8px;margin-bottom:16px;'>
                    <div style='color:#00d4ff;font-weight:900;font-size:20px;
                                margin-bottom:8px;'>
                        실질 {solutions.get('grade', '2급')} 판정
                    </div>
                    <div style='color:white;font-size:14px;'>
                        {solutions.get('reason', '철근콘크리트 구조이나 외벽 패널 마감으로 인해 2급 판정')}
                    </div>
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    <b style='color:#ffd700;'>✓ 효과:</b><br>
                    • 고지의무 위반 방지<br>
                    • 최적 요율 적용 (15% 절감 예상)<br>
                    • 사고 시 보상 분쟁 최소화
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_medical_solution(self, solutions: Dict):
        """의무기록 인수 전략 솔루션"""
        st.markdown(
            f"""
            <div class='pro-card'>
                <div style='color:#ff6b6b;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    🎯 인수 가능성 분석
                </div>
                <div style='background:rgba(255,107,107,0.1);border-left:4px solid #ff6b6b;
                            padding:16px;border-radius:8px;margin-bottom:16px;'>
                    <div style='color:#ff6b6b;font-weight:900;font-size:20px;
                                margin-bottom:8px;'>
                        부담보 해소 전략 필요
                    </div>
                    <div style='color:white;font-size:14px;'>
                        {solutions.get('strategy', '과거 수술 이력에 따른 부담보 조건 예상')}
                    </div>
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    <b style='color:#ffd700;'>⚠️ 주의사항:</b><br>
                    • 현재 계약 유지 시 보상 한도 초과 리스크 40% 존재<br>
                    • 인플레이션에 따른 보장액 부족 우려<br>
                    • 추가 진단비 특약 가입 권장
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_financial_solution(self, solutions: Dict):
        """재무 자산 보전 솔루션"""
        st.markdown(
            f"""
            <div class='pro-card'>
                <div style='color:#ffd700;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    🎯 자산 보전 전략
                </div>
                <div style='background:rgba(255,215,0,0.1);border-left:4px solid #ffd700;
                            padding:16px;border-radius:8px;margin-bottom:16px;'>
                    <div style='color:#ffd700;font-weight:900;font-size:20px;
                                margin-bottom:8px;'>
                        CEO 유고 대비 필요
                    </div>
                    <div style='color:white;font-size:14px;'>
                        {solutions.get('strategy', '상속세 추정 15억 원, 경영권 보전 자금 부족')}
                    </div>
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    <b style='color:#ffd700;'>✓ 권장 조치:</b><br>
                    • 경영인정기보험 추가 가입 (30억 원)<br>
                    • 법인 납입 보험료 손금 산입 활용<br>
                    • 가업승계 플랜 재설계
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_general_solution(self, solutions: Dict):
        """일반 솔루션"""
        st.markdown(
            f"""
            <div class='pro-card'>
                <div style='color:#00d4ff;font-weight:900;font-size:16px;
                            margin-bottom:16px;'>
                    🎯 분석 결과
                </div>
                <div style='color:white;font-size:14px;line-height:1.8;'>
                    {solutions.get('summary', '솔루션이 여기에 표시됩니다')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _process_uploaded_files(self, files: List):
        """
        업로드된 파일 처리 + Cross-Device Sync
        
        Args:
            files: 업로드된 파일 리스트
        """
        from modules.geometric_correction_engine import GeometricCorrectionEngine
        from modules.deterministic_table_parser import DeterministicTableParser
        
        # 기하학적 보정 엔진 초기화
        correction_engine = GeometricCorrectionEngine()
        
        for file in files:
            # 1. 이미지 로드
            try:
                image = Image.open(file)
                image_array = np.array(image)
                
                # 2. High-Fi Scanning + AI De-warping 적용
                if len(image_array.shape) == 3:
                    image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                else:
                    image_bgr = image_array
                
                # 자동 보정 (High-Fi 모드)
                corrected_bgr, correction_info = correction_engine.auto_correct(
                    image_bgr, high_fi=True
                )
                
                # RGB 변환
                if len(corrected_bgr.shape) == 3:
                    corrected_rgb = cv2.cvtColor(corrected_bgr, cv2.COLOR_BGR2RGB)
                else:
                    corrected_rgb = corrected_bgr
                
                corrected_image = Image.fromarray(corrected_rgb)
                
            except Exception as e:
                st.warning(f"이미지 보정 실패: {e}")
                corrected_image = None
                correction_info = {}
            
            # 3. 파일 정보 저장
            scan_info = {
                "filename": file.name,
                "category": self._detect_category(file.name),
                "status": "completed",
                "status_text": "진단 완료",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "correction_info": correction_info
            }
            
            # 4. 최근 스캔 목록에 추가
            st.session_state[self.session_key]["recent_scans"].append(scan_info)
            
            # 5. Mock 분석 결과 생성
            analysis = self._generate_mock_analysis(scan_info["category"])
            st.session_state[self.session_key]["current_analysis"] = analysis
            
            # 6. Cross-Device Sync (작업 상태 자동 저장)
            if "user_id" in st.session_state and "crm_selected_pid" in st.session_state:
                try:
                    from modules.cross_device_state_sync import CrossDeviceStateSync
                    sync = CrossDeviceStateSync()
                    sync.auto_save_current_state(
                        user_id=st.session_state["user_id"],
                        customer_id=st.session_state.get("crm_selected_pid")
                    )
                except Exception:
                    pass
            
            st.success(f"✅ {file.name} 분석 완료 (High-Fi Scanning 적용)")
            st.rerun()
    
    def _detect_category(self, filename: str) -> str:
        """파일명으로 카테고리 감지"""
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ["건축", "대장", "building"]):
            return "건물"
        elif any(keyword in filename_lower for keyword in ["의무", "진단", "medical"]):
            return "의료"
        elif any(keyword in filename_lower for keyword in ["재무", "손익", "financial"]):
            return "재무"
        else:
            return "일반"
    
    def _generate_mock_analysis(self, category: str) -> Dict:
        """Mock 분석 결과 생성"""
        if category == "건물":
            return {
                "category": "건물",
                "insights": {
                    "structure": "철근콘크리트조",
                    "wall": "샌드위치 패널 마감",
                    "roof": "철근콘크리트",
                    "warning": "가연성 마감재 혼용 확인"
                },
                "solutions": {
                    "grade": "2급",
                    "reason": "철근콘크리트 구조이나 외벽 패널 마감으로 인해 2급 판정"
                }
            }
        elif category == "의료":
            return {
                "category": "의료",
                "insights": {
                    "kcd_code": "I63.9 (뇌경색)",
                    "diagnosis": "뇌경색",
                    "diagnosis_date": "2024-01-15",
                    "gap_probability": "80"
                },
                "solutions": {
                    "strategy": "과거 수술 이력에 따른 부담보 조건 예상"
                }
            }
        elif category == "재무":
            return {
                "category": "재무",
                "insights": {
                    "stock_value": "45억 원",
                    "total_assets": "120억 원",
                    "debt_ratio": "35%",
                    "warning": "자산 보전 구조 재설계 시급"
                },
                "solutions": {
                    "strategy": "상속세 추정 15억 원, 경영권 보전 자금 부족"
                }
            }
        else:
            return {
                "category": "일반",
                "insights": {
                    "summary": "문서 분석이 완료되었습니다"
                },
                "solutions": {
                    "summary": "추가 분석이 필요합니다"
                }
            }


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_scan_master_dashboard():
    """
    스캔 마스터 대시보드 렌더링
    
    사용법:
        from modules.scan_master_dashboard import render_scan_master_dashboard
        render_scan_master_dashboard()
    """
    dashboard = ScanMasterDashboard()
    dashboard.render()
