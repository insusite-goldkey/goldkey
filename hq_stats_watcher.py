"""
hq_stats_watcher.py — 실시간 외부 통계 동기화 및 지식 베이스 자동 패치 엔진
[GP-STEP14] Goldkey AI Masters 2026

4단계 파이프라인:
1. 데이터 소스 연결 (API Connector) - KOSIS, HIRA 등
2. 변화 감지 및 비교 (Change Detection)
3. Supabase 자동 업데이트 (Database Patch)
4. AI 컨텍스트 즉시 반영 (RAG Refresh)

에이젠틱 가드레일: "승인 후 반영" 모드
"""
from __future__ import annotations
import requests
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import streamlit as st


# ══════════════════════════════════════════════════════════════════════════════
# [1] 데이터 소스 연결 (API Connector)
# ══════════════════════════════════════════════════════════════════════════════

class KOSISConnector:
    """
    국가통계포털(KOSIS) API 인터페이스
    
    주요 통계:
    - 암 발생률 (국가암등록통계)
    - 평균 치료비
    - 5년 생존율
    """
    
    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: KOSIS API 인증키 (선택)
        """
        self.api_key = api_key or self._get_api_key()
        self.base_url = "https://kosis.kr/openapi"
        
    def _get_api_key(self) -> str:
        """API 키 가져오기 (st.secrets 또는 환경변수)"""
        try:
            return st.secrets.get("KOSIS_API_KEY", "")
        except:
            import os
            return os.environ.get("KOSIS_API_KEY", "")
    
    def fetch_cancer_incidence_rate(self) -> Dict[str, Any]:
        """
        암 발생률 통계 수집
        
        Returns:
            dict: {
                "male_rate": 39.1,
                "female_rate": 36.0,
                "total_rate": 38.1,
                "source": "KOSIS",
                "updated_at": "2026-04-01",
                "reference_year": "2021"
            }
        """
        # [GP-STEP14] 실제 KOSIS API 호출 로직
        # 현재는 Mock 데이터 반환 (실제 API 키 발급 후 구현)
        
        # TODO: 실제 API 호출 구현
        # endpoint = f"{self.base_url}/Param/statisticsParameterData.do"
        # params = {
        #     "method": "getList",
        #     "apiKey": self.api_key,
        #     "itmId": "T10+",  # 암 발생률 항목 ID
        #     "objL1": "ALL",
        #     "format": "json"
        # }
        # response = requests.get(endpoint, params=params)
        # data = response.json()
        
        # Mock 데이터 (2026년 최신 통계 가정)
        return {
            "male_rate": 39.1,
            "female_rate": 36.0,
            "total_rate": 38.1,
            "source": "KOSIS",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d"),
            "reference_year": "2021",
            "data_type": "cancer_incidence_rate"
        }
    
    def fetch_cancer_treatment_cost(self) -> Dict[str, Any]:
        """
        암 치료비 평균 통계 수집
        
        Returns:
            dict: {
                "average_cost": 38000000,
                "ngs_test_cost": 1500000,
                "targeted_therapy_yearly": 50000000,
                "immunotherapy_yearly": 100000000,
                "source": "HIRA",
                "updated_at": "2026-04-01"
            }
        """
        # Mock 데이터
        return {
            "average_cost": 38000000,
            "ngs_test_cost": 1500000,
            "targeted_therapy_yearly": 50000000,
            "immunotherapy_yearly": 100000000,
            "source": "HIRA",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d"),
            "data_type": "cancer_treatment_cost"
        }


class HIRAConnector:
    """
    건강보험심사평가원(HIRA) API 인터페이스
    
    주요 통계:
    - 비급여 치료비
    - 진료비 통계
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._get_api_key()
        self.base_url = "https://openapi.hira.or.kr"
    
    def _get_api_key(self) -> str:
        """API 키 가져오기"""
        try:
            return st.secrets.get("HIRA_API_KEY", "")
        except:
            import os
            return os.environ.get("HIRA_API_KEY", "")
    
    def fetch_non_covered_costs(self) -> Dict[str, Any]:
        """
        비급여 치료비 통계 수집
        
        Returns:
            dict: 비급여 치료비 데이터
        """
        # Mock 데이터
        return {
            "average_non_covered": 28000000,
            "min_non_covered": 15000000,
            "max_non_covered": 55000000,
            "source": "HIRA",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d"),
            "data_type": "non_covered_costs"
        }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 변화 감지 및 비교 (Change Detection)
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    """Supabase 클라이언트 가져오기"""
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def compare_stats(
    current_stats: Dict[str, Any],
    new_stats: Dict[str, Any],
    threshold: float = 0.5
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    지능형 데이터 비교 엔진
    
    Args:
        current_stats: 현재 Supabase에 저장된 통계
        new_stats: 새로 수집된 통계
        threshold: 유의미한 변화 판단 임계값 (%)
    
    Returns:
        tuple: (변화 발생 여부, 변화 상세 목록)
    """
    changes = []
    has_significant_change = False
    
    # 암 발생률 비교
    if "total_rate" in current_stats and "total_rate" in new_stats:
        current_rate = float(current_stats["total_rate"])
        new_rate = float(new_stats["total_rate"])
        diff_percent = abs(new_rate - current_rate)
        
        if diff_percent >= threshold:
            has_significant_change = True
            changes.append({
                "field": "암 발생률 (전체)",
                "current_value": current_rate,
                "new_value": new_rate,
                "diff_percent": diff_percent,
                "change_type": "increase" if new_rate > current_rate else "decrease",
                "significance": "high" if diff_percent >= 1.0 else "medium"
            })
    
    # 남성 암 발생률 비교
    if "male_rate" in current_stats and "male_rate" in new_stats:
        current_male = float(current_stats["male_rate"])
        new_male = float(new_stats["male_rate"])
        diff_percent = abs(new_male - current_male)
        
        if diff_percent >= threshold:
            has_significant_change = True
            changes.append({
                "field": "암 발생률 (남성)",
                "current_value": current_male,
                "new_value": new_male,
                "diff_percent": diff_percent,
                "change_type": "increase" if new_male > current_male else "decrease",
                "significance": "high" if diff_percent >= 1.0 else "medium"
            })
    
    # 여성 암 발생률 비교
    if "female_rate" in current_stats and "female_rate" in new_stats:
        current_female = float(current_stats["female_rate"])
        new_female = float(new_stats["female_rate"])
        diff_percent = abs(new_female - current_female)
        
        if diff_percent >= threshold:
            has_significant_change = True
            changes.append({
                "field": "암 발생률 (여성)",
                "current_value": current_female,
                "new_value": new_female,
                "diff_percent": diff_percent,
                "change_type": "increase" if new_female > current_female else "decrease",
                "significance": "high" if diff_percent >= 1.0 else "medium"
            })
    
    # 평균 치료비 비교
    if "average_cost" in current_stats and "average_cost" in new_stats:
        current_cost = float(current_stats["average_cost"])
        new_cost = float(new_stats["average_cost"])
        diff_percent = abs((new_cost - current_cost) / current_cost * 100)
        
        if diff_percent >= threshold:
            has_significant_change = True
            changes.append({
                "field": "암 평균 치료비",
                "current_value": current_cost,
                "new_value": new_cost,
                "diff_percent": diff_percent,
                "change_type": "increase" if new_cost > current_cost else "decrease",
                "significance": "high" if diff_percent >= 5.0 else "medium"
            })
    
    return has_significant_change, changes


def save_pending_update(
    changes: List[Dict[str, Any]],
    source: str,
    agent_id: str = "system"
) -> bool:
    """
    변동 사항을 pending_updates 테이블에 임시 저장
    
    Args:
        changes: 변화 상세 목록
        source: 데이터 출처 (KOSIS, HIRA 등)
        agent_id: 관리자 ID
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        for change in changes:
            sb.table("gk_pending_updates").insert({
                "field_name": change["field"],
                "current_value": str(change["current_value"]),
                "new_value": str(change["new_value"]),
                "diff_percent": change["diff_percent"],
                "change_type": change["change_type"],
                "significance": change["significance"],
                "source": source,
                "status": "pending",
                "created_at": datetime.datetime.now().isoformat(),
                "agent_id": agent_id
            }).execute()
        
        return True
    except Exception as e:
        print(f"[ERROR] save_pending_update: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [3] Supabase 자동 업데이트 (Database Patch)
# ══════════════════════════════════════════════════════════════════════════════

def apply_global_stats_patch(
    pending_update_ids: List[str],
    agent_id: str
) -> Dict[str, Any]:
    """
    원클릭 전역 업데이트 (Global Patch)
    
    관리자 승인 시, 관련된 모든 워룸 스크립트, RAG 지식, AI 제안서 프롬프트 내의 숫자를 일괄 업데이트
    
    Args:
        pending_update_ids: 승인할 pending_updates 레코드 ID 목록
        agent_id: 관리자 ID
    
    Returns:
        dict: {
            "success": True,
            "updated_count": 5,
            "affected_tables": ["gk_knowledge_base", "gk_war_room_scripts"],
            "audit_log_id": "uuid"
        }
    """
    try:
        sb = _get_sb()
        if not sb:
            return {"success": False, "error": "Supabase connection failed"}
        
        updated_count = 0
        affected_tables = set()
        
        # pending_updates에서 승인 대기 중인 변경사항 조회
        pending_updates = (
            sb.table("gk_pending_updates")
            .select("*")
            .in_("id", pending_update_ids)
            .eq("status", "pending")
            .execute()
        )
        
        if not pending_updates.data:
            return {"success": False, "error": "No pending updates found"}
        
        for update in pending_updates.data:
            field_name = update["field_name"]
            new_value = update["new_value"]
            source = update["source"]
            
            # [GP-STEP14] gk_knowledge_base 테이블 업데이트
            if "암 발생률" in field_name:
                # 암 발생률 관련 지식 베이스 업데이트
                result = sb.table("gk_knowledge_base").update({
                    "content": sb.rpc("replace_stat_value", {
                        "old_value": update["current_value"],
                        "new_value": new_value,
                        "field_name": field_name
                    }),
                    "updated_at": datetime.datetime.now().isoformat(),
                    "source_tag": f"[출처: {source} {datetime.datetime.now().strftime('%Y-%m-%d')} 업데이트]"
                }).eq("document_category", "PSP-01-암보험").execute()
                
                affected_tables.add("gk_knowledge_base")
                updated_count += len(result.data) if result.data else 0
            
            elif "치료비" in field_name:
                # 치료비 관련 지식 베이스 업데이트
                result = sb.table("gk_knowledge_base").update({
                    "content": sb.rpc("replace_stat_value", {
                        "old_value": update["current_value"],
                        "new_value": new_value,
                        "field_name": field_name
                    }),
                    "updated_at": datetime.datetime.now().isoformat(),
                    "source_tag": f"[출처: {source} {datetime.datetime.now().strftime('%Y-%m-%d')} 업데이트]"
                }).eq("document_category", "PSP-01-암보험").execute()
                
                affected_tables.add("gk_knowledge_base")
                updated_count += len(result.data) if result.data else 0
            
            # pending_updates 상태를 'approved'로 변경
            sb.table("gk_pending_updates").update({
                "status": "approved",
                "approved_at": datetime.datetime.now().isoformat(),
                "approved_by": agent_id
            }).eq("id", update["id"]).execute()
        
        # Audit Log 기록
        audit_log = sb.table("gk_audit_log").insert({
            "action": "global_stats_patch",
            "agent_id": agent_id,
            "affected_tables": list(affected_tables),
            "updated_count": updated_count,
            "pending_update_ids": pending_update_ids,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        
        audit_log_id = audit_log.data[0]["id"] if audit_log.data else None
        
        return {
            "success": True,
            "updated_count": updated_count,
            "affected_tables": list(affected_tables),
            "audit_log_id": audit_log_id
        }
    
    except Exception as e:
        print(f"[ERROR] apply_global_stats_patch: {e}")
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# [4] 스케줄러 및 메인 워처 함수
# ══════════════════════════════════════════════════════════════════════════════

def run_stats_watcher(agent_id: str = "system") -> Dict[str, Any]:
    """
    통계 감시 스케줄러 메인 함수
    
    정기적으로(예: 매월 1일) 실행되어 최신 통계를 수집하고 변화를 감지
    
    Args:
        agent_id: 실행 주체 ID
    
    Returns:
        dict: {
            "success": True,
            "changes_detected": True,
            "pending_updates_count": 3,
            "message": "3개의 통계 변동이 감지되었습니다. 승인 대기 중입니다."
        }
    """
    try:
        # 1. 데이터 소스 연결
        kosis = KOSISConnector()
        hira = HIRAConnector()
        
        # 2. 최신 통계 수집
        new_cancer_stats = kosis.fetch_cancer_incidence_rate()
        new_treatment_cost = kosis.fetch_cancer_treatment_cost()
        new_non_covered = hira.fetch_non_covered_costs()
        
        # 3. 현재 DB에 저장된 통계 조회
        sb = _get_sb()
        if not sb:
            return {"success": False, "error": "Supabase connection failed"}
        
        current_stats_result = (
            sb.table("gk_current_stats")
            .select("*")
            .eq("data_type", "cancer_incidence_rate")
            .execute()
        )
        
        current_stats = current_stats_result.data[0] if current_stats_result.data else {}
        
        # 4. 변화 감지
        has_change, changes = compare_stats(current_stats, new_cancer_stats)
        
        if has_change:
            # 5. pending_updates 테이블에 저장
            save_pending_update(changes, new_cancer_stats["source"], agent_id)
            
            return {
                "success": True,
                "changes_detected": True,
                "pending_updates_count": len(changes),
                "changes": changes,
                "message": f"{len(changes)}개의 통계 변동이 감지되었습니다. 승인 대기 중입니다."
            }
        else:
            return {
                "success": True,
                "changes_detected": False,
                "pending_updates_count": 0,
                "message": "유의미한 통계 변동이 감지되지 않았습니다."
            }
    
    except Exception as e:
        print(f"[ERROR] run_stats_watcher: {e}")
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# [5] 출처 자동 태깅 유틸리티
# ══════════════════════════════════════════════════════════════════════════════

def add_source_tag(content: str, source: str, updated_at: str) -> str:
    """
    출처 자동 태깅
    
    Args:
        content: 원본 텍스트
        source: 출처 (KOSIS, HIRA 등)
        updated_at: 업데이트 날짜
    
    Returns:
        str: 출처 태그가 추가된 텍스트
    """
    source_tag = f" [출처: {source} {updated_at} 업데이트]"
    
    # 기존 출처 태그가 있으면 교체
    if "[출처:" in content:
        import re
        content = re.sub(r'\[출처:.*?\]', source_tag, content)
    else:
        # 없으면 끝에 추가
        content += source_tag
    
    return content


def render_stats_approval_dashboard(agent_id: str):
    """
    통계 승인 대시보드 렌더링 (Streamlit UI)
    
    Args:
        agent_id: 관리자 ID
    """
    st.markdown("### 💡 AI 통계 업데이트 알림")
    
    sb = _get_sb()
    if not sb:
        st.error("Supabase 연결 실패")
        return
    
    # pending_updates 조회
    pending_updates = (
        sb.table("gk_pending_updates")
        .select("*")
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    
    if not pending_updates.data:
        st.info("승인 대기 중인 통계 업데이트가 없습니다.")
        return
    
    st.warning(f"⚠️ {len(pending_updates.data)}개의 통계 변동이 감지되었습니다.")
    
    # 변동 사항 표시
    for update in pending_updates.data:
        with st.expander(f"📊 {update['field_name']} - {update['change_type']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("현재 값", update["current_value"])
            
            with col2:
                st.metric("신규 값", update["new_value"], 
                         delta=f"{update['diff_percent']:.2f}%")
            
            with col3:
                st.metric("중요도", update["significance"])
            
            st.caption(f"출처: {update['source']} | 감지 시각: {update['created_at']}")
    
    # 일괄 승인 버튼
    if st.button("✅ 전체 승인 및 앱 전체 반영", type="primary"):
        update_ids = [u["id"] for u in pending_updates.data]
        result = apply_global_stats_patch(update_ids, agent_id)
        
        if result["success"]:
            st.success(f"✅ {result['updated_count']}개 항목이 업데이트되었습니다.")
            st.info(f"영향받은 테이블: {', '.join(result['affected_tables'])}")
            st.rerun()
        else:
            st.error(f"❌ 업데이트 실패: {result.get('error', 'Unknown error')}")
