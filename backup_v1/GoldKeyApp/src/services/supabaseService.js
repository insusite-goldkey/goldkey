/**
 * supabaseService.js — Goldkey AI Masters 2026
 * gk_people / gk_schedules / gk_scan_results / gk_policies CRUD
 * GP-IMMORTAL §2: agent_id 격리 강제 적용
 */
import { createClient } from '@supabase/supabase-js';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '../config';

let _client = null;

export function getSupabase() {
  if (!_client) {
    _client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return _client;
}

// ── gk_people ────────────────────────────────────────────────────────────────

export async function fetchPeople(agentId, filters = {}) {
  const sb = getSupabase();
  let q = sb.from('gk_people')
    .select('*')
    .eq('is_deleted', false)
    .order('management_tier', { ascending: true })
    .order('name', { ascending: true });

  if (agentId) q = q.eq('agent_id', agentId);
  if (filters.management_tier != null) q = q.eq('management_tier', filters.management_tier);
  if (filters.is_favorite != null)     q = q.eq('is_favorite', filters.is_favorite);
  if (filters.prospecting_stage)       q = q.eq('prospecting_stage', filters.prospecting_stage);
  if (filters.renewal_month != null) {
    q = q.or(`auto_renewal_month.eq.${filters.renewal_month},fire_renewal_month.eq.${filters.renewal_month}`);
  }
  if (filters.query) q = q.ilike('name', `%${filters.query}%`);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function upsertPerson(person) {
  const sb = getSupabase();
  const row = { ...person, updated_at: new Date().toISOString() };
  const { data, error } = await sb
    .from('gk_people')
    .upsert(row, { onConflict: 'person_id' })
    .select()
    .single();
  if (error) throw error;
  return data;
}

export async function softDeletePerson(personId) {
  const sb = getSupabase();
  const { error } = await sb
    .from('gk_people')
    .update({ is_deleted: true, updated_at: new Date().toISOString() })
    .eq('person_id', personId);
  if (error) throw error;
  return true;
}

// ── gk_schedules ─────────────────────────────────────────────────────────────

export async function fetchSchedules(agentId, personId = null) {
  const sb = getSupabase();
  let q = sb.from('gk_schedules')
    .select('*')
    .eq('is_deleted', false)
    .order('date', { ascending: true });

  if (agentId)  q = q.eq('agent_id', agentId);
  if (personId) q = q.eq('person_id', personId);

  const { data, error } = await q;
  if (error) throw error;
  return data || [];
}

export async function upsertSchedule(schedule) {
  const sb = getSupabase();
  const row = { ...schedule, updated_at: new Date().toISOString() };
  const { data, error } = await sb
    .from('gk_schedules')
    .upsert(row, { onConflict: 'id' })
    .select()
    .single();
  if (error) throw error;
  return data;
}

// ── gk_scan_results ──────────────────────────────────────────────────────────

export async function fetchScanResults(personId) {
  const sb = getSupabase();
  const { data, error } = await sb
    .from('gk_scan_results')
    .select('*')
    .eq('person_id', personId)
    .eq('is_deleted', false)
    .order('created_at', { ascending: false });
  if (error) throw error;
  return data || [];
}

export async function upsertScanResult(scanResult) {
  const sb = getSupabase();
  const row = { ...scanResult, updated_at: new Date().toISOString() };
  const { data, error } = await sb
    .from('gk_scan_results')
    .upsert(row, { onConflict: 'id' })
    .select()
    .single();
  if (error) throw error;
  return data;
}

// ── gk_policies ───────────────────────────────────────────────────────────────

/**
 * 특정 고객의 보험 계약을 만기일 임박 순으로 조회
 * idx_policy_person_expiry 인덱스 활용
 */
export async function fetchPolicies(personId) {
  const sb = getSupabase();
  const { data, error } = await sb
    .from('gk_policies')
    .select('*')
    .eq('person_id', personId)
    .order('expiry_date', { ascending: true });
  if (error) throw error;
  return data || [];
}

/**
 * 신규 보험 계약 등록 (증권 스캔 결과 저장 시 사용)
 */
export async function createPolicy(policyData) {
  const sb = getSupabase();
  const row = { ...policyData, created_at: new Date().toISOString() };
  const { data, error } = await sb
    .from('gk_policies')
    .insert([row])
    .select()
    .single();
  if (error) throw error;
  return data;
}

/**
 * 보험 계약 상태 변경 (active → lapsed / terminated)
 */
export async function updatePolicyStatus(policyId, status) {
  const sb = getSupabase();
  const { data, error } = await sb
    .from('gk_policies')
    .update({ status })
    .eq('id', policyId)
    .select()
    .single();
  if (error) throw error;
  return data;
}

/**
 * 고객의 전체 보험 계약 + 고객 정보 JOIN 조회
 * management_tier → name 순 정렬 (idx_people_tier_name 인덱스 활용)
 */
export async function fetchPeopleWithPolicies(agentId) {
  const sb = getSupabase();
  const { data, error } = await sb
    .from('gk_people')
    .select(`
      *,
      gk_policies (
        id, policy_number, insurance_company,
        product_name, expiry_date, premium, status
      )
    `)
    .eq('agent_id', agentId)
    .eq('is_deleted', false)
    .order('management_tier', { ascending: true })
    .order('name',            { ascending: true });
  if (error) throw error;
  return data || [];
}
