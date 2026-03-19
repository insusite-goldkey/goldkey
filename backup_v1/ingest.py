"""
GoldKey AI — 데이터 인제스션 파이프라인 (ingest.py)
======================================================
사용법:
    python ingest.py --file 삼성화재_약관.pdf --insurer 삼성화재 --category 보험약관
    python ingest.py --dir ./docs --insurer KB손해보험
    python ingest.py --url https://www.ins.co.kr/terms/약관.pdf --insurer 현대해상
    python ingest.py --stats

파이프라인:
    PDF/TXT/DOCX → 텍스트 추출 → AI 자동분류 → 청크 분할(슬라이딩 윈도우)
    → 메타데이터 태깅 → Supabase(rag_sources / rag_docs) 저장
"""

import os
import sys
import io
import re
import html
import json
import argparse
import logging
import datetime
import urllib.request
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gk_ingest")

# ── 환경변수 로드 (.env 지원) ──────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

VALID_CATEGORIES = ["보험약관", "공문서", "상담자료", "판례", "보도자료", "세무자료", "기타"]
CHUNK_SIZE = int(os.environ.get("GK_CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.environ.get("GK_CHUNK_OVERLAP", "128"))


# ══════════════════════════════════════════════════════════════════════════════
# 1. 텍스트 추출
# ══════════════════════════════════════════════════════════════════════════════

def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    fn = filename.lower()
    text = ""
    if fn.endswith(".pdf"):
        text = _extract_pdf(file_bytes)
    elif fn.endswith(".txt"):
        text = file_bytes.decode("utf-8", errors="replace")
    elif fn.endswith(".docx"):
        text = _extract_docx(file_bytes)
    else:
        # 알 수 없는 형식 → UTF-8 plain text 시도
        try:
            text = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass
    return text.strip()


def _extract_pdf(file_bytes: bytes) -> str:
    # 1차: pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = [p.extract_text() or "" for p in reader.pages]
        text = "\n".join(pages)
        if len(text.strip()) > 100:
            return text
    except Exception:
        pass
    # 2차: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n".join(pg.extract_text() or "" for pg in pdf.pages)
        if len(text.strip()) > 100:
            return text
    except Exception:
        pass
    # 3차: pymupdf
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception:
        pass
    return ""


def _extract_docx(file_bytes: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_text_from_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 GoldKey-Ingest/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    if url.lower().endswith(".pdf"):
        return _extract_pdf(raw)
    # HTML 파싱
    txt = raw.decode("utf-8", errors="replace")
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = html.unescape(txt)
    txt = re.sub(r'\s+', ' ', txt)
    return txt.strip()


# ══════════════════════════════════════════════════════════════════════════════
# 2. AI 자동 분류
# ══════════════════════════════════════════════════════════════════════════════

def ai_classify(text: str) -> str:
    if not GEMINI_API_KEY:
        return "기타"
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            "다음 문서의 분류를 정확히 하나만 선택하세요.\n"
            f"선택지: {', '.join(VALID_CATEGORIES)}\n"
            f"문서 앞부분:\n{text[:600]}\n\n분류 (단어 하나만):"
        )
        resp = model.generate_content(prompt)
        result = (resp.text or "기타").strip().split()[0]
        return result if result in VALID_CATEGORIES else "기타"
    except Exception as e:
        logger.warning(f"AI 분류 실패: {e}")
        return "기타"


# ══════════════════════════════════════════════════════════════════════════════
# 3. 청크 분할 (슬라이딩 윈도우)
# ══════════════════════════════════════════════════════════════════════════════

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# 4. Supabase 저장
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return None


def save_to_supabase(
    chunks: list[str],
    filename: str,
    category: str,
    insurer: str = "",
    doc_date: str = "",
    summary: str = "",
) -> dict:
    sb = _get_sb()
    if not sb:
        return {"success": False, "message": "Supabase 미연결 — SUPABASE_URL/SUPABASE_KEY 환경변수를 확인하세요."}

    now = datetime.datetime.now().isoformat()
    # rag_sources 레코드 생성
    src_row = {
        "filename": filename,
        "category": category,
        "insurer": insurer,
        "doc_date": doc_date,
        "chunk_cnt": len(chunks),
        "summary": summary or f"인제스션: {filename}",
        "processed": True,
        "uploaded": now,
        "error_flag": None,
    }
    try:
        src_res = sb.table("rag_sources").insert(src_row).execute()
        src_id = src_res.data[0]["id"] if src_res.data else None
    except Exception as e:
        return {"success": False, "message": f"rag_sources 저장 실패: {e}"}

    # rag_docs 청크 일괄 저장
    doc_rows = [
        {
            "src_id": src_id,
            "chunk": chunk,
            "filename": filename,
            "category": category,
            "insurer": insurer,
            "doc_date": doc_date,
            "uploaded": now,
        }
        for chunk in chunks
    ]
    try:
        # Supabase 최대 1000행 제한 — 배치 처리
        batch_size = 200
        for start in range(0, len(doc_rows), batch_size):
            sb.table("rag_docs").insert(doc_rows[start : start + batch_size]).execute()
    except Exception as e:
        return {"success": False, "message": f"rag_docs 청크 저장 실패: {e}"}

    return {
        "success": True,
        "src_id": src_id,
        "chunks_indexed": len(chunks),
        "message": f"✅ {filename} — {len(chunks)}청크 Supabase 저장 완료",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. 통합 파이프라인
# ══════════════════════════════════════════════════════════════════════════════

def ingest_file(
    file_path: str,
    insurer: str = "",
    category: str = "AI 자동분류",
    doc_date: str = "",
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "message": f"파일 없음: {file_path}"}

    logger.info(f"[인제스션 시작] {path.name}")
    file_bytes = path.read_bytes()
    text = extract_text_from_bytes(file_bytes, path.name)
    if len(text) < 50:
        return {"success": False, "message": f"텍스트 추출 실패 (추출 결과 {len(text)}자): {path.name}"}

    logger.info(f"  텍스트 추출 완료: {len(text)}자")

    # AI 분류
    cat = category
    if cat == "AI 자동분류":
        cat = ai_classify(text)
        logger.info(f"  AI 분류 결과: {cat}")
    else:
        logger.info(f"  수동 분류: {cat}")

    # 청크 분할
    chunks = split_into_chunks(text, chunk_size, chunk_overlap)
    logger.info(f"  청크 분할: {len(chunks)}개 (size={chunk_size}, overlap={chunk_overlap})")

    # 저장
    result = save_to_supabase(chunks, path.name, cat, insurer, doc_date)
    if result["success"]:
        logger.info(f"  {result['message']}")
    else:
        logger.error(f"  저장 실패: {result['message']}")
    return result


def ingest_url(
    url: str,
    insurer: str = "",
    category: str = "보험약관",
    doc_date: str = "",
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> dict:
    logger.info(f"[URL 인제스션] {url}")
    try:
        text = extract_text_from_url(url)
    except Exception as e:
        return {"success": False, "message": f"URL 접속 실패: {e}"}

    if len(text) < 50:
        return {"success": False, "message": f"텍스트 추출 실패: {url}"}

    logger.info(f"  텍스트 추출: {len(text)}자")

    cat = category
    if cat == "AI 자동분류":
        cat = ai_classify(text)
        logger.info(f"  AI 분류: {cat}")

    fname = url.split("/")[-1].split("?")[0] or "url_doc"
    chunks = split_into_chunks(text, chunk_size, chunk_overlap)
    logger.info(f"  청크: {len(chunks)}개")

    result = save_to_supabase(chunks, fname, cat, insurer, doc_date)
    if result["success"]:
        logger.info(f"  {result['message']}")
    else:
        logger.error(f"  실패: {result['message']}")
    return result


def ingest_directory(
    dir_path: str,
    insurer: str = "",
    category: str = "AI 자동분류",
    doc_date: str = "",
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    extensions: tuple = (".pdf", ".txt", ".docx"),
) -> dict:
    p = Path(dir_path)
    files = [f for f in p.iterdir() if f.suffix.lower() in extensions]
    if not files:
        return {"success": False, "message": f"디렉토리에 처리할 파일 없음: {dir_path}"}

    ok, fail = 0, 0
    for f in files:
        r = ingest_file(str(f), insurer, category, doc_date, chunk_size, chunk_overlap)
        if r["success"]:
            ok += 1
        else:
            fail += 1
            logger.warning(f"  실패: {f.name} — {r['message']}")

    return {
        "success": ok > 0,
        "ok": ok, "fail": fail,
        "message": f"디렉토리 인제스션 완료: {ok}건 성공 / {fail}건 실패",
    }


def print_stats():
    sb = _get_sb()
    if not sb:
        print("❌ Supabase 미연결")
        return
    try:
        src_cnt = sb.table("rag_sources").select("id", count="exact").execute().count or 0
        doc_cnt = sb.table("rag_docs").select("id", count="exact").execute().count or 0
        pending = sb.table("rag_sources").select("id", count="exact").eq("processed", False).execute().count or 0
        print(f"\n📊 RAG 버킷 현황")
        print(f"  소스 문서:  {src_cnt}건")
        print(f"  총 청크:    {doc_cnt}개")
        print(f"  미처리 대기: {pending}건")
        rows = sb.table("rag_sources").select("category").execute().data or []
        cat_map = {}
        for r in rows:
            c = r.get("category", "기타")
            cat_map[c] = cat_map.get(c, 0) + 1
        print(f"\n  카테고리별:")
        for c, n in sorted(cat_map.items(), key=lambda x: -x[1]):
            print(f"    {c}: {n}건")
    except Exception as e:
        print(f"❌ 통계 조회 실패: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 6. CLI 진입점
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="GoldKey RAG 데이터 인제스션 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python ingest.py --file 삼성화재_약관.pdf --insurer 삼성화재 --category 보험약관
  python ingest.py --dir ./docs --insurer KB손해보험
  python ingest.py --url https://www.ins.co.kr/terms/약관.pdf
  python ingest.py --stats
        """,
    )
    parser.add_argument("--file",     help="단일 파일 경로 (PDF/TXT/DOCX)")
    parser.add_argument("--dir",      help="디렉토리 경로 (전체 파일 일괄 처리)")
    parser.add_argument("--url",      help="URL (약관 링크 직접 인제스션)")
    parser.add_argument("--insurer",  default="", help="보험사/기관명")
    parser.add_argument("--category", default="AI 자동분류",
                        choices=["AI 자동분류"] + VALID_CATEGORIES,
                        help="문서 분류 (기본: AI 자동분류)")
    parser.add_argument("--date",     default="", help="문서 날짜 (예: 2024-01)")
    parser.add_argument("--chunk-size",    type=int, default=CHUNK_SIZE,   help=f"청크 크기 (기본: {CHUNK_SIZE})")
    parser.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP, help=f"청크 중첩 (기본: {CHUNK_OVERLAP})")
    parser.add_argument("--stats",    action="store_true", help="RAG DB 현황 출력")
    parser.add_argument("--output",   help="결과 JSON 저장 경로 (선택)")

    args = parser.parse_args()

    if args.stats:
        print_stats()
        return

    result = None
    if args.file:
        result = ingest_file(args.file, args.insurer, args.category, args.date,
                             args.chunk_size, args.chunk_overlap)
    elif args.dir:
        result = ingest_directory(args.dir, args.insurer, args.category, args.date,
                                  args.chunk_size, args.chunk_overlap)
    elif args.url:
        result = ingest_url(args.url, args.insurer, args.category, args.date,
                            args.chunk_size, args.chunk_overlap)
    else:
        parser.print_help()
        sys.exit(0)

    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.output:
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info(f"결과 저장: {args.output}")
        sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
