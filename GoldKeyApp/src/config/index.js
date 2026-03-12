// ── 앱 식별 ─────────────────────────────────────────────────────────────────
export const APP_NAME    = 'Goldkey AI Masters 2026';
export const APP_VERSION = '1.0.0';
export const APP_PACKAGE = 'com.goldkeyai';

// ── Supabase ─────────────────────────────────────────────────────────────────
export const SUPABASE_URL     = 'https://idfzizqidhnpzbqioqqo.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkZnppenFpZGhucHpicWlvcXFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4Mjk4NDIsImV4cCI6MjA4NzQwNTg0Mn0.49WC1s9iDKE1eZfwPi2zP8WZTFA8vfYSUYnqb-qITNM';

// ── CRM 앱 Play Store URL (인앱 설치 유도용) ────────────────────────────────
export const CRM_PLAY_STORE_URL = 'https://play.google.com/store/apps/details?id=com.goldkeycrm';

// ── 관리 등급 레이블 ─────────────────────────────────────────────────────────
export const MANAGEMENT_TIER = {
  1: { label: 'VVIP', color: '#b45309', bg: '#fef3c7' },
  2: { label: '핵심', color: '#1d4ed8', bg: '#dbeafe' },
  3: { label: '일반', color: '#374151', bg: '#f3f4f6' },
};

// ── 개척 단계 ────────────────────────────────────────────────────────────────
export const PROSPECTING_STAGE = {
  lead:        { label: '발굴',   color: '#6b7280' },
  contact:     { label: '접촉',   color: '#2563eb' },
  proposal:    { label: '제안',   color: '#d97706' },
  contracted:  { label: '계약',   color: '#16a34a' },
};

// ── 고객 상태 ────────────────────────────────────────────────────────────────
export const CUSTOMER_STATUS = {
  potential:   { label: '가망',   color: '#6b7280' },
  active:      { label: '진행중', color: '#2563eb' },
  contracted:  { label: '계약',   color: '#16a34a' },
  closed:      { label: '종료',   color: '#dc2626' },
};
