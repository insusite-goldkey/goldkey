# =============================================================================
# policy_ocr_engine.py — 보험증권 OCR 후처리 엔진
# 기능:
#   1. 이미지 전처리 (OpenCV) — 이진화·잡음제거·투영변환 보정
#   2. 보험 도메인 사전(Dictionary) 기반 OCR 오타 교정
#   3. 정규식 강제 보정 — 날짜·금액·담보명 패턴
#   4. 퍼지 매칭(Fuzzy Matching) — 유사도 기반 담보명 치환
#   5. 개인정보 마스킹 — 주민등록번호 뒷자리 즉시 처리
#   6. [GP-SCAN-TABLE] 표 구조 직접 파싱 — Document AI 좌표 기반 담보-금액 매칭
# =============================================================================

from __future__ import annotations
import re
import base64
import io
from typing import Optional, List, Tuple, Dict

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

# ── 표 구조 파싱 모듈 임포트 ────────────────────────────────────────────────
try:
    from modules.table_structure_parser import TableStructureParser
    TABLE_PARSER_AVAILABLE = True
except ImportError:
    TABLE_PARSER_AVAILABLE = False


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


# =============================================================================
# 7. [GP91] 의학 약어 번역 사전 — 진단서·의무기록 필기체 약어 표준화
# =============================================================================

MEDICAL_ABBREVIATION_DICT: dict[str, str] = {
    # ── 주訴·현병력 ───────────────────────────────────────────────────────────
    "C.C":    "Chief Complaint (주소증)",
    "CC":     "Chief Complaint (주소증)",
    "C/C":    "Chief Complaint (주소증)",
    "P.I":    "Present Illness (현병력)",
    "PI":     "Present Illness (현병력)",
    "P/I":    "Present Illness (현병력)",
    "P.H":    "Past History (과거력)",
    "PH":     "Past History (과거력)",
    "F.H":    "Family History (가족력)",
    "FH":     "Family History (가족력)",
    "S.H":    "Social History (사회력)",
    "SH":     "Social History (사회력)",
    # ── 진단·처치 ─────────────────────────────────────────────────────────────
    "Imp":    "Impression (임상적 추정 진단)",
    "Dx":     "Diagnosis (진단)",
    "DDx":    "Differential Diagnosis (감별 진단)",
    "Tx":     "Treatment (치료)",
    "Rx":     "Prescription (처방)",
    "Hx":     "History (병력)",
    "Op":     "Operation (수술)",
    "Sx":     "Symptoms (증상)",
    "Bx":     "Biopsy (조직검사)",
    "Fx":     "Fracture (골절)",
    "SOB":    "Shortness of Breath (호흡곤란)",
    "LOC":    "Loss of Consciousness (의식소실)",
    "GCS":    "Glasgow Coma Scale (의식수준 점수)",
    # ── 활력징후 ─────────────────────────────────────────────────────────────
    "V/S":    "Vital Signs (활력징후)",
    "VS":     "Vital Signs (활력징후)",
    "BP":     "Blood Pressure (혈압)",
    "HR":     "Heart Rate (맥박수)",
    "BT":     "Body Temperature (체온)",
    "RR":     "Respiratory Rate (호흡수)",
    "SpO2":   "Oxygen Saturation (산소포화도)",
    # ── 검사·영상 ─────────────────────────────────────────────────────────────
    "EKG":    "Electrocardiogram (심전도)",
    "ECG":    "Electrocardiogram (심전도)",
    "EEG":    "Electroencephalogram (뇌파)",
    "EMG":    "Electromyography (근전도)",
    "MRI":    "Magnetic Resonance Imaging (자기공명영상)",
    "CT":     "Computed Tomography (전산화단층촬영)",
    "PET":    "Positron Emission Tomography (양전자방출단층촬영)",
    "U/S":    "Ultrasound (초음파)",
    "US":     "Ultrasound (초음파)",
    "CXR":    "Chest X-Ray (흉부X선)",
    "CBC":    "Complete Blood Count (전혈구검사)",
    "LFT":    "Liver Function Test (간기능검사)",
    "RFT":    "Renal Function Test (신기능검사)",
    "ABG":    "Arterial Blood Gas Analysis (동맥혈가스분석)",
    # ── 심장·혈관 ─────────────────────────────────────────────────────────────
    "AMI":    "Acute Myocardial Infarction (급성심근경색)",
    "MI":     "Myocardial Infarction (심근경색)",
    "CHF":    "Congestive Heart Failure (울혈성심부전)",
    "CAD":    "Coronary Artery Disease (관상동맥질환)",
    "PCI":    "Percutaneous Coronary Intervention (경피적관상동맥중재술)",
    "CABG":   "Coronary Artery Bypass Graft (관상동맥우회술)",
    "AF":     "Atrial Fibrillation (심방세동)",
    "DVT":    "Deep Vein Thrombosis (심부정맥혈전증)",
    "PE":     "Pulmonary Embolism (폐색전증)",
    # ── 뇌·신경 ──────────────────────────────────────────────────────────────
    "CVA":    "Cerebrovascular Accident (뇌졸중)",
    "TIA":    "Transient Ischemic Attack (일과성뇌허혈발작)",
    "ICH":    "Intracerebral Hemorrhage (뇌내출혈)",
    "SAH":    "Subarachnoid Hemorrhage (지주막하출혈)",
    "TBI":    "Traumatic Brain Injury (외상성뇌손상)",
    "ICP":    "Intracranial Pressure (두개내압)",
    # ── 암·종양 ──────────────────────────────────────────────────────────────
    "Ca":     "Cancer (암)",
    "CA":     "Cancer (암)",
    "Mets":   "Metastasis (전이)",
    "TNM":    "Tumor Node Metastasis 병기 분류",
    "chemo":  "Chemotherapy (항암화학요법)",
    "RT":     "Radiation Therapy (방사선치료)",
    # ── 정형외과·장해 ────────────────────────────────────────────────────────
    "ROM":    "Range of Motion (관절가동범위)",
    "ORIF":   "Open Reduction Internal Fixation (관혈적정복내고정술)",
    "THA":    "Total Hip Arthroplasty (인공고관절전치환술)",
    "TKA":    "Total Knee Arthroplasty (인공슬관절전치환술)",
    "HIVD":   "Herniated Intervertebral Disc (추간판탈출증)",
    "HNP":    "Herniated Nucleus Pulposus (수핵탈출증)",
    "CTS":    "Carpal Tunnel Syndrome (수근관증후군)",
    "AVN":    "Avascular Necrosis (무혈성괴사)",
    # ── 입원·처치 ─────────────────────────────────────────────────────────────
    "ICU":    "Intensive Care Unit (중환자실)",
    "ER":     "Emergency Room (응급실)",
    "OPD":    "Outpatient Department (외래)",
    "Ward":   "입원병동",
    "D/C":    "Discharge (퇴원)",
    "DC":     "Discharge (퇴원)",
    "NPO":    "Nil Per Os — 금식",
    "IV":     "Intravenous (정맥내)",
    "IM":     "Intramuscular (근육내)",
    "SC":     "Subcutaneous (피하)",
    "prn":    "Pro Re Nata — 필요시",
    "qd":     "Quaque Die — 1일 1회",
    "bid":    "Bis In Die — 1일 2회",
    "tid":    "Ter In Die — 1일 3회",
    "qid":    "Quater In Die — 1일 4회",
    # ── 결과·판정 ─────────────────────────────────────────────────────────────
    "N/A":    "Not Applicable (해당없음)",
    "NOS":    "Not Otherwise Specified (달리 명시되지 않음)",
    "NEC":    "Not Elsewhere Classified (달리 분류되지 않음)",
    "WNL":    "Within Normal Limits (정상 범위)",
    "STAT":   "즉시 처치",
    "f/u":    "Follow-Up (추적관찰)",
    "F/U":    "Follow-Up (추적관찰)",
    "s/p":    "Status Post (수술/처치 후 상태)",
    "S/P":    "Status Post (수술/처치 후 상태)",
    "r/o":    "Rule Out (감별 중)",
    "R/O":    "Rule Out (감별 중)",
}


def translate_medical_abbreviations(text: str) -> str:
    """
    의무기록·진단서 텍스트 내 의학 약어를 표준 한국어 용어로 병기.
    원본 약어는 괄호 안에 보존: "C.C → C.C [Chief Complaint (주소증)]"
    """
    if not text:
        return text
    for abbr, full in MEDICAL_ABBREVIATION_DICT.items():
        pattern = re.compile(
            r'(?<![A-Za-z0-9])' + re.escape(abbr) + r'(?![A-Za-z0-9])'
        )
        replacement = f"{abbr} [{full}]"
        text = pattern.sub(replacement, text)
    return text


def extract_medical_key_fields(text: str) -> dict:
    """
    의무기록·진단서 텍스트에서 보험청구 핵심 필드를 정규식으로 추출.
    반환:
      diagnosis_date  : 진단 확정일 (YYYY-MM-DD)
      admission_date  : 입원일
      discharge_date  : 퇴원일
      stay_days       : 입원일수 (정수, 미추출 시 None)
      kcd_codes       : KCD 코드 목록 ['C18', 'I63.9', ...]
      doctor_name     : 의사 성명
      hospital_name   : 병원명
    """
    result: dict = {
        "diagnosis_date":  None,
        "admission_date":  None,
        "discharge_date":  None,
        "stay_days":       None,
        "kcd_codes":       [],
        "doctor_name":     None,
        "hospital_name":   None,
    }

    # KCD 코드: 알파벳 1~2자 + 숫자 2자리 + 선택적 소수점·숫자
    kcd_pattern = re.compile(r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b')
    result["kcd_codes"] = list(dict.fromkeys(kcd_pattern.findall(text)))

    # 날짜: YYYY-MM-DD / YYYY.MM.DD / YYYY년MM월DD일
    date_pat = re.compile(
        r'(\d{4})[-./년](\d{1,2})[-./월](\d{1,2})[일]?'
    )
    dates_found = date_pat.findall(text)
    iso_dates = [
        f"{y}-{int(m):02d}-{int(d):02d}" for y, m, d in dates_found
    ]

    # 진단일 키워드 매칭
    for kw in ["진단일", "진단확정일", "확진일", "진단 확정"]:
        idx = text.find(kw)
        if idx != -1:
            snippet = text[idx:idx+30]
            m = date_pat.search(snippet)
            if m:
                result["diagnosis_date"] = (
                    f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                )
            break

    # 입원일
    for kw in ["입원일", "입원 일자", "입원날짜", "입원: "]:
        idx = text.find(kw)
        if idx != -1:
            snippet = text[idx:idx+30]
            m = date_pat.search(snippet)
            if m:
                result["admission_date"] = (
                    f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                )
            break

    # 퇴원일
    for kw in ["퇴원일", "퇴원 일자", "퇴원날짜", "퇴원: "]:
        idx = text.find(kw)
        if idx != -1:
            snippet = text[idx:idx+30]
            m = date_pat.search(snippet)
            if m:
                result["discharge_date"] = (
                    f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                )
            break

    # 입원일수 직접 표기: "X일", "X days"
    stay_m = re.search(r'입원(?:일수|기간)[^\d]{0,5}(\d+)\s*일', text)
    if stay_m:
        result["stay_days"] = int(stay_m.group(1))
    elif result["admission_date"] and result["discharge_date"]:
        try:
            from datetime import date as _date
            _adm = _date.fromisoformat(result["admission_date"])
            _dis = _date.fromisoformat(result["discharge_date"])
            result["stay_days"] = max(0, (_dis - _adm).days)
        except Exception:
            pass

    # 의사명: "담당의사 홍길동" / "주치의: 홍길동"
    doc_m = re.search(r'(?:담당의사|주치의|작성의사)[^\w가-힣]{0,3}([가-힣]{2,4})', text)
    if doc_m:
        result["doctor_name"] = doc_m.group(1)

    # 병원명
    hosp_m = re.search(r'([가-힣]{2,10}(?:병원|의원|클리닉|센터|요양원))', text)
    if hosp_m:
        result["hospital_name"] = hosp_m.group(1)

    return result


# =============================================================================
# 8. [GP91] SW 환경 종합 감사 — 분석 엔진 기동 전 무결성 점검
# =============================================================================

def gp91_audit_environment() -> dict:
    """
    GP91 제2항: 분석 엔진 기동 전 SW 무결성 전수 점검.
    반환:
      status  : 'OK' | 'DEGRADED' | 'CRITICAL'
      checks  : 각 컴포넌트별 {name, ok, version, note}
      summary : 한 줄 요약 문자열
    """
    checks = []

    # 1. OpenCV
    try:
        import cv2
        checks.append({"name": "OpenCV (이미지 전처리)", "ok": True,
                        "version": cv2.__version__, "note": "이진화·잡음제거·투영변환 정상"})
    except ImportError:
        checks.append({"name": "OpenCV (이미지 전처리)", "ok": False,
                        "version": None, "note": "미설치 — 이미지 전처리 비활성화"})

    # 2. Pillow
    try:
        import PIL
        checks.append({"name": "Pillow (PIL)", "ok": True,
                        "version": PIL.__version__, "note": "이미지 포맷 변환 정상"})
    except ImportError:
        checks.append({"name": "Pillow (PIL)", "ok": False,
                        "version": None, "note": "미설치 — 이미지 로딩 불가"})

    # 3. RapidFuzz
    try:
        import rapidfuzz
        checks.append({"name": "RapidFuzz (퍼지매칭)", "ok": True,
                        "version": rapidfuzz.__version__, "note": "담보명 교정 정상"})
    except ImportError:
        checks.append({"name": "RapidFuzz (퍼지매칭)", "ok": False,
                        "version": None, "note": "미설치 — 퍼지매칭 비활성화"})

    # 4. pdfplumber
    try:
        import pdfplumber
        checks.append({"name": "pdfplumber (PDF 텍스트)", "ok": True,
                        "version": getattr(pdfplumber, "__version__", "설치됨"),
                        "note": "PDF 텍스트 추출 정상"})
    except ImportError:
        checks.append({"name": "pdfplumber (PDF 텍스트)", "ok": False,
                        "version": None, "note": "미설치 — PDF 분석 불가"})

    # 5. pymupdf (fitz)
    try:
        import fitz
        checks.append({"name": "PyMuPDF (스캔PDF→이미지)", "ok": True,
                        "version": fitz.version[0], "note": "스캔본 PDF 이미지 변환 정상"})
    except ImportError:
        checks.append({"name": "PyMuPDF (스캔PDF→이미지)", "ok": False,
                        "version": None, "note": "미설치 — 스캔 PDF 처리 불가"})

    # 6. google-genai (Vision LLM)
    try:
        import google.genai as _genai
        checks.append({"name": "Google Gemini Vision LLM", "ok": True,
                        "version": getattr(_genai, "__version__", "설치됨"),
                        "note": "의학 맥락 추론·KCD 추출 정상"})
    except ImportError:
        checks.append({"name": "Google Gemini Vision LLM", "ok": False,
                        "version": None, "note": "미설치 — AI 분석 불가 (CRITICAL)"})

    # 7. supabase (영구 DB)
    try:
        import supabase as _sb
        checks.append({"name": "Supabase (PostgreSQL 영구DB)", "ok": True,
                        "version": getattr(_sb, "__version__", "설치됨"),
                        "note": "회원·의무기록 영구 저장 정상 (GP100 연동)"})
    except ImportError:
        checks.append({"name": "Supabase (PostgreSQL 영구DB)", "ok": False,
                        "version": None, "note": "미설치 — 데이터 영구 저장 불가 (GP100 위반)"})

    # 8. cryptography (AES-256)
    try:
        import cryptography
        checks.append({"name": "cryptography (AES-256 암호화)", "ok": True,
                        "version": cryptography.__version__,
                        "note": "의무기록 전송·저장 암호화 정상"})
    except ImportError:
        checks.append({"name": "cryptography (AES-256 암호화)", "ok": False,
                        "version": None, "note": "미설치 — 보안 전송 불가"})

    # 9. 의학 약어 사전
    checks.append({"name": "의학 약어 사전 (GP91 내장)", "ok": True,
                    "version": f"{len(MEDICAL_ABBREVIATION_DICT)}개 항목",
                    "note": "C.C/P.I/KCD 등 표준 번역 정상"})

    # 10. KCD-8 레지스트리 (app.py 연동 여부는 런타임에서 확인)
    checks.append({"name": "보험 도메인 사전 (OCR 교정)", "ok": True,
                    "version": f"{len(INSURANCE_DOMAIN_DICT)}개 항목",
                    "note": "담보명 OCR 오타 자동 교정 정상"})

    failed = [c for c in checks if not c["ok"]]
    if not failed:
        status = "OK"
        summary = f"✅ 전체 {len(checks)}개 SW 컴포넌트 정상 — 의무기록 분석 파이프라인 100% 가동 준비"
    elif len(failed) <= 2:
        status = "DEGRADED"
        names = ", ".join(c["name"] for c in failed)
        summary = f"⚠️ DEGRADED — {names} 미설치. 핵심 기능 저하 가능"
    else:
        status = "CRITICAL"
        names = ", ".join(c["name"] for c in failed)
        summary = f"🚨 CRITICAL — {names} 등 {len(failed)}개 컴포넌트 장애. 즉각 설치 필요"

    return {"status": status, "checks": checks, "summary": summary}


def analyze_medical_record(text: str, kcd_registry: Optional[dict] = None) -> dict:
    """
    [GP91] 의무기록·진단서 텍스트 종합 분석 파이프라인.
    단계:
      1) 개인정보 마스킹
      2) 날짜·금액 정규화
      3) 의학 약어 번역 병기
      4) 핵심 필드 추출 (KCD코드, 진단일, 입원일수, 의사명, 병원명)
      5) KCD 레지스트리 대조 → 보험 카테고리 분류
    반환 dict:
      masked_text, translated_text, fields, kcd_mapped, expert_flag
    """
    masked   = mask_personal_info(text)
    normed   = normalize_date(normalize_amount(masked))
    translated = translate_medical_abbreviations(normed)
    fields   = extract_medical_key_fields(normed)

    kcd_mapped = []
    if kcd_registry and fields.get("kcd_codes"):
        for code in fields["kcd_codes"]:
            for disease_name, info in kcd_registry.items():
                if info.get("code", "").startswith(code[:3]):
                    kcd_mapped.append({
                        "kcd_code":  code,
                        "disease":   disease_name,
                        "category":  info.get("category", ""),
                        "sub":       info.get("sub", ""),
                    })
                    break
            else:
                kcd_mapped.append({
                    "kcd_code": code,
                    "disease":  "질병명 확인 필요",
                    "category": "분류 불명확",
                    "sub":      "",
                })

    expert_flag = (
        not fields["kcd_codes"]
        or any(m["category"] == "분류 불명확" for m in kcd_mapped)
    )

    return {
        "masked_text":   masked,
        "translated_text": translated,
        "fields":        fields,
        "kcd_mapped":    kcd_mapped,
        "expert_flag":   expert_flag,
    }


# =============================================================================
# [GP-PHASE3] 의무기록 이미지 → 구조화 데이터 추출 (Gemini Vision API)
# =============================================================================

def extract_medical_record_data(image_bytes: bytes) -> dict:
    """
    [GP-PHASE3] 의무기록 이미지에서 구조화된 데이터 추출.
    
    Args:
        image_bytes: 의무기록 이미지 바이트 (JPG/PNG/PDF)
    
    Returns:
        dict: {
            "hospital_name": str,
            "doctor_name": str,
            "visit_date": str (YYYY-MM-DD),
            "diagnosis_names": list[str],
            "diagnosis_codes": list[str],
            "prescriptions": dict,
            "lab_results": dict,
            "raw_text": str,
            "confidence": float (0.0 ~ 1.0),
        }
    """
    try:
        from shared_components import get_master_model
        import json
        
        # Gemini Vision API 클라이언트
        client, _ = get_master_model()
        
        # 이미지 파트 준비
        img_part = {"mime_type": "image/jpeg", "data": image_bytes}
        
        # [GP-IDENTITY] 의무기록 분석 프롬프트 - 인물 식별 강화 (의사/간호사 제외)
        prompt = """이 이미지는 의무기록(진단서, 처방전, 검사 결과지 등)입니다.
다음 정보를 JSON 형식으로 추출하세요:

**[중요] 인물 식별 규칙:**
- patient_name: 환자(피보험자, 진료 대상자)의 성명만 추출하세요
- 의사명, 간호사명, 병원 담당자명은 절대 patient_name에 포함하지 마세요
- doctor_name은 별도 필드로 추출하되, patient_name과 혼동하지 마세요

1. patient_name: 환자(피보험자) 성명 (진료 받은 사람, 의사가 아님)
2. hospital_name: 병원명 (예: 서울대학교병원, 삼성서울병원)
3. doctor_name: 담당 의사명 (환자와 구분, 별도 필드)
4. visit_date: 진료일 또는 발급일 (YYYY-MM-DD 형식)
5. diagnosis_names: 진단명 배열 (예: ["급성 상기도 감염", "고혈압"])
6. diagnosis_codes: ICD-10 코드 배열 (예: ["J06.9", "I10"])
7. prescriptions: 처방 내역 객체 {
     "medications": [{"name": "약물명", "dosage": "용량", "duration": "기간"}]
   }
8. lab_results: 검사 결과 객체 {
     "tests": [{"name": "검사명", "value": "수치", "unit": "단위", "normal_range": "정상범위"}]
   }
9. raw_text: OCR로 추출한 전체 텍스트
10. confidence: 추출 신뢰도 (0.0 ~ 1.0)

정보가 없는 필드는 빈 문자열("") 또는 빈 배열([])로 반환하세요.
JSON만 반환하고 설명 없이 출력하세요."""
        
        # Gemini API 호출
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, img_part],
        )
        
        response_text = response.text.strip()
        
        # JSON 파싱
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed_data = json.loads(json_match.group())
        else:
            parsed_data = {
                "hospital_name": "",
                "doctor_name": "",
                "visit_date": "",
                "diagnosis_names": [],
                "diagnosis_codes": [],
                "prescriptions": {},
                "lab_results": {},
                "raw_text": response_text,
                "confidence": 0.5,
            }
        
        # [GP-IDENTITY] 기본값 보장 - patient_name 필드 추가
        result = {
            "patient_name": parsed_data.get("patient_name", ""),
            "hospital_name": parsed_data.get("hospital_name", ""),
            "doctor_name": parsed_data.get("doctor_name", ""),
            "visit_date": parsed_data.get("visit_date", ""),
            "diagnosis_names": parsed_data.get("diagnosis_names", []),
            "diagnosis_codes": parsed_data.get("diagnosis_codes", []),
            "prescriptions": parsed_data.get("prescriptions", {}),
            "lab_results": parsed_data.get("lab_results", {}),
            "raw_text": parsed_data.get("raw_text", ""),
            "confidence": float(parsed_data.get("confidence", 0.0)),
        }
        
        # 의학 약어 번역 적용
        if result["raw_text"]:
            result["raw_text"] = translate_medical_abbreviations(result["raw_text"])
        
        return result
        
    except Exception as e:
        return {
            "patient_name": "",
            "hospital_name": "",
            "doctor_name": "",
            "visit_date": "",
            "diagnosis_names": [],
            "diagnosis_codes": [],
            "prescriptions": {},
            "lab_results": {},
            "raw_text": f"OCR 분석 오류: {str(e)}",
            "confidence": 0.0,
            "error": str(e),
        }


# =============================================================================
# [GP-SCAN-TABLE] 표 구조 직접 파싱 — Document AI 좌표 기반
# =============================================================================

def parse_policy_table_with_coordinates(document) -> List[Dict]:
    """
    Document AI 결과에서 표 구조를 기하학적으로 파싱하여 담보-금액 쌍 추출
    
    Args:
        document: Document AI 파싱 결과 (documentai.Document)
    
    Returns:
        [
            {
                'table_index': 0,
                'coverage_amount_pairs': [('일반암진단비', 50000000), ...]
            },
            ...
        ]
    """
    if not TABLE_PARSER_AVAILABLE:
        print("⚠️ TableStructureParser 모듈이 설치되지 않았습니다. 표 구조 파싱을 건너뜁니다.")
        return []
    
    try:
        parser = TableStructureParser()
        results = parser.parse_all_tables(document)
        
        print(f"✅ 표 구조 파싱 완료: {len(results)}개 표에서 담보-금액 쌍 추출")
        
        return results
    
    except Exception as e:
        print(f"❌ 표 구조 파싱 실패: {e}")
        return []


def merge_table_parsing_with_llm(
    table_results: List[Dict],
    llm_results: Dict
) -> Dict:
    """
    표 구조 파싱 결과와 LLM 추론 결과를 병합
    
    Args:
        table_results: parse_policy_table_with_coordinates() 결과
        llm_results: Gemini LLM이 추출한 증권 데이터
    
    Returns:
        병합된 증권 데이터 (표 파싱 우선, LLM 보완)
    """
    if not table_results:
        # 표 파싱 실패 시 LLM 결과만 반환
        return llm_results
    
    # 표 파싱 결과에서 담보 리스트 추출
    table_coverages = []
    
    for table_result in table_results:
        pairs = table_result.get('coverage_amount_pairs', [])
        
        for coverage_name, amount in pairs:
            table_coverages.append({
                'name': coverage_name,
                'amount': amount,
                'original_name': coverage_name,
                'source': 'table_parsing'  # 출처 표시
            })
    
    # LLM 결과와 병합
    llm_coverages = llm_results.get('coverages', [])
    
    # 표 파싱 결과를 우선하되, LLM에서만 발견된 담보는 추가
    merged_coverages = table_coverages.copy()
    
    for llm_coverage in llm_coverages:
        llm_name = llm_coverage.get('name', '')
        
        # 이미 표 파싱에 있는지 확인
        if not any(tc['name'] == llm_name for tc in table_coverages):
            llm_coverage['source'] = 'llm_inference'
            merged_coverages.append(llm_coverage)
    
    # 병합된 결과 반환
    merged_results = llm_results.copy()
    merged_results['coverages'] = merged_coverages
    merged_results['parsing_method'] = 'hybrid'  # 하이브리드 파싱 표시
    
    print(f"✅ 하이브리드 파싱 완료: 표 파싱 {len(table_coverages)}개 + LLM {len(llm_coverages) - len(table_coverages)}개 = 총 {len(merged_coverages)}개 담보")
    
    return merged_results
