"""
정적 데이터 전역 변수 로더
서버 부팅 시 JSON 파일들을 메모리에 적재하여 상시 대기 (Standby)
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional

# 정적 데이터 디렉토리 경로
STATIC_DATA_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "static"

# 전역 변수 (서버 부팅 시 즉시 메모리 적재)
COVERAGE_16_MAPPING: Optional[Dict] = None
KB_TRINITY_STANDARDS: Optional[Dict] = None

def load_static_data() -> bool:
    """
    서버 부팅 시 모든 정적 데이터를 메모리에 적재 (Standby)
    
    Returns:
        성공 여부
    """
    global COVERAGE_16_MAPPING, KB_TRINITY_STANDARDS
    
    try:
        # 16대 보장항목 매핑표
        mapping_path = STATIC_DATA_DIR / "coverage_16_categories_mapping.json"
        if mapping_path.exists():
            with open(mapping_path, "r", encoding="utf-8") as f:
                COVERAGE_16_MAPPING = json.load(f)
            print(f"✅ 16대 보장항목 매핑표 로드 완료: {len(COVERAGE_16_MAPPING['mappings'])}개 카테고리")
        else:
            print(f"⚠️ 16대 보장항목 매핑표 파일 없음: {mapping_path}")
        
        # KB/트리니티 기준
        standards_path = STATIC_DATA_DIR / "kb_trinity_standards.json"
        if standards_path.exists():
            with open(standards_path, "r", encoding="utf-8") as f:
                KB_TRINITY_STANDARDS = json.load(f)
            print(f"✅ KB/트리니티 기준 로드 완료: {len(KB_TRINITY_STANDARDS['kb_standards'])}개 항목")
        else:
            print(f"⚠️ KB/트리니티 기준 파일 없음: {standards_path}")
        
        if COVERAGE_16_MAPPING and KB_TRINITY_STANDARDS:
            print("✅ 정적 데이터 메모리 적재 완료 (Standby)")
            return True
        else:
            print("⚠️ 일부 정적 데이터 로드 실패")
            return False
    
    except FileNotFoundError as e:
        print(f"❌ 정적 데이터 파일 없음: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 정적 데이터 로드 오류: {e}")
        return False

def get_coverage_mapping() -> Optional[Dict]:
    """16대 보장항목 매핑표 반환"""
    return COVERAGE_16_MAPPING

def get_kb_trinity_standards() -> Optional[Dict]:
    """KB/트리니티 기준 반환"""
    return KB_TRINITY_STANDARDS

def reload_static_data() -> bool:
    """정적 데이터 재로드 (개발/디버깅용)"""
    return load_static_data()

# 모듈 임포트 시 자동 실행
if __name__ != "__main__":
    load_static_data()
