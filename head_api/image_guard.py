"""HEAD Image Guard: 문서 이미지 지능형 전처리 엔진."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import cv2
import numpy as np


@dataclass
class ImageGuardResult:
    ok: bool
    reason: str
    quality_score: float
    processed_b64: str
    meta: dict
    gcs_uri: str


def _read_img(img_bytes: bytes) -> np.ndarray | None:
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def _auto_crop_perspective(img: np.ndarray) -> tuple[np.ndarray, bool]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edge = cv2.Canny(blur, 60, 180)
    cnts, _ = cv2.findContours(edge, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return img, False
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
    target = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            target = approx.reshape(4, 2)
            break
    if target is None:
        return img, False

    rect = _order_points(target)
    (tl, tr, br, bl) = rect
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_w = max(int(width_a), int(width_b))
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_h = max(int(height_a), int(height_b))
    if max_w < 100 or max_h < 100:
        return img, False
    dst = np.array([[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]], dtype="float32")
    m = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, m, (max_w, max_h))
    return warped, True


def _illumination_normalize(gray: np.ndarray) -> np.ndarray:
    bg = cv2.medianBlur(gray, 31)
    norm = cv2.divide(gray, bg, scale=255)
    return cv2.equalizeHist(norm)


def _adaptive_binarize(gray_norm: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(
        gray_norm,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        12,
    )


def _preserve_strokes(gray_norm: np.ndarray, bin_img: np.ndarray) -> np.ndarray:
    edge = cv2.Canny(gray_norm, 50, 150)
    edge = cv2.dilate(edge, np.ones((2, 2), np.uint8), iterations=1)
    out = bin_img.copy()
    out[edge > 0] = 0
    return out


def _quality_score(gray: np.ndarray) -> tuple[float, dict]:
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    bright = float(np.mean(gray))
    contrast = float(np.std(gray))
    score = min(100.0, (lap_var / 6.0) + (contrast * 0.8) - abs(128.0 - bright) * 0.2 + 20.0)
    return max(0.0, score), {"lap_var": lap_var, "brightness": bright, "contrast": contrast}


def _to_b64(img: np.ndarray) -> str:
    ok, enc = cv2.imencode(".png", img)
    if not ok:
        return ""
    return base64.b64encode(enc.tobytes()).decode()


def _upload_gcs(raw_bytes: bytes, proc_bytes: bytes, agent_id: str, person_id: str) -> str:
    bucket_name = os.environ.get("GCS_BUCKET_NAME", "").strip()
    if not bucket_name:
        return ""
    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        rid = uuid4().hex[:10]
        base = f"scan_guard/{agent_id}/{person_id}/{ts}_{rid}"
        b1 = bucket.blob(f"{base}_raw.jpg")
        b1.upload_from_string(raw_bytes, content_type="image/jpeg")
        b2 = bucket.blob(f"{base}_processed.png")
        b2.upload_from_string(proc_bytes, content_type="image/png")
        return f"gs://{bucket_name}/{base}_processed.png"
    except Exception:
        return ""


def run_image_guard(img_bytes: bytes, agent_id: str, person_id: str) -> ImageGuardResult:
    img = _read_img(img_bytes)
    if img is None:
        return ImageGuardResult(False, "invalid_image", 0.0, "", {}, "")

    cropped, crop_ok = _auto_crop_perspective(img)
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    norm = _illumination_normalize(gray)
    bin_img = _adaptive_binarize(norm)
    guarded = _preserve_strokes(norm, bin_img)

    score, details = _quality_score(norm)
    if score < 35.0:
        return ImageGuardResult(
            ok=False,
            reason="low_quality",
            quality_score=score,
            processed_b64="",
            meta={"auto_crop": crop_ok, **details},
            gcs_uri="",
        )

    ok, enc = cv2.imencode(".png", guarded)
    if not ok:
        return ImageGuardResult(False, "encode_failed", score, "", {"auto_crop": crop_ok, **details}, "")
    proc_bytes = enc.tobytes()
    gcs_uri = _upload_gcs(img_bytes, proc_bytes, agent_id, person_id)
    return ImageGuardResult(
        ok=True,
        reason="ready",
        quality_score=score,
        processed_b64=base64.b64encode(proc_bytes).decode(),
        meta={"auto_crop": crop_ok, **details},
        gcs_uri=gcs_uri,
    )
