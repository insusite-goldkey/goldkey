'use strict';
/**
 * functions/index.js — Goldkey AI Masters 2026
 * GCP Cloud Functions Gen2: verifyOTP (TOTP RFC 6238)
 * GCP Project ID: gen-lang-client-0777682955
 *
 * ⚠️  이 파일은 백엔드 전용입니다. React Native 앱 코드와 절대 혼용 금지.
 *
 * 배포 명령 (crm_app/functions/ 디렉터리에서 실행):
 *   gcloud functions deploy verifyOTP \
 *     --gen2 \
 *     --runtime=nodejs22 \
 *     --region=asia-northeast3 \
 *     --trigger-http \
 *     --allow-unauthenticated \
 *     --entry-point=verifyOTP \
 *     --project=gen-lang-client-0777682955 \
 *     --set-env-vars GCP_PROJECT=gen-lang-client-0777682955
 *
 * Firestore 경로: users/{personId}/secrets/totp → { secret: "BASE32..." }
 * 시도 횟수 제한:  otp_attempts/{personId}       → { count: N, reset_at: ISO }
 */

const functions   = require('@google-cloud/functions-framework');
const { totp }    = require('otplib');
const admin       = require('firebase-admin');
const crypto      = require('crypto');

// ── 상수 ──────────────────────────────────────────────────────────────────
const GCP_PROJECT   = process.env.GCP_PROJECT || 'gen-lang-client-0777682955';
const APP_SALT      = 'GK-AI-2026-TOTP-SALT';
const MAX_ATTEMPTS  = 5;
const WINDOW_STEP   = 4;   // ±2분 (총 9토큰 허용 — 폰 시계 오차 대응)
const ATTEMPT_TTL_MS = 10 * 60 * 1000;  // 10분 후 시도 횟수 리셋

// ── Firebase Admin 초기화 (Cloud 환경: ADC 자동 인증) ──────────────────────
if (!admin.apps.length) {
  admin.initializeApp({ projectId: GCP_PROJECT });
}
const db = admin.firestore();

// ── CORS 헤더 ──────────────────────────────────────────────────────────────
const CORS_HEADERS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// ── TOTP 전역 옵션 설정 (RFC 6238 표준) ────────────────────────────────────
totp.options = {
  step:   30,          // 30초 갱신 주기
  digits: 6,           // 6자리
  window: WINDOW_STEP, // ±1 윈도우 (±30초)
  algorithm: 'sha1',   // RFC 6238 기본 알고리즘
};

/**
 * person_id 기반 결정론적 TOTP Secret 파생 (DB secret 없을 때 fallback).
 * @param {string} personId
 * @returns {string} Base32 encoded secret
 */
function deriveSecret(personId) {
  const raw = crypto
    .createHmac('sha256', APP_SALT)
    .update(personId)
    .digest();
  return raw.slice(0, 20).toString('base64').replace(/[^A-Z2-7]/gi, 'A')
    .toUpperCase().slice(0, 32);
}

/**
 * Firestore에서 personId의 TOTP secret 조회.
 * users/{personId}/secrets/totp 문서의 secret 필드 반환.
 * 없으면 파생값(fallback) 반환.
 * @param {string} personId
 * @returns {Promise<string>}
 */
async function getSecret(personId) {
  try {
    const snap = await db
      .collection('users').doc(personId)
      .collection('secrets').doc('totp')
      .get();
    if (snap.exists) {
      const data = snap.data();
      if (data && data.secret) return data.secret;
    }
  } catch (_) { /* Firestore 접근 실패 시 fallback */ }
  return deriveSecret(personId);
}

/**
 * 시도 횟수 조회 + 증가. 초과 시 null 반환.
 * @param {string} personId
 * @returns {Promise<{count:number}|null>} null = 초과
 */
async function checkAndIncrAttempts(personId) {
  const ref = db.collection('otp_attempts').doc(personId);
  return db.runTransaction(async (tx) => {
    const snap = await tx.get(ref);
    const now  = Date.now();
    let count  = 0;

    if (snap.exists) {
      const d = snap.data();
      const resetAt = d.reset_at ? new Date(d.reset_at).getTime() : 0;
      count = (now < resetAt) ? (d.count || 0) : 0;
    }

    if (count >= MAX_ATTEMPTS) return null;

    tx.set(ref, {
      count:    count + 1,
      reset_at: new Date(now + ATTEMPT_TTL_MS).toISOString(),
    });
    return { count: count + 1 };
  });
}

/**
 * 시도 횟수 초기화 (인증 성공 시 호출).
 * @param {string} personId
 */
async function resetAttempts(personId) {
  await db.collection('otp_attempts').doc(personId).set({ count: 0 });
}

// ── Cloud Function 진입점 ──────────────────────────────────────────────────
functions.http('verifyOTP', async (req, res) => {
  // CORS 프리플라이트
  res.set(CORS_HEADERS);
  if (req.method === 'OPTIONS') {
    return res.status(204).send('');
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ valid: false, message: 'POST only' });
  }

  const body      = req.body || {};
  const personId  = (body.person_id || '').trim();
  const token     = (body.token     || '').trim();

  // ── 입력 유효성 검사 ──────────────────────────────────────────────────
  if (!personId || !token) {
    return res.status(400).json({
      valid:   false,
      message: 'person_id와 token은 필수입니다.',
    });
  }
  if (!/^\d{6}$/.test(token)) {
    return res.status(400).json({
      valid:   false,
      message: 'token은 6자리 숫자여야 합니다.',
    });
  }

  // ── 시도 횟수 확인 ────────────────────────────────────────────────────
  let attemptResult;
  try {
    attemptResult = await checkAndIncrAttempts(personId);
  } catch (e) {
    console.error('Firestore attempt check error:', e);
    attemptResult = { count: 1 };  // Firestore 오류 시 검증은 계속
  }

  if (attemptResult === null) {
    return res.status(429).json({
      valid:   false,
      message: `시도 횟수(${MAX_ATTEMPTS}회) 초과. 10분 후 재시도하세요.`,
    });
  }

  // ── TOTP 검증 ─────────────────────────────────────────────────────────
  const secret = await getSecret(personId);
  console.log(`[verifyOTP] personId=${personId} secret=${secret} token=${token}`);
  const valid  = totp.check(token, secret);

  if (valid) {
    try { await resetAttempts(personId); } catch (_) {}
    return res.status(200).json({
      valid:   true,
      message: '인증 성공',
    });
  } else {
    const left = MAX_ATTEMPTS - (attemptResult.count);
    return res.status(401).json({
      valid:   false,
      message: `코드 불일치. 남은 시도: ${left < 0 ? 0 : left}회`,
    });
  }
});
