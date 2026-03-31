# -*- coding: utf-8 -*-
"""
Version Control Service (버전 관리 서비스)
구버전 카탈로그 데이터 격리 및 Hot-Swap 로직

작성일: 2026-03-31
목적: 과거 자료가 섞여서 오답이 나가는 것을 방지
원칙: 물리적 삭제 금지, is_active 플래그로 논리적 격리
"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass

# Supabase
try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase 라이브러리가 설치되어 있지 않습니다.")
    print("pip install supabase 를 실행하세요.")
    raise


@dataclass
class VersionInfo:
    """버전 정보"""
    company: str
    reference_date: str
    is_active: bool
    document_count: int
    chunk_count: int
    version_date: Optional[date] = None


@dataclass
class ArchiveResult:
    """아카이브 결과"""
    archived_count: int
    archived_documents: List[str]
    target_company: str
    target_reference_date: str
    timestamp: str


class VersionControlService:
    """
    버전 관리 서비스
    
    핵심 기능:
    1. 구버전 데이터 아카이브 (Hot-Swap)
    2. 활성 버전 조회
    3. 버전 통계 조회
    4. 버전 복원 (롤백)
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """
        Args:
            supabase_url: Supabase URL
            supabase_key: Supabase Service Key
        """
        # Supabase 클라이언트 초기화
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def archive_old_versions(
        self,
        company: str,
        reference_date: str
    ) -> ArchiveResult:
        """
        구버전 데이터 아카이브 (Hot-Swap)
        
        동일 보험사의 이전 버전 데이터를 is_active=False로 변경
        
        Args:
            company: 보험사명
            reference_date: 기준연월 (YYYY-MM)
        
        Returns:
            ArchiveResult: 아카이브 결과
        """
        print(f"\n{'='*70}")
        print(f"🔄 Hot-Swap 시작: {company} - {reference_date}")
        print(f"{'='*70}")
        
        try:
            # Supabase RPC 함수 호출
            result = self.supabase.rpc(
                "archive_old_versions",
                {
                    "target_company": company,
                    "target_reference_date": reference_date
                }
            ).execute()
            
            if result.data and len(result.data) > 0:
                archived_count = result.data[0].get("archived_count", 0)
                archived_documents = result.data[0].get("archived_documents", [])
            else:
                archived_count = 0
                archived_documents = []
            
            print(f"\n✅ 아카이브 완료:")
            print(f"   - 보험사: {company}")
            print(f"   - 기준연월: {reference_date}")
            print(f"   - 아카이브된 Chunk 수: {archived_count}개")
            
            if archived_documents:
                print(f"   - 아카이브된 문서:")
                for doc in archived_documents[:5]:
                    print(f"     • {doc}")
                if len(archived_documents) > 5:
                    print(f"     ... 외 {len(archived_documents) - 5}개")
            
            return ArchiveResult(
                archived_count=archived_count,
                archived_documents=archived_documents or [],
                target_company=company,
                target_reference_date=reference_date,
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            print(f"\n❌ 아카이브 실패: {e}")
            raise
    
    def get_active_versions(self) -> List[VersionInfo]:
        """
        활성 버전 목록 조회 (is_active=true)
        
        Returns:
            List[VersionInfo]: 활성 버전 목록
        """
        try:
            result = self.supabase.rpc("get_active_versions").execute()
            
            versions = []
            for row in result.data:
                versions.append(VersionInfo(
                    company=row.get("company"),
                    reference_date=row.get("reference_date"),
                    is_active=True,
                    document_count=row.get("document_count", 0),
                    chunk_count=row.get("chunk_count", 0),
                    version_date=row.get("version_date")
                ))
            
            return versions
        
        except Exception as e:
            print(f"❌ 활성 버전 조회 실패: {e}")
            return []
    
    def get_version_statistics(self) -> List[VersionInfo]:
        """
        버전별 통계 조회 (활성 + 아카이브)
        
        Returns:
            List[VersionInfo]: 버전 통계 목록
        """
        try:
            result = self.supabase.rpc("get_version_statistics").execute()
            
            versions = []
            for row in result.data:
                versions.append(VersionInfo(
                    company=row.get("company"),
                    reference_date=row.get("reference_date"),
                    is_active=row.get("is_active", False),
                    document_count=row.get("document_count", 0),
                    chunk_count=row.get("chunk_count", 0),
                    version_date=row.get("latest_version_date")
                ))
            
            return versions
        
        except Exception as e:
            print(f"❌ 버전 통계 조회 실패: {e}")
            return []
    
    def restore_version(
        self,
        company: str,
        reference_date: str
    ) -> int:
        """
        버전 복원 (롤백)
        
        특정 버전을 다시 활성화
        
        Args:
            company: 보험사명
            reference_date: 기준연월 (YYYY-MM)
        
        Returns:
            int: 복원된 Chunk 수
        """
        print(f"\n{'='*70}")
        print(f"🔄 버전 복원: {company} - {reference_date}")
        print(f"{'='*70}")
        
        try:
            # 해당 버전을 is_active=true로 변경
            result = self.supabase.table("gk_knowledge_base").update({
                "is_active": True,
                "archived_at": None
            }).eq("company", company).eq("reference_date", reference_date).execute()
            
            restored_count = len(result.data) if result.data else 0
            
            print(f"\n✅ 복원 완료:")
            print(f"   - 보험사: {company}")
            print(f"   - 기준연월: {reference_date}")
            print(f"   - 복원된 Chunk 수: {restored_count}개")
            
            return restored_count
        
        except Exception as e:
            print(f"\n❌ 버전 복원 실패: {e}")
            raise
    
    def deactivate_all_versions(self, company: str) -> int:
        """
        특정 보험사의 모든 버전 비활성화
        
        Args:
            company: 보험사명
        
        Returns:
            int: 비활성화된 Chunk 수
        """
        print(f"\n{'='*70}")
        print(f"⚠️ 전체 버전 비활성화: {company}")
        print(f"{'='*70}")
        
        try:
            result = self.supabase.table("gk_knowledge_base").update({
                "is_active": False,
                "archived_at": datetime.now().isoformat()
            }).eq("company", company).eq("is_active", True).execute()
            
            deactivated_count = len(result.data) if result.data else 0
            
            print(f"\n✅ 비활성화 완료:")
            print(f"   - 보험사: {company}")
            print(f"   - 비활성화된 Chunk 수: {deactivated_count}개")
            
            return deactivated_count
        
        except Exception as e:
            print(f"\n❌ 비활성화 실패: {e}")
            raise
    
    def get_version_by_company(self, company: str) -> List[VersionInfo]:
        """
        특정 보험사의 모든 버전 조회
        
        Args:
            company: 보험사명
        
        Returns:
            List[VersionInfo]: 버전 목록
        """
        all_versions = self.get_version_statistics()
        return [v for v in all_versions if v.company == company]
    
    def print_version_summary(self):
        """버전 요약 정보 출력"""
        print("\n" + "="*70)
        print("📊 RAG Knowledge Base 버전 요약")
        print("="*70)
        
        # 활성 버전
        active_versions = self.get_active_versions()
        print(f"\n✅ 활성 버전 ({len(active_versions)}개):")
        for version in active_versions:
            print(f"   • {version.company} - {version.reference_date}")
            print(f"     문서: {version.document_count}개, Chunk: {version.chunk_count}개")
        
        # 전체 통계
        all_versions = self.get_version_statistics()
        archived_count = sum(1 for v in all_versions if not v.is_active)
        
        print(f"\n📦 아카이브 버전: {archived_count}개")
        
        # 보험사별 요약
        companies = set(v.company for v in all_versions)
        print(f"\n🏢 보험사별 요약:")
        for company in sorted(companies):
            company_versions = [v for v in all_versions if v.company == company]
            active = [v for v in company_versions if v.is_active]
            archived = [v for v in company_versions if not v.is_active]
            print(f"   • {company}: 활성 {len(active)}개, 아카이브 {len(archived)}개")


def main():
    """
    테스트 및 예제 실행
    """
    print("=" * 70)
    print("🔄 Version Control Service (버전 관리 서비스)")
    print("=" * 70)
    
    try:
        # Version Control Service 초기화
        service = VersionControlService()
        
        # 버전 요약 출력
        service.print_version_summary()
        
        print("\n" + "=" * 70)
        print("💡 사용 예시")
        print("=" * 70)
        
        print("""
# 1. 구버전 아카이브 (Hot-Swap)
result = service.archive_old_versions(
    company="삼성생명",
    reference_date="2026-03"
)
print(f"아카이브: {result.archived_count}개")

# 2. 활성 버전 조회
active_versions = service.get_active_versions()
for version in active_versions:
    print(f"{version.company} - {version.reference_date}")

# 3. 버전 복원 (롤백)
restored = service.restore_version(
    company="삼성생명",
    reference_date="2026-02"
)
print(f"복원: {restored}개")

# 4. 특정 보험사 버전 조회
versions = service.get_version_by_company("삼성생명")
for version in versions:
    status = "활성" if version.is_active else "아카이브"
    print(f"{version.reference_date}: {status}")
        """)
        
        print("\n" + "=" * 70)
        print("✅ Version Control Service 초기화 완료")
        print("=" * 70)
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
