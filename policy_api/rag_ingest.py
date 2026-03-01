"""
RAG 인제스천 파이프라인 뼈대
GCS 업로드 완료 후 벡터 DB로 문서를 주입하는 파이프라인입니다.

현재 구현: 로깅 + 주석 처리된 LangChain 파이프라인 뼈대
실제 사용 시: 아래 TODO 주석을 따라 구현하세요.
"""

import os
import logging

logger = logging.getLogger("rag_ingest")


def ingest_policy_document(
    gcs_uri: str,
    blob_name: str,
    original_filename: str,
    file_bytes: bytes,
) -> dict:
    """
    GCS에 업로드된 약관 문서를 RAG 벡터 DB에 인제스트합니다.

    Args:
        gcs_uri: gs://bucket/path/file.pdf
        blob_name: 버킷 내 경로
        original_filename: 원본 파일명
        file_bytes: 파일 바이트 (직접 파싱용)

    Returns:
        {"success": bool, "chunks_indexed": int, "message": str}
    """

    # ── [뼈대 1] pdfplumber / PyMuPDF로 텍스트 추출 ──────────────────────
    # import pdfplumber
    # import io
    # with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
    #     full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # ── [뼈대 2] LangChain 텍스트 분할 ───────────────────────────────────
    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=500,
    #     chunk_overlap=50,
    #     separators=["\n\n", "\n", "。", ".", " "],
    # )
    # chunks = splitter.split_text(full_text)

    # ── [뼈대 3] Gemini / OpenAI 임베딩 생성 ─────────────────────────────
    # from langchain_google_genai import GoogleGenerativeAIEmbeddings
    # embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    # ── [뼈대 4] Supabase pgvector 또는 FAISS에 저장 ─────────────────────
    # from langchain_community.vectorstores import SupabaseVectorStore
    # from supabase import create_client
    # sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    # vector_store = SupabaseVectorStore.from_texts(
    #     texts=chunks,
    #     embedding=embeddings,
    #     client=sb,
    #     table_name="rag_docs",
    #     query_name="match_documents",
    #     chunk_size=500,
    # )

    # ── [뼈대 5] 기존 app.py의 _rag_db_add_document 직접 호출 (현재 시스템 연동) ──
    # 현재 goldkey 앱은 SQLite + Supabase 기반 RAG를 사용합니다.
    # FastAPI에서 직접 호출하려면 아래처럼 공통 DB 함수를 분리된 모듈로 이전해야 합니다.
    #
    # from rag_shared import add_document_to_db
    # add_document_to_db(full_text, original_filename, meta={
    #     "category": "보험약관",
    #     "insurer": "",
    #     "doc_date": "",
    #     "summary": f"GCS 자동 수집: {original_filename}",
    # })

    logger.info(f"[RAG 인제스트 대기] {original_filename} → {gcs_uri}")

    # TODO: 위 뼈대 중 사용할 구현체를 선택하여 주석 해제하세요.
    return {
        "success": True,
        "chunks_indexed": 0,
        "message": f"GCS 업로드 완료. RAG 인제스트 파이프라인을 rag_ingest.py에서 구현하세요. ({gcs_uri})",
    }
