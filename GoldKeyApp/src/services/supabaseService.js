/**
 * supabaseService.js — Goldkey AI Masters 2026
 * gk_people / gk_schedules / gk_scan_results CRUD
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
