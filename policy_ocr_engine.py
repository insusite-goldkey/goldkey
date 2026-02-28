# =============================================================================
# policy_ocr_engine.py — 보험증권 OCR 후처리 엔진
# 기능:
#   1. 이미지 전처리 (OpenCV) — 이진화·잡음제거·투영변환 보정
#   2. 보험 도메인 사전(Dictionary) 기반 OCR 오타 교정
#   3. 정규식 강제 보정 — 날짜·금액·담보명 패턴
#   4. 퍼지 매칭(Fuzzy Matching) — 유사도 기반 담보명 치환
#   5. 개인정보 마스킹 — 주민등록번호 뒷자리 즉시 처리
# =============================================================================

from __future__ import annotations
import re
import base64
import io
from typing import Optional

# ── 선택적 임포트 (미설치 시 해당 기능만 graceful 비활성화) ──────────────────
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from rapidfuzz import fuzz, process as rfprocess
    FUZZY_AVAILABLE = True
except ImportError:
    try:
        from fuzzywuzzy import fuzz, process as rfprocess
        FUZZY_AVAILABLE = True
    except ImportError:
        FUZZY_AVAILABLE = False


# =============================================================================
# 1. 보험 도메인 사전 — OCR 오타 → 정규 담보명 매핑
# =============================================================================

INSURANCE_DOMAIN_DICT: dict[str, str] = {
    # ── 암 ──────────────────────────────────────────────────────────────────
    "일반앎진단비":     "일반암진단비",
    "일반암진닫비":     "일반암진단비",
    "암진달비":         "암진단비",
    "소액앎진단비":     "소액암진단비",
    "유사앎진단비":     "유사암진단비",
    "고액앎진단비":     "고액암진단비",
    "항앙치료비":       "항암치료비",
    "항알치료비":       "항암치료비",
    "표적항앙":         "표적항암",
    # ── 뇌·심장 ─────────────────────────────────────────────────────────────
    "뇌출형진단비":     "뇌출혈진단비",
    "뇌좈중진단비":     "뇌졸중진단비",
    "뇌졸종진단비":     "뇌졸중진단비",
    "뇌경색증진달비":   "뇌경색증진단비",
    "심금경색진단비":   "심근경색진단비",
    "심근경색증진달비": "심근경색증진단비",
    "허혈성심장질홤":   "허혈성심장질환",
    "심장질홤진단비":   "심장질환진단비",
    # ── 실손의료비 ───────────────────────────────────────────────────────────
    "실손의표비":       "실손의료비",
    "실손의로비":       "실손의료비",
    "실손의료비특약":   "실손의료비",
    "급여실손의료비":   "급여실손의료비",
    "비급여실손의로비": "비급여실손의료비",
    "도수치료특약":     "비급여도수치료",
    "비급여도수치뇨":   "비급여도수치료",
    # ── 장해/후유장해 ────────────────────────────────────────────────────────
    "상해후유쟝해":     "상해후유장해",
    "후유쟝해":         "후유장해",
    "후유장혜":         "후유장해",
    "재해후유쟝해":     "재해후유장해",
    # ── 진단·수술·입원 ───────────────────────────────────────────────────────
    "질병입원일닺":     "질병입원일당",
    "상해입원일닺":     "상해입원일당",
    "입원일닺":         "입원일당",
    "질병수솔비":       "질병수술비",
    "상해수솔비":       "상해수술비",
    "수솔비":           "수술비",
    # ── 치매·간병 ────────────────────────────────────────────────────────────
    "경증치멩진단비":   "경증치매진단비",
    "중증치멩진단비":   "중증치매진단비",
    "치매진달비":       "치매진단비",
    "간병일닺":         "간병일당",
    "간호간병입원일닺": "간호간병입원일당",
    # ── 운전자보험 ───────────────────────────────────────────────────────────
    "교통상해사망":     "교통상해사망보험금",
    "자동차사고변호사비용": "자동차사고변호사비용",
    "면허정지위로금":   "운전면허정지위로금",
    # ── 기타 ────────────────────────────────────────────────────────────────
    "사맘보험금":       "사망보험금",
    "사망보험금":       "사망보험금",
    "사맛보험금":       "사망보험금",
}

# 퍼지 매칭용 정규 담보명 목록
STANDARD_COVERAGE_NAMES: list[str] = sorted(set(INSURANCE_DOMAIN_DICT.values())) + [
    "일반암진단비", "소액암진단비", "고액암진단비", "표적항암치료비",
    "뇌출혈진단비", "뇌졸중진단비", "급성심근경색증진단비", "허혈성심장질환진단비",
    "실손의료비", "비급여도수치료", "비급여MRI", "비급여주사",
    "상해후유장해", "재해후유장해", "질병후유장해",
    "질병입원일당", "상해입원일당", "질병수술비", "상해수술비",
    "경증치매진단비", "중증치매진단비", "간호간병입원일당",
    "사망보험금", "정기보험금",
    "운전면허정지위로금", "자동차사고변호사비용",
]


# =============================================================================
# 2. 개인정보 마스킹
# =============================================================================

# 주민등록번호: 6자리-7자리 패턴
_RRN_PATTERN = re.compile(r"(\d{6})-?(\d{7})")
# 주민등록번호 뒷자리 앞 1자리 보존, 나머지 6자리 마스킹
_RRN_MASK = r"\1-\g<2>"[:4] + "******"  # fallback — 아래 함수 사용


def mask_personal_info(text: str) -> str:
    """주민등록번호 뒷자리 마스킹 + 전화번호 중간자리 마스킹."""
    # 주민등록번호: XXXXXX-XXXXXXX → XXXXXX-X******
    text = _RRN_PATTERN.sub(
        lambda m: f"{m.group(1)}-{m.group(2)[0]}{'*' * 6}", text
    )
    # 전화번호: 010-XXXX-XXXX → 010-****-XXXX
    text = re.sub(
        r"(01[016789])-?(\d{3,4})-?(\d{4})",
        lambda m: f"{m.group(1)}-{'*' * len(m.group(2))}-{m.group(3)}",
        text,
    )
    return text


# =============================================================================
# 3. 정규식 강제 보정 — 날짜·금액
# =============================================================================

def normalize_date(text: str) -> str:
    """
    다양한 날짜 표기를 YYYY-MM-DD 로 통일.
    예: 2025.03.15 → 2025-03-15 / 25년3월15일 → 2025-03-15
    """
    # YYYY.MM.DD → YYYY-MM-DD
    text = re.sub(r"(\d{4})\.(\d{1,2})\.(\d{1,2})",
                  lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", text)
    # YY년 MM월 DD일 → 20YY-MM-DD
    text = re.sub(r"(\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일",
                  lambda m: f"20{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", text)
    # YYYY년 MM월 DD일 → YYYY-MM-DD
    text = re.sub(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
                  lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", text)
    return text


def normalize_amount(text: str) -> str:
    """
    금액 표기 통일: '1억5천만원' → '150,000,000원' 형식 유지,
    숫자+억/천/만 혼합 → 숫자 변환 후 원래 단위 문자열 복원.
    주로 담보 금액 파싱 전 정제용.
    """
    # 콤마·공백 포함 숫자 정리 (예: 1, 000만원 → 1000만원)
    text = re.sub(r"(\d),\s*(\d{3})", r"\1\2", text)
    # '만 원' → '만원'
    text = re.sub(r"만\s+원", "만원", text)
    # '원 정' → '원'
    text = re.sub(r"원\s*정", "원", text)
    return text


# =============================================================================
# 4. 퍼지 담보명 교정
# =============================================================================

_FUZZY_THRESHOLD = 82  # 유사도 82% 이상일 때만 치환


def correct_coverage_name(name: str, threshold: int = _FUZZY_THRESHOLD) -> str:
    """
    OCR 오인식 담보명을 보험 도메인 사전 → 퍼지 매칭 순으로 교정.
    원본이 표준명보다 확실히 나쁠 때만 치환.
    """
    if not name:
        return name

    name_stripped = name.replace(" ", "")

    # 1차: 완전 일치 사전 교정
    if name_stripped in INSURANCE_DOMAIN_DICT:
        return INSURANCE_DOMAIN_DICT[name_stripped]

    # 2차: 부분 포함 교정 (짧은 오타 키가 담보명 내부에 있는 경우)
    for typo, correct in INSURANCE_DOMAIN_DICT.items():
        if typo in name_stripped:
            return name.replace(typo, correct)

    # 3차: 퍼지 매칭 (rapidfuzz 또는 fuzzywuzzy)
    if FUZZY_AVAILABLE:
        result = rfprocess.extractOne(
            name_stripped,
            STANDARD_COVERAGE_NAMES,
            scorer=fuzz.ratio,
        )
        if result and result[1] >= threshold:
            return result[0]

    return name  # 교정 불가 시 원본 반환


def postprocess_coverages(coverages: list[dict]) -> list[dict]:
    """
    AI가 반환한 담보 목록에 퍼지 교정 + 금액 정규화 적용.
    원본 name은 'raw_name'으로 보존.
    """
    for c in coverages:
        raw = c.get("name", "")
        corrected = correct_coverage_name(raw)
        if corrected != raw:
            c["raw_name"] = raw
            c["name"] = corrected
        # standard_name도 함께 교정
        std = c.get("standard_name", "")
        if std:
            c["standard_name"] = correct_coverage_name(std)
    return coverages


# =============================================================================
# 5. OpenCV 이미지 전처리
# =============================================================================

def preprocess_image_bytes(img_bytes: bytes) -> bytes:
    """
    이미지 바이트를 받아 OpenCV 전처리 후 PNG 바이트 반환.
    처리 순서:
      ① 그레이스케일 변환
      ② CLAHE 대비 향상 (히스토그램 평활화)
      ③ 가우시안 블러 잡음 제거
      ④ 적응형 이진화 (Otsu 또는 Adaptive Gaussian)
      ⑤ 투영 변환 (Perspective Correction) — 기울어진 증권 자동 보정
    CV2 미설치 시 원본 그대로 반환 (graceful fallback).
    """
    if not CV2_AVAILABLE or not PIL_AVAILABLE:
        return img_bytes

    try:
        # bytes → numpy array
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return img_bytes

        # ① 그레이스케일
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ② CLAHE 대비 향상
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # ③ 가우시안 블러 (잡음 제거)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # ④ 적응형 이진화
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 15, 8
        )

        # ⑤ 투영 변환 (기울어진 문서 자동 보정)
        binary = _perspective_correction(binary)

        # numpy → PNG bytes
        success, enc = cv2.imencode(".png", binary)
        if success:
            return enc.tobytes()
        return img_bytes

    except Exception:
        return img_bytes  # 전처리 실패 시 원본 반환


def _perspective_correction(binary_img) -> "np.ndarray":
    """
    이진화된 이미지에서 문서 경계(최대 윤곽선)를 찾아
    투영 변환으로 수평 보정. 윤곽선 미검출 시 원본 반환.
    """
    if not CV2_AVAILABLE:
        return binary_img
    try:
        # 윤곽선 검출
        contours, _ = cv2.findContours(
            binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return binary_img

        # 가장 큰 윤곽선 선택
        largest = max(contours, key=cv2.contourArea)
        img_area = binary_img.shape[0] * binary_img.shape[1]

        # 문서가 이미지 면적의 30% 이상인 경우에만 보정 적용
        if cv2.contourArea(largest) < img_area * 0.30:
            return binary_img

        # 근사 다각형 (4꼭짓점 사각형 근사)
        peri = cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, 0.02 * peri, True)

        if len(approx) != 4:
            return binary_img

        pts = approx.reshape(4, 2).astype("float32")
        pts = _order_points(pts)

        (tl, tr, br, bl) = pts
        w = int(max(
            np.linalg.norm(br - bl),
            np.linalg.norm(tr - tl)
        ))
        h = int(max(
            np.linalg.norm(tr - br),
            np.linalg.norm(tl - bl)
        ))

        dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]],
                       dtype="float32")
        M = cv2.getPerspectiveTransform(pts, dst)
        warped = cv2.warpPerspective(binary_img, M, (w, h))
        return warped

    except Exception:
        return binary_img


def _order_points(pts: "np.ndarray") -> "np.ndarray":
    """좌상·우상·우하·좌하 순으로 꼭짓점 정렬."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # 좌상
    rect[2] = pts[np.argmax(s)]   # 우하
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # 우상
    rect[3] = pts[np.argmax(diff)]  # 좌하
    return rect


# =============================================================================
# 6. 통합 전처리 파이프라인 — parse_policy_with_vision에서 호출
# =============================================================================

def prepare_image_for_vision(img_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """
    이미지 바이트를 Vision AI 전송 전 전처리.
    반환: (전처리된 바이트, 출력 mime_type)
    이미지가 아닌 경우(PDF 등) 원본 그대로 반환.
    """
    if not mime_type.startswith("image/"):
        return img_bytes, mime_type
    processed = preprocess_image_bytes(img_bytes)
    return processed, "image/png"


def postprocess_ocr_text(text: str) -> str:
    """
    OCR 원문 텍스트에 전처리 파이프라인 적용.
      ① 개인정보 마스킹
      ② 날짜 정규화
      ③ 금액 정규화
    """
    text = mask_personal_info(text)
    text = normalize_date(text)
    text = normalize_amount(text)
    return text


def get_engine_status() -> dict:
    """
    현재 엔진 가용 상태를 반환 (진단용).
    """
    return {
        "opencv":   CV2_AVAILABLE,
        "pil":      PIL_AVAILABLE,
        "fuzzy":    FUZZY_AVAILABLE,
        "dict_entries": len(INSURANCE_DOMAIN_DICT),
        "std_names":    len(STANDARD_COVERAGE_NAMES),
    }
