"""
GCS 업로드 모듈
google-cloud-storage 라이브러리를 사용하여 파일을 GCS 버킷에 업로드합니다.
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from google.cloud import storage
from google.oauth2 import service_account


def _get_gcs_client() -> storage.Client:
    """GCS 클라이언트 생성 — 서비스 계정 키 또는 환경변수 ADC 사용"""
    key_path = os.environ.get("GCS_KEY_PATH", "")
    if key_path and os.path.exists(key_path):
        credentials = service_account.Credentials.from_service_account_file(key_path)
        return storage.Client(credentials=credentials)
    # Application Default Credentials (Cloud Run / GCE 환경에서 자동 인증)
    return storage.Client()


def upload_to_gcs(
    file_bytes: bytes,
    original_filename: str,
    bucket_name: Optional[str] = None,
    destination_folder: str = "policies",
) -> dict:
    """
    파일을 GCS 버킷에 업로드합니다.

    Returns:
        {
            "success": bool,
            "gcs_uri": str,          # gs://bucket/path/file.pdf
            "public_url": str,       # https://storage.googleapis.com/...
            "blob_name": str,        # 버킷 내 경로
            "size_bytes": int,
        }
    """
    bucket_name = bucket_name or os.environ.get("GCS_BUCKET", "goldkey-policy-rag")

    # 중복 방지: 날짜 + UUID prefix 붙이기
    date_prefix = datetime.now().strftime("%Y/%m/%d")
    uid = uuid.uuid4().hex[:8]
    safe_name = original_filename.replace(" ", "_")
    blob_name = f"{destination_folder}/{date_prefix}/{uid}_{safe_name}"

    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    content_type = "application/pdf" if safe_name.endswith(".pdf") else "application/octet-stream"
    blob.upload_from_string(file_bytes, content_type=content_type)

    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    return {
        "success": True,
        "gcs_uri": gcs_uri,
        "public_url": public_url,
        "blob_name": blob_name,
        "size_bytes": len(file_bytes),
    }
