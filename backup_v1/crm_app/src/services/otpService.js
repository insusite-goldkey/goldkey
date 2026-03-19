'use strict';
/**
 * src/services/otpService.js — Goldkey AI Masters 2026
 * verifyOTP Cloud Functions 통신 전용 모듈.
 * 프론트엔드(React Native)와 백엔드(functions/) 사이의 유일한 통신 레이어.
 *
 * ⚠️  이 파일 외부에서 verifyOTP URL을 직접 호출하지 마세요.
 */

const VERIFY_OTP_URL =
  'https://asia-northeast3-gen-lang-client-0777682955.cloudfunctions.net/verifyOTP';

const REQUEST_TIMEOUT_MS = 10000; // 10초

/**
 * 서버 에러 응답에서 message 필드를 파싱.
 * HTTP 4xx/5xx 응답 body가 JSON { valid, message } 형태임을 보장.
 * @param {Response} response - fetch Response 객체
 * @returns {Promise<string>} 사람이 읽을 수 있는 에러 메시지
 */
async function _parseErrorMessage(response) {
  try {
    const data = await response.json();
    return data?.message || `서버 오류 (HTTP ${response.status})`;
  } catch (_) {
    return `서버 오류 (HTTP ${response.status})`;
  }
}

/**
 * TOTP 코드를 서버에서 검증.
 *
 * @param {string} personId  - Supabase gk_people.id (UUID)
 * @param {string} token     - 사용자가 입력한 6자리 TOTP 코드
 * @returns {Promise<{ valid: boolean, message: string }>}
 *
 * 절대 throw하지 않음 — 모든 실패는 { valid: false, message } 로 반환.
 */
export async function verifyOtp(personId, token) {
  // ── 클라이언트 사전 검증 ─────────────────────────────────
  if (!personId || typeof personId !== 'string') {
    return { valid: false, message: '로그인 정보가 없습니다. 다시 검색해 주세요.' };
  }
  if (!token || !/^\d{6}$/.test(token.trim())) {
    return { valid: false, message: '6자리 숫자를 입력해 주세요.' };
  }

  // ── AbortController (타임아웃) ───────────────────────────
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(VERIFY_OTP_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        person_id: personId.trim(),
        token:     token.trim(),
      }),
      signal: controller.signal,
    });

    clearTimeout(timer);

    // ── 성공 (200) ──────────────────────────────────────────
    if (response.ok) {
      const data = await response.json();
      return { valid: true, message: data?.message || '인증 성공' };
    }

    // ── 클라이언트/서버 에러 (4xx/5xx) ─────────────────────
    const errMsg = await _parseErrorMessage(response);
    return { valid: false, message: errMsg };

  } catch (err) {
    clearTimeout(timer);

    if (err.name === 'AbortError') {
      return { valid: false, message: '네트워크 응답이 없습니다. 인터넷 연결을 확인해 주세요.' };
    }
    return { valid: false, message: `연결 오류: ${err.message || '알 수 없는 오류'}` };
  }
}
