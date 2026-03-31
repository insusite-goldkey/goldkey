# -*- coding: utf-8 -*-
"""
결정론적 테이블 파서 (Deterministic Table Parser)
Bounding Box 기반 담보명-금액 1:1 매칭

작성일: 2026-03-31
목적: LLM 추론 의존도 최소화, 좌표 기반 정확한 데이터 추출
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from PIL import Image
import pytesseract
import re


class DeterministicTableParser:
    """
    결정론적 테이블 파서
    
    핵심 기능:
    1. 테이블 구조 자동 감지 (Bounding Box)
    2. 셀 좌표 기반 텍스트 추출
    3. 담보명-금액 1:1 매칭
    4. 좌표 기반 검증 (LLM 불필요)
    """
    
    def __init__(self):
        """초기화"""
        self.min_cell_width = 50
        self.min_cell_height = 20
        self.table_confidence_threshold = 0.7
    
    def parse_insurance_table(self, image: np.ndarray) -> Dict:
        """
        보험증권 테이블 파싱 (Main Entry Point)
        
        Args:
            image: 입력 이미지 (numpy array)
        
        Returns:
            구조화된 테이블 데이터
        """
        # 1. 테이블 영역 감지
        table_regions = self._detect_table_regions(image)
        
        # 2. 각 테이블 영역 파싱
        parsed_tables = []
        for region in table_regions:
            table_data = self._parse_single_table(image, region)
            if table_data:
                parsed_tables.append(table_data)
        
        # 3. 담보명-금액 매칭
        coverage_items = self._extract_coverage_items(parsed_tables)
        
        return {
            "tables": parsed_tables,
            "coverage_items": coverage_items,
            "total_coverage_amount": sum(item["amount"] for item in coverage_items)
        }
    
    def _detect_table_regions(self, image: np.ndarray) -> List[Dict]:
        """
        테이블 영역 자동 감지
        
        Args:
            image: 입력 이미지
        
        Returns:
            테이블 영역 리스트 (Bounding Box)
        """
        # 1. 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 2. 이진화
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 3. 수평선 검출
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        
        # 4. 수직선 검출
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        
        # 5. 테이블 구조 결합
        table_mask = cv2.add(horizontal_lines, vertical_lines)
        
        # 6. 윤곽선 검출
        contours, _ = cv2.findContours(
            table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 7. 테이블 영역 필터링
        table_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 최소 크기 필터
            if w > 200 and h > 100:
                table_regions.append({
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "area": w * h
                })
        
        # 면적 기준 정렬 (큰 테이블 우선)
        table_regions.sort(key=lambda r: r["area"], reverse=True)
        
        return table_regions
    
    def _parse_single_table(self, image: np.ndarray, region: Dict) -> Optional[Dict]:
        """
        단일 테이블 파싱
        
        Args:
            image: 전체 이미지
            region: 테이블 영역 (Bounding Box)
        
        Returns:
            테이블 데이터
        """
        # 1. 테이블 영역 추출
        x, y, w, h = region["x"], region["y"], region["width"], region["height"]
        table_image = image[y:y+h, x:x+w]
        
        # 2. 셀 감지
        cells = self._detect_cells(table_image)
        
        if not cells:
            return None
        
        # 3. 각 셀의 텍스트 추출
        cell_data = []
        for cell in cells:
            text = self._extract_cell_text(table_image, cell)
            cell_data.append({
                "bbox": cell,
                "text": text,
                "row": cell["row"],
                "col": cell["col"]
            })
        
        # 4. 행/열 구조화
        structured_data = self._structure_table_data(cell_data)
        
        return {
            "region": region,
            "cells": cell_data,
            "structured": structured_data
        }
    
    def _detect_cells(self, table_image: np.ndarray) -> List[Dict]:
        """
        테이블 셀 감지
        
        Args:
            table_image: 테이블 영역 이미지
        
        Returns:
            셀 리스트 (Bounding Box + 행/열 정보)
        """
        # 1. 그레이스케일 변환
        if len(table_image.shape) == 3:
            gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = table_image.copy()
        
        # 2. 이진화
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 3. 윤곽선 검출
        contours, _ = cv2.findContours(
            binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 4. 셀 후보 필터링
        cells = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 최소 크기 필터
            if w > self.min_cell_width and h > self.min_cell_height:
                cells.append({
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "center_x": x + w // 2,
                    "center_y": y + h // 2
                })
        
        # 5. 행/열 정보 추가
        cells = self._assign_row_col(cells)
        
        return cells
    
    def _assign_row_col(self, cells: List[Dict]) -> List[Dict]:
        """
        셀에 행/열 번호 할당
        
        Args:
            cells: 셀 리스트
        
        Returns:
            행/열 정보가 추가된 셀 리스트
        """
        # Y 좌표 기준 정렬 (행)
        cells_sorted_y = sorted(cells, key=lambda c: c["center_y"])
        
        # 행 그룹핑 (Y 좌표 유사도 기반)
        rows = []
        current_row = []
        prev_y = -1000
        
        for cell in cells_sorted_y:
            if abs(cell["center_y"] - prev_y) < 30:  # 같은 행
                current_row.append(cell)
            else:  # 새로운 행
                if current_row:
                    rows.append(current_row)
                current_row = [cell]
            prev_y = cell["center_y"]
        
        if current_row:
            rows.append(current_row)
        
        # 각 행 내에서 X 좌표 기준 정렬 (열)
        for row_idx, row in enumerate(rows):
            row_sorted_x = sorted(row, key=lambda c: c["center_x"])
            for col_idx, cell in enumerate(row_sorted_x):
                cell["row"] = row_idx
                cell["col"] = col_idx
        
        return cells
    
    def _extract_cell_text(self, table_image: np.ndarray, cell: Dict) -> str:
        """
        셀 텍스트 추출 (OCR)
        
        Args:
            table_image: 테이블 이미지
            cell: 셀 정보
        
        Returns:
            추출된 텍스트
        """
        # 1. 셀 영역 추출
        x, y, w, h = cell["x"], cell["y"], cell["width"], cell["height"]
        cell_image = table_image[y:y+h, x:x+w]
        
        # 2. 전처리
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()
        
        # 3. OCR
        try:
            text = pytesseract.image_to_string(
                gray, lang='kor+eng', config='--psm 6'
            )
            return text.strip()
        except Exception:
            return ""
    
    def _structure_table_data(self, cell_data: List[Dict]) -> Dict:
        """
        셀 데이터를 행/열 구조로 변환
        
        Args:
            cell_data: 셀 데이터 리스트
        
        Returns:
            구조화된 테이블 데이터
        """
        # 행/열 기준 그룹핑
        max_row = max(cell["row"] for cell in cell_data) if cell_data else 0
        max_col = max(cell["col"] for cell in cell_data) if cell_data else 0
        
        # 2D 배열 생성
        table = [[None for _ in range(max_col + 1)] for _ in range(max_row + 1)]
        
        for cell in cell_data:
            row, col = cell["row"], cell["col"]
            table[row][col] = cell["text"]
        
        return {
            "rows": max_row + 1,
            "cols": max_col + 1,
            "data": table
        }
    
    def _extract_coverage_items(self, parsed_tables: List[Dict]) -> List[Dict]:
        """
        담보명-금액 추출
        
        Args:
            parsed_tables: 파싱된 테이블 리스트
        
        Returns:
            담보 항목 리스트
        """
        coverage_items = []
        
        for table in parsed_tables:
            structured = table.get("structured", {})
            data = structured.get("data", [])
            
            # 각 행 분석
            for row in data:
                if not row:
                    continue
                
                # 담보명 감지 (첫 번째 열 또는 두 번째 열)
                coverage_name = None
                amount = 0
                
                for cell_text in row:
                    if not cell_text:
                        continue
                    
                    # 담보명 패턴 매칭
                    if self._is_coverage_name(cell_text):
                        coverage_name = cell_text
                    
                    # 금액 추출
                    extracted_amount = self._extract_amount(cell_text)
                    if extracted_amount > 0:
                        amount = extracted_amount
                
                # 담보명과 금액이 모두 있으면 추가
                if coverage_name and amount > 0:
                    coverage_items.append({
                        "name": coverage_name,
                        "amount": amount,
                        "source": "deterministic_parser"
                    })
        
        return coverage_items
    
    def _is_coverage_name(self, text: str) -> bool:
        """담보명 여부 판단"""
        coverage_keywords = [
            "사망", "진단비", "수술", "입원", "실손", "배상", "장해",
            "골절", "화상", "치아", "치매", "간병", "암", "뇌졸중", "심근경색"
        ]
        
        return any(keyword in text for keyword in coverage_keywords)
    
    def _extract_amount(self, text: str) -> int:
        """텍스트에서 금액 추출"""
        # 억원 단위
        billion_match = re.search(r"(\d+(?:\.\d+)?)\s*억", text)
        if billion_match:
            return int(float(billion_match.group(1)) * 100_000_000)
        
        # 만원 단위
        ten_thousand_match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*만원", text)
        if ten_thousand_match:
            amount_str = ten_thousand_match.group(1).replace(',', '')
            return int(amount_str) * 10_000
        
        # 원 단위
        won_match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*원", text)
        if won_match:
            amount_str = won_match.group(1).replace(',', '')
            return int(amount_str)
        
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_deterministic_table_parser_demo():
    """
    결정론적 테이블 파서 데모 UI
    
    사용법:
        from modules.deterministic_table_parser import render_deterministic_table_parser_demo
        render_deterministic_table_parser_demo()
    """
    import streamlit as st
    
    st.markdown("### 📊 결정론적 테이블 파서")
    
    uploaded_file = st.file_uploader(
        "보험증권 이미지 업로드",
        type=["jpg", "jpeg", "png"],
        key="table_parser_demo"
    )
    
    if uploaded_file:
        # 이미지 로드
        image = Image.open(uploaded_file)
        image_array = np.array(image)
        
        # BGR 변환 (OpenCV 형식)
        if len(image_array.shape) == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        # 테이블 파싱
        parser = DeterministicTableParser()
        result = parser.parse_insurance_table(image_bgr)
        
        # 결과 표시
        st.markdown("### 📊 파싱 결과")
        
        # 원본 이미지
        st.image(image, caption="원본 이미지", use_container_width=True)
        
        # 담보 항목
        st.markdown("#### 담보 항목")
        coverage_items = result.get("coverage_items", [])
        
        if coverage_items:
            for item in coverage_items:
                st.markdown(
                    f"- **{item['name']}**: {item['amount']:,}원"
                )
            
            st.markdown(f"\n**총 보장액**: {result['total_coverage_amount']:,}원")
        else:
            st.warning("담보 항목을 찾을 수 없습니다")
        
        # JSON 데이터
        with st.expander("JSON 데이터", expanded=False):
            st.json(result)
