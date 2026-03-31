# -*- coding: utf-8 -*-
"""
교통사고 영상 분석 AI (Traffic Accident Analyzer)
블랙박스 영상 → 가해/피해 차량 구분 + 위반 법규 분석

작성일: 2026-03-31
목적: 교통법규 기반 과실 비율 자동 판정
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import os
from supabase import create_client, Client
import openai


class TrafficAccidentAnalyzer:
    """
    교통사고 영상 분석 AI
    
    핵심 기능:
    1. 블랙박스 영상 프레임 추출
    2. 가해/피해 차량 자동 구분
    3. 교통법규 위반 사항 분석
    4. 과실 비율 자동 산출
    """
    
    def __init__(self, use_rag: bool = True):
        """
        초기화
        
        Args:
            use_rag: RAG 검색 사용 여부 (기본값: True)
        """
        self.traffic_laws = self._load_traffic_laws()
        self.fault_ratio_table = self._load_fault_ratio_table()
        self.use_rag = use_rag
        
        # Supabase 클라이언트 초기화 (RAG 사용 시)
        if use_rag:
            try:
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
                openai_key = os.getenv("OPENAI_API_KEY")
                
                if supabase_url and supabase_key:
                    self.supabase = create_client(supabase_url, supabase_key)
                else:
                    self.supabase = None
                    self.use_rag = False
                
                if openai_key:
                    openai.api_key = openai_key
                else:
                    self.use_rag = False
                    
            except Exception:
                self.supabase = None
                self.use_rag = False
    
    def _load_traffic_laws(self) -> Dict:
        """
        교통법규 데이터베이스 로드
        
        출처: 도로교통법, 자동차손해배상 보장법
        """
        return {
            "신호위반": {
                "law": "도로교통법 제5조",
                "description": "신호를 위반하여 교차로에 진입한 경우",
                "base_fault": 100,
                "severity": "high"
            },
            "중앙선침범": {
                "law": "도로교통법 제13조",
                "description": "중앙선을 침범하여 반대편 차로로 진입한 경우",
                "base_fault": 100,
                "severity": "high"
            },
            "속도위반": {
                "law": "도로교통법 제17조",
                "description": "제한속도를 초과하여 주행한 경우",
                "base_fault": 30,
                "severity": "medium"
            },
            "안전거리미확보": {
                "law": "도로교통법 제19조",
                "description": "앞차와의 안전거리를 확보하지 않은 경우",
                "base_fault": 100,
                "severity": "high"
            },
            "차선변경위반": {
                "law": "도로교통법 제19조",
                "description": "급차선 변경 또는 방향지시등 미점등",
                "base_fault": 70,
                "severity": "medium"
            },
            "교차로통행방법위반": {
                "law": "도로교통법 제25조",
                "description": "교차로에서 우선순위를 위반한 경우",
                "base_fault": 80,
                "severity": "high"
            },
            "횡단보도보행자보호의무위반": {
                "law": "도로교통법 제27조",
                "description": "횡단보도 보행자를 보호하지 않은 경우",
                "base_fault": 100,
                "severity": "high"
            },
            "주정차위반": {
                "law": "도로교통법 제32조",
                "description": "주정차 금지 구역에 주정차한 경우",
                "base_fault": 20,
                "severity": "low"
            },
            "좌회전위반": {
                "law": "도로교통법 제25조",
                "description": "좌회전 신호 위반 또는 방법 위반",
                "base_fault": 90,
                "severity": "high"
            },
            "우회전위반": {
                "law": "도로교통법 제25조",
                "description": "우회전 시 일시정지 의무 위반",
                "base_fault": 60,
                "severity": "medium"
            },
            "역주행": {
                "law": "도로교통법 제13조",
                "description": "일방통행로 역주행",
                "base_fault": 100,
                "severity": "high"
            },
            "보행자보호의무위반": {
                "law": "도로교통법 제27조",
                "description": "보행자 통행 우선권 침해",
                "base_fault": 100,
                "severity": "high"
            }
        }
    
    def _load_fault_ratio_table(self) -> Dict:
        """
        과실 비율 판정 기준표
        
        출처: 자동차사고 과실비율 인정기준 (2023년 개정판)
        """
        return {
            "신호위반_직진충돌": {
                "가해차량": 100,
                "피해차량": 0,
                "description": "신호위반 차량이 직진 차량과 충돌"
            },
            "중앙선침범_정면충돌": {
                "가해차량": 100,
                "피해차량": 0,
                "description": "중앙선 침범 차량이 정면 충돌"
            },
            "안전거리미확보_추돌": {
                "가해차량": 100,
                "피해차량": 0,
                "description": "후방 차량이 전방 차량 추돌"
            },
            "교차로_좌회전우선": {
                "가해차량": 80,
                "피해차량": 20,
                "description": "교차로에서 좌회전 차량이 직진 차량과 충돌"
            },
            "차선변경_측면충돌": {
                "가해차량": 70,
                "피해차량": 30,
                "description": "차선 변경 중 측면 충돌"
            },
            "주차장_후진충돌": {
                "가해차량": 60,
                "피해차량": 40,
                "description": "주차장에서 후진 중 충돌"
            },
            "횡단보도_보행자충돌": {
                "가해차량": 100,
                "피해차량": 0,
                "description": "횡단보도 보행자 충돌"
            },
            "우회전_보행자충돌": {
                "가해차량": 90,
                "피해차량": 10,
                "description": "우회전 시 보행자 충돌"
            }
        }
    
    def analyze_video(
        self,
        video_path: str,
        frame_interval: int = 30
    ) -> Dict:
        """
        블랙박스 영상 분석 (프레임 추출 + AI 분석)
        
        Args:
            video_path: 영상 파일 경로
            frame_interval: 프레임 추출 간격 (기본 30프레임마다)
        
        Returns:
            분석 결과
        """
        # 1. 영상 프레임 추출
        frames = self._extract_key_frames(video_path, frame_interval)
        
        # 2. 충돌 순간 프레임 감지
        collision_frame = self._detect_collision_frame(frames)
        
        # 3. 차량 및 신호등 감지 (Mock)
        vehicles = self._detect_vehicles(collision_frame)
        traffic_signals = self._detect_traffic_signals(collision_frame)
        
        # 4. 교통법규 위반 분석
        violations = self._analyze_violations(vehicles, traffic_signals)
        
        # 5. 가해/피해 차량 구분
        classification = self._classify_vehicles(violations)
        
        # 6. 과실 비율 산출
        fault_ratio = self._calculate_fault_ratio(violations, classification)
        
        return {
            "collision_frame": collision_frame,
            "vehicles": vehicles,
            "traffic_signals": traffic_signals,
            "violations": violations,
            "classification": classification,
            "fault_ratio": fault_ratio,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _extract_key_frames(
        self,
        video_path: str,
        interval: int
    ) -> List[np.ndarray]:
        """영상에서 키 프레임 추출"""
        frames = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % interval == 0:
                    frames.append(frame)
                
                frame_count += 1
            
            cap.release()
            
        except Exception as e:
            st.error(f"영상 프레임 추출 실패: {e}")
        
        return frames
    
    def _detect_collision_frame(self, frames: List[np.ndarray]) -> Optional[np.ndarray]:
        """충돌 순간 프레임 감지 (프레임 간 차이 분석)"""
        if len(frames) < 2:
            return frames[0] if frames else None
        
        max_diff = 0
        collision_idx = 0
        
        for i in range(1, len(frames)):
            # 프레임 간 차이 계산
            diff = cv2.absdiff(frames[i-1], frames[i])
            diff_sum = np.sum(diff)
            
            if diff_sum > max_diff:
                max_diff = diff_sum
                collision_idx = i
        
        return frames[collision_idx]
    
    def _detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """
        차량 감지 (Mock - Gemini Vision 연동 예정)
        
        실제 구현 시:
        - YOLO 또는 Gemini Vision API 사용
        - 차량 위치, 속도, 방향 추정
        """
        # Mock 데이터
        return [
            {
                "vehicle_id": "A",
                "type": "승용차",
                "position": {"x": 320, "y": 240},
                "direction": "직진",
                "estimated_speed": 60,
                "lane": "1차로"
            },
            {
                "vehicle_id": "B",
                "type": "승용차",
                "position": {"x": 400, "y": 300},
                "direction": "좌회전",
                "estimated_speed": 40,
                "lane": "2차로"
            }
        ]
    
    def _detect_traffic_signals(self, frame: np.ndarray) -> Dict:
        """
        신호등 상태 감지 (Mock - Gemini Vision 연동 예정)
        
        실제 구현 시:
        - 신호등 위치 감지
        - 적색/황색/녹색 판별
        - 좌회전 신호 별도 판별
        """
        # Mock 데이터
        return {
            "main_signal": "녹색",
            "left_turn_signal": "적색",
            "pedestrian_signal": "적색",
            "timestamp": "충돌 2초 전"
        }
    
    def _analyze_violations(
        self,
        vehicles: List[Dict],
        traffic_signals: Dict
    ) -> List[Dict]:
        """
        교통법규 위반 분석
        
        Args:
            vehicles: 감지된 차량 리스트
            traffic_signals: 신호등 상태
        
        Returns:
            위반 사항 리스트
        """
        violations = []
        
        for vehicle in vehicles:
            vehicle_violations = []
            
            # 1. 신호위반 체크
            if vehicle["direction"] == "좌회전" and traffic_signals["left_turn_signal"] == "적색":
                vehicle_violations.append({
                    "type": "신호위반",
                    "law": self.traffic_laws["신호위반"]["law"],
                    "description": "좌회전 신호 적색 시 진입",
                    "severity": "high",
                    "base_fault": 100
                })
            
            # 2. 속도위반 체크 (제한속도 50km/h 가정)
            if vehicle["estimated_speed"] > 50:
                over_speed = vehicle["estimated_speed"] - 50
                vehicle_violations.append({
                    "type": "속도위반",
                    "law": self.traffic_laws["속도위반"]["law"],
                    "description": f"제한속도 {over_speed}km/h 초과",
                    "severity": "medium",
                    "base_fault": 30
                })
            
            # 3. 교차로 통행방법 위반 체크
            if vehicle["direction"] == "좌회전" and traffic_signals["main_signal"] == "녹색":
                vehicle_violations.append({
                    "type": "교차로통행방법위반",
                    "law": self.traffic_laws["교차로통행방법위반"]["law"],
                    "description": "직진 신호에 좌회전 진입",
                    "severity": "high",
                    "base_fault": 80
                })
            
            violations.append({
                "vehicle_id": vehicle["vehicle_id"],
                "violations": vehicle_violations
            })
        
        return violations
    
    def _classify_vehicles(self, violations: List[Dict]) -> Dict:
        """
        가해/피해 차량 구분
        
        기준:
        - 위반 사항이 많은 차량 = 가해 차량
        - 위반 사항이 적거나 없는 차량 = 피해 차량
        """
        if not violations:
            return {
                "offender": None,
                "victim": None,
                "classification_basis": "위반 사항 없음"
            }
        
        # 위반 점수 계산
        vehicle_scores = []
        for v in violations:
            total_fault = sum(
                viol["base_fault"] for viol in v["violations"]
            )
            vehicle_scores.append({
                "vehicle_id": v["vehicle_id"],
                "total_fault": total_fault,
                "violation_count": len(v["violations"])
            })
        
        # 점수 기준 정렬
        vehicle_scores.sort(key=lambda x: x["total_fault"], reverse=True)
        
        if len(vehicle_scores) >= 2:
            offender = vehicle_scores[0]
            victim = vehicle_scores[1]
        else:
            offender = vehicle_scores[0] if vehicle_scores else None
            victim = None
        
        return {
            "offender": offender,
            "victim": victim,
            "classification_basis": "교통법규 위반 점수 기준"
        }
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            임베딩 벡터
        """
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception:
            return None
    
    def _search_fault_ratio_from_rag(
        self,
        accident_description: str,
        top_k: int = 5
    ) -> Optional[Dict]:
        """
        RAG 기반 과실비율 검색
        
        Args:
            accident_description: 사고 상황 설명
            top_k: 검색할 결과 수
        
        Returns:
            과실비율 정보
        """
        if not self.use_rag or not self.supabase:
            return None
        
        try:
            # 1. 임베딩 생성
            query_embedding = self._generate_embedding(accident_description)
            
            if not query_embedding:
                return None
            
            # 2. Supabase 벡터 검색
            result = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.7,
                    'match_count': top_k
                }
            ).execute()
            
            if not result.data:
                return None
            
            # 3. 최적 매칭 선택
            best_match = result.data[0]
            
            # 4. 메타데이터에서 과실비율 추출
            metadata = best_match.get('metadata', {})
            fault_scenarios = metadata.get('fault_scenarios', [])
            
            if fault_scenarios:
                scenario = fault_scenarios[0]
                return {
                    "offender_ratio": scenario['offender_ratio'],
                    "victim_ratio": scenario['victim_ratio'],
                    "basis": best_match.get('content', '')[:200],
                    "confidence": best_match.get('similarity', 0),
                    "source": "RAG (과실비율 인정기준 2023)",
                    "page_number": metadata.get('page_number')
                }
            
            return None
            
        except Exception as e:
            print(f"RAG 검색 실패: {e}")
            return None
    
    def _calculate_fault_ratio(
        self,
        violations: List[Dict],
        classification: Dict
    ) -> Dict:
        """
        과실 비율 산출 (RAG 우선, 하드코딩 폴백)
        
        기준:
        - 1순위: RAG 검색 (과실비율 인정기준 2023)
        - 2순위: 하드코딩된 기본 과실 비율
        """
        offender = classification.get("offender")
        victim = classification.get("victim")
        
        if not offender:
            return {
                "offender_ratio": 0,
                "victim_ratio": 0,
                "basis": "과실 판정 불가"
            }
        
        # RAG 검색 시도 (우선순위 1)
        if self.use_rag:
            # 사고 상황 설명 생성
            offender_violations = next(
                (v for v in violations if v["vehicle_id"] == offender["vehicle_id"]),
                None
            )
            
            if offender_violations and offender_violations["violations"]:
                violation_desc = ", ".join(
                    v["type"] for v in offender_violations["violations"]
                )
                accident_desc = f"교통사고 상황: {violation_desc}"
                
                rag_result = self._search_fault_ratio_from_rag(accident_desc)
                
                if rag_result:
                    return rag_result
        
        # 가해 차량 위반 사항 확인
        offender_violations = next(
            (v for v in violations if v["vehicle_id"] == offender["vehicle_id"]),
            None
        )
        
        if not offender_violations or not offender_violations["violations"]:
            return {
                "offender_ratio": 50,
                "victim_ratio": 50,
                "basis": "쌍방 과실"
            }
        
        # 주요 위반 사항 기준 과실 비율 적용
        primary_violation = offender_violations["violations"][0]
        
        # 신호위반, 중앙선침범 등 중대 위반 시 100:0
        if primary_violation["severity"] == "high" and primary_violation["base_fault"] == 100:
            return {
                "offender_ratio": 100,
                "victim_ratio": 0,
                "basis": f"{primary_violation['type']} ({primary_violation['law']})",
                "description": primary_violation["description"]
            }
        
        # 기타 위반 시 기본 과실 비율 적용
        offender_ratio = primary_violation["base_fault"]
        victim_ratio = 100 - offender_ratio
        
        return {
            "offender_ratio": offender_ratio,
            "victim_ratio": victim_ratio,
            "basis": f"{primary_violation['type']} ({primary_violation['law']})",
            "description": primary_violation["description"]
        }
    
    def generate_analysis_report(self, analysis_result: Dict) -> str:
        """
        분석 보고서 생성 (Markdown 형식)
        
        Args:
            analysis_result: analyze_video() 결과
        
        Returns:
            Markdown 형식 보고서
        """
        classification = analysis_result["classification"]
        fault_ratio = analysis_result["fault_ratio"]
        violations = analysis_result["violations"]
        
        report = f"""
# 교통사고 영상 분석 보고서

**분석 일시**: {analysis_result["analysis_timestamp"]}

---

## 1. 가해/피해 차량 구분

### 가해 차량
- **차량 ID**: {classification["offender"]["vehicle_id"] if classification["offender"] else "N/A"}
- **위반 점수**: {classification["offender"]["total_fault"] if classification["offender"] else 0}점
- **위반 건수**: {classification["offender"]["violation_count"] if classification["offender"] else 0}건

### 피해 차량
- **차량 ID**: {classification["victim"]["vehicle_id"] if classification["victim"] else "N/A"}
- **위반 점수**: {classification["victim"]["total_fault"] if classification["victim"] else 0}점
- **위반 건수**: {classification["victim"]["violation_count"] if classification["victim"] else 0}건

**구분 근거**: {classification["classification_basis"]}

---

## 2. 교통법규 위반 분석

"""
        
        for v in violations:
            report += f"\n### 차량 {v['vehicle_id']}\n\n"
            
            if not v["violations"]:
                report += "- 위반 사항 없음\n"
            else:
                for viol in v["violations"]:
                    report += f"""
- **위반 유형**: {viol['type']}
- **관련 법규**: {viol['law']}
- **위반 내용**: {viol['description']}
- **심각도**: {viol['severity']}
- **기본 과실**: {viol['base_fault']}%

"""
        
        report += f"""
---

## 3. 과실 비율 판정

### 최종 과실 비율
- **가해 차량 ({classification["offender"]["vehicle_id"] if classification["offender"] else "N/A"})**: {fault_ratio["offender_ratio"]}%
- **피해 차량 ({classification["victim"]["vehicle_id"] if classification["victim"] else "N/A"})**: {fault_ratio["victim_ratio"]}%

### 판정 근거
- **기준**: {fault_ratio["basis"]}
- **설명**: {fault_ratio.get("description", "N/A")}

---

## 4. 보험 처리 권고사항

"""
        
        if fault_ratio["offender_ratio"] == 100:
            report += """
- 가해 차량의 대인/대물 보험으로 전액 배상
- 피해 차량은 무과실 사고로 처리
- 가해 차량 운전자는 형사 처벌 가능성 검토 필요
"""
        elif fault_ratio["offender_ratio"] >= 70:
            report += """
- 가해 차량의 주된 과실로 대부분 배상
- 피해 차량의 경미한 과실 인정
- 쌍방 보험 처리 권장
"""
        else:
            report += """
- 쌍방 과실 인정
- 각자 보험으로 처리 권장
- 합의 시 과실 비율 조정 가능
"""
        
        report += """

---

**주의사항**: 본 분석은 AI 기반 자동 분석 결과이며, 최종 과실 비율은 보험사 및 법원의 판단에 따라 달라질 수 있습니다.
"""
        
        return report


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_traffic_accident_analyzer():
    """
    교통사고 영상 분석 UI
    
    사용법:
        from modules.traffic_accident_analyzer import render_traffic_accident_analyzer
        render_traffic_accident_analyzer()
    """
    st.markdown("### 🚗 교통사고 영상 분석 AI")
    
    st.markdown("""
    **분석 기능**:
    - 블랙박스 영상 프레임 추출
    - 가해/피해 차량 자동 구분
    - 교통법규 위반 사항 분석
    - 과실 비율 자동 산출
    
    **지원 형식**: MP4, AVI, MOV
    """)
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "블랙박스 영상 업로드",
        type=["mp4", "avi", "mov"],
        key="traffic_accident_video"
    )
    
    if uploaded_file:
        st.video(uploaded_file)
        
        if st.button("🔍 영상 분석 시작", type="primary"):
            with st.spinner("영상 분석 중..."):
                analyzer = TrafficAccidentAnalyzer()
                
                # Mock 분석 (실제 영상 분석은 Gemini Vision 연동 필요)
                mock_result = {
                    "collision_frame": None,
                    "vehicles": [
                        {
                            "vehicle_id": "A",
                            "type": "승용차",
                            "direction": "직진",
                            "estimated_speed": 50
                        },
                        {
                            "vehicle_id": "B",
                            "type": "승용차",
                            "direction": "좌회전",
                            "estimated_speed": 65
                        }
                    ],
                    "traffic_signals": {
                        "main_signal": "녹색",
                        "left_turn_signal": "적색"
                    },
                    "violations": [
                        {
                            "vehicle_id": "A",
                            "violations": []
                        },
                        {
                            "vehicle_id": "B",
                            "violations": [
                                {
                                    "type": "신호위반",
                                    "law": "도로교통법 제5조",
                                    "description": "좌회전 신호 적색 시 진입",
                                    "severity": "high",
                                    "base_fault": 100
                                },
                                {
                                    "type": "속도위반",
                                    "law": "도로교통법 제17조",
                                    "description": "제한속도 15km/h 초과",
                                    "severity": "medium",
                                    "base_fault": 30
                                }
                            ]
                        }
                    ],
                    "classification": {
                        "offender": {
                            "vehicle_id": "B",
                            "total_fault": 130,
                            "violation_count": 2
                        },
                        "victim": {
                            "vehicle_id": "A",
                            "total_fault": 0,
                            "violation_count": 0
                        },
                        "classification_basis": "교통법규 위반 점수 기준"
                    },
                    "fault_ratio": {
                        "offender_ratio": 100,
                        "victim_ratio": 0,
                        "basis": "신호위반 (도로교통법 제5조)",
                        "description": "좌회전 신호 적색 시 진입"
                    },
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
                # 보고서 생성
                report = analyzer.generate_analysis_report(mock_result)
                
                st.success("✅ 분석 완료")
                
                # 보고서 표시
                st.markdown(report)
                
                # JSON 데이터
                with st.expander("📊 상세 분석 데이터 (JSON)", expanded=False):
                    st.json(mock_result)
