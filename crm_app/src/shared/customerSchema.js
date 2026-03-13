'use strict';
/**
 * src/shared/customerSchema.js — Goldkey AI Masters 2026
 *
 * [GP 마스터-그림자 원칙 §1] 공통 고객 데이터 스키마
 * 모 앱과 자 앱이 동일한 스키마를 공유한다.
 * 이 파일이 바뀌면 양쪽 앱 모두 자동으로 반영된다.
 */

// ── Supabase gk_people 테이블 컬럼 정의 ─────────────────────────────────────
export const CUSTOMER_SCHEMA = {
  person_id:           { type: 'string',  required: true,  label: 'ID' },
  name:                { type: 'string',  required: true,  label: '이름' },
  contact:             { type: 'string',  required: true,  label: '연락처' },
  birth_date:          { type: 'date',    required: false, label: '생년월일' },
  gender:              { type: 'string',  required: false, label: '성별', options: ['남성', '여성'] },
  address:             { type: 'string',  required: false, label: '주소' },
  job:                 { type: 'string',  required: false, label: '직업' },
  memo:                { type: 'text',    required: false, label: '메모' },
  status:              { type: 'string',  required: false, label: '상태',
                          options: ['potential', 'active', 'contracted', 'closed'],
                          default: 'potential' },
  last_consulted_at:   { type: 'date',    required: false, label: '최근 상담일' },
  is_favorite:         { type: 'boolean', required: false, label: '즐겨찾기', default: false },
  management_tier:     { type: 'number',  required: false, label: '관리 등급',
                          options: [1, 2, 3], default: 3 },
  auto_renewal_month:  { type: 'number',  required: false, label: '자동차보험 만기월' },
  fire_renewal_month:  { type: 'number',  required: false, label: '화재보험 만기월' },
  last_auto_carrier:   { type: 'string',  required: false, label: '기존 자동차보험사' },
  wedding_anniversary: { type: 'date',    required: false, label: '결혼기념일' },
  driving_status:      { type: 'string',  required: false, label: '운전 형태' },
  risk_note:           { type: 'text',    required: false, label: '고위험 메모' },
  lead_source:         { type: 'string',  required: false, label: '유입 경로' },
  referrer_id:         { type: 'string',  required: false, label: '소개자 ID' },
  referrer_relation:   { type: 'string',  required: false, label: '소개자 관계' },
  community_tags:      { type: 'array',   required: false, label: '소속 모임' },
  prospecting_stage:   { type: 'string',  required: false, label: '개척 단계',
                          options: ['lead', 'contact', 'proposal', 'contracted'],
                          default: 'lead' },
};

// ── 관리 등급 레이블 (모/자 앱 공통) ─────────────────────────────────────────
export const MANAGEMENT_TIER_LABELS = {
  1: { label: 'VVIP',  color: '#b45309', bg: '#fef3c7', icon: '👑' },
  2: { label: '핵심',  color: '#1d4ed8', bg: '#dbeafe', icon: '⭐' },
  3: { label: '일반',  color: '#374151', bg: '#f3f4f6', icon: '👤' },
};

// ── 고객 상태 레이블 ──────────────────────────────────────────────────────────
export const CUSTOMER_STATUS_LABELS = {
  potential:  { label: '가망',   color: '#6b7280', bg: '#f3f4f6' },
  active:     { label: '진행중', color: '#2563eb', bg: '#dbeafe' },
  contracted: { label: '계약',   color: '#16a34a', bg: '#dcfce7' },
  closed:     { label: '종료',   color: '#dc2626', bg: '#fee2e2' },
};

// ── 개척 단계 레이블 ──────────────────────────────────────────────────────────
export const PROSPECTING_STAGE_LABELS = {
  lead:       { label: '발굴', color: '#6b7280', step: 1 },
  contact:    { label: '접촉', color: '#2563eb', step: 2 },
  proposal:   { label: '제안', color: '#d97706', step: 3 },
  contracted: { label: '계약', color: '#16a34a', step: 4 },
};

// ── 빈 고객 객체 생성 헬퍼 ───────────────────────────────────────────────────
export function createEmptyCustomer(agentId = '') {
  return {
    person_id:           `CUST_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    name:                '',
    contact:             '',
    birth_date:          null,
    gender:              null,
    address:             '',
    job:                 '',
    memo:                '',
    status:              'potential',
    is_favorite:         false,
    management_tier:     3,
    prospecting_stage:   'lead',
    community_tags:      [],
    agent_id:            agentId,
    is_deleted:          false,
    created_at:          new Date().toISOString(),
    updated_at:          new Date().toISOString(),
  };
}

// ── 고객 유효성 검사 ──────────────────────────────────────────────────────────
export function validateCustomer(customer) {
  const errors = {};
  if (!customer.name?.trim())    errors.name    = '이름을 입력해 주세요.';
  if (!customer.contact?.trim()) errors.contact = '연락처를 입력해 주세요.';
  return { valid: Object.keys(errors).length === 0, errors };
}

// ── 모 앱 딥링크 URL 생성 (자 앱 → 모 앱 발사대) ────────────────────────────
export const MOTHER_APP_URL = 'https://goldkey-ai-817097913199.asia-northeast3.run.app';

export function buildMotherDeepLink(action, params = {}) {
  const qs = Object.entries(params)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&');
  return `${MOTHER_APP_URL}/?gk_action=${encodeURIComponent(action)}${qs ? `&${qs}` : ''}`;
}
