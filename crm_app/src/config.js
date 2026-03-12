'use strict';

// ── Supabase ──────────────────────────────────────────────────────────────────
export const SUPABASE_URL      = 'https://idfzizqidhnpzbqioqqo.supabase.co'; // ← [1] 여기
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkZnppenFpZGhucHpicWlvcXFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4Mjk4NDIsImV4cCI6MjA4NzQwNTg0Mn0.49WC1s9iDKE1eZfwPi2zP8WZTFA8vfYSUYnqb-qITNM'; // ← [2] 여기

// ── GCP Cloud Functions (고정값 — 수정 불필요) ───────────────────────────────
export const VERIFY_OTP_URL =
  'https://asia-northeast3-gen-lang-client-0777682955.cloudfunctions.net/verifyOTP';

// ── 앱 식별 (고정값 — 수정 불필요) ────────────────────────────────────────────
export const GCP_PROJECT_ID = 'gen-lang-client-0777682955';
export const APP_NAME       = 'Goldkey AI Masters 2026';
export const APP_VERSION    = '1.0.0';
