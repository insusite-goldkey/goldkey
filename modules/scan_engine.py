# modules/scan_engine.py
# ══════════════════════════════════════════════════════════════════════════════
# [통합 가이딩 프로토콜 제190조] 전역 무결성 스캔 인프라 및 자동 상속 표준
#
# GP190 §1  — 단일 지능형 파이프라인: 앱 내 모든 파일 업로드는 이 엔진을 통과
# GP190 §2  — Pre-process: 이미지 Deskew·대비 최적화 + PII 자동 마스킹
# GP190 §3  — Secure Storage: 공적 자산 ↔ 개인자료 GCS 물리 분리
# GP190 §4  — Precision Extraction: Core-8 정밀 추출 + 50P 분할 분석
# GP190 §5  — KCD Verification: 질병명/코드 KCD-10 실시간 대조 검증
# GP190 §6  — Master Approval: Human-in-the-loop 마스터 검수·승인 후 RAG 반영
# GP191 §1  — 공적 자산 분류 격리 (약관/설명서 ↔ 개인자료 물리 분리)
# GP191 §2  — 즉시 가공: 핵심 담보·보장한도·면책조항 추출
# GP191 §3  — RAG 실시간 반영 + 1인칭 상담 연동
# GP192      — Core-8 정밀 추출 (지급기준·판매주기·특장점·용어·세일즈멘트)
# GP193      — 전역 지식 동기화 후크 + 상담 팩트 시트
# GP194      — 무결성 가드레일 (보안·품질 강제)
# GP195      — 신규 모듈 자동 상속 표준 (Single Source of Truth)
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import io
import os
import re
import uuid
import json
import logging
import datetime
from typing import Optional, Callable

logger = logging.getLogger("scan_engine")

# ── 공적 자산 문서 유형 목록 (GP191 §1 — 개인자료 제외) ──────────────────────
PUBLIC_ASSET_TYPES: set[str] = {
    "보험약관", "상품설명서", "홍보자료", "리플렛", "교육자료",
    "감독지침", "업무지침", "공문", "판례", "법령", "의학서적",
}

# 개인자료 문서 유형 목록 (GCS 격리 버킷 사용, RAG 인덱싱 제외)
PERSONAL_DATA_TYPES: set[str] = {
    "진단서", "의무기록", "처방전", "보험청구서", "고객계약서",
    "신분증", "개인정보동의서",
}

# GCS 버킷 경로 구분 (GP191 §1)
_GCS_PUBLIC_PREFIX    = "public_assets"   # 약관·설명서 등 공적 자산
_GCS_PRIVATE_PREFIX   = "private_data"    # 개인자료 (RAG 인덱싱 금지)
_GCS_KNOWLEDGE_PREFIX = "knowledge"       # know_pipe 지식베이스 전용

# 대용량 문서 분할 기준 (GP190 §4)
_CHUNK_PAGE_THRESHOLD = 50    # 50페이지 이상이면 분할 분석
_CHUNK_CHAR_SIZE      = 3000  # 청크당 최대 문자수

# PII 마스킹 패턴 (GP190 §2 / GP194)
_PII_PATTERNS: list[tuple[str, str]] = [
    (r"\d{6}-[1-4]\d{6}",            "***주민번호***"),    # 주민등록번호
    (r"\d{3}-\d{2}-\d{5}",           "***사업자번호***"),  # 사업자등록번호
    (r"010[-\s]?\d{4}[-\s]?\d{4}",   "***전화번호***"),    # 휴대전화
    (r"0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}", "***전화번호***"),
    (r"[가-힣]{2,4}\s*\d{4,7}",      "***계좌번호***"),    # 은행계좌 패턴
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "***이메일***"),
]

# ── GP190 §5: KCD-10 핵심 질병 코드 매핑 DB ──────────────────────────────────
# 주요 보험 관련 질환 대표 코드 (상위 70개 수록)
KCD10_DB: dict[str, str] = {
    # 암(신생물)
    "암": "C00-C97", "악성신생물": "C00-C97", "폐암": "C34", "위암": "C16",
    "대장암": "C18", "간암": "C22", "유방암": "C50", "자궁경부암": "C53",
    "전립선암": "C61", "췌장암": "C25", "갑상선암": "C73", "혈액암": "C81-C96",
    "뇌종양": "C71", "방광암": "C67", "신장암": "C64", "식도암": "C15",
    "난소암": "C56", "자궁암": "C54", "구강암": "C00-C14",
    # 심장·혈관
    "급성심근경색": "I21", "심근경색": "I21", "뇌졸중": "I60-I64",
    "뇌출혈": "I60-I62", "뇌경색": "I63", "협심증": "I20",
    "심부전": "I50", "부정맥": "I47-I49", "고혈압": "I10",
    "동맥경화": "I70", "심장판막질환": "I05-I08",
    # 당뇨·내분비
    "당뇨병": "E11", "당뇨": "E10-E14", "갑상선기능저하증": "E03",
    "갑상선기능항진증": "E05",
    # 뇌·신경
    "치매": "F00-F03", "알츠하이머": "F00", "파킨슨": "G20",
    "뇌전증": "G40", "간질": "G40",
    # 근골격계
    "골절": "S00-S99", "디스크": "M51", "허리디스크": "M51",
    "관절염": "M15-M19", "류마티스": "M05-M06", "골다공증": "M80-M81",
    # 호흡기
    "폐렴": "J18", "천식": "J45", "만성폐쇄성폐질환": "J44", "COPD": "J44",
    # 소화기
    "간경변": "K74", "간염": "B15-B19", "B형간염": "B16", "C형간염": "B17",
    "크론병": "K50", "궤양성대장염": "K51",
    # 신장
    "만성신부전": "N18", "신부전": "N17-N19", "신장질환": "N00-N29",
    # 정신건강
    "우울증": "F32-F33", "조현병": "F20", "조울증": "F31",
    # 외상·사고
    "교통사고": "V01-V99", "낙상": "W00-W19", "화상": "T20-T32",
    # 선천성
    "선천성질환": "Q00-Q99",
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. 파일 감지 (Detect) — GP190 §1
# ══════════════════════════════════════════════════════════════════════════════

def detect_file_type(filename: str, mime_type: str = "") -> dict:
    """
    파일명·MIME 타입으로 문서 형식을 감지합니다.
    반환: {"ext": str, "is_pdf": bool, "is_image": bool, "is_text": bool,
           "mime": str, "supported": bool}
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    is_pdf   = ext in {"pdf"} or "pdf" in mime_type
    is_image = ext in {"jpg", "jpeg", "png", "bmp", "tiff", "webp"} or mime_type.startswith("image/")
    is_text  = ext in {"txt", "docx", "doc", "csv"} or "text" in mime_type
    return {
        "ext":       ext,
        "is_pdf":    is_pdf,
        "is_image":  is_image,
        "is_text":   is_text,
        "mime":      mime_type or f"application/{ext}",
        "supported": is_pdf or is_image or is_text,
    }


def classify_doc_type(filename: str, doc_type_hint: str = "") -> str:
    """
    파일명 기반 공적/개인 자산 자동 분류 (GP191 §1).
    doc_type_hint가 제공되면 우선 적용.
    """
    if doc_type_hint:
        return doc_type_hint
    name_lower = filename.lower()
    if any(k in name_lower for k in ["약관", "특약", "보통약관", "표준약관"]):
        return "보험약관"
    if any(k in name_lower for k in ["설명서", "상품설명", "안내장"]):
        return "상품설명서"
    if any(k in name_lower for k in ["리플렛", "leaflet", "홍보", "팜플렛"]):
        return "리플렛"
    if any(k in name_lower for k in ["판례", "결정문", "조정결과"]):
        return "판례"
    if any(k in name_lower for k in ["지침", "감독", "업무지침"]):
        return "감독지침"
    if any(k in name_lower for k in ["진단서", "소견서", "의무기록"]):
        return "진단서"
    if any(k in name_lower for k in ["처방", "처방전"]):
        return "처방전"
    return "기타"


# ══════════════════════════════════════════════════════════════════════════════
# GP194 §1 — 무결성 가드레일: Pre-process (이미지 보정 + PII 마스킹)
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_image(file_bytes: bytes, filename: str) -> bytes:
    """
    GP190 §2 / GP194 §1 — 이미지 수평 보정(Deskew) + 대비 최적화.
    OpenCV 사용 가능 시 적용, 없으면 원본 반환.
    반환: 처리된 이미지 바이트 (PNG 포맷)
    """
    file_info = detect_file_type(filename)
    if not file_info["is_image"]:
        return file_bytes
    try:
        import cv2
        import numpy as np
        img_array = np.frombuffer(file_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return file_bytes

        # ── 대비 최적화 (CLAHE) ─────────────────────────────────────────
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # ── 수평 보정 (Deskew via Hough Transform) ──────────────────────
        edges = cv2.Canny(enhanced, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        angle = 0.0
        if lines is not None:
            angles = []
            for rho, theta in lines[:20, 0]:
                a = np.degrees(theta) - 90
                if abs(a) < 45:
                    angles.append(a)
            if angles:
                angle = float(np.median(angles))

        if abs(angle) > 0.5:
            h, w = enhanced.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            enhanced = cv2.warpAffine(
                enhanced, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )

        # ── 재인코딩 ─────────────────────────────────────────────────────
        _, buf = cv2.imencode(".png", enhanced)
        logger.info(f"[GP194] 이미지 보정 완료: angle={angle:.1f}°")
        return buf.tobytes()

    except ImportError:
        logger.warning("[GP194] OpenCV 미설치 — 이미지 보정 생략")
        return file_bytes
    except Exception as e:
        logger.warning(f"[GP194] 이미지 보정 실패 (원본 유지): {e}")
        return file_bytes


def mask_pii(text: str) -> tuple[str, list[str]]:
    """
    GP190 §2 / GP194 §2 — 텍스트 내 PII(개인정보) 자동 마스킹.
    반환: (마스킹된 텍스트, 감지된 PII 유형 목록)
    """
    masked = text
    detected: list[str] = []
    for pattern, label in _PII_PATTERNS:
        hits = re.findall(pattern, masked)
        if hits:
            detected.append(f"{label}({len(hits)}건)")
            masked = re.sub(pattern, label, masked)
    return masked, detected


# ══════════════════════════════════════════════════════════════════════════════
# GP190 §5 — KCD-10 검증 엔진
# ══════════════════════════════════════════════════════════════════════════════

def verify_kcd10(text: str) -> dict:
    """
    GP190 §5 — 추출 텍스트에서 질병명/KCD코드를 감지하여 KCD-10 DB와 대조 검증.
    반환: {"verified": list[{"term":str,"code":str}], "unverified": list[str],
           "total_found": int, "coverage_pct": float}
    """
    verified: list[dict] = []
    unverified: list[str] = []

    # ① KCD 코드 직접 패턴 (예: C34, I21, J45 등)
    code_pattern = re.compile(r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b')
    code_hits = set(code_pattern.findall(text))

    # ② 질병명 키워드 매칭
    for term, code in KCD10_DB.items():
        if term in text:
            verified.append({"term": term, "code": code})

    # ③ 직접 코드 매칭 (DB에 없는 코드도 포함)
    db_codes = set(KCD10_DB.values())
    for c in code_hits:
        already = any(v["code"].startswith(c[:3]) for v in verified)
        if not already:
            matched_name = next((k for k, v in KCD10_DB.items() if v.startswith(c[:3])), None)
            if matched_name:
                if not any(v["term"] == matched_name for v in verified):
                    verified.append({"term": matched_name, "code": c})
            else:
                unverified.append(c)

    total = len(verified) + len(unverified)
    coverage = round(len(verified) / total * 100, 1) if total > 0 else 0.0

    logger.info(f"[GP190§5] KCD 검증: 확인 {len(verified)}건 / 미확인 {len(unverified)}건")
    return {
        "verified":      verified[:20],
        "unverified":    unverified[:10],
        "total_found":   total,
        "coverage_pct":  coverage,
    }


# ══════════════════════════════════════════════════════════════════════════════
# GP190 §4 — 대용량 문서 분할 분석 (50P+ Chunking)
# ══════════════════════════════════════════════════════════════════════════════

def chunk_text_for_analysis(text: str, pages: int, chunk_size: int = _CHUNK_CHAR_SIZE) -> list[dict]:
    """
    GP190 §4 — 50페이지 초과 또는 150,000자 초과 문서를 청크로 분할.
    반환: [{"chunk_idx": int, "text": str, "char_start": int, "char_end": int}]
    """
    if pages <= _CHUNK_PAGE_THRESHOLD and len(text) <= chunk_size * 50:
        return [{"chunk_idx": 0, "text": text, "char_start": 0, "char_end": len(text)}]

    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # 단어 경계 보정
        if end < len(text):
            boundary = text.rfind("\n", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunks.append({"chunk_idx": idx, "text": text[start:end],
                        "char_start": start, "char_end": end})
        start = end
        idx += 1

    logger.info(f"[GP190§4] 대용량 분할: {pages}P → {len(chunks)}청크")
    return chunks




# ══════════════════════════════════════════════════════════════════════════════
# 2. GCS 백업 (Backup)
# ══════════════════════════════════════════════════════════════════════════════

def backup_to_gcs(
    file_bytes: bytes,
    filename: str,
    doc_type: str,
    gcs_client,
    bucket_name: str,
    max_retries: int = 3,
) -> dict:
    """
    GP190 §2, GP191 §2 — 파일을 GCS에 즉시 격리 보관.
    공적 자산 vs 개인자료 버킷 경로 자동 분리.
    실패 시 재시도 로직(최대 3회) 내장.

    반환: {"success": bool, "gcs_uri": str, "blob_name": str,
           "is_public_asset": bool, "error": str}
    """
    is_public  = doc_type in PUBLIC_ASSET_TYPES
    is_private = doc_type in PERSONAL_DATA_TYPES
    prefix     = _GCS_PUBLIC_PREFIX if is_public else (
                 _GCS_PRIVATE_PREFIX if is_private else _GCS_PUBLIC_PREFIX)

    date_str  = datetime.datetime.now().strftime("%Y/%m/%d")
    uid       = uuid.uuid4().hex[:8]
    safe_name = filename.replace(" ", "_")
    blob_name = f"{prefix}/{date_str}/{uid}_{safe_name}"

    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            bucket = gcs_client.bucket(bucket_name)
            blob   = bucket.blob(blob_name)
            mime   = "application/pdf" if safe_name.endswith(".pdf") else "application/octet-stream"
            blob.upload_from_string(file_bytes, content_type=mime)
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"[GP190] GCS 백업 완료 (시도 {attempt}): {gcs_uri}")
            return {
                "success":         True,
                "gcs_uri":         gcs_uri,
                "blob_name":       blob_name,
                "is_public_asset": is_public,
                "error":           "",
            }
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[GP190] GCS 백업 실패 (시도 {attempt}/{max_retries}): {e}")

    logger.error(f"[GP190] GCS 백업 최종 실패: {last_error}")
    return {
        "success":         False,
        "gcs_uri":         f"local://{filename}",
        "blob_name":       blob_name,
        "is_public_asset": is_public,
        "error":           last_error,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. 텍스트 추출 (Extract)
# ══════════════════════════════════════════════════════════════════════════════

def extract_text(
    file_bytes: bytes,
    filename: str,
    gcs_uri: str = "",
    dai_project: str = "",
    dai_location: str = "us",
    dai_processor_id: str = "",
    gcs_credentials=None,
) -> dict:
    """
    GP190 §2, GP191 §2 — PDF/이미지에서 텍스트 추출.
    우선순위: Document AI → pdfplumber → pypdf → 빈 문자열
    반환: {"text": str, "tables": list, "engine": str, "pages": int}
    """
    file_info = detect_file_type(filename)

    # ── 1차: Document AI (고정밀 OCR + 표 추출) ───────────────────────────
    if dai_processor_id and gcs_uri and not gcs_uri.startswith("local://"):
        try:
            result = _extract_via_documentai(
                file_bytes, gcs_uri, dai_project, dai_location,
                dai_processor_id, gcs_credentials,
            )
            if result.get("text") or result.get("tables"):
                return result
        except Exception as e:
            logger.warning(f"[GP190] Document AI 실패 → 폴백: {e}")

    # ── 2차: pdfplumber (PDF 텍스트·표 추출) ──────────────────────────────
    if file_info["is_pdf"]:
        try:
            result = _extract_via_pdfplumber(file_bytes)
            if result.get("text"):
                return result
        except Exception as e:
            logger.warning(f"[GP190] pdfplumber 실패 → pypdf 폴백: {e}")

        # ── 3차: pypdf 폴백 ────────────────────────────────────────────────
        try:
            result = _extract_via_pypdf(file_bytes)
            if result.get("text"):
                return result
        except Exception as e:
            logger.warning(f"[GP190] pypdf 실패: {e}")

    # ── 4차: 이미지 — Pillow 기반 메타 반환 (OCR 미지원 시) ──────────────
    if file_info["is_image"]:
        return {
            "text":   "",
            "tables": [],
            "engine": "image_no_ocr",
            "pages":  1,
            "note":   "이미지 파일 — Document AI OCR 미설정 상태. 텍스트 추출 불가.",
        }

    return {"text": "", "tables": [], "engine": "unsupported", "pages": 0}


def _extract_via_documentai(
    file_bytes: bytes, gcs_uri: str,
    project: str, location: str, processor_id: str,
    credentials=None,
) -> dict:
    from google.cloud import documentai_v1 as documentai
    opts = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    client = (
        documentai.DocumentProcessorServiceClient(credentials=credentials, client_options=opts)
        if credentials else
        documentai.DocumentProcessorServiceClient(client_options=opts)
    )
    proc_name = client.processor_path(project, location, processor_id)

    if file_bytes and len(file_bytes) < 20 * 1024 * 1024:
        req = documentai.ProcessRequest(
            name=proc_name,
            raw_document=documentai.RawDocument(content=file_bytes, mime_type="application/pdf"),
        )
    else:
        req = documentai.ProcessRequest(
            name=proc_name,
            gcs_document=documentai.GcsDocument(gcs_uri=gcs_uri, mime_type="application/pdf"),
        )

    result = client.process_document(request=req)
    doc    = result.document
    text   = doc.text or ""

    tables = []
    for page in doc.pages:
        for tbl in page.tables:
            def _cell(c):
                try:
                    seg = c.layout.text_anchor.text_segments[0]
                    return text[seg.start_index: seg.end_index].strip()
                except Exception:
                    return ""
            hdrs = [[_cell(c) for c in r.cells] for r in tbl.header_rows]
            rows = [[_cell(c) for c in r.cells] for r in tbl.body_rows]
            if hdrs or rows:
                tables.append({"page": page.page_number, "headers": hdrs, "rows": rows})

    return {
        "text":   text,
        "tables": tables,
        "engine": f"DocumentAI ({len(tables)}표)",
        "pages":  len(doc.pages),
    }


def _extract_via_pdfplumber(file_bytes: bytes) -> dict:
    import pdfplumber
    tables, pages_text = [], []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pn, page in enumerate(pdf.pages, 1):
            pages_text.append(page.extract_text() or "")
            for t in (page.extract_tables() or []):
                if t and len(t) > 1:
                    tables.append({"page": pn, "headers": [t[0]], "rows": t[1:]})
    return {
        "text":   "\n".join(pages_text),
        "tables": tables,
        "engine": f"pdfplumber ({len(tables)}표)",
        "pages":  len(pages_text),
    }


def _extract_via_pypdf(file_bytes: bytes) -> dict:
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text   = "\n".join(p.extract_text() or "" for p in reader.pages)
    return {
        "text":   text,
        "tables": [],
        "engine": "pypdf",
        "pages":  len(reader.pages),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. AI 분류 — GP192 Core-8 정밀 추출 (GP191 §2 + GP192 전면 확장)
# ══════════════════════════════════════════════════════════════════════════════

_CLASSIFY_PROMPT = """당신은 보험 법리 전문 AI입니다.
아래 보험 문서에서 GP192 Core-8 항목을 정밀 추출하여 JSON으로만 반환하세요 (다른 텍스트 절대 없음).

[GP192 Core-8 추출 항목]
1. doc_class: "약관" / "리플렛" / "설명서" / "판례" / "공문" / "기타" 중 하나
2. insurer: 보험사명 (없으면 "미확인")
3. product_name: 상품명 전체 (버전·개정번호 포함, 없으면 "미확인")
4. sale_start_date: 판매기준일자/출시일 (YYYY-MM-DD 또는 "YYYY년 MM월", 없으면 "미확인")
5. sale_end_date: 판매종료일자/절판일/개정일 (YYYY-MM-DD 또는 "YYYY년 MM월", 없으면 "현재판매중")
6. key_coverages: 핵심 담보 목록 (최대 10개, 문자열 배열)
7. payout_logic: 보험금 지급기준 및 산출 방식 설명 (예: "진단일 기준 1회 지급, 암진단금=가입금액×100%"). 수식 포함.
8. coverage_limits: 보장 한도 요약 (예: "암진단금 5,000만원, 입원일당 3만원")
9. risk_factors: 지급 영향 변수 목록 — 면책 기간, 감액 기간, 지급 횟수 제한, 지급 제외 조건 (문자열 배열, 최대 10개)
10. exclusions: 주요 면책 조항 요약 (최대 5줄)
11. product_highlights: 보험사가 강조하는 특·장점, 업계 최초/유일 담보, 핵심 셀링 포인트 (문자열 배열, 최대 8개)
12. terminology: 약관상 주요 용어 정의 목록. 각 항목: {{"term": "용어", "definition": "정의"}} 형태 (최대 15개)
13. issue_date: 약관 발행일 또는 기준일 (없으면 "미확인")
14. summary_1st_person: "내가 분석한 이 약관의 핵심 지급 기준은 다음과 같습니다. " 으로 시작하는 1인칭 요약 (3~4문장, 판매주기·특장점 포함)
15. sales_pitch: "내가 이 상품을 추천하는 이유는 [특장점 항목] 때문입니다" 구조의 1인칭 세일즈 초안 (2~3문장)

[문서 텍스트 (앞 4000자)]
{text}

JSON만 출력하세요:"""


# ── GP192: 판매주기 비교 헬퍼 ────────────────────────────────────────────────
def compare_policy_version(
    customer_join_date: str,
    sale_start: str,
    sale_end: str,
) -> dict:
    """
    GP192 §3 — 고객 가입일과 상품 판매주기 대조.
    반환: {"is_latest": bool, "version_label": str, "analysis": str}
    """
    import re as _re
    def _parse(s: str):
        if not s or s in ("미확인", "현재판매중"):
            return None
        m = _re.search(r"(\d{4})[\-년\s]*(\d{1,2})?", s)
        if m:
            y = int(m.group(1))
            mo = int(m.group(2)) if m.group(2) else 1
            return datetime.date(y, mo, 1)
        return None

    join_dt  = _parse(customer_join_date)
    start_dt = _parse(sale_start)
    end_dt   = _parse(sale_end) if sale_end and sale_end != "현재판매중" else None

    if not join_dt or not start_dt:
        return {
            "is_latest":     None,
            "version_label": "판별 불가",
            "analysis":      "가입일 또는 판매기준일 데이터가 없어 약관 버전 판별이 불가합니다.",
        }

    in_range = start_dt <= join_dt and (end_dt is None or join_dt <= end_dt)

    if end_dt is None:
        label    = "현행 약관"
        analysis = (
            f"고객 가입일({customer_join_date})은 현재 판매 중인 약관 범위에 해당합니다. "
            "최신 약관이 적용됩니다."
        )
    elif in_range:
        label    = f"구형 약관 ({sale_start} ~ {sale_end})"
        analysis = (
            f"고객 가입일({customer_join_date})은 {sale_start}~{sale_end} 판매 구간에 해당합니다. "
            f"이 약관은 {sale_end}에 판매 종료된 구형 버전입니다. "
            "현행 약관과의 지급기준 차이를 반드시 확인하세요."
        )
    else:
        label    = "범위 외 (가입일 불일치)"
        analysis = (
            f"고객 가입일({customer_join_date})이 해당 약관의 판매기간 "
            f"({sale_start} ~ {sale_end})에 포함되지 않습니다. "
            "다른 버전의 약관을 확인하세요."
        )

    return {"is_latest": end_dt is None and in_range, "version_label": label, "analysis": analysis}


def classify_document(text: str, ai_call_fn=None) -> dict:
    """
    GP192 — Core-8 정밀 추출. GP191 기본값에 판매주기·특장점·용어·지급기준·세일즈멘트 추가.
    ai_call_fn: (prompt: str) -> str. None이면 기본값 반환.
    """
    default = {
        "doc_class":          "기타",
        "insurer":            "미확인",
        "product_name":       "미확인",
        "sale_start_date":    "미확인",
        "sale_end_date":      "현재판매중",
        "key_coverages":      [],
        "payout_logic":       "",
        "coverage_limits":    "",
        "risk_factors":       [],
        "exclusions":         "",
        "product_highlights": [],
        "terminology":        [],
        "issue_date":         "미확인",
        "summary_1st_person": "",
        "sales_pitch":        "",
    }
    if not ai_call_fn or not text.strip():
        return default

    import json, re
    prompt = _CLASSIFY_PROMPT.format(text=text[:4000])
    try:
        raw = ai_call_fn(prompt)
        m   = re.search(r"\{[\s\S]+\}", raw)
        if m:
            parsed = json.loads(m.group(0))
            default.update(parsed)
    except Exception as e:
        logger.warning(f"[GP192] AI 정밀 추출 실패: {e}")
    return default


# ══════════════════════════════════════════════════════════════════════════════
# 5. RAG 인덱싱 연동 (GP191 §3)
# ══════════════════════════════════════════════════════════════════════════════

def index_to_rag(
    text: str,
    filename: str,
    doc_type: str,
    classification: dict,
    rag_add_fn=None,
) -> dict:
    """
    GP191 §3 — 공적 자산만 RAG에 즉시 등록. 개인자료 제외.
    rag_add_fn: (text, filename, meta) -> int (document_id). None이면 세션 기록만.
    반환: {"indexed": bool, "doc_id": int, "chunks": int, "skipped_reason": str}
    """
    if doc_type in PERSONAL_DATA_TYPES:
        logger.info(f"[GP191] 개인자료 RAG 인덱싱 제외: {filename}")
        return {"indexed": False, "doc_id": -1, "chunks": 0,
                "skipped_reason": "개인자료 — RAG 인덱싱 금지 (GP191 §1)"}

    if not text.strip():
        return {"indexed": False, "doc_id": -1, "chunks": 0,
                "skipped_reason": "텍스트 추출 실패 — 인덱싱 불가"}

    meta = {
        "category":          doc_type,
        "insurer":           classification.get("insurer", ""),
        "product_name":      classification.get("product_name", ""),
        "doc_class":         classification.get("doc_class", "기타"),
        "issue_date":        classification.get("issue_date", ""),
        "sale_start_date":   classification.get("sale_start_date", "미확인"),
        "sale_end_date":     classification.get("sale_end_date", "현재판매중"),
        "key_coverages":     ", ".join(classification.get("key_coverages", [])[:5]),
        "payout_logic":      classification.get("payout_logic", "")[:300],
        "coverage_limits":   classification.get("coverage_limits", ""),
        "product_highlights": "; ".join(classification.get("product_highlights", [])[:4]),
        "summary":           classification.get("summary_1st_person", "")[:300],
        "indexed_at":        datetime.datetime.now().isoformat(timespec="seconds"),
    }

    doc_id = -1
    if rag_add_fn:
        try:
            doc_id = rag_add_fn(text, filename, meta) or -1
            logger.info(f"[GP191] RAG 인덱싱 완료: {filename} → doc_id={doc_id}")
        except Exception as e:
            logger.error(f"[GP191] RAG 인덱싱 실패: {e}")
            return {"indexed": False, "doc_id": -1, "chunks": 0,
                    "skipped_reason": f"RAG 오류: {e}"}

    chunks = max(1, len(text) // 500)
    return {"indexed": True, "doc_id": doc_id, "chunks": chunks, "skipped_reason": ""}


# ══════════════════════════════════════════════════════════════════════════════
# 5b. GCS JSON 정밀 데이터 저장 (GP192 §2)
# ══════════════════════════════════════════════════════════════════════════════

def save_precision_json_to_gcs(
    classification: dict,
    filename: str,
    doc_type: str,
    gcs_client,
    bucket_name: str,
    source_gcs_uri: str = "",
) -> dict:
    """
    GP192 §2 — 정밀 추출된 Core-8 데이터를 JSON으로 GCS에 즉시 저장.
    원본 파일 URI와 매칭하여 문서 ID별로 저장.
    반환: {"success": bool, "json_uri": str, "error": str}
    """
    if not gcs_client or not bucket_name:
        return {"success": False, "json_uri": "", "error": "GCS 클라이언트 없음"}

    import json as _json
    date_str  = datetime.datetime.now().strftime("%Y/%m/%d")
    uid       = uuid.uuid4().hex[:8]
    safe_name = filename.replace(" ", "_").rsplit(".", 1)[0]
    blob_name = f"precision_data/{date_str}/{uid}_{safe_name}.json"

    payload = {
        "schema_version":    "GP192-Core8",
        "extracted_at":      datetime.datetime.now().isoformat(timespec="seconds"),
        "source_file":       filename,
        "source_gcs_uri":    source_gcs_uri,
        "doc_type":          doc_type,
        "insurer":           classification.get("insurer", "미확인"),
        "product_name":      classification.get("product_name", "미확인"),
        "doc_class":         classification.get("doc_class", "기타"),
        "sale_start_date":   classification.get("sale_start_date", "미확인"),
        "sale_end_date":     classification.get("sale_end_date", "현재판매중"),
        "issue_date":        classification.get("issue_date", "미확인"),
        "key_coverages":     classification.get("key_coverages", []),
        "payout_logic":      classification.get("payout_logic", ""),
        "coverage_limits":   classification.get("coverage_limits", ""),
        "risk_factors":      classification.get("risk_factors", []),
        "exclusions":        classification.get("exclusions", ""),
        "product_highlights":classification.get("product_highlights", []),
        "terminology":       classification.get("terminology", []),
        "summary_1st_person":classification.get("summary_1st_person", ""),
        "sales_pitch":       classification.get("sales_pitch", ""),
    }

    try:
        bucket = gcs_client.bucket(bucket_name)
        blob   = bucket.blob(blob_name)
        blob.upload_from_string(
            _json.dumps(payload, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        json_uri = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"[GP192] 정밀 JSON 저장 완료: {json_uri}")
        return {"success": True, "json_uri": json_uri, "error": ""}
    except Exception as e:
        logger.warning(f"[GP192] 정밀 JSON 저장 실패: {e}")
        return {"success": False, "json_uri": "", "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# 6. 통합 파이프라인 실행 (메인 엔트리포인트)
# ══════════════════════════════════════════════════════════════════════════════

def run_scan_pipeline(
    file_bytes: bytes,
    filename: str,
    doc_type: str = "",
    gcs_client=None,
    gcs_bucket: str = "",
    dai_project: str = "",
    dai_location: str = "us",
    dai_processor_id: str = "",
    gcs_credentials=None,
    ai_call_fn=None,
    rag_add_fn=None,
    progress_callback=None,
    skip_preprocess: bool = False,
) -> dict:
    """
    [GP190 통합 파이프라인] 6단계 무결성 프로세스:
      P0: Pre-process (이미지 보정 + PII 마스킹)
      P1: 파일 감지 + 문서 유형 분류
      P2: GCS 즉시 격리 백업
      P3: 텍스트 추출 (DocAI → pdfplumber → pypdf)
      P3b: 50P+ 대용량 분할 분석 (Chunking)
      P3c: KCD-10 질병코드 검증
      P4: GP192 Core-8 정밀 AI 추출
      P4b: 정밀 JSON → GCS 저장
      P5: RAG 지식베이스 인덱싱 (Master Approval 대기 상태로 저장)
    """
    log = []

    def _progress(step: str, pct: float, msg: str):
        log.append(f"[{step}] {msg}")
        if progress_callback:
            try:
                progress_callback(step, pct, msg)
            except Exception:
                pass

    # ── Step P0: Pre-process (GP190 §2 / GP194) ──────────────────────────
    if not skip_preprocess:
        _progress("P0", 0.05, "이미지 보정(Deskew) + 대비 최적화 중...")
        file_bytes = preprocess_image(file_bytes, filename)
        _progress("P0", 0.08, "이미지 보정 완료")

    # ── Step P1: 파일 감지 ────────────────────────────────────────────────
    _progress("P1", 0.1, f"파일 감지: {filename}")
    file_info = detect_file_type(filename)
    if not file_info["supported"]:
        err = f"지원하지 않는 파일 형식: .{file_info['ext']}"
        _progress("P1", 0.1, f"오류: {err}")
        return _fail_result(filename, doc_type, err, log)

    doc_type = classify_doc_type(filename, doc_type)
    _progress("P1", 0.2, f"문서 유형 감지: {doc_type}")

    # ── Step P2: GCS 백업 ────────────────────────────────────────────────
    gcs_uri = f"local://{filename}"
    is_public_asset = doc_type in PUBLIC_ASSET_TYPES

    if gcs_client and gcs_bucket:
        _progress("P2", 0.3, "GCS 즉시 격리 백업 중...")
        gcs_result = backup_to_gcs(file_bytes, filename, doc_type, gcs_client, gcs_bucket)
        gcs_uri         = gcs_result["gcs_uri"]
        is_public_asset = gcs_result["is_public_asset"]
        if gcs_result["success"]:
            _progress("P2", 0.40, f"GCS 백업 완료: {gcs_uri}")
        else:
            _progress("P2", 0.40, f"GCS 백업 실패 (로컬 폴백): {gcs_result['error']}")
    else:
        _progress("P2", 0.40, "GCS 클라이언트 미연결 — 로컬 처리 모드")

    # ── Step P3: 텍스트 추출 ─────────────────────────────────────────────
    _progress("P3", 0.50, "AI 마스터가 정밀 분석 중입니다...")
    extract_result = extract_text(
        file_bytes, filename, gcs_uri,
        dai_project, dai_location, dai_processor_id, gcs_credentials,
    )
    raw_text       = extract_result.get("text", "")
    tables         = extract_result.get("tables", [])
    extract_engine = extract_result.get("engine", "unknown")
    pages          = extract_result.get("pages", 1)
    _progress("P3", 0.62, f"텍스트 추출 완료: {len(raw_text)}자, {len(tables)}표, {pages}P ({extract_engine})")

    # ── Step P3a: PII 마스킹 (GP194 §2) ──────────────────────────────────
    text, pii_detected = mask_pii(raw_text)
    if pii_detected:
        _progress("P3a", 0.64, f"PII 마스킹 완료: {', '.join(pii_detected)}")
    else:
        _progress("P3a", 0.64, "PII 감지 없음")

    # ── Step P3b: 대용량 분할 분석 (GP190 §4, 50P+) ───────────────────────
    chunks = chunk_text_for_analysis(text, pages)
    is_chunked = len(chunks) > 1
    if is_chunked:
        _progress("P3b", 0.66, f"대용량 문서 분할: {pages}P → {len(chunks)}청크 (각 {_CHUNK_CHAR_SIZE}자)")
        analysis_text = text[:4000]   # AI 분류는 앞 4000자 대표 청크 사용
    else:
        _progress("P3b", 0.66, f"단일 분석 모드 ({pages}P, {len(text)}자)")
        analysis_text = text

    # ── Step P3c: KCD-10 검증 (GP190 §5) ────────────────────────────────
    kcd_result: dict = {"verified": [], "unverified": [], "total_found": 0, "coverage_pct": 0.0}
    if text:
        kcd_result = verify_kcd10(text)
        _progress(
            "P3c", 0.68,
            f"KCD-10 검증: 확인 {len(kcd_result['verified'])}건 / "
            f"미확인 {len(kcd_result['unverified'])}건 (커버율 {kcd_result['coverage_pct']}%)"
        )

    # ── Step P4: GP192 정밀 AI 추출 (공적 자산만) ────────────────────────
    classification: dict = {
        "doc_class": "기타", "insurer": "미확인", "product_name": "미확인",
        "sale_start_date": "미확인", "sale_end_date": "현재판매중",
        "key_coverages": [], "payout_logic": "", "coverage_limits": "",
        "risk_factors": [], "exclusions": "", "product_highlights": [],
        "terminology": [], "issue_date": "미확인",
        "summary_1st_person": "", "sales_pitch": "",
    }
    if is_public_asset and text and ai_call_fn:
        _progress("P4", 0.72, "GP192 Core-8 정밀 추출 중 — 용어·지급기준·판매주기·특장점...")
        classification = classify_document(analysis_text, ai_call_fn)
        n_terms  = len(classification.get("terminology", []))
        n_covers = len(classification.get("key_coverages", []))
        n_highs  = len(classification.get("product_highlights", []))
        _progress("P4", 0.84,
            f"추출 완료: {classification.get('doc_class','?')} / "
            f"{classification.get('product_name','?')} | "
            f"담보 {n_covers}건 · 용어 {n_terms}건 · 특장점 {n_highs}건"
        )
    else:
        _progress("P4", 0.84, "AI 정밀 추출 생략 (개인자료 또는 AI 미연결)")

    # ── Step P4b: GP192 정밀 JSON → GCS 저장 ────────────────────────────
    json_gcs_uri = ""
    if is_public_asset and gcs_client and gcs_bucket and classification.get("product_name") != "미확인":
        _progress("P4b", 0.88, "GP192 정밀 데이터 JSON → GCS 저장 중...")
        _json_result = save_precision_json_to_gcs(
            classification, filename, doc_type, gcs_client, gcs_bucket, gcs_uri
        )
        json_gcs_uri = _json_result.get("json_uri", "")
        if _json_result["success"]:
            _progress("P4b", 0.91, f"JSON 저장 완료: {json_gcs_uri}")
        else:
            _progress("P4b", 0.91, f"JSON 저장 실패: {_json_result['error']}")

    # ── Step P5: RAG 인덱싱 (GP190 §6: Master Approval 대기) ─────────────
    _progress("P5", 0.94, "RAG 지식베이스 등록 중...")
    rag_result = index_to_rag(text, filename, doc_type, classification, rag_add_fn)
    if rag_result["indexed"]:
        _progress("P5", 1.0, f"RAG 등록 완료: {rag_result['chunks']}청크 | 마스터 승인 대기")
    else:
        _progress("P5", 1.0, f"RAG 등록 생략: {rag_result['skipped_reason']}")

    return {
        "success":            True,
        "filename":           filename,
        "doc_type":           doc_type,
        "is_public_asset":    is_public_asset,
        "gcs_uri":            gcs_uri,
        "json_gcs_uri":       json_gcs_uri,
        "text_length":        len(text),
        "tables_count":       len(tables),
        "extract_engine":     extract_engine,
        "pages":              pages,
        "is_chunked":         is_chunked,
        "chunks_count":       len(chunks),
        "pii_detected":       pii_detected,
        "kcd":                kcd_result,
        "classification":     classification,
        "rag":                rag_result,
        "error":              "",
        "pipeline_log":       log,
        "master_approved":    False,
        "summary_1st_person": classification.get("summary_1st_person", ""),
        "sales_pitch":        classification.get("sales_pitch", ""),
        "gp192_counts": {
            "terminology":        len(classification.get("terminology", [])),
            "key_coverages":      len(classification.get("key_coverages", [])),
            "product_highlights": len(classification.get("product_highlights", [])),
            "risk_factors":       len(classification.get("risk_factors", [])),
        },
    }


def _fail_result(filename: str, doc_type: str, error: str, log: list) -> dict:
    return {
        "success": False, "filename": filename, "doc_type": doc_type,
        "is_public_asset": False, "gcs_uri": "", "json_gcs_uri": "",
        "text_length": 0, "tables_count": 0, "extract_engine": "none",
        "pages": 0, "is_chunked": False, "chunks_count": 0,
        "pii_detected": [], "kcd": {"verified": [], "unverified": [], "total_found": 0, "coverage_pct": 0.0},
        "classification": {}, "rag": {"indexed": False, "doc_id": -1, "chunks": 0, "skipped_reason": error},
        "error": error, "pipeline_log": log, "master_approved": False,
        "summary_1st_person": "", "sales_pitch": "",
        "gp192_counts": {"terminology": 0, "key_coverages": 0, "product_highlights": 0, "risk_factors": 0},
    }


# ══════════════════════════════════════════════════════════════════════════════
# 7. Streamlit UI 헬퍼 (GP190 §3 — 상태 피드백 컴포넌트)
# ══════════════════════════════════════════════════════════════════════════════

def render_scan_progress_ui(result: dict) -> None:
    """
    GP190 §4 / GP192 §4 — 스캔 결과를 Streamlit에 렌더링하는 표준 UI 함수.
    성공 시: GP192 분석완료 알림 + Core-8 추출 수치 + 1인칭 요약 + 세일즈 멘트.
    실패 시: 적색 카드 + 1인칭 복구 안내.
    """
    import streamlit as st

    if result["success"]:
        cls_data  = result.get("classification", {})
        rag_data  = result.get("rag", {})
        summary   = result.get("summary_1st_person", "")
        pitch     = result.get("sales_pitch", "")
        gcs_uri   = result.get("gcs_uri", "")
        json_uri  = result.get("json_gcs_uri", "")
        counts    = result.get("gp192_counts", {})
        n_terms   = counts.get("terminology", 0)
        n_covers  = counts.get("key_coverages", 0)
        n_highs   = counts.get("product_highlights", 0)
        n_risks   = counts.get("risk_factors", 0)
        sale_s    = cls_data.get("sale_start_date", "")
        sale_e    = cls_data.get("sale_end_date", "")
        payout    = cls_data.get("payout_logic", "")
        highlights= cls_data.get("product_highlights", [])

        # ── GP192 §4 분석완료 알림 (밝은 파스텔 톤) ─────────────────────
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#f0fdf4,#ecfdf5);border:2px solid #22c55e;
  border-radius:12px;padding:14px 18px;margin:8px 0;">
  <div style="font-size:0.95rem;font-weight:900;color:#166534;margin-bottom:6px;">
    ✅ 분석 완료: 지급기준 및 상품 특·장점 업데이트됨
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
    <span style="background:#dcfce7;color:#166534;border-radius:20px;padding:2px 10px;font-size:0.73rem;font-weight:700;">📋 담보 {n_covers}건</span>
    <span style="background:#dbeafe;color:#1e40af;border-radius:20px;padding:2px 10px;font-size:0.73rem;font-weight:700;">📖 용어 {n_terms}건</span>
    <span style="background:#fef9c3;color:#92400e;border-radius:20px;padding:2px 10px;font-size:0.73rem;font-weight:700;">⭐ 특장점 {n_highs}건</span>
    <span style="background:#fee2e2;color:#991b1b;border-radius:20px;padding:2px 10px;font-size:0.73rem;font-weight:700;">⚠️ 리스크 {n_risks}건</span>
    {f'<span style="background:#f0f9ff;color:#0369a1;border-radius:20px;padding:2px 10px;font-size:0.73rem;font-weight:700;">📚 RAG {rag_data.get("chunks",0)}청크</span>' if rag_data.get("indexed") else ''}
  </div>
  <div style="font-size:0.78rem;color:#64748b;margin-bottom:4px;">
    🔧 {result['extract_engine']} &nbsp;|&nbsp;
    📄 {result['text_length']:,}자 &nbsp;|&nbsp;
    📊 {result['tables_count']}표 &nbsp;|&nbsp;
    🏷️ {result['doc_type']}
    {f'&nbsp;|&nbsp; 판매: {sale_s} ~ {sale_e}' if sale_s and sale_s != '미확인' else ''}
  </div>
  {f'<div style="font-size:0.78rem;color:#334155;background:#f8fafc;border-radius:6px;padding:6px 10px;margin-top:6px;">⚖️ <b>지급기준:</b> {payout[:200]}{'...' if len(payout)>200 else ''}</div>' if payout else ''}
  {f'<div style="font-size:0.80rem;color:#0369a1;font-style:italic;margin-top:6px;">💬 {summary}</div>' if summary else ''}
  {f'<div style="font-size:0.80rem;color:#166534;margin-top:4px;">🎯 {pitch}</div>' if pitch else ''}
  {f'<div style="font-size:0.73rem;color:#64748b;margin-top:4px;">🗂️ JSON: <code>{json_uri[:70]}{'...' if len(json_uri)>70 else ''}</code></div>' if json_uri else ''}
</div>""", unsafe_allow_html=True)

        # ── 특장점 목록 (있을 때만) ──────────────────────────────────────
        if highlights:
            hl_html = "".join(
                f'<li style="margin:3px 0;">{h}</li>' for h in highlights[:6]
            )
            st.markdown(f"""
<div style="background:#fffbeb;border-left:3px solid #f59e0b;border-radius:6px;
  padding:8px 14px;margin:4px 0;font-size:0.80rem;">
  <b style="color:#92400e;">⭐ 보험사 강조 특·장점</b>
  <ul style="margin:6px 0 0 0;padding-left:18px;color:#78350f;">{hl_html}</ul>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="background:#fff1f2;border-left:4px solid #ef4444;border-radius:8px;
  padding:12px 16px;margin:6px 0;font-size:0.83rem;">
  ❌ <b>{result['filename']}</b> 처리 실패
  <br><span style="color:#dc2626;font-size:0.80rem;">{result['error']}</span>
  <br><span style="font-size:0.78rem;color:#64748b;font-style:italic;">
    💡 내가 이 파일을 다시 확인하겠습니다. 파일 형식(PDF/JPG/PNG)을 확인하거나 잠시 후 재시도해 주세요.
  </span>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 8. GP193 전역 지식 동기화 — Universal Ingest Hook
# ══════════════════════════════════════════════════════════════════════════════

def global_ingest_hook(
    file_bytes: bytes,
    filename: str,
    source_tab: str = "unknown",
    doc_type: str = "",
    gcs_client=None,
    gcs_bucket: str = "",
    dai_project: str = "",
    dai_location: str = "us",
    dai_processor_id: str = "",
    gcs_credentials=None,
    ai_call_fn=None,
    rag_add_fn=None,
    session_state=None,
) -> dict:
    """
    [GP193 §1~§4] 전역 지식 동기화 후크.

    앱 내 어느 화면에서 파일이 업로드되든 동일한
    [OCR → GP192 Core-8 추출 → GCS 보관 → RAG 인덱싱 → 상담 팩트 시트 저장]
    파이프라인을 강제 실행합니다.

    Args:
        file_bytes:   업로드된 파일 바이트
        filename:     파일명
        source_tab:   호출 출처 탭 식별자 (예: "gp96_leaflet", "gp88_ocr", "policy_scan")
        doc_type:     문서 유형 힌트 (없으면 파일명 기반 자동 감지)
        session_state: Streamlit session_state 객체 (팩트 시트 저장용)
        나머지:       run_scan_pipeline과 동일

    반환:
        run_scan_pipeline 결과 dict + {"source_tab": str, "ingest_id": str}
    """
    ingest_id = f"{uuid.uuid4().hex[:6]}_{filename[:20].replace(' ','_')}"
    logger.info(f"[GP193] 전역 인제스트 시작: {ingest_id} (출처: {source_tab})")

    result = run_scan_pipeline(
        file_bytes=file_bytes,
        filename=filename,
        doc_type=doc_type,
        gcs_client=gcs_client,
        gcs_bucket=gcs_bucket,
        dai_project=dai_project,
        dai_location=dai_location,
        dai_processor_id=dai_processor_id,
        gcs_credentials=gcs_credentials,
        ai_call_fn=ai_call_fn,
        rag_add_fn=rag_add_fn,
    )
    result["source_tab"] = source_tab
    result["ingest_id"]  = ingest_id

    # ── GP193 §3: 상담 팩트 시트로 변환 → session_state 저장 ─────────────
    if session_state is not None and result.get("success"):
        cls = result.get("classification", {})
        fact_sheet = {
            "ingest_id":         ingest_id,
            "source_tab":        source_tab,
            "filename":          filename,
            "doc_type":          result.get("doc_type", ""),
            "ingested_at":       datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "product_name":      cls.get("product_name", "미확인"),
            "insurer":           cls.get("insurer", "미확인"),
            "sale_start_date":   cls.get("sale_start_date", "미확인"),
            "sale_end_date":     cls.get("sale_end_date", "현재판매중"),
            "key_coverages":     cls.get("key_coverages", []),
            "payout_logic":      cls.get("payout_logic", ""),
            "coverage_limits":   cls.get("coverage_limits", ""),
            "risk_factors":      cls.get("risk_factors", []),
            "product_highlights":cls.get("product_highlights", []),
            "terminology":       cls.get("terminology", []),
            "summary_1st_person":cls.get("summary_1st_person", ""),
            "sales_pitch":       cls.get("sales_pitch", ""),
            "gcs_uri":           result.get("gcs_uri", ""),
            "json_gcs_uri":      result.get("json_gcs_uri", ""),
            "rag_indexed":       result.get("rag", {}).get("indexed", False),
            "rag_chunks":        result.get("rag", {}).get("chunks", 0),
            "text_length":       result.get("text_length", 0),
        }

        # 최신 팩트 시트를 리스트 선두에 삽입 (최대 20건 유지)
        _live = session_state.get("gp193_live_context", [])
        _live.insert(0, fact_sheet)
        session_state["gp193_live_context"] = _live[:20]

        # 최신 단일 참조용 (상담 탭에서 즉시 접근)
        session_state["gp193_latest_fact"] = fact_sheet

        logger.info(
            f"[GP193] 팩트 시트 저장 완료: {filename} | "
            f"{cls.get('product_name','?')} | "
            f"담보 {len(cls.get('key_coverages',[]))}건 | "
            f"RAG {'✓' if fact_sheet['rag_indexed'] else '✗'}"
        )

    return result


def render_gp193_live_badge(session_state=None) -> str:
    """
    GP193 §4 — 최신 인제스트 자료 상단 배지 HTML 반환.
    상담 탭에서 '방금 로드된 자료에 따르면...' 컨텍스트 표시용.
    session_state가 없거나 데이터가 없으면 빈 문자열 반환.
    """
    if session_state is None:
        return ""
    fact = session_state.get("gp193_latest_fact")
    if not fact:
        return ""

    pname   = fact.get("product_name", "미확인")
    insurer = fact.get("insurer", "미확인")
    covers  = fact.get("key_coverages", [])
    pitch   = fact.get("sales_pitch", "")
    at      = fact.get("ingested_at", "")
    src     = fact.get("source_tab", "")
    n_cov   = len(covers)
    cov_preview = " · ".join(covers[:3]) + ("..." if n_cov > 3 else "")

    return f"""
<div style="background:linear-gradient(90deg,#eff6ff,#f0fdf4);border:2px solid #22c55e;
  border-radius:10px;padding:10px 14px;margin:8px 0;font-size:0.82rem;">
  <div style="font-weight:900;color:#166534;margin-bottom:4px;">
    🌐 [GP193] 방금 로드된 자료에 따르면 &nbsp;
    <span style="background:#dcfce7;color:#166534;border-radius:12px;padding:1px 8px;font-size:0.70rem;">
      전역 지식 베이스 업데이트 완료
    </span>
  </div>
  <div style="color:#0f172a;">
    📦 <b>{pname}</b> &nbsp;|&nbsp; 🏢 {insurer} &nbsp;|&nbsp;
    📋 핵심담보 {n_cov}건{f": {cov_preview}" if cov_preview else ""}
  </div>
  {f'<div style="color:#1e40af;margin-top:3px;font-style:italic;">🎯 {pitch}</div>' if pitch else ''}
  <div style="color:#94a3b8;font-size:0.72rem;margin-top:3px;">
    ⏱ {at} &nbsp;|&nbsp; 출처: {src}
  </div>
</div>"""


def get_uploader_css() -> str:
    """
    [GP190 §3 / GP194 §4] 전역 file_uploader 시각화 CSS.
    UI 표준: 파스텔 블루(#E0F2FE) 배경 + 2px 붉은색 실선(#EF4444) 외곽선.
    """
    return """
/* ═══════════════════════════════════════════════════════════════════════════
   GP190 §3 / GP194 §4 — 전역 스캔 업로드 박스 UI 표준
   배경: 파스텔 블루 #E0F2FE / 테두리: 2px solid #EF4444 (붉은색 실선)
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] > section {
    border: 2px solid #EF4444 !important;
    border-radius: 12px !important;
    background: #E0F2FE !important;
    transition: background 0.25s ease, border-color 0.25s ease,
                box-shadow 0.25s ease !important;
    padding: 12px 16px !important;
}
[data-testid="stFileUploader"] > section:hover {
    background: #BAE6FD !important;
    border-color: #DC2626 !important;
    box-shadow: 0 0 0 3px rgba(239,68,68,0.18) !important;
}
[data-testid="stFileUploader"] > section > div {
    color: #0369a1 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #1e40af !important;
    font-weight: 700 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span {
    font-size: 0.85rem !important;
}
/* 파스텔 톤 프로그레스 바 (분석 중 표시) */
.gk-scan-progress-bar {
    width: 100%;
    height: 10px;
    background: #dbeafe;
    border-radius: 99px;
    overflow: hidden;
    margin: 6px 0;
}
.gk-scan-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #93c5fd, #60a5fa, #3b82f6);
    border-radius: 99px;
    transition: width 0.4s ease;
    animation: gk-scan-shimmer 1.8s infinite;
}
@keyframes gk-scan-shimmer {
    0%   { opacity: 0.75; }
    50%  { opacity: 1.0;  }
    100% { opacity: 0.75; }
}
"""


# ══════════════════════════════════════════════════════════════════════════════
# 9. 마스터 검수 루프 (Human-in-the-Loop) — GP190 §6
# ══════════════════════════════════════════════════════════════════════════════

def render_master_review_loop(
    result: dict,
    session_state=None,
    rag_add_fn=None,
    result_key: str = "scan_pending_result",
) -> bool:
    """
    [GP190 §6] 마스터 검수 루프 (Human-in-the-Loop).

    AI 추출 결과를 마스터가 직접 확인하고 '승인' 또는 '반려' 처리합니다.
    - 승인 시: RAG 지식베이스에 즉시 반영 + session_state gp193_live_context 동기화
    - 반려 시: RAG 인덱싱 차단, 결과 폐기

    Args:
        result:        run_scan_pipeline 또는 global_ingest_hook 반환 dict
        session_state: Streamlit session_state
        rag_add_fn:    RAG 추가 함수 (text, filename, meta) -> int
        result_key:    session_state에 대기 중 결과를 저장할 키

    반환:
        True  = 마스터 승인 완료 (RAG 인덱싱 실행됨)
        False = 대기 중 또는 반려됨
    """
    import streamlit as st

    if not result or not result.get("success"):
        return False

    cls       = result.get("classification", {})
    filename  = result.get("filename", "")
    doc_type  = result.get("doc_type", "")
    text_len  = result.get("text_length", 0)
    kcd       = result.get("kcd", {})
    pii       = result.get("pii_detected", [])
    counts    = result.get("gp192_counts", {})
    is_public = result.get("is_public_asset", False)
    pname     = cls.get("product_name", "미확인")
    insurer   = cls.get("insurer", "미확인")
    n_covers  = counts.get("key_coverages", 0)
    n_terms   = counts.get("terminology", 0)
    n_risks   = counts.get("risk_factors", 0)
    n_highs   = counts.get("product_highlights", 0)
    kcd_ver   = len(kcd.get("verified", []))
    kcd_un    = len(kcd.get("unverified", []))
    kcd_pct   = kcd.get("coverage_pct", 0.0)
    chunks    = result.get("chunks_count", 1)
    pages     = result.get("pages", 1)

    st.markdown(f"""
<div style="background:linear-gradient(135deg,#fefce8,#fffbeb);
  border:2px solid #f59e0b;border-radius:14px;padding:16px 20px;margin:10px 0;">
  <div style="font-size:1.0rem;font-weight:900;color:#92400e;margin-bottom:10px;">
    🛡️ [GP190 §6] 마스터 검수 대기 — AI 분석 결과 승인 필요
  </div>
  <table style="width:100%;font-size:0.82rem;border-collapse:collapse;">
    <tr><td style="color:#64748b;padding:2px 8px 2px 0;width:35%;">📄 파일명</td>
        <td style="font-weight:700;color:#0f172a;">{filename}</td></tr>
    <tr><td style="color:#64748b;padding:2px 8px 2px 0;">🏷️ 문서유형</td>
        <td style="color:#1e40af;">{doc_type} {'(공적자산)' if is_public else '(개인자료)'}</td></tr>
    <tr><td style="color:#64748b;padding:2px 8px 2px 0;">🏢 보험사/상품</td>
        <td style="color:#166534;font-weight:700;">{insurer} / {pname}</td></tr>
    <tr><td style="color:#64748b;padding:2px 8px 2px 0;">📊 분석 수치</td>
        <td>담보 {n_covers}건 · 용어 {n_terms}건 · 특장점 {n_highs}건 · 리스크 {n_risks}건</td></tr>
    <tr><td style="color:#64748b;padding:2px 8px 2px 0;">📋 문서 규모</td>
        <td>{pages}P / {text_len:,}자 {f"/ {chunks}청크 분할" if chunks > 1 else ""}</td></tr>
    <tr><td style="color:#64748b;padding:2px 8px 2px 0;">🔬 KCD-10 검증</td>
        <td>{'✅ '+str(kcd_ver)+'건 확인' if kcd_ver else ''} {'⚠️ '+str(kcd_un)+'건 미확인' if kcd_un else ''} {f'(커버율 {kcd_pct}%)' if kcd_ver+kcd_un > 0 else '해당없음'}</td></tr>
    <tr><td style="color:#64748b;padding:2px 8px 2px 0;">🔒 PII 마스킹</td>
        <td>{'🔴 '+', '.join(pii) if pii else '✅ 감지 없음'}</td></tr>
  </table>
</div>""", unsafe_allow_html=True)

    # ── 승인/반려 버튼 ──────────────────────────────────────────────────────
    col_a, col_r, _ = st.columns([2, 2, 3])
    approved = False
    rejected = False
    with col_a:
        if st.button("✅ 승인 — RAG 반영", key=f"master_approve_{filename[:20]}", type="primary"):
            approved = True
    with col_r:
        if st.button("❌ 반려 — 폐기", key=f"master_reject_{filename[:20]}"):
            rejected = True

    if approved:
        # RAG 인덱싱 실행
        rag_result = index_to_rag(
            session_state.get("_pending_scan_text_" + filename[:20], ""),
            filename, doc_type,
            result.get("classification", {}),
            rag_add_fn,
        )
        result["rag"]            = rag_result
        result["master_approved"] = True

        # GP193 팩트 시트 동기화
        if session_state is not None:
            cls_data = result.get("classification", {})
            ingest_id = result.get("ingest_id", uuid.uuid4().hex[:6])
            fact_sheet = {
                "ingest_id":          ingest_id,
                "source_tab":         result.get("source_tab", "master_review"),
                "filename":           filename,
                "doc_type":           doc_type,
                "ingested_at":        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "product_name":       cls_data.get("product_name", "미확인"),
                "insurer":            cls_data.get("insurer", "미확인"),
                "sale_start_date":    cls_data.get("sale_start_date", "미확인"),
                "sale_end_date":      cls_data.get("sale_end_date", "현재판매중"),
                "key_coverages":      cls_data.get("key_coverages", []),
                "payout_logic":       cls_data.get("payout_logic", ""),
                "coverage_limits":    cls_data.get("coverage_limits", ""),
                "risk_factors":       cls_data.get("risk_factors", []),
                "product_highlights": cls_data.get("product_highlights", []),
                "terminology":        cls_data.get("terminology", []),
                "summary_1st_person": cls_data.get("summary_1st_person", ""),
                "sales_pitch":        cls_data.get("sales_pitch", ""),
                "gcs_uri":            result.get("gcs_uri", ""),
                "json_gcs_uri":       result.get("json_gcs_uri", ""),
                "rag_indexed":        rag_result.get("indexed", False),
                "rag_chunks":         rag_result.get("chunks", 0),
                "text_length":        result.get("text_length", 0),
                "kcd":                result.get("kcd", {}),
                "pii_detected":       result.get("pii_detected", []),
                "master_approved":    True,
            }
            _live = session_state.get("gp193_live_context", [])
            _live.insert(0, fact_sheet)
            session_state["gp193_live_context"] = _live[:20]
            session_state["gp193_latest_fact"]  = fact_sheet

        st.markdown("""
<div style="background:#f0fdf4;border:2px solid #22c55e;border-radius:10px;
  padding:10px 16px;margin:6px 0;font-size:0.88rem;font-weight:700;color:#166534;">
  ✅ 마스터 승인 완료 — RAG 지식베이스 반영 및 전역 동기화 완료
</div>""", unsafe_allow_html=True)
        logger.info(f"[GP190§6] 마스터 승인: {filename}")
        return True

    if rejected:
        st.markdown("""
<div style="background:#fff1f2;border:2px solid #ef4444;border-radius:10px;
  padding:10px 16px;margin:6px 0;font-size:0.88rem;font-weight:700;color:#991b1b;">
  ❌ 반려 처리 — RAG 인덱싱 차단됨. 분석 결과가 폐기되었습니다.
</div>""", unsafe_allow_html=True)
        logger.info(f"[GP190§6] 마스터 반려: {filename}")
        return False

    return False


# ══════════════════════════════════════════════════════════════════════════════
# 10. unified_scan_interface — 통합 스캔 팩토리 (GP195 §1)
# ══════════════════════════════════════════════════════════════════════════════

def unified_scan_interface(
    file_bytes: bytes,
    filename: str,
    source_tab: str = "unknown",
    doc_type: str = "",
    gcs_client=None,
    gcs_bucket: str = "",
    dai_project: str = "",
    dai_location: str = "us",
    dai_processor_id: str = "",
    gcs_credentials=None,
    ai_call_fn=None,
    rag_add_fn=None,
    session_state=None,
    skip_preprocess: bool = False,
    progress_callback=None,
) -> dict:
    """
    [GP195 §1] 통합 스캔 인터페이스 팩토리.

    신규 스캔 모듈이 이 함수를 호출하면 자동으로:
      1. GP190 전체 파이프라인 (Pre-process → 백업 → 추출 → KCD → AI 분류)
      2. GP193 전역 지식 동기화 (session_state["gp193_live_context"] 즉시 업데이트)
      3. Master Approval 대기 상태로 반환 (RAG는 승인 후 별도 반영)

    모든 스캔 모듈은 반드시 이 함수를 통해 파이프라인을 실행해야 합니다.
    직접 run_scan_pipeline 호출 금지 (GP195 §2 강제 상속 원칙).

    반환: run_scan_pipeline 결과 + {source_tab, ingest_id, master_approved: False}
    """
    ingest_id = f"{uuid.uuid4().hex[:6]}_{filename[:20].replace(' ','_')}"
    logger.info(f"[GP195] unified_scan_interface 호출: {ingest_id} (출처: {source_tab})")

    result = run_scan_pipeline(
        file_bytes=file_bytes,
        filename=filename,
        doc_type=doc_type,
        gcs_client=gcs_client,
        gcs_bucket=gcs_bucket,
        dai_project=dai_project,
        dai_location=dai_location,
        dai_processor_id=dai_processor_id,
        gcs_credentials=gcs_credentials,
        ai_call_fn=ai_call_fn,
        rag_add_fn=None,           # RAG는 마스터 승인 후에만 반영
        progress_callback=progress_callback,
        skip_preprocess=skip_preprocess,
    )
    result["source_tab"]  = source_tab
    result["ingest_id"]   = ingest_id
    result["master_approved"] = False

    # ── GP193 §3: 임시 팩트 시트 저장 (master_approved=False 상태) ───────────
    if session_state is not None and result.get("success"):
        cls = result.get("classification", {})
        fact_sheet = {
            "ingest_id":          ingest_id,
            "source_tab":         source_tab,
            "filename":           filename,
            "doc_type":           result.get("doc_type", ""),
            "ingested_at":        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "product_name":       cls.get("product_name", "미확인"),
            "insurer":            cls.get("insurer", "미확인"),
            "sale_start_date":    cls.get("sale_start_date", "미확인"),
            "sale_end_date":      cls.get("sale_end_date", "현재판매중"),
            "key_coverages":      cls.get("key_coverages", []),
            "payout_logic":       cls.get("payout_logic", ""),
            "coverage_limits":    cls.get("coverage_limits", ""),
            "risk_factors":       cls.get("risk_factors", []),
            "product_highlights": cls.get("product_highlights", []),
            "terminology":        cls.get("terminology", []),
            "summary_1st_person": cls.get("summary_1st_person", ""),
            "sales_pitch":        cls.get("sales_pitch", ""),
            "gcs_uri":            result.get("gcs_uri", ""),
            "json_gcs_uri":       result.get("json_gcs_uri", ""),
            "rag_indexed":        False,
            "rag_chunks":         0,
            "text_length":        result.get("text_length", 0),
            "kcd":                result.get("kcd", {}),
            "pii_detected":       result.get("pii_detected", []),
            "master_approved":    False,
        }
        # 임시 팩트 시트를 선두에 삽입 (최대 20건)
        _live = session_state.get("gp193_live_context", [])
        _live.insert(0, fact_sheet)
        session_state["gp193_live_context"] = _live[:20]
        session_state["gp193_latest_fact"]  = fact_sheet
        # 마스터 검수용 텍스트 임시 저장
        session_state[f"_pending_scan_text_{filename[:20]}"] = result.get("_raw_text_for_rag", "")

        logger.info(
            f"[GP195] 전역 동기화 완료 (승인 대기): {filename} | "
            f"{cls.get('product_name','?')} | "
            f"담보 {len(cls.get('key_coverages',[]))}건"
        )

    return result


# ══════════════════════════════════════════════════════════════════════════════
# 11. unified_scan_component — 통합 Streamlit UI 컴포넌트 (GP195 §3)
# ══════════════════════════════════════════════════════════════════════════════

def unified_scan_component(
    label: str = "📎 문서 업로드 (PDF/JPG/PNG)",
    source_tab: str = "unknown",
    doc_type: str = "",
    accept_types: list = None,
    show_master_review: bool = True,
    gcs_client=None,
    gcs_bucket: str = "",
    dai_project: str = "",
    dai_location: str = "us",
    dai_processor_id: str = "",
    gcs_credentials=None,
    ai_call_fn=None,
    rag_add_fn=None,
    session_state=None,
    uploader_key: str = "unified_scan",
) -> dict | None:
    """
    [GP195 §3] 통합 스캔 Streamlit 컴포넌트.

    신규 스캔 모듈에서 이 함수를 한 줄로 호출하면:
      - UI 표준(파스텔 블루 배경 + 붉은색 실선 + 프로그레스 바) 자동 적용
      - unified_scan_interface 파이프라인 자동 실행
      - 결과 UI (render_scan_progress_ui) 자동 렌더링
      - 마스터 검수 루프 (render_master_review_loop) 자동 표시

    GP195 §2: 모든 스캔 업로드 UI는 반드시 이 컴포넌트를 사용해야 합니다.

    반환: unified_scan_interface 결과 dict, 업로드 없으면 None
    """
    import streamlit as st

    if accept_types is None:
        accept_types = ["pdf", "jpg", "jpeg", "png", "bmp", "tiff", "txt"]

    # ── UI 표준 CSS 주입 ────────────────────────────────────────────────────
    st.markdown(f"<style>{get_uploader_css()}</style>", unsafe_allow_html=True)

    uploaded = st.file_uploader(label, type=accept_types, key=uploader_key)
    if uploaded is None:
        return None

    file_bytes = uploaded.read()
    filename   = uploaded.name

    # ── 파스텔 톤 프로그레스 바 표시 ────────────────────────────────────────
    prog_placeholder = st.empty()
    prog_placeholder.markdown(f"""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
  padding:10px 14px;margin:6px 0;font-size:0.82rem;color:#1e40af;">
  🔍 <b>분석 중...</b>
  <div class="gk-scan-progress-bar">
    <div class="gk-scan-progress-fill" style="width:30%;"></div>
  </div>
</div>
<style>{get_uploader_css()}</style>""", unsafe_allow_html=True)

    # 진행률 업데이트용 콜백
    _pct_ref = [0.3]
    def _prog_cb(step: str, pct: float, msg: str):
        _pct_ref[0] = pct
        pct_int = int(pct * 100)
        prog_placeholder.markdown(f"""
<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
  padding:10px 14px;margin:6px 0;font-size:0.82rem;color:#1e40af;">
  🔍 <b>[{step}] {msg}</b>
  <div class="gk-scan-progress-bar">
    <div class="gk-scan-progress-fill" style="width:{pct_int}%;animation:none;opacity:1;"></div>
  </div>
  <span style="font-size:0.72rem;color:#64748b;">{pct_int}% 완료</span>
</div>
<style>{get_uploader_css()}</style>""", unsafe_allow_html=True)

    # ── 통합 파이프라인 실행 ─────────────────────────────────────────────────
    result = unified_scan_interface(
        file_bytes=file_bytes,
        filename=filename,
        source_tab=source_tab,
        doc_type=doc_type,
        gcs_client=gcs_client,
        gcs_bucket=gcs_bucket,
        dai_project=dai_project,
        dai_location=dai_location,
        dai_processor_id=dai_processor_id,
        gcs_credentials=gcs_credentials,
        ai_call_fn=ai_call_fn,
        rag_add_fn=rag_add_fn,
        session_state=session_state,
        progress_callback=_prog_cb,
    )

    # ── 프로그레스 바 완료 표시 ───────────────────────────────────────────────
    prog_placeholder.markdown(f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
  padding:10px 14px;margin:6px 0;font-size:0.82rem;color:#166534;">
  ✅ <b>분석 완료</b> — {filename}
  <div class="gk-scan-progress-bar">
    <div class="gk-scan-progress-fill"
      style="width:100%;animation:none;opacity:1;background:linear-gradient(90deg,#86efac,#4ade80);"></div>
  </div>
</div>
<style>{get_uploader_css()}</style>""", unsafe_allow_html=True)

    # ── 결과 UI 렌더링 ───────────────────────────────────────────────────────
    render_scan_progress_ui(result)

    # ── 마스터 검수 루프 ─────────────────────────────────────────────────────
    if show_master_review:
        render_master_review_loop(
            result,
            session_state=session_state,
            rag_add_fn=rag_add_fn,
            result_key=f"scan_pending_{source_tab}",
        )

    return result


# ══════════════════════════════════════════════════════════════════════════════
# 12. GP195 자동 상속 레지스트리 — 신규 스캔 모듈 강제 등록
# ══════════════════════════════════════════════════════════════════════════════

_GP195_REGISTRY: dict[str, dict] = {}


def gp195_register(
    module_id: str,
    label: str,
    source_tab: str,
    doc_type: str = "",
    accept_types: list = None,
    show_master_review: bool = True,
) -> None:
    """
    [GP195 §2] 신규 스캔 모듈 자동 등록.

    새로운 스캔 탭/기능이 추가될 때 이 함수로 등록하면
    unified_scan_component를 통한 표준 파이프라인이 자동으로 적용됩니다.

    사용법:
        gp195_register(
            module_id="gp96_leaflet",
            label="📄 리플렛 업로드",
            source_tab="gp96_leaflet",
            doc_type="리플렛",
        )
    """
    if accept_types is None:
        accept_types = ["pdf", "jpg", "jpeg", "png"]

    _GP195_REGISTRY[module_id] = {
        "label":               label,
        "source_tab":          source_tab,
        "doc_type":            doc_type,
        "accept_types":        accept_types,
        "show_master_review":  show_master_review,
        "registered_at":       datetime.datetime.now().isoformat(timespec="seconds"),
    }
    logger.info(f"[GP195] 스캔 모듈 등록: {module_id} → source_tab={source_tab}")


def gp195_render(
    module_id: str,
    gcs_client=None,
    gcs_bucket: str = "",
    dai_project: str = "",
    dai_location: str = "us",
    dai_processor_id: str = "",
    gcs_credentials=None,
    ai_call_fn=None,
    rag_add_fn=None,
    session_state=None,
) -> dict | None:
    """
    [GP195 §3] 등록된 스캔 모듈을 unified_scan_component로 자동 렌더링.

    gp195_register()로 등록된 module_id를 넘기면 표준 UI + 파이프라인이
    자동으로 실행됩니다. 신규 스캔 모듈 추가 시 이 두 함수만 호출하면 됩니다.
    """
    cfg = _GP195_REGISTRY.get(module_id)
    if cfg is None:
        import streamlit as st
        st.warning(f"[GP195] 미등록 모듈: {module_id}. gp195_register()를 먼저 호출하세요.")
        return None

    return unified_scan_component(
        label=cfg["label"],
        source_tab=cfg["source_tab"],
        doc_type=cfg["doc_type"],
        accept_types=cfg["accept_types"],
        show_master_review=cfg["show_master_review"],
        gcs_client=gcs_client,
        gcs_bucket=gcs_bucket,
        dai_project=dai_project,
        dai_location=dai_location,
        dai_processor_id=dai_processor_id,
        gcs_credentials=gcs_credentials,
        ai_call_fn=ai_call_fn,
        rag_add_fn=rag_add_fn,
        session_state=session_state,
        uploader_key=f"gp195_{module_id}",
    )


def get_gp195_registry() -> dict:
    """[GP195] 등록된 전체 스캔 모듈 목록 반환."""
    return dict(_GP195_REGISTRY)
