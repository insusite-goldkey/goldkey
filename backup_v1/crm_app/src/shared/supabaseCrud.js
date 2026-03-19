'use strict';
/**
 * src/shared/supabaseCrud.js — Goldkey AI Masters 2026
 *
 * [GP 마스터-그림자 원칙 §2] 양방향 고객 CRUD 공통 함수
 * 모 앱과 자 앱 양쪽에서 동일한 함수로 Supabase를 업데이트한다.
 * 어느 쪽에서 입력해도 동일한 gk_people 테이블이 업데이트된다.
 */

import { getSupabase } from '../services/supabaseService';
import { createEmptyCustomer, validateCustomer } from './customerSchema';

// ── 고객 목록 조회 (양방향 공통) ─────────────────────────────────────────────
/**
 * @param {string} agentId
 * @param {{ management_tier?: number, is_favorite?: boolean,
 *           prospecting_stage?: string, renewal_month?: number,
 *           query?: string }} filters
 */
export async function fetchCustomers(agentId, filters = {}) {
  const sb = getSupabase();
  let q = sb.from('gk_people')
    .select('*')
    .eq('is_deleted', false)
    .order('management_tier', { ascending: true })
    .order('name',            { ascending: true });

  if (agentId)                          q = q.eq('agent_id', agentId);
  if (filters.management_tier != null)  q = q.eq('management_tier', filters.management_tier);
  if (filters.is_favorite != null)      q = q.eq('is_favorite', filters.is_favorite);
  if (filters.prospecting_stage)        q = q.eq('prospecting_stage', filters.prospecting_stage);
  if (filters.renewal_month != null) {
    q = q.or(
      `auto_renewal_month.eq.${filters.renewal_month},` +
      `fire_renewal_month.eq.${filters.renewal_month}`
    );
  }
  if (filters.query) q = q.ilike('name', `%${filters.query}%`);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

// ── 고객 단건 조회 ────────────────────────────────────────────────────────────
export async function fetchCustomerById(personId) {
  const sb = getSupabase();
  const { data, error } = await sb
    .from('gk_people')
    .select('*')
    .eq('person_id', personId)
    .single();
  if (error) throw error;
  return data;
}

// ── [GP §2] 고객 정보 입력/수정 — 모/자 앱 양방향 공통 함수 ──────────────────
/**
 * customerInputForm() — 이름 그대로 "고객 정보 입력 폼의 저장 로직"
 * 모 앱(app.py 사이드)과 자 앱(CRM) 양쪽에서 동일하게 호출된다.
 *
 * @param {object} customerData — CUSTOMER_SCHEMA 기반 객체
 * @param {string} agentId      — 현재 로그인 설계사 ID
 * @returns {Promise<object>}   — 저장된 고객 레코드
 */
export async function customerInputForm(customerData, agentId) {
  const { valid, errors } = validateCustomer(customerData);
  if (!valid) {
    throw new Error('입력 오류: ' + Object.values(errors).join(', '));
  }

  const sb  = getSupabase();
  const row = {
    ...customerData,
    agent_id:   agentId,
    updated_at: new Date().toISOString(),
  };

  // person_id 없으면 신규 생성
  if (!row.person_id) {
    const empty = createEmptyCustomer(agentId);
    row.person_id  = empty.person_id;
    row.created_at = empty.created_at;
  }

  const { data, error } = await sb
    .from('gk_people')
    .upsert(row, { onConflict: 'person_id' })
    .select()
    .single();

  if (error) throw error;
  return data;
}

// ── 고객 즐겨찾기 토글 ────────────────────────────────────────────────────────
export async function toggleFavorite(personId, currentValue) {
  const sb = getSupabase();
  const { data, error } = await sb
    .from('gk_people')
    .update({ is_favorite: !currentValue, updated_at: new Date().toISOString() })
    .eq('person_id', personId)
    .select()
    .single();
  if (error) throw error;
  return data;
}

// ── 고객 관리 등급 변경 ───────────────────────────────────────────────────────
export async function updateManagementTier(personId, tier) {
  const sb = getSupabase();
  const { data, error } = await sb
    .from('gk_people')
    .update({ management_tier: tier, updated_at: new Date().toISOString() })
    .eq('person_id', personId)
    .select()
    .single();
  if (error) throw error;
  return data;
}

// ── 고객 Soft Delete ──────────────────────────────────────────────────────────
export async function softDeleteCustomer(personId) {
  const sb = getSupabase();
  const { error } = await sb
    .from('gk_people')
    .update({ is_deleted: true, updated_at: new Date().toISOString() })
    .eq('person_id', personId);
  if (error) throw error;
  return true;
}

// ── 오늘의 만기/기념일 고객 조회 (대시보드 TODAY 섹션용) ─────────────────────
export async function fetchTodayAlerts(agentId) {
  const today = new Date();
  const month = today.getMonth() + 1;
  const sb    = getSupabase();

  const { data, error } = await sb
    .from('gk_people')
    .select('person_id, name, contact, auto_renewal_month, fire_renewal_month, management_tier, is_favorite')
    .eq('agent_id', agentId)
    .eq('is_deleted', false)
    .or(`auto_renewal_month.eq.${month},fire_renewal_month.eq.${month}`);

  if (error) throw error;
  return data || [];
}
