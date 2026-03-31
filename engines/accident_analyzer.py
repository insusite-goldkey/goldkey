"""
[Phase 5 고도화] 사고 분석 엔진 - 블랙박스 영상 분석 및 과실비율 추정
Gemini 1.5 Pro를 사용한 영상 분석 + RAG 기반 과실비율 매칭

작성일: 2026-03-30
"""
import os
import base64
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from supabase import create_client, Client


class AccidentAnalyzer:
    """
    블랙박스 영상 분석 및 과실비율 추정 엔진
    
    주요 기능:
    1. Gemini 1.5 Pro를 사용한 영상 분석 (가해/피해 차량 구분, 사고 상황 요약)
    2. RAG 기반 과실비율 인정기준 매칭
    3. 파손 부위 분석 및 수리비 추정
    """
    
    def __init__(
        self,
        gemini_api_key: str,
        supabase_url: str,
        supabase_key: str
    ):
        """
        Args:
            gemini_api_key: Google Gemini API 키
            supabase_url: Supabase 프로젝트 URL
            supabase_key: Supabase 서비스 키
        """
        # Gemini 초기화
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Supabase 초기화 (RAG 검색용)
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def analyze_dashcam_video(
        self,
        video_path: str,
        frame_interval: int = 30
    ) -> Dict:
        """
        블랙박스 영상 분석 (Gemini 1.5 Pro)
        
        Args:
            video_path: 블랙박스 영상 파일 경로 (MP4)
            frame_interval: 프레임 추출 간격 (기본 30프레임마다)
        
        Returns:
            {
                "success": bool,
                "summary": str,  # 사고 상황 요약
                "vehicles": {
                    "attacker": str,  # 가해 차량 정보
                    "victim": str     # 피해 차량 정보
                },
                "accident_type": str,  # 사고 유형 (추돌, 측면충돌, 교차로, 주차장 등)
                "damage_assessment": {
                    "damaged_parts": List[str],  # 파손 부위
                    "severity": str  # 경미/중간/심각
                },
                "timestamp": str,  # 사고 발생 시각
                "location_hint": str  # 위치 힌트
            }
        """
        try:
            print(f"📹 블랙박스 영상 분석 시작: {video_path}")
            
            # 영상 파일 업로드
            video_file = genai.upload_file(path=video_path)
            print(f"✅ 영상 업로드 완료: {video_file.name}")
            
            # Gemini 1.5 Pro 프롬프트 (신호 및 노면 정밀 인식 강화)
            prompt = """
당신은 자동차 사고 전문 분석가입니다. 제공된 블랙박스 영상을 분석하여 다음 정보를 추출하세요:

1. **사고 상황 요약** (3-5문장으로 명확하게)
   - 사고가 발생한 상황 (시간대, 도로 상황, 날씨 등)
   - 사고 발생 과정 (어떤 차량이 어떻게 움직였는지)
   - 충돌 지점 및 방식

2. **차량 정보**
   - 가해 차량: 차종, 색상, 번호판(보이는 경우), 주행 방향
   - 피해 차량: 차종, 색상, 번호판(보이는 경우), 주행 방향

3. **사고 유형 분류**
   다음 중 하나로 분류:
   - 추돌 (후미추돌, 전방추돌)
   - 측면충돌 (좌측, 우측)
   - 교차로 사고 (신호위반, 우회전, 좌회전)
   - 주차장 사고
   - 차선변경 사고
   - 기타

4. **파손 부위 및 심각도**
   - 파손된 차량 부위 (범퍼, 도어, 휀더, 후드, 트렁크, 헤드라이트, 테일라이트 등)
   - 심각도: 경미(스크래치/찌그러짐) / 중간(부품 교체 필요) / 심각(프레임 손상)

5. **사고 발생 시각** (영상에서 확인 가능한 경우)

6. **위치 힌트** (도로명, 건물, 표지판 등 식별 가능한 정보)

7. **🚥 신호 및 도로 상황 분석 (정밀 인식)**
   
   **A. 신호등 색상 변화 추적 (사고 전후 5~10초)**
   - 우리 차량(블랙박스 장착 차량) 진행 방향 신호등:
     * 사고 5초 전: [색상]
     * 사고 직전(1~2초 전): [색상]
     * 충돌 시점: [색상]
     * 사고 직후: [색상]
   
   - 상대 차량 진행 방향 신호등 (추정):
     * 사고 5초 전: [색상 또는 "확인 불가"]
     * 사고 직전(1~2초 전): [색상 또는 "확인 불가"]
     * 충돌 시점: [색상 또는 "확인 불가"]
   
   - 신호 변화 타이밍: [예: "충돌 3초 전 황색 → 적색 전환" 또는 "신호 변화 없음"]
   
   **B. 노면 표시 및 지시 인식**
   - 노면 화살표: [직진, 좌회전, 우회전, 유턴, 좌회전 전용, 직진+우회전 등]
   - 차로 구분선: [실선, 점선, 이중 실선 등]
   - 횡단보도: [있음/없음]
   - 정지선: [있음/없음]
   - 기타 노면 표시: [버스전용차로, 주정차금지구역, 어린이보호구역 등]
   
   **C. 교통 표지판 인식**
   - 규제 표지판: [일시정지, 진입금지, 주차금지, 속도제한 등]
   - 지시 표지판: [직진, 좌회전, 우회전, 유턴 등]
   - 주의 표지판: [교차로, 횡단보도, 어린이보호구역 등]
   - 보조 표지판: [시간대, 요일 제한 등]
   
   **D. 법규 위반 여부 판별**
   
   **우리 차량(블랙박스 장착 차량) 위반 사항:**
   - 신호위반: [있음/없음] - [상세 설명]
   - 지시위반: [있음/없음] - [상세 설명: 노면 화살표 또는 표지판 불이행]
   - 차로위반: [있음/없음] - [상세 설명: 실선 침범, 차로 변경 금지 구역 등]
   - 속도위반: [있음/없음] - [상세 설명: 제한속도 초과 여부]
   - 안전거리 미확보: [있음/없음] - [상세 설명]
   - 기타 위반: [있음/없음] - [상세 설명]
   
   **상대 차량 위반 사항:**
   - 신호위반: [있음/없음] - [상세 설명]
   - 지시위반: [있음/없음] - [상세 설명]
   - 차로위반: [있음/없음] - [상세 설명]
   - 속도위반: [있음/없음] - [상세 설명]
   - 안전거리 미확보: [있음/없음] - [상세 설명]
   - 기타 위반: [있음/없음] - [상세 설명]
   
   **E. 과실 판단 근거 (법규 위반 기반)**
   - 주요 과실 차량: [우리 차량/상대 차량/쌍방]
   - 과실 근거: [신호위반, 지시위반, 차로위반 등의 법규 위반 사항을 바탕으로 구체적 설명]
   - 예상 과실비율: [100:0, 80:20, 70:30, 50:50 등] - [근거 설명]

8. **🚨 경미 상해 및 과장 행동 분석 (연성 사기 감지)**
   
   **A. 초저속 미세 충돌 판별**
   - 블랙박스 지평선 흔들림 정도: [심함/보통/미세/거의 없음]
   - 차량 파손 정도: [심각/중간/경미/거의 없음]
   - 접근 속도 추정: [시속 __km/h 이하로 추정]
   - 미세 충돌 여부: [예/아니오] - [근거 설명]
   
   **B. 과장 행동 감지 (생체역학적 분석)**
   - 충돌 시 탑승자 신체 움직임:
     * 머리/목 움직임: [자연스러움/과도함/시간차 있음]
     * 상체 움직임: [자연스러움/과도함/시간차 있음]
     * 충격 강도 대비 신체 반응: [일치함/과장됨]
   
   - 과장 행동 의심 지표:
     * 물리적 충격 강도와 신체 움직임의 불일치: [있음/없음] - [상세 설명]
     * 시간차를 둔 과장된 행동: [있음/없음] - [상세 설명]
     * 생체역학적 모순: [있음/없음] - [상세 설명]
   
   **C. 과장 청구 추론**
   - 물리적 충격과 신체 움직임의 인과관계 모순: [있음/없음]
   - 과장 청구 의심 소견: [높음/보통/낮음/없음]
   - 의심 근거: [구체적 설명]
   
   **D. 보험사기 대응 필요성**
   - 연성 사기(Soft Fraud) 가능성: [높음/보통/낮음/없음]
   - 대응 권고 수위: [강력 권고/권고/모니터링/불필요]
   - 권고 사유: [구체적 설명]

**출력 형식 (JSON)**:
```json
{
  "summary": "사고 상황 요약 (3-5문장)",
  "vehicles": {
    "attacker": "가해 차량 정보",
    "victim": "피해 차량 정보"
  },
  "accident_type": "사고 유형",
  "damage_assessment": {
    "damaged_parts": ["파손 부위1", "파손 부위2"],
    "severity": "경미/중간/심각"
  },
  "timestamp": "사고 발생 시각 (HH:MM:SS 또는 알 수 없음)",
  "location_hint": "위치 힌트 (또는 알 수 없음)",
  "signal_and_road_analysis": {
    "traffic_signals": {
      "our_vehicle": {
        "5_seconds_before": "색상 또는 확인 불가",
        "1_second_before": "색상 또는 확인 불가",
        "at_collision": "색상 또는 확인 불가",
        "after_collision": "색상 또는 확인 불가"
      },
      "opponent_vehicle": {
        "5_seconds_before": "색상 또는 확인 불가",
        "1_second_before": "색상 또는 확인 불가",
        "at_collision": "색상 또는 확인 불가"
      },
      "signal_change_timing": "신호 변화 타이밍 설명"
    },
    "road_markings": {
      "arrows": "노면 화살표 설명",
      "lane_lines": "차로 구분선 설명",
      "crosswalk": "있음/없음",
      "stop_line": "있음/없음",
      "other_markings": "기타 노면 표시"
    },
    "traffic_signs": {
      "regulatory": "규제 표지판 목록",
      "guide": "지시 표지판 목록",
      "warning": "주의 표지판 목록",
      "auxiliary": "보조 표지판 목록"
    },
    "violations": {
      "our_vehicle": {
        "signal_violation": {"exists": true/false, "detail": "상세 설명"},
        "direction_violation": {"exists": true/false, "detail": "상세 설명"},
        "lane_violation": {"exists": true/false, "detail": "상세 설명"},
        "speed_violation": {"exists": true/false, "detail": "상세 설명"},
        "safe_distance_violation": {"exists": true/false, "detail": "상세 설명"},
        "other_violations": {"exists": true/false, "detail": "상세 설명"}
      },
      "opponent_vehicle": {
        "signal_violation": {"exists": true/false, "detail": "상세 설명"},
        "direction_violation": {"exists": true/false, "detail": "상세 설명"},
        "lane_violation": {"exists": true/false, "detail": "상세 설명"},
        "speed_violation": {"exists": true/false, "detail": "상세 설명"},
        "safe_distance_violation": {"exists": true/false, "detail": "상세 설명"},
        "other_violations": {"exists": true/false, "detail": "상세 설명"}
      }
    },
    "fault_judgment": {
      "primary_fault_vehicle": "우리 차량/상대 차량/쌍방",
      "fault_basis": "과실 근거 상세 설명",
      "estimated_fault_ratio": "예상 과실비율 (예: 100:0, 80:20 등)",
      "ratio_basis": "과실비율 근거 설명"
    }
  },
  "minor_injury_analysis": {
    "minor_collision_detection": {
      "horizon_shake": "심함/보통/미세/거의 없음",
      "vehicle_damage": "심각/중간/경미/거의 없음",
      "approach_speed": "시속 __km/h 이하로 추정",
      "is_minor_collision": true/false,
      "basis": "근거 설명"
    },
    "exaggerated_behavior_detection": {
      "occupant_movement": {
        "head_neck": "자연스러움/과도함/시간차 있음",
        "upper_body": "자연스러움/과도함/시간차 있음",
        "reaction_vs_impact": "일치함/과장됨"
      },
      "suspicious_indicators": {
        "physical_inconsistency": {"exists": true/false, "detail": "상세 설명"},
        "delayed_exaggeration": {"exists": true/false, "detail": "상세 설명"},
        "biomechanical_contradiction": {"exists": true/false, "detail": "상세 설명"}
      }
    },
    "exaggerated_claim_inference": {
      "causal_contradiction": true/false,
      "suspicion_level": "높음/보통/낮음/없음",
      "suspicion_basis": "구체적 설명"
    },
    "fraud_response_necessity": {
      "soft_fraud_possibility": "높음/보통/낮음/없음",
      "response_level": "강력 권고/권고/모니터링/불필요",
      "response_reason": "구체적 설명"
    }
  }
}
```

**중요**: 
1. 반드시 JSON 형식으로만 응답하세요. 추가 설명은 포함하지 마세요.
2. 신호등이 보이지 않거나 확인이 어려운 경우 "확인 불가"로 표시하세요.
3. 법규 위반 여부는 영상에서 명확히 확인되는 경우에만 "있음"으로 표시하세요.
4. 과실 판단은 법규 위반 사항을 바탕으로 객관적으로 작성하세요.
5. 경미 상해 분석은 영상에서 탑승자가 보이고 충돌이 미세한 경우에만 수행하세요. 탑승자가 보이지 않거나 충돌이 명확히 큰 경우 "없음" 또는 "불필요"로 표시하세요.
"""
            
            # Gemini API 호출
            print("🤖 Gemini 1.5 Pro 분석 중...")
            response = self.gemini_model.generate_content([video_file, prompt])
            
            # JSON 파싱
            import json
            response_text = response.text.strip()
            
            # JSON 코드 블록 제거
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            result = json.loads(response_text.strip())
            
            print("✅ 영상 분석 완료")
            
            return {
                "success": True,
                **result
            }
        
        except Exception as e:
            print(f"❌ 영상 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": "",
                "vehicles": {"attacker": "", "victim": ""},
                "accident_type": "",
                "damage_assessment": {"damaged_parts": [], "severity": ""},
                "timestamp": "",
                "location_hint": ""
            }
    
    def match_fault_ratio(
        self,
        accident_summary: str,
        accident_type: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        RAG 기반 과실비율 인정기준 매칭
        
        Args:
            accident_summary: 사고 상황 요약
            accident_type: 사고 유형
            top_k: 상위 K개 결과 반환
        
        Returns:
            [
                {
                    "document_name": str,
                    "content": str,
                    "similarity": float,
                    "fault_ratio": str  # 예: "가해 80% : 피해 20%"
                }
            ]
        """
        try:
            print(f"🔍 과실비율 인정기준 검색 중...")
            print(f"  사고 유형: {accident_type}")
            
            # 검색 쿼리 생성
            search_query = f"{accident_type} {accident_summary}"
            
            # OpenAI 임베딩 생성
            from openai import OpenAI
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            embedding_response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=search_query
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Supabase에서 유사도 검색 (과실비율 인정기준 문서만)
            result = self.supabase.rpc(
                'match_gk_knowledge',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.5,
                    'match_count': top_k,
                    'filter_category': '과실비율'
                }
            ).execute()
            
            if not result.data:
                print("⚠️ 과실비율 인정기준을 찾을 수 없습니다.")
                return []
            
            # 결과 포맷팅
            matched_results = []
            for item in result.data:
                matched_results.append({
                    "document_name": item.get("document_name", ""),
                    "content": item.get("content", ""),
                    "similarity": item.get("similarity", 0.0),
                    "fault_ratio": self._extract_fault_ratio(item.get("content", ""))
                })
            
            print(f"✅ {len(matched_results)}개 과실비율 기준 발견")
            return matched_results
        
        except Exception as e:
            print(f"❌ 과실비율 매칭 실패: {e}")
            return []
    
    def _extract_fault_ratio(self, content: str) -> str:
        """
        텍스트에서 과실비율 추출 (예: "80:20", "100:0")
        """
        import re
        
        # 패턴 1: "80:20", "100:0"
        pattern1 = r'(\d{1,3})\s*:\s*(\d{1,3})'
        match1 = re.search(pattern1, content)
        if match1:
            return f"가해 {match1.group(1)}% : 피해 {match1.group(2)}%"
        
        # 패턴 2: "80대 20", "100대 0"
        pattern2 = r'(\d{1,3})\s*대\s*(\d{1,3})'
        match2 = re.search(pattern2, content)
        if match2:
            return f"가해 {match2.group(1)}% : 피해 {match2.group(2)}%"
        
        return "과실비율 정보 없음"
    
    def estimate_repair_cost(
        self,
        damaged_parts: List[str],
        severity: str,
        vehicle_type: str = "승용차"
    ) -> Dict:
        """
        수리비 추정 (파손 부위 기반)
        
        Args:
            damaged_parts: 파손 부위 리스트
            severity: 심각도 (경미/중간/심각)
            vehicle_type: 차량 종류 (승용차/SUV/트럭 등)
        
        Returns:
            {
                "total_estimate": int,  # 총 예상 수리비 (원)
                "parts_detail": [
                    {
                        "part": str,
                        "repair_type": str,  # 교체/복원/도색
                        "cost_range": str    # 예: "50만원 ~ 100만원"
                    }
                ],
                "disclaimer": str  # 면책 조항
            }
        """
        # 부위별 평균 수리비 (승용차 기준, 2026년 기준)
        REPAIR_COST_TABLE = {
            "범퍼": {"교체": (300000, 500000), "복원": (150000, 300000), "도색": (100000, 200000)},
            "도어": {"교체": (500000, 1000000), "복원": (300000, 600000), "도색": (150000, 300000)},
            "휀더": {"교체": (400000, 700000), "복원": (200000, 400000), "도색": (100000, 250000)},
            "후드": {"교체": (600000, 1200000), "복원": (300000, 600000), "도색": (150000, 350000)},
            "트렁크": {"교체": (500000, 1000000), "복원": (250000, 500000), "도색": (150000, 300000)},
            "헤드라이트": {"교체": (300000, 800000), "복원": (0, 0), "도색": (0, 0)},
            "테일라이트": {"교체": (200000, 600000), "복원": (0, 0), "도색": (0, 0)},
            "사이드미러": {"교체": (150000, 400000), "복원": (50000, 150000), "도색": (30000, 80000)},
            "프레임": {"교체": (3000000, 10000000), "복원": (1000000, 3000000), "도색": (0, 0)},
        }
        
        # 심각도에 따른 수리 방식 결정
        repair_type_map = {
            "경미": "도색",
            "중간": "복원",
            "심각": "교체"
        }
        
        repair_type = repair_type_map.get(severity, "복원")
        
        parts_detail = []
        total_min = 0
        total_max = 0
        
        for part in damaged_parts:
            # 부위 매칭 (유사 단어 처리)
            matched_part = None
            for key in REPAIR_COST_TABLE.keys():
                if key in part or part in key:
                    matched_part = key
                    break
            
            if not matched_part:
                matched_part = "기타"
                cost_range = (100000, 500000)
            else:
                cost_range = REPAIR_COST_TABLE[matched_part].get(repair_type, (100000, 500000))
            
            # 프레임 손상은 무조건 교체
            if "프레임" in part or "골격" in part:
                repair_type = "교체"
                cost_range = REPAIR_COST_TABLE["프레임"]["교체"]
            
            parts_detail.append({
                "part": part,
                "repair_type": repair_type,
                "cost_range": f"{cost_range[0]:,}원 ~ {cost_range[1]:,}원"
            })
            
            total_min += cost_range[0]
            total_max += cost_range[1]
        
        # 차량 종류에 따른 보정 (SUV는 +20%, 트럭은 +30%)
        if "SUV" in vehicle_type or "suv" in vehicle_type:
            total_min = int(total_min * 1.2)
            total_max = int(total_max * 1.2)
        elif "트럭" in vehicle_type or "truck" in vehicle_type:
            total_min = int(total_min * 1.3)
            total_max = int(total_max * 1.3)
        
        return {
            "total_estimate": (total_min + total_max) // 2,
            "total_range": f"{total_min:,}원 ~ {total_max:,}원",
            "parts_detail": parts_detail,
            "disclaimer": "※ 본 수리비는 일반적인 시장 가격을 기준으로 한 예상 금액이며, 실제 수리비는 정비소, 차량 연식, 부품 가격 등에 따라 달라질 수 있습니다. 정확한 수리비는 정비소 견적을 받아보시기 바랍니다."
        }
    
    def analyze_accident_full(
        self,
        video_path: str
    ) -> Dict:
        """
        사고 전체 분석 (영상 분석 + 과실비율 매칭 + 수리비 추정)
        
        Args:
            video_path: 블랙박스 영상 파일 경로
        
        Returns:
            {
                "video_analysis": Dict,  # 영상 분석 결과
                "fault_ratio_matches": List[Dict],  # 과실비율 매칭 결과
                "repair_estimate": Dict  # 수리비 추정 결과
            }
        """
        print("\n" + "="*80)
        print("🚗 사고 전체 분석 시작")
        print("="*80)
        
        # 1. 영상 분석
        video_analysis = self.analyze_dashcam_video(video_path)
        
        if not video_analysis["success"]:
            return {
                "video_analysis": video_analysis,
                "fault_ratio_matches": [],
                "repair_estimate": {}
            }
        
        # 2. 과실비율 매칭
        fault_ratio_matches = self.match_fault_ratio(
            accident_summary=video_analysis["summary"],
            accident_type=video_analysis["accident_type"]
        )
        
        # 3. 수리비 추정
        repair_estimate = self.estimate_repair_cost(
            damaged_parts=video_analysis["damage_assessment"]["damaged_parts"],
            severity=video_analysis["damage_assessment"]["severity"]
        )
        
        print("\n" + "="*80)
        print("✅ 사고 전체 분석 완료")
        print("="*80)
        
        # 4. 보험사기 대응 가이드 생성 (경미 상해 분석 결과 기반)
        fraud_response_guide = self.generate_fraud_response_guide(video_analysis)
        
        return {
            "video_analysis": video_analysis,
            "fault_ratio_matches": fault_ratio_matches,
            "repair_estimate": repair_estimate,
            "fraud_response_guide": fraud_response_guide
        }
    
    def generate_fraud_response_guide(self, video_analysis: Dict) -> Dict:
        """
        보험사기 대응 법률 가이드 생성
        
        Args:
            video_analysis: 영상 분석 결과
        
        Returns:
            {
                "is_applicable": bool,  # 가이드 적용 여부
                "response_level": str,  # 대응 수위
                "legal_guide": str,  # 법률 가이드 텍스트
                "action_steps": List[str]  # 실행 단계
            }
        """
        minor_injury = video_analysis.get("minor_injury_analysis", {})
        
        if not minor_injury:
            return {
                "is_applicable": False,
                "response_level": "불필요",
                "legal_guide": "",
                "action_steps": []
            }
        
        fraud_necessity = minor_injury.get("fraud_response_necessity", {})
        response_level = fraud_necessity.get("response_level", "불필요")
        soft_fraud_possibility = fraud_necessity.get("soft_fraud_possibility", "없음")
        
        if response_level == "불필요" or soft_fraud_possibility == "없음":
            return {
                "is_applicable": False,
                "response_level": response_level,
                "legal_guide": "",
                "action_steps": []
            }
        
        # 대응 수위별 가이드 생성
        legal_guide = self._generate_legal_guide_text(response_level, soft_fraud_possibility, minor_injury)
        action_steps = self._generate_action_steps(response_level)
        
        return {
            "is_applicable": True,
            "response_level": response_level,
            "soft_fraud_possibility": soft_fraud_possibility,
            "legal_guide": legal_guide,
            "action_steps": action_steps
        }
    
    def _generate_legal_guide_text(self, response_level: str, fraud_possibility: str, minor_injury: Dict) -> str:
        """보험사기 대응 법률 가이드 텍스트 생성"""
        
        guide = f"""
⚖️ 보험사기 대응 법률 가이드

【 분석 결과 】
- 연성 사기(Soft Fraud) 가능성: {fraud_possibility}
- 대응 권고 수위: {response_level}

【 법적 근거 】
본 사고는 미세 충돌임에도 불구하고 과장된 신체 반응이 감지되어, 보험사기방지 특별법상 '연성 사기(Soft Fraud)'에 해당할 가능성이 있습니다.

▶ 보험사기방지 특별법 제8조 (보험사기행위)
"거짓이나 그 밖의 부정한 방법으로 보험금을 청구하거나 수령한 자는 10년 이하의 징역 또는 5천만 원 이하의 벌금에 처한다."

【 대응 전략 】
"""
        
        if response_level == "강력 권고":
            guide += """
1단계: 객관적 증거 확보
- 마디모(Madimo) 프로그램 신청: 도로교통공단의 충격량 분석을 통해 '인명 피해가 발생할 정도의 충격이 아님'을 증명
- AI 정밀 분석 리포트: 본 앱의 "물리 법칙에 위배되는 과장된 신체 움직임" 분석 자료 활용

2단계: 보험사 SIU(사기조사팀) 연계
- 해당 보험사 SIU에 '보험사기 의심 건'으로 정식 조사 의뢰
- 과거 유사업종 및 동일 부위 반복 청구 이력 확인 요청

3단계: 법적 고지 및 압박
- 보험사기방지 특별법 위반 시 처벌 수위를 내용증명 또는 문자로 고지
- 금융감독원(FSS) 보험사기 신고 센터 접수 예고

4단계: 채무부존재 확인 소송 (최후의 수단)
- 치료비 지급을 거부하고, 법원에 "배상 책임 없음"을 확인하는 소송 제기
- 소송 부담감으로 상대방이 합의를 포기하는 경우가 많음
"""
        elif response_level == "권고":
            guide += """
1단계: 객관적 증거 확보
- 마디모(Madimo) 프로그램 신청 검토
- AI 정밀 분석 리포트 보관

2단계: 보험사 상담
- 보험사 담당자에게 미세 충돌 사실 및 AI 분석 결과 전달
- 과도한 청구 시 SIU 조사 의뢰 가능성 언급

3단계: 법적 고지 준비
- 필요 시 보험사기방지 특별법 안내 준비
"""
        else:  # 모니터링
            guide += """
1단계: 상황 모니터링
- 상대방의 치료 기간 및 청구 금액 추이 관찰
- 과도한 청구 시 즉시 대응 전환

2단계: 증거 보관
- 블랙박스 영상 및 AI 분석 리포트 안전하게 보관
"""
        
        guide += """

【 주요 연락처 】
- 금융감독원 보험사기 신고 센터: 1332
- 도로교통공단 마디모 프로그램: 1577-1120
- 경찰청 보험범죄 신고: 112

【 주의사항 】
본 가이드는 법률 자문이 아니며, 실제 대응 시에는 변호사 등 전문가와 상담하시기 바랍니다.
"""
        
        return guide.strip()
    
    def _generate_action_steps(self, response_level: str) -> List[str]:
        """실행 단계 리스트 생성"""
        
        if response_level == "강력 권고":
            return [
                "📋 마디모(Madimo) 프로그램 신청 (도로교통공단 1577-1120)",
                "🔍 보험사 SIU(사기조사팀)에 조사 의뢰",
                "📄 보험사기방지 특별법 위반 고지 (내용증명 발송)",
                "⚖️ 금융감독원 보험사기 신고 센터 접수 (1332)",
                "🏛️ 채무부존재 확인 소송 준비 (변호사 상담)"
            ]
        elif response_level == "권고":
            return [
                "📋 마디모(Madimo) 프로그램 신청 검토",
                "📞 보험사 담당자에게 미세 충돌 사실 전달",
                "📄 AI 분석 리포트 보관 및 제출 준비",
                "⚠️ 과도한 청구 시 SIU 조사 의뢰 가능성 언급"
            ]
        else:  # 모니터링
            return [
                "👀 상대방 치료 기간 및 청구 금액 추이 관찰",
                "💾 블랙박스 영상 및 AI 분석 리포트 안전 보관",
                "📊 과도한 청구 발생 시 즉시 대응 전환"
            ]


# ══════════════════════════════════════════════════════════════════════════════
# 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
        print("❌ 환경변수 미설정:")
        print("  - GEMINI_API_KEY")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_KEY")
        sys.exit(1)
    
    # 분석기 초기화
    analyzer = AccidentAnalyzer(
        gemini_api_key=GEMINI_API_KEY,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
    
    print("✅ 사고 분석 엔진 모듈 로드 완료")
    print("사용 예시:")
    print("  result = analyzer.analyze_accident_full('dashcam_video.mp4')")
