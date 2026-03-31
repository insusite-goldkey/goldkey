# -*- coding: utf-8 -*-
"""
기하학적 보정 AI 엔진 (Geometric Correction AI Engine)
문서 비틀림·왜곡·구김 자동 보정

작성일: 2026-03-31
목적: 스캔 문서 품질 향상 → OCR 인식률 극대화
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from PIL import Image
import io


class GeometricCorrectionEngine:
    """
    기하학적 보정 AI 엔진
    
    핵심 기능:
    1. De-skew (비틀림 보정)
    2. De-warp (왜곡 보정)
    3. Flattening (구김 제거)
    4. Perspective Transform (투영 변환)
    """
    
    def __init__(self):
        """초기화"""
        self.min_contour_area = 1000
        self.max_angle_deviation = 45
    
    def deskew_document(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        문서 비틀림 자동 보정 (De-skew)
        
        Args:
            image: 입력 이미지 (numpy array)
        
        Returns:
            (보정된 이미지, 회전 각도)
        """
        # 1. 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 2. 이진화 (Otsu's method)
        _, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        
        # 3. 회전 각도 계산 (Minima Bounding Box)
        coords = np.column_stack(np.where(binary > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # 4. 각도 보정 (0~90도 범위로 정규화)
        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90
        
        # 5. 회전 변환 행렬 생성
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 6. 이미지 회전
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated, angle
    
    def dewarp_document(self, image: np.ndarray) -> np.ndarray:
        """
        문서 왜곡 보정 (De-warp)
        
        렌즈 왜곡 및 원근 왜곡 제거
        
        Args:
            image: 입력 이미지
        
        Returns:
            보정된 이미지
        """
        # 1. 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 2. 가우시안 블러 (노이즈 제거)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Canny 엣지 검출
        edges = cv2.Canny(blurred, 50, 150)
        
        # 4. 윤곽선 검출
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 5. 가장 큰 사각형 윤곽선 찾기
        document_contour = None
        max_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area:
                # 윤곽선 근사화 (Douglas-Peucker)
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                
                # 사각형 검출 (4개 꼭짓점)
                if len(approx) == 4 and area > max_area:
                    document_contour = approx
                    max_area = area
        
        # 6. 문서 윤곽선이 없으면 원본 반환
        if document_contour is None:
            return image
        
        # 7. 투영 변환 (Perspective Transform)
        warped = self._apply_perspective_transform(image, document_contour)
        
        return warped
    
    def _apply_perspective_transform(
        self, 
        image: np.ndarray, 
        contour: np.ndarray
    ) -> np.ndarray:
        """
        투영 변환 적용
        
        Args:
            image: 입력 이미지
            contour: 문서 윤곽선 (4개 꼭짓점)
        
        Returns:
            변환된 이미지
        """
        # 1. 꼭짓점 정렬 (좌상, 우상, 우하, 좌하)
        pts = contour.reshape(4, 2)
        rect = self._order_points(pts)
        
        # 2. 목표 사각형 크기 계산
        (tl, tr, br, bl) = rect
        
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # 3. 목표 좌표 설정
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # 4. 투영 변환 행렬 계산
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # 5. 변환 적용
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        꼭짓점 정렬 (좌상, 우상, 우하, 좌하)
        
        Args:
            pts: 4개 꼭짓점 좌표
        
        Returns:
            정렬된 좌표
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # 1. 좌상: 합이 가장 작음
        # 2. 우하: 합이 가장 큼
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # 3. 우상: 차이가 가장 작음
        # 4. 좌하: 차이가 가장 큼
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def flatten_document(self, image: np.ndarray, preserve_color: bool = True) -> np.ndarray:
        """
        문서 구김 제거 (Flattening) + High-Fi Scanning
        
        종이 주름 및 굴곡 평면화 + 원본 색감 보존 (Low-Exposure)
        
        Args:
            image: 입력 이미지
            preserve_color: 원본 색감 보존 여부 (High-Fi Scanning)
        
        Returns:
            평면화된 이미지
        """
        # 1. 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 2. High-Fi Scanning: 원본 색감 보존 (Low-Exposure)
        if preserve_color and len(image.shape) == 3:
            # LAB 색공간으로 변환 (색감 보존)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # CLAHE 적용 (clipLimit 낮춤 → 빛 번짐 억제)
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            
            # 병합 후 BGR로 변환
            merged = cv2.merge([l_enhanced, a, b])
            result = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
            
            # 샤프닝 (글자 획 선명도 극대화)
            kernel_sharpen = np.array([
                [-1, -1, -1],
                [-1,  9, -1],
                [-1, -1, -1]
            ])
            result = cv2.filter2D(result, -1, kernel_sharpen)
            
        else:
            # 그레이스케일 처리
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 모폴로지 연산 (주름 제거)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            result = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
        
        return result
    
    def mesh_grid_dewarp(self, image: np.ndarray, grid_size: int = 20) -> np.ndarray:
        """
        Mesh-grid 기반 AI De-warping (두꺼운 증권 굴곡 보정)
        
        Args:
            image: 입력 이미지
            grid_size: 메쉬 그리드 크기
        
        Returns:
            보정된 이미지
        """
        h, w = image.shape[:2]
        
        # 1. 메쉬 그리드 생성
        rows = h // grid_size
        cols = w // grid_size
        
        # 2. 소스 포인트 (원본 그리드)
        src_points = []
        for i in range(rows + 1):
            for j in range(cols + 1):
                src_points.append([j * grid_size, i * grid_size])
        src_points = np.float32(src_points)
        
        # 3. 목적지 포인트 (평평한 그리드)
        dst_points = src_points.copy()
        
        # 4. 중앙 영역 굴곡 보정 (두꺼운 증권의 중앙 굴곡)
        center_row = rows // 2
        center_col = cols // 2
        
        for i in range(rows + 1):
            for j in range(cols + 1):
                idx = i * (cols + 1) + j
                
                # 중앙에서 멀어질수록 보정 강도 감소
                dist_from_center = np.sqrt(
                    (i - center_row) ** 2 + (j - center_col) ** 2
                )
                max_dist = np.sqrt(center_row ** 2 + center_col ** 2)
                
                if max_dist > 0:
                    correction_factor = 1 - (dist_from_center / max_dist)
                    
                    # 중앙 영역 Y축 보정 (위로 볼록한 굴곡 펴기)
                    if i > center_row * 0.3 and i < center_row * 1.7:
                        y_offset = -10 * correction_factor
                        dst_points[idx][1] += y_offset
        
        # 5. TPS (Thin Plate Spline) 변환 적용
        try:
            # OpenCV TPS 변환
            tps = cv2.createThinPlateSplineShapeTransformer()
            matches = [cv2.DMatch(i, i, 0) for i in range(len(src_points))]
            
            src_shape = src_points.reshape(1, -1, 2)
            dst_shape = dst_points.reshape(1, -1, 2)
            
            tps.estimateTransformation(dst_shape, src_shape, matches)
            result = tps.warpImage(image)
            
        except Exception:
            # TPS 실패 시 Perspective Transform 폴백
            result = self.dewarp_document(image)
        
        return result
    
    def auto_correct(self, image: np.ndarray, high_fi: bool = True) -> Tuple[np.ndarray, dict]:
        """
        자동 기하학적 보정 (All-in-One) + High-Fi Scanning
        
        De-skew → Mesh-grid De-warp → Flattening (Low-Exposure) 순차 적용
        
        Args:
            image: 입력 이미지
            high_fi: High-Fi Scanning 모드 (원본 색감 보존)
        
        Returns:
            (보정된 이미지, 보정 정보)
        """
        correction_info = {}
        
        # 1. De-skew (비틀림 보정)
        corrected, angle = self.deskew_document(image)
        correction_info["deskew_angle"] = angle
        
        # 2. Mesh-grid De-warp (AI 굴곡 보정)
        try:
            corrected = self.mesh_grid_dewarp(corrected)
            correction_info["mesh_dewarp_applied"] = True
        except Exception:
            corrected = self.dewarp_document(corrected)
            correction_info["dewarp_applied"] = True
        
        # 3. Flattening (구김 제거 + High-Fi Scanning)
        corrected = self.flatten_document(corrected, preserve_color=high_fi)
        correction_info["flatten_applied"] = True
        correction_info["high_fi_mode"] = high_fi
        
        return corrected, correction_info
    
    def process_pil_image(self, pil_image: Image.Image) -> Tuple[Image.Image, dict]:
        """
        PIL 이미지 처리 (Streamlit 호환)
        
        Args:
            pil_image: PIL Image 객체
        
        Returns:
            (보정된 PIL Image, 보정 정보)
        """
        # 1. PIL → numpy 변환
        image_array = np.array(pil_image)
        
        # 2. RGB → BGR 변환 (OpenCV 형식)
        if len(image_array.shape) == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        # 3. 기하학적 보정 적용
        corrected, info = self.auto_correct(image_bgr)
        
        # 4. BGR → RGB 변환
        if len(corrected.shape) == 3:
            corrected_rgb = cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)
        else:
            corrected_rgb = corrected
        
        # 5. numpy → PIL 변환
        corrected_pil = Image.fromarray(corrected_rgb)
        
        return corrected_pil, info


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_geometric_correction_demo():
    """
    기하학적 보정 데모 UI
    
    사용법:
        from modules.geometric_correction_engine import render_geometric_correction_demo
        render_geometric_correction_demo()
    """
    import streamlit as st
    
    st.markdown("### 🔧 기하학적 보정 AI 엔진")
    
    uploaded_file = st.file_uploader(
        "문서 이미지 업로드",
        type=["jpg", "jpeg", "png"],
        key="geo_correction_demo"
    )
    
    if uploaded_file:
        # 원본 이미지 로드
        original_image = Image.open(uploaded_file)
        
        # 기하학적 보정 적용
        engine = GeometricCorrectionEngine()
        corrected_image, info = engine.process_pil_image(original_image)
        
        # 결과 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**원본 이미지**")
            st.image(original_image, use_container_width=True)
        
        with col2:
            st.markdown("**보정된 이미지**")
            st.image(corrected_image, use_container_width=True)
        
        # 보정 정보 표시
        st.markdown("**보정 정보**")
        st.json(info)
