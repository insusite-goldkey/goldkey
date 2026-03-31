"""
표 구조 직접 파싱 엔진 (Table Structure Parser)
Document AI 기반 표 좌표 추출 및 담보-금액 1:1 매칭

[GP-SCAN-TABLE] 우선순위 1 권고사항 구현
- Document AI table.layout.bounding_poly 좌표 활용
- 헤더 행에서 "담보명", "가입금액" 열 인덱스 자동 감지
- 각 바디 행을 순회하며 (담보명, 금액) 튜플 추출
"""

from typing import Dict, List, Tuple, Optional
import re
from google.cloud import documentai_v1 as documentai


class TableStructureParser:
    """표 구조 기하학적 파싱 엔진"""
    
    # 담보명 관련 헤더 키워드
    COVERAGE_HEADER_KEYWORDS = [
        "담보명", "특약명", "보장명", "보험담보", "담보", "특약", "보장내용"
    ]
    
    # 가입금액 관련 헤더 키워드
    AMOUNT_HEADER_KEYWORDS = [
        "가입금액", "보험가입금액", "보험금액", "보장금액", "금액", "한도"
    ]
    
    def __init__(self):
        """초기화"""
        pass
    
    def extract_tables_from_document(
        self, 
        document: documentai.Document
    ) -> List[Dict]:
        """
        Document AI 결과에서 표 추출
        
        Args:
            document: Document AI 파싱 결과
        
        Returns:
            표 리스트 (각 표는 헤더·바디 행 포함)
        """
        tables = []
        
        for page in document.pages:
            for table in page.tables:
                parsed_table = self._parse_table_structure(table, document)
                if parsed_table:
                    tables.append(parsed_table)
        
        return tables
    
    def _parse_table_structure(
        self, 
        table: documentai.Document.Page.Table,
        document: documentai.Document
    ) -> Optional[Dict]:
        """
        단일 표 구조 파싱
        
        Args:
            table: Document AI 표 객체
            document: 전체 문서 객체 (텍스트 추출용)
        
        Returns:
            {
                'headers': [['담보명', '가입금액', ...]],
                'rows': [['일반암진단비', '50000000', ...], ...]
            }
        """
        headers = []
        rows = []
        
        # 헤더 행 추출
        for header_row in table.header_rows:
            header_cells = []
            for cell in header_row.cells:
                cell_text = self._extract_cell_text(cell, document)
                header_cells.append(cell_text)
            headers.append(header_cells)
        
        # 바디 행 추출
        for body_row in table.body_rows:
            row_cells = []
            for cell in body_row.cells:
                cell_text = self._extract_cell_text(cell, document)
                row_cells.append(cell_text)
            rows.append(row_cells)
        
        if not headers or not rows:
            return None
        
        return {
            'headers': headers,
            'rows': rows
        }
    
    def _extract_cell_text(
        self, 
        cell: documentai.Document.Page.Table.TableCell,
        document: documentai.Document
    ) -> str:
        """
        셀에서 텍스트 추출
        
        Args:
            cell: 표 셀 객체
            document: 전체 문서 객체
        
        Returns:
            셀 텍스트
        """
        text_segments = []
        
        for segment in cell.layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else 0
            
            text_segments.append(document.text[start_index:end_index])
        
        return " ".join(text_segments).strip()
    
    def find_column_indices(
        self, 
        headers: List[List[str]]
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        헤더에서 담보명·가입금액 열 인덱스 자동 감지
        
        Args:
            headers: 헤더 행 리스트
        
        Returns:
            (담보명_열_인덱스, 가입금액_열_인덱스)
        """
        coverage_col_idx = None
        amount_col_idx = None
        
        # 첫 번째 헤더 행에서 검색
        if headers:
            header_row = headers[0]
            
            for idx, cell_text in enumerate(header_row):
                # 담보명 열 감지
                if coverage_col_idx is None:
                    for keyword in self.COVERAGE_HEADER_KEYWORDS:
                        if keyword in cell_text:
                            coverage_col_idx = idx
                            break
                
                # 가입금액 열 감지
                if amount_col_idx is None:
                    for keyword in self.AMOUNT_HEADER_KEYWORDS:
                        if keyword in cell_text:
                            amount_col_idx = idx
                            break
        
        return (coverage_col_idx, amount_col_idx)
    
    def parse_amount(self, amount_text: str) -> int:
        """
        금액 텍스트를 숫자로 변환
        
        Args:
            amount_text: 금액 텍스트 (예: "5천만원", "50,000,000원")
        
        Returns:
            금액 (정수)
        """
        if not amount_text:
            return 0
        
        # 쉼표 제거
        amount_text = amount_text.replace(",", "").replace(" ", "")
        
        # 한글 단위 처리
        amount_text = amount_text.replace("억", "00000000")
        amount_text = amount_text.replace("천만", "0000000")
        amount_text = amount_text.replace("백만", "000000")
        amount_text = amount_text.replace("만", "0000")
        amount_text = amount_text.replace("천", "000")
        amount_text = amount_text.replace("백", "00")
        
        # 원, 금액 등 문자 제거
        amount_text = re.sub(r"[^0-9]", "", amount_text)
        
        try:
            return int(amount_text)
        except ValueError:
            return 0
    
    def extract_coverage_amount_pairs(
        self, 
        table_data: Dict
    ) -> List[Tuple[str, int]]:
        """
        표에서 (담보명, 가입금액) 튜플 리스트 추출
        
        Args:
            table_data: parse_table_structure() 결과
        
        Returns:
            [(담보명, 가입금액), ...]
        """
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        # 열 인덱스 감지
        coverage_col_idx, amount_col_idx = self.find_column_indices(headers)
        
        if coverage_col_idx is None or amount_col_idx is None:
            # 열 감지 실패 시 휴리스틱 적용
            # 첫 번째 열 = 담보명, 두 번째 열 = 금액 (일반적 패턴)
            if len(headers) > 0 and len(headers[0]) >= 2:
                coverage_col_idx = 0
                amount_col_idx = 1
            else:
                return []
        
        # 각 행에서 담보명·금액 추출
        pairs = []
        
        for row in rows:
            if len(row) <= max(coverage_col_idx, amount_col_idx):
                continue
            
            coverage_name = row[coverage_col_idx].strip()
            amount_text = row[amount_col_idx].strip()
            
            # 빈 행 스킵
            if not coverage_name:
                continue
            
            # 금액 파싱
            amount = self.parse_amount(amount_text)
            
            pairs.append((coverage_name, amount))
        
        return pairs
    
    def parse_all_tables(
        self, 
        document: documentai.Document
    ) -> List[Dict]:
        """
        문서 내 모든 표에서 담보-금액 쌍 추출
        
        Args:
            document: Document AI 파싱 결과
        
        Returns:
            [
                {
                    'table_index': 0,
                    'coverage_amount_pairs': [('일반암진단비', 50000000), ...]
                },
                ...
            ]
        """
        tables = self.extract_tables_from_document(document)
        
        results = []
        
        for idx, table_data in enumerate(tables):
            pairs = self.extract_coverage_amount_pairs(table_data)
            
            if pairs:
                results.append({
                    'table_index': idx,
                    'coverage_amount_pairs': pairs
                })
        
        return results


# 사용 예시
if __name__ == "__main__":
    # Document AI 파싱 결과가 있다고 가정
    # parser = TableStructureParser()
    # results = parser.parse_all_tables(document)
    # 
    # for result in results:
    #     print(f"표 {result['table_index']}:")
    #     for coverage, amount in result['coverage_amount_pairs']:
    #         print(f"  - {coverage}: {amount:,}원")
    pass
