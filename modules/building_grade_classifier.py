# -*- coding: utf-8 -*-
"""
건물 급수 자동 판정 AI (Building Grade Classifier)
건축물대장 + 건물 사진 교차 분석 → 화재보험 급수 판정

작성일: 2026-03-31
목적: 화재보험 요율 산정 자동화 + 데이터 불일치 감지
"""

import re
from typing import Dict, List, Optional, Tuple
from PIL import Image
import numpy as np


class BuildingGradeClassifier:
    """
    건물 급수 자동 판정 AI
    
    핵심 기능:
    1. 건축물대장 텍스트 분석 → 1차 급수 판정
    2. 건물 외관 사진 분석 → 외벽 재질 감지
    3. 교차 검증 → 데이터 불일치 경고
    4. 화재보험 요율 시뮬레이션
    """
    
    # 화재보험 급수 기준 (KB손해보험 기준)
    GRADE_CRITERIA = {
        "1급": {
            "structure": ["철근콘크리트조", "철골철근콘크리트조"],
            "roof": ["철근콘크리트조", "기와", "슬레이트(불연재)"],
            "wall": ["철근콘크리트", "벽돌", "블록"],
            "description": "우량 건물 (최저 요율)"
        },
        "2급": {
            "structure": ["철골조", "연와조", "석조", "블록조"],
            "roof": ["철골조", "아연도금강판", "칼라강판"],
            "wall": ["철골", "연와", "석재", "블록"],
            "description": "양호 건물"
        },
        "3급": {
            "structure": ["목조", "경량철골조"],
            "roof": ["목조", "샌드위치패널", "가연성자재"],
            "wall": ["목재", "샌드위치패널", "비닐"],
            "description": "주의 건물"
        },
        "4급": {
            "structure": ["천막", "비닐하우스", "컨테이너"],
            "roof": ["천막", "비닐", "임시자재"],
            "wall": ["천막", "비닐", "임시자재"],
            "description": "고위험 건물 (최고 요율)"
        }
    }
    
    # 샌드위치 패널 감지 키워드
    SANDWICH_PANEL_KEYWORDS = [
        "샌드위치패널", "샌드위치판넬", "샌드위치 패널",
        "우레탄패널", "스티로폼패널", "EPS패널",
        "단열패널", "조립식패널"
    ]
    
    def __init__(self):
        """초기화"""
        self.register_data = None
        self.photo_analysis = None
        self.final_grade = None
        self.conflict_detected = False
    
    def analyze_building_register(self, ocr_text: str) -> Dict:
        """
        건축물대장 분석 (1차 급수 판정)
        
        Args:
            ocr_text: 건축물대장 OCR 텍스트
        
        Returns:
            분석 결과
        """
        result = {
            "structure": self._extract_structure(ocr_text),
            "roof": self._extract_roof(ocr_text),
            "wall": self._extract_wall(ocr_text),
            "total_floor_area": self._extract_floor_area(ocr_text),
            "building_floors": self._extract_floors(ocr_text),
            "construction_year": self._extract_construction_year(ocr_text),
            "primary_grade": None,
            "grade_reason": ""
        }
        
        # 1차 급수 판정
        result["primary_grade"] = self._determine_grade_from_register(result)
        
        self.register_data = result
        return result
    
    def _extract_structure(self, text: str) -> Optional[str]:
        """구조 추출"""
        structure_patterns = [
            r"주구조[:\s]*([가-힣]+조)",
            r"구조[:\s]*([가-힣]+조)",
            r"(철근콘크리트조|철골철근콘크리트조|철골조|연와조|석조|블록조|목조|경량철골조)"
        ]
        
        for pattern in structure_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        
        return None
    
    def _extract_roof(self, text: str) -> Optional[str]:
        """지붕 재질 추출"""
        roof_patterns = [
            r"지붕[:\s]*([가-힣]+)",
            r"옥상[:\s]*([가-힣]+)",
            r"(철근콘크리트|기와|슬레이트|철골|아연도금강판|칼라강판|샌드위치패널)"
        ]
        
        for pattern in roof_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        
        return None
    
    def _extract_wall(self, text: str) -> Optional[str]:
        """외벽 재질 추출"""
        wall_patterns = [
            r"외벽[:\s]*([가-힣]+)",
            r"벽체[:\s]*([가-힣]+)",
            r"(철근콘크리트|벽돌|블록|철골|연와|석재|목재|샌드위치패널)"
        ]
        
        for pattern in wall_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        
        return None
    
    def _extract_floor_area(self, text: str) -> Optional[float]:
        """연면적 추출"""
        area_match = re.search(r"연면적[:\s]*([\d,\.]+)\s*㎡", text)
        if area_match:
            area_str = area_match.group(1).replace(',', '')
            return float(area_str)
        return None
    
    def _extract_floors(self, text: str) -> Optional[int]:
        """층수 추출"""
        floors_match = re.search(r"(지상|층수)[:\s]*(\d+)\s*층", text)
        if floors_match:
            return int(floors_match.group(2))
        return None
    
    def _extract_construction_year(self, text: str) -> Optional[int]:
        """건축년도 추출"""
        year_match = re.search(r"건축년도[:\s]*(\d{4})", text)
        if year_match:
            return int(year_match.group(1))
        return None
    
    def _determine_grade_from_register(self, register_data: Dict) -> str:
        """건축물대장 기반 1차 급수 판정"""
        structure = register_data.get("structure", "")
        roof = register_data.get("roof", "")
        wall = register_data.get("wall", "")
        
        # 1급 판정
        if any(s in structure for s in self.GRADE_CRITERIA["1급"]["structure"]):
            if not any(keyword in roof + wall for keyword in self.SANDWICH_PANEL_KEYWORDS):
                register_data["grade_reason"] = "철근콘크리트 구조 + 불연재 마감"
                return "1급"
        
        # 2급 판정
        if any(s in structure for s in self.GRADE_CRITERIA["2급"]["structure"]):
            register_data["grade_reason"] = "철골 또는 연와 구조"
            return "2급"
        
        # 3급 판정 (샌드위치 패널 감지)
        if any(keyword in structure + roof + wall for keyword in self.SANDWICH_PANEL_KEYWORDS):
            register_data["grade_reason"] = "샌드위치 패널 사용 (가연성 자재)"
            return "3급"
        
        # 3급 판정 (목조)
        if any(s in structure for s in self.GRADE_CRITERIA["3급"]["structure"]):
            register_data["grade_reason"] = "목조 또는 경량철골 구조"
            return "3급"
        
        # 4급 판정
        if any(s in structure for s in self.GRADE_CRITERIA["4급"]["structure"]):
            register_data["grade_reason"] = "임시 구조물"
            return "4급"
        
        # 기본값
        register_data["grade_reason"] = "판정 불가 (추가 정보 필요)"
        return "2급"
    
    def analyze_building_photo(self, image: Image.Image) -> Dict:
        """
        건물 외관 사진 분석 (Vision AI)
        
        Args:
            image: 건물 외관 사진
        
        Returns:
            분석 결과
        """
        # 실제 구현 시 Gemini Vision API 연동
        # 현재는 Mock 데이터 반환
        
        result = {
            "wall_material_detected": None,
            "sandwich_panel_detected": False,
            "fire_risk_indicators": [],
            "adjacent_building_risk": "low",
            "visual_grade_estimate": None
        }
        
        # Mock: 실제로는 Vision AI가 분석
        # 예시: "샌드위치 패널로 보이는 외벽 마감재 감지"
        
        self.photo_analysis = result
        return result
    
    def cross_validate(self) -> Dict:
        """
        교차 검증 (건축물대장 vs 건물 사진)
        
        Returns:
            교차 검증 결과
        """
        if not self.register_data or not self.photo_analysis:
            return {
                "conflict_detected": False,
                "message": "교차 검증을 위한 데이터가 부족합니다."
            }
        
        conflicts = []
        
        # 1. 샌드위치 패널 불일치 검사
        register_has_panel = any(
            keyword in str(self.register_data.get("wall", "")) + 
                      str(self.register_data.get("roof", ""))
            for keyword in self.SANDWICH_PANEL_KEYWORDS
        )
        
        photo_has_panel = self.photo_analysis.get("sandwich_panel_detected", False)
        
        if not register_has_panel and photo_has_panel:
            conflicts.append({
                "type": "sandwich_panel_mismatch",
                "severity": "high",
                "message": "⚠️ 대장상에는 샌드위치 패널 미기재, 실제 사진상 패널 마감 확인",
                "impact": "실질 급수 하향 위험 (1급 → 2급 또는 3급)"
            })
            self.conflict_detected = True
        
        # 2. 외벽 재질 불일치 검사
        register_wall = self.register_data.get("wall", "")
        photo_wall = self.photo_analysis.get("wall_material_detected", "")
        
        if register_wall and photo_wall and register_wall != photo_wall:
            conflicts.append({
                "type": "wall_material_mismatch",
                "severity": "medium",
                "message": f"외벽 재질 불일치: 대장({register_wall}) vs 사진({photo_wall})",
                "impact": "급수 재판정 필요"
            })
            self.conflict_detected = True
        
        return {
            "conflict_detected": len(conflicts) > 0,
            "conflicts": conflicts,
            "recommendation": self._generate_recommendation(conflicts)
        }
    
    def _generate_recommendation(self, conflicts: List[Dict]) -> str:
        """권고사항 생성"""
        if not conflicts:
            return "건축물대장과 실제 건물 상태가 일치합니다. 안전하게 급수 판정 가능합니다."
        
        recommendations = []
        
        for conflict in conflicts:
            if conflict["severity"] == "high":
                recommendations.append(
                    f"🚨 {conflict['message']}\n"
                    f"   → {conflict['impact']}\n"
                    f"   → 현장 실사 또는 추가 사진 확보 권장"
                )
            else:
                recommendations.append(
                    f"⚠️ {conflict['message']}\n"
                    f"   → {conflict['impact']}"
                )
        
        return "\n\n".join(recommendations)
    
    def determine_final_grade(self) -> Dict:
        """
        최종 급수 판정
        
        Returns:
            최종 판정 결과
        """
        if not self.register_data:
            return {
                "final_grade": None,
                "message": "건축물대장 데이터가 필요합니다."
            }
        
        primary_grade = self.register_data.get("primary_grade", "2급")
        
        # 교차 검증 결과 반영
        if self.conflict_detected:
            # 샌드위치 패널 감지 시 급수 하향
            if any(c["type"] == "sandwich_panel_mismatch" for c in 
                   self.cross_validate().get("conflicts", [])):
                if primary_grade == "1급":
                    final_grade = "2급"
                    reason = "대장상 1급이나, 실제 사진상 샌드위치 패널 마감 확인 → 2급으로 하향"
                elif primary_grade == "2급":
                    final_grade = "3급"
                    reason = "대장상 2급이나, 실제 사진상 샌드위치 패널 마감 확인 → 3급으로 하향"
                else:
                    final_grade = primary_grade
                    reason = self.register_data.get("grade_reason", "")
            else:
                final_grade = primary_grade
                reason = "교차 검증 결과 경미한 불일치 → 대장 기준 유지"
        else:
            final_grade = primary_grade
            reason = self.register_data.get("grade_reason", "")
        
        self.final_grade = final_grade
        
        return {
            "final_grade": final_grade,
            "primary_grade": primary_grade,
            "grade_adjusted": final_grade != primary_grade,
            "reason": reason,
            "description": self.GRADE_CRITERIA[final_grade]["description"],
            "conflict_detected": self.conflict_detected
        }
    
    def generate_report(self) -> str:
        """
        급수 판정 리포트 생성 (리딩 파트너 멘트)
        
        Returns:
            리포트 텍스트
        """
        if not self.final_grade:
            self.determine_final_grade()
        
        final_result = self.determine_final_grade()
        
        report_lines = []
        
        # 오프닝
        report_lines.append("### 🏢 건물 급수 자동 판정 결과")
        report_lines.append("")
        
        # 건축물대장 분석
        report_lines.append("#### 📄 건축물대장 분석")
        if self.register_data:
            report_lines.append(f"- **구조**: {self.register_data.get('structure', '정보 없음')}")
            report_lines.append(f"- **지붕**: {self.register_data.get('roof', '정보 없음')}")
            report_lines.append(f"- **외벽**: {self.register_data.get('wall', '정보 없음')}")
            report_lines.append(f"- **1차 판정**: {self.register_data.get('primary_grade', '판정 불가')}")
            report_lines.append(f"- **판정 근거**: {self.register_data.get('grade_reason', '')}")
        report_lines.append("")
        
        # 교차 검증
        cross_result = self.cross_validate()
        if cross_result["conflict_detected"]:
            report_lines.append("#### ⚠️ 교차 검증 결과")
            report_lines.append(cross_result["recommendation"])
            report_lines.append("")
        
        # 최종 판정
        report_lines.append("#### 🎯 최종 급수 판정")
        report_lines.append(f"**{final_result['final_grade']}: {final_result['description']}**")
        report_lines.append("")
        report_lines.append(f"**판정 근거**: {final_result['reason']}")
        
        if final_result["grade_adjusted"]:
            report_lines.append("")
            report_lines.append(f"⚠️ **급수 조정**: {final_result['primary_grade']} → {final_result['final_grade']}")
        
        # 리딩 파트너 멘트
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("**💼 리딩 파트너 분석 코멘트**")
        report_lines.append("")
        
        if self.conflict_detected:
            report_lines.append(
                f"대표님, 건축물대장과 외관 사진을 **교차 분석**했습니다. "
                f"본 건물은 {self.register_data.get('structure', '정보 없음')} 구조이나 "
                f"외벽 마감재로 인해 실질 화재 급수는 **{final_result['final_grade']}**로 판단됩니다. "
                f"이를 바탕으로 한 정밀 요율 시뮬레이션을 시작합니다."
            )
        else:
            report_lines.append(
                f"대표님, 건축물대장과 외관 사진이 일치합니다. "
                f"본 건물은 **{final_result['final_grade']} ({final_result['description']})**로 판정되며, "
                f"안전하게 화재보험 설계를 진행하실 수 있습니다."
            )
        
        return "\n".join(report_lines)


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_building_grade_classifier():
    """
    건물 급수 판정 UI
    
    사용법:
        from modules.building_grade_classifier import render_building_grade_classifier
        render_building_grade_classifier()
    """
    import streamlit as st
    
    st.markdown("### 🏢 건물 급수 자동 판정 AI")
    
    # 듀얼 Drop Zone
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div style='background:#fff8e1;border:2px dashed #f57c00;
                        border-radius:12px;padding:30px;text-align:center;
                        min-height:200px;display:flex;flex-direction:column;
                        justify-content:center;'>
                <div style='font-size:40px;margin-bottom:12px;'>📄</div>
                <div style='font-size:16px;font-weight:900;color:#e65100;'>
                    건축물대장 Drop
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        register_file = st.file_uploader(
            "건축물대장 업로드",
            type=["pdf", "jpg", "jpeg", "png"],
            key="building_register_upload",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown(
            """
            <div style='background:#e3f2fd;border:2px dashed #1976d2;
                        border-radius:12px;padding:30px;text-align:center;
                        min-height:200px;display:flex;flex-direction:column;
                        justify-content:center;'>
                <div style='font-size:40px;margin-bottom:12px;'>📸</div>
                <div style='font-size:16px;font-weight:900;color:#0d47a1;'>
                    건물 사진 Drop
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        photo_file = st.file_uploader(
            "건물 외관 사진 업로드",
            type=["jpg", "jpeg", "png"],
            key="building_photo_upload",
            label_visibility="collapsed"
        )
    
    # 분석 시작
    if register_file and photo_file:
        # 스파크 애니메이션 (CSS)
        st.markdown(
            """
            <div style='text-align:center;margin:20px 0;'>
                <div style='font-size:48px;animation:spark 1s infinite;'>⚡</div>
                <div style='font-size:14px;color:#666;'>교차 분석 중...</div>
            </div>
            <style>
                @keyframes spark {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.5; transform: scale(1.2); }
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # 샘플 OCR 텍스트 (실제로는 OCR 엔진 연동)
        sample_register_text = """
        건축물대장
        
        주구조: 철근콘크리트조
        지붕: 철근콘크리트
        외벽: 샌드위치패널
        연면적: 1,500㎡
        층수: 지상 3층
        건축년도: 2015
        """
        
        # 분석 실행
        classifier = BuildingGradeClassifier()
        
        # 1. 건축물대장 분석
        register_result = classifier.analyze_building_register(sample_register_text)
        
        # 2. 건물 사진 분석 (Mock)
        photo_image = Image.open(photo_file)
        photo_result = classifier.analyze_building_photo(photo_image)
        photo_result["sandwich_panel_detected"] = True  # Mock
        
        # 3. 교차 검증
        cross_result = classifier.cross_validate()
        
        # 4. 최종 판정
        final_result = classifier.determine_final_grade()
        
        # 5. 리포트 생성
        report = classifier.generate_report()
        
        # 결과 표시
        st.markdown("---")
        
        # 최종 급수 인포그래픽
        grade = final_result["final_grade"]
        grade_colors = {
            "1급": "#4caf50",
            "2급": "#ff9800",
            "3급": "#ff5722",
            "4급": "#f44336"
        }
        
        st.markdown(
            f"""
            <div style='background:{grade_colors.get(grade, "#ccc")};
                        color:white;border-radius:16px;padding:40px;
                        text-align:center;margin:20px 0;
                        box-shadow:0 8px 32px rgba(0,0,0,0.2);'>
                <div style='font-size:72px;font-weight:900;margin-bottom:16px;'>
                    {grade}
                </div>
                <div style='font-size:24px;font-weight:700;'>
                    {final_result['description']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 상세 리포트
        st.markdown(report)
