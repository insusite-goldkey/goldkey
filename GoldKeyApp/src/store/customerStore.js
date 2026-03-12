/**
 * customerStore.js — Goldkey AI Masters 2026
 * Zustand 전역 상태: 고객 목록, 선택 고객, 일정
 */
import { create } from 'zustand';
import {
  fetchPeople, upsertPerson, softDeletePerson,
  fetchSchedules, upsertSchedule,
} from '../services/supabaseService';

export const useCustomerStore = create((set, get) => ({
  // ── 상태 ──────────────────────────────────────────────────────────────────
  people:          [],
  schedules:       [],
  activePersonId:  null,
  isLoading:       false,
  error:           null,
  agentId:         '',
  filters:         {},

  // ── 에이전트 설정 ──────────────────────────────────────────────────────────
  setAgentId: (agentId) => set({ agentId }),

  // ── 고객 목록 ─────────────────────────────────────────────────────────────
  loadPeople: async (filters = {}) => {
    const { agentId } = get();
    set({ isLoading: true, error: null, filters });
    try {
      const people = await fetchPeople(agentId, filters);
      set({ people, isLoading: false });
    } catch (e) {
      set({ error: e.message, isLoading: false });
    }
  },

  savePerson: async (person) => {
    const { agentId } = get();
    const row = { ...person, agent_id: agentId };
    const saved = await upsertPerson(row);
    set((s) => {
      const idx = s.people.findIndex((p) => p.person_id === saved.person_id);
      const people = idx >= 0
        ? s.people.map((p) => p.person_id === saved.person_id ? saved : p)
        : [saved, ...s.people];
      return { people };
    });
    return saved;
  },

  deletePerson: async (personId) => {
    await softDeletePerson(personId);
    set((s) => ({ people: s.people.filter((p) => p.person_id !== personId) }));
    if (get().activePersonId === personId) set({ activePersonId: null });
  },

  // ── 선택 고객 ─────────────────────────────────────────────────────────────
  openProfile:  (personId) => set({ activePersonId: personId }),
  closeProfile: ()         => set({ activePersonId: null }),

  getActivePerson: () => {
    const { people, activePersonId } = get();
    return people.find((p) => p.person_id === activePersonId) || null;
  },

  // ── 일정 ──────────────────────────────────────────────────────────────────
  loadSchedules: async (personId = null) => {
    const { agentId } = get();
    try {
      const schedules = await fetchSchedules(agentId, personId);
      set({ schedules });
    } catch (e) {
      set({ error: e.message });
    }
  },

  saveSchedule: async (schedule) => {
    const { agentId } = get();
    const row = { ...schedule, agent_id: agentId };
    if (!row.id) row.id = `SCH_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    const saved = await upsertSchedule(row);
    set((s) => {
      const idx = s.schedules.findIndex((x) => x.id === saved.id);
      const schedules = idx >= 0
        ? s.schedules.map((x) => x.id === saved.id ? saved : x)
        : [...s.schedules, saved];
      return { schedules };
    });
    return saved;
  },

  // ── 이번 달 갱신 대상자 ───────────────────────────────────────────────────
  getRenewalThisMonth: () => {
    const month = new Date().getMonth() + 1;
    return get().people.filter(
      (p) => p.auto_renewal_month === month || p.fire_renewal_month === month
    );
  },

  // ── VVIP 고객 ─────────────────────────────────────────────────────────────
  getVvipPeople: () => get().people.filter((p) => p.management_tier === 1),
}));
