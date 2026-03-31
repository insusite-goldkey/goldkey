# -*- coding: utf-8 -*-
"""
RAG Knowledge Base 폴더 구조 관리 유틸리티
연도/월별 계층적 폴더 구조 자동 생성 및 관리

작성일: 2026-03-31
목적: source_docs 하위에 YYYY/MM/ 구조로 문서를 체계적으로 관리
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
import shutil


class FolderManager:
    """
    RAG Knowledge Base 폴더 구조 관리자
    
    기본 구조:
    hq_backend/knowledge_base/source_docs/
        ├── 2026/
        │   ├── 01/
        │   ├── 02/
        │   ├── 03/
        │   └── ...
        ├── 2027/
        │   └── ...
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Args:
            base_path: source_docs 기본 경로 (기본값: 프로젝트 루트 기준)
        """
        if base_path is None:
            # 프로젝트 루트에서 상대 경로로 설정
            project_root = Path(__file__).parent.parent.parent
            self.base_path = project_root / "hq_backend" / "knowledge_base" / "source_docs"
        else:
            self.base_path = Path(base_path)
        
        # 기본 경로가 없으면 생성
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_insurance_leaflet_folder(
        self,
        company_name: str,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Path:
        """
        보험사 리플릿 폴더 생성
        
        구조: source_docs/보험사 리플릿_{YYYY}년_{MM}월_{보험사명}/
        
        Args:
            company_name: 보험사명 (예: 삼성생명, KB손해보험)
            year: 연도 (기본값: 현재 연도)
            month: 월 (기본값: 현재 월)
        
        Returns:
            Path: 생성된 폴더 경로
        """
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        # 폴더명 생성: 보험사 리플릿_2026년_03월_삼성생명
        folder_name = f"보험사 리플릿_{year}년_{month:02d}월_{company_name}"
        folder_path = self.base_path / folder_name
        
        # 폴더 생성
        folder_path.mkdir(parents=True, exist_ok=True)
        
        return folder_path
    
    def create_month_folder(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Path:
        """
        연도/월 폴더 생성
        
        Args:
            year: 연도 (기본값: 현재 연도)
            month: 월 (기본값: 현재 월)
        
        Returns:
            Path: 생성된 폴더 경로
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        # YYYY/MM 경로 생성
        folder_path = self.base_path / str(year) / f"{month:02d}"
        folder_path.mkdir(parents=True, exist_ok=True)
        
        return folder_path
    
    def get_current_month_folder(self) -> Path:
        """
        현재 연도/월 폴더 경로 반환 (없으면 생성)
        
        Returns:
            Path: 현재 월 폴더 경로
        """
        return self.create_month_folder()
    
    def get_month_folder(self, year: int, month: int) -> Path:
        """
        특정 연도/월 폴더 경로 반환
        
        Args:
            year: 연도
            month: 월
        
        Returns:
            Path: 폴더 경로
        """
        folder_path = self.base_path / str(year) / f"{month:02d}"
        return folder_path
    
    def list_years(self) -> List[int]:
        """
        존재하는 연도 폴더 목록 반환
        
        Returns:
            List[int]: 연도 목록 (정렬됨)
        """
        years = []
        for item in self.base_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                years.append(int(item.name))
        return sorted(years)
    
    def list_months(self, year: int) -> List[int]:
        """
        특정 연도의 월 폴더 목록 반환
        
        Args:
            year: 연도
        
        Returns:
            List[int]: 월 목록 (정렬됨)
        """
        year_path = self.base_path / str(year)
        if not year_path.exists():
            return []
        
        months = []
        for item in year_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                months.append(int(item.name))
        return sorted(months)
    
    def list_all_folders(self) -> List[Tuple[int, int, Path]]:
        """
        모든 연도/월 폴더 목록 반환
        
        Returns:
            List[Tuple[int, int, Path]]: (연도, 월, 경로) 튜플 리스트
        """
        folders = []
        for year in self.list_years():
            for month in self.list_months(year):
                folder_path = self.get_month_folder(year, month)
                folders.append((year, month, folder_path))
        return folders
    
    def move_file_to_month_folder(
        self,
        file_path: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        create_folder: bool = True
    ) -> Path:
        """
        파일을 특정 연도/월 폴더로 이동
        
        Args:
            file_path: 이동할 파일 경로
            year: 대상 연도 (기본값: 현재 연도)
            month: 대상 월 (기본값: 현재 월)
            create_folder: 폴더가 없으면 생성 여부
        
        Returns:
            Path: 이동된 파일 경로
        """
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 대상 폴더 생성
        if create_folder:
            target_folder = self.create_month_folder(year, month)
        else:
            target_folder = self.get_month_folder(
                year or datetime.now().year,
                month or datetime.now().month
            )
            if not target_folder.exists():
                raise FileNotFoundError(f"대상 폴더가 없습니다: {target_folder}")
        
        # 파일 이동
        target_path = target_folder / source.name
        shutil.move(str(source), str(target_path))
        
        return target_path
    
    def copy_file_to_month_folder(
        self,
        file_path: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        create_folder: bool = True
    ) -> Path:
        """
        파일을 특정 연도/월 폴더로 복사
        
        Args:
            file_path: 복사할 파일 경로
            year: 대상 연도 (기본값: 현재 연도)
            month: 대상 월 (기본값: 현재 월)
            create_folder: 폴더가 없으면 생성 여부
        
        Returns:
            Path: 복사된 파일 경로
        """
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 대상 폴더 생성
        if create_folder:
            target_folder = self.create_month_folder(year, month)
        else:
            target_folder = self.get_month_folder(
                year or datetime.now().year,
                month or datetime.now().month
            )
            if not target_folder.exists():
                raise FileNotFoundError(f"대상 폴더가 없습니다: {target_folder}")
        
        # 파일 복사
        target_path = target_folder / source.name
        shutil.copy2(str(source), str(target_path))
        
        return target_path
    
    def get_folder_stats(self, year: int, month: int) -> dict:
        """
        특정 연도/월 폴더의 통계 정보 반환
        
        Args:
            year: 연도
            month: 월
        
        Returns:
            dict: 통계 정보 (파일 수, 총 크기 등)
        """
        folder_path = self.get_month_folder(year, month)
        if not folder_path.exists():
            return {
                "exists": False,
                "file_count": 0,
                "total_size": 0,
                "file_types": {}
            }
        
        file_count = 0
        total_size = 0
        file_types = {}
        
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
                
                # 파일 확장자별 카운트
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            "exists": True,
            "file_count": file_count,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types
        }
    
    def cleanup_empty_folders(self) -> List[Path]:
        """
        비어있는 연도/월 폴더 삭제
        
        Returns:
            List[Path]: 삭제된 폴더 경로 리스트
        """
        deleted_folders = []
        
        for year, month, folder_path in self.list_all_folders():
            # 폴더가 비어있는지 확인
            if folder_path.exists() and not any(folder_path.iterdir()):
                folder_path.rmdir()
                deleted_folders.append(folder_path)
        
        # 비어있는 연도 폴더도 삭제
        for year in self.list_years():
            year_path = self.base_path / str(year)
            if year_path.exists() and not any(year_path.iterdir()):
                year_path.rmdir()
                deleted_folders.append(year_path)
        
        return deleted_folders
    
    def get_base_path(self) -> Path:
        """
        기본 경로 반환
        
        Returns:
            Path: source_docs 기본 경로
        """
        return self.base_path
    
    def __repr__(self) -> str:
        return f"FolderManager(base_path='{self.base_path}')"


def main():
    """
    테스트 및 예제 실행
    """
    print("=" * 60)
    print("RAG Knowledge Base 폴더 구조 관리 유틸리티")
    print("=" * 60)
    
    # FolderManager 초기화
    manager = FolderManager()
    print(f"\n✅ 기본 경로: {manager.get_base_path()}")
    
    # 현재 월 폴더 생성
    current_folder = manager.get_current_month_folder()
    print(f"✅ 현재 월 폴더 생성: {current_folder}")
    
    # 특정 월 폴더 생성
    jan_2026 = manager.create_month_folder(2026, 1)
    print(f"✅ 2026년 1월 폴더 생성: {jan_2026}")
    
    feb_2026 = manager.create_month_folder(2026, 2)
    print(f"✅ 2026년 2월 폴더 생성: {feb_2026}")
    
    # 연도 목록 조회
    years = manager.list_years()
    print(f"\n📊 존재하는 연도: {years}")
    
    # 월 목록 조회
    if years:
        for year in years:
            months = manager.list_months(year)
            print(f"📊 {year}년 월 목록: {months}")
    
    # 모든 폴더 목록 조회
    all_folders = manager.list_all_folders()
    print(f"\n📂 전체 폴더 수: {len(all_folders)}")
    for year, month, path in all_folders:
        stats = manager.get_folder_stats(year, month)
        print(f"  - {year}년 {month:02d}월: {stats['file_count']}개 파일, {stats['total_size_mb']}MB")
    
    print("\n" + "=" * 60)
    print("✅ 폴더 구조 관리 유틸리티 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
