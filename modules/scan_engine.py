# modules/scan_engine.py
# ══════════════════════════════════════════════════════════════════════════════
# [가이딩 프로토콜 제190~191조] 전역 통합 스캔 엔진
#
# GP190 §1 — 기능 단일화: 앱 내 모든 스캔·업로드 모듈이 공유하는 단일 파이프라인
# GP190 §2 — 파일 감지 → GCS 백업 → 텍스트 추출 → AI 분류
# GP190 §3 — 상태 피드백: 진행창, 재시도 로직, 오류 복구 안내
# GP191 §1 — 공적 자산 분류 격리: 약관/설명서 ↔ 개인자료 물리적 분리
# GP191 §2 — 즉시 가공: 저장 후 0.1초 내 핵심 담보·보장한도·면책조항 추출
# GP191 §3 — RAG 실시간 반영 + 1인칭 상담 연동
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import io
import os
import uuid
import logging
import datetime
from typing import Optional

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
_GCS_PUBLIC_PREFIX  = "public_assets"   # 약관·설명서 등 공적 자산
_GCS_PRIVATE_PREFIX = "private_data"    # 개인자료 (RAG 인덱싱 금지)
_GCS_KNOWLEDGE_PREFIX = "knowledge"     # know_pipe 지식베이스 전용


# ══════════════════════════════════════════════════════════════════════════════
# 1. 파일 감지 (Detect)
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
) -> dict:
    """
    GP190 §2 전체 파이프라인:
      파일 감지 → GCS 백업 → 텍스트 추출 → AI 분류 → RAG 인덱싱

    Args:
        file_bytes:        업로드된 파일의 바이트
        filename:          파일명
        doc_type:          문서 유형 힌트 (없으면 자동 감지)
        gcs_client:        google.cloud.storage.Client 인스턴스
        gcs_bucket:        GCS 버킷명
        dai_project:       Document AI 프로젝트 ID
        dai_location:      Document AI 위치 (기본 "us")
        dai_processor_id:  Document AI 프로세서 ID
        gcs_credentials:   서비스 계정 Credentials (Document AI용)
        ai_call_fn:        AI 호출 함수 (prompt) -> str
        rag_add_fn:        RAG 추가 함수 (text, filename, meta) -> int
        progress_callback: (step: str, pct: float, msg: str) -> None

    반환:
        {
          "success": bool,
          "filename": str,
          "doc_type": str,
          "is_public_asset": bool,
          "gcs_uri": str,
          "text_length": int,
          "tables_count": int,
          "extract_engine": str,
          "classification": dict,
          "rag": dict,
          "error": str,
          "pipeline_log": list[str],
          "summary_1st_person": str,
        }
    """
    log  = []
    err  = ""

    def _progress(step: str, pct: float, msg: str):
        log.append(f"[{step}] {msg}")
        if progress_callback:
            try:
                progress_callback(step, pct, msg)
            except Exception:
                pass

    # ── Step 1: 파일 감지 ─────────────────────────────────────────────────
    _progress("P1", 0.1, f"파일 감지: {filename}")
    file_info = detect_file_type(filename)
    if not file_info["supported"]:
        err = f"지원하지 않는 파일 형식: .{file_info['ext']}"
        _progress("P1", 0.1, f"오류: {err}")
        return _fail_result(filename, doc_type, err, log)

    doc_type = classify_doc_type(filename, doc_type)
    _progress("P1", 0.2, f"문서 유형 감지: {doc_type}")

    # ── Step 2: GCS 백업 ──────────────────────────────────────────────────
    gcs_uri = f"local://{filename}"
    is_public_asset = doc_type in PUBLIC_ASSET_TYPES

    if gcs_client and gcs_bucket:
        _progress("P2", 0.3, "GCS 즉시 격리 백업 중...")
        gcs_result = backup_to_gcs(file_bytes, filename, doc_type, gcs_client, gcs_bucket)
        gcs_uri        = gcs_result["gcs_uri"]
        is_public_asset = gcs_result["is_public_asset"]
        if gcs_result["success"]:
            _progress("P2", 0.45, f"GCS 백업 완료: {gcs_uri}")
        else:
            _progress("P2", 0.45, f"GCS 백업 실패 (로컬 폴백): {gcs_result['error']}")
    else:
        _progress("P2", 0.45, "GCS 클라이언트 미연결 — 로컬 처리 모드")

    # ── Step 3: 텍스트 추출 ───────────────────────────────────────────────
    _progress("P3", 0.55, "AI 마스터가 정밀 분석 중입니다...")
    extract_result = extract_text(
        file_bytes, filename, gcs_uri,
        dai_project, dai_location, dai_processor_id, gcs_credentials,
    )
    text          = extract_result.get("text", "")
    tables        = extract_result.get("tables", [])
    extract_engine = extract_result.get("engine", "unknown")
    _progress("P3", 0.70, f"텍스트 추출 완료: {len(text)}자, {len(tables)}표 ({extract_engine})")

    # ── Step 4: GP192 정밀 AI 추출 (공적 자산만) ────────────────────────
    classification: dict = {
        "doc_class": "기타", "insurer": "미확인", "product_name": "미확인",
        "sale_start_date": "미확인", "sale_end_date": "현재판매중",
        "key_coverages": [], "payout_logic": "", "coverage_limits": "",
        "risk_factors": [], "exclusions": "", "product_highlights": [],
        "terminology": [], "issue_date": "미확인",
        "summary_1st_person": "", "sales_pitch": "",
    }
    if is_public_asset and text and ai_call_fn:
        _progress("P4", 0.78, "GP192 Core-8 정밀 추출 중 — 용어·지급기준·판매주기·특장점...")
        classification = classify_document(text, ai_call_fn)
        n_terms    = len(classification.get("terminology", []))
        n_covers   = len(classification.get("key_coverages", []))
        n_highs    = len(classification.get("product_highlights", []))
        _progress("P4", 0.88,
            f"추출 완료: {classification.get('doc_class','?')} / "
            f"{classification.get('product_name','?')} | "
            f"담보 {n_covers}건 · 용어 {n_terms}건 · 특장점 {n_highs}건"
        )
    else:
        _progress("P4", 0.88, "AI 정밀 추출 생략 (개인자료 또는 AI 미연결)")

    # ── Step 4b: GP192 정밀 JSON → GCS 저장 ──────────────────────────────
    json_gcs_uri = ""
    if is_public_asset and gcs_client and gcs_bucket and classification.get("product_name") != "미확인":
        _progress("P4b", 0.91, "GP192 정밀 데이터 JSON → GCS 저장 중...")
        _json_result = save_precision_json_to_gcs(
            classification, filename, doc_type, gcs_client, gcs_bucket, gcs_uri
        )
        json_gcs_uri = _json_result.get("json_uri", "")
        if _json_result["success"]:
            _progress("P4b", 0.93, f"JSON 저장 완료: {json_gcs_uri}")
        else:
            _progress("P4b", 0.93, f"JSON 저장 실패: {_json_result['error']}")

    # ── Step 5: RAG 인덱싱 ────────────────────────────────────────────────
    _progress("P5", 0.95, "RAG 지식베이스 등록 중...")
    rag_result = index_to_rag(text, filename, doc_type, classification, rag_add_fn)
    if rag_result["indexed"]:
        _progress("P5", 1.0, f"RAG 등록 완료: {rag_result['chunks']}청크")
    else:
        _progress("P5", 1.0, f"RAG 등록 생략: {rag_result['skipped_reason']}")

    return {
        "success":           True,
        "filename":          filename,
        "doc_type":          doc_type,
        "is_public_asset":   is_public_asset,
        "gcs_uri":           gcs_uri,
        "json_gcs_uri":      json_gcs_uri,
        "text_length":       len(text),
        "tables_count":      len(tables),
        "extract_engine":    extract_engine,
        "classification":    classification,
        "rag":               rag_result,
        "error":             "",
        "pipeline_log":      log,
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
        "classification": {}, "rag": {"indexed": False, "doc_id": -1, "chunks": 0, "skipped_reason": error},
        "error": error, "pipeline_log": log, "summary_1st_person": "",
        "sales_pitch": "", "gp192_counts": {"terminology": 0, "key_coverages": 0, "product_highlights": 0, "risk_factors": 0},
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
    GP190 §3 — 전역 file_uploader 시각화 CSS.
    모든 Streamlit 업로드 박스에 점선 외곽선 + 호버 파스텔블루 적용.
    """
    return """
/* §GP190 — 전역 파일 업로드 박스 시각화 (점선 외곽선 + Drag & Drop 강조) */
[data-testid="stFileUploader"] > section {
    border: 2.5px dashed #0284c7 !important;
    border-radius: 12px !important;
    background: #f0f9ff !important;
    transition: background 0.25s ease, border-color 0.25s ease !important;
    padding: 10px 14px !important;
}
[data-testid="stFileUploader"] > section:hover {
    background: #bae6fd !important;
    border-color: #0369a1 !important;
    box-shadow: 0 0 0 3px rgba(2,132,199,0.18) !important;
}
[data-testid="stFileUploader"] > section > div {
    color: #0369a1 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #0369a1 !important;
    font-weight: 700 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span {
    font-size: 0.85rem !important;
}
"""
