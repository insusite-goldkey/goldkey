/**
 * CRM 전역 상태 스토어 (Zustand)
 * - 할 일(Task) 관리
 * - 실손 세대 자동 산출
 * - 고객 기본/보험 정보
 * - 달력 동기화 이벤트 목록
 */

import { create } from 'zustand';

// ── 실손 세대 판별 순수 함수 ─────────────────────────────────────────────────
const _getSilsonGeneration = (dateString) => {
  if (!dateString || !/^\d{4}-\d{2}$/.test(dateString)) return '';
  const [y, m] = dateString.split('-').map(Number);
  // 월말 기준 비교: 해당 월의 마지막 날로 Date 생성
  const d = new Date(y, m - 1, 28); // 28일은 모든 월에 존재

  if (d <= new Date(2009, 8, 30))  return '1세대 구실손';      // ~2009.09
  if (d <= new Date(2017, 2, 31))  return '2세대 표준화실손';  // 2009.10~2017.03
  if (d <= new Date(2021, 5, 30))  return '3세대 착한실손';    // 2017.04~2021.06
  return '4세대 실손';                                          // 2021.07~
};

// ── 세대별 Badge 색상 매핑 ───────────────────────────────────────────────────
export const SILSON_BADGE_COLORS = {
  '1세대 구실손':     { bg: '#fef3c7', text: '#92400e', border: '#f59e0b' },
  '2세대 표준화실손': { bg: '#dbeafe', text: '#1e40af', border: '#3b82f6' },
  '3세대 착한실손':   { bg: '#dcfce7', text: '#166534', border: '#22c55e' },
  '4세대 실손':       { bg: '#f3e8ff', text: '#6b21a8', border: '#a855f7' },
};

// ── 초기 샘플 Task 데이터 ────────────────────────────────────────────────────
const INITIAL_TASKS = [
  { id: 1, title: '자동차보험 만기 안내 (D-30)',      isDone: false, priority: 'high',   dueDate: '2026-03-15' },
  { id: 2, title: '신규 고객 실손 청구 접수',          isDone: false, priority: 'high',   dueDate: '2026-03-10' },
  { id: 3, title: '박○○ 고객 종신보험 설계 전달',     isDone: false, priority: 'medium', dueDate: '2026-03-12' },
  { id: 4, title: '월별 영업 실적 보고서 제출',        isDone: false, priority: 'low',    dueDate: '2026-03-31' },
];

// ── 달력 이벤트 초기 샘플 ───────────────────────────────────────────────────
const INITIAL_CALENDAR_EVENTS = [
  { id: 'ev1', title: '자동차보험 만기', date: '2026-03-15', synced: false },
  { id: 'ev2', title: '건강보험 갱신일', date: '2026-04-01', synced: false },
];

// ── Zustand 스토어 ───────────────────────────────────────────────────────────
export const useCrmStore = create((set, get) => ({

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 상태: 할 일 목록
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  tasks: INITIAL_TASKS,

  /** Task 완료 토글 — 해당 아이템만 교체하여 최소 리렌더링 */
  toggleTask: (taskId) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId ? { ...t, isDone: !t.isDone } : t
      ),
    })),

  /** 새 Task 추가 */
  addTask: (title, priority = 'medium', dueDate = '') =>
    set((state) => ({
      tasks: [
        ...state.tasks,
        {
          id: Date.now(),
          title,
          isDone: false,
          priority,
          dueDate,
        },
      ],
    })),

  /** Task 삭제 */
  removeTask: (taskId) =>
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== taskId),
    })),

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 상태: 실손 세대 자동 산출
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  silsonDate: '',
  silsonGeneration: '',

  /** 가입 연월(YYYY-MM) 입력 → 세대 자동 판별 */
  calculateSilson: (dateString) => {
    const generation = _getSilsonGeneration(dateString);
    set({ silsonDate: dateString, silsonGeneration: generation });
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 상태: 고객 정보 (기본/보험)
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  customerBasic: {
    name: '',
    phone: '',
    birthDate: '',
    gender: '',
  },

  customerInsurance: {
    carInsuranceExpiry: '',
    healthInsuranceType: '',
    lifeInsurancePremium: '',
    memo: '',
  },

  /** 고객 기본 정보 일괄 업데이트 */
  updateCustomerBasic: (fields) =>
    set((state) => ({
      customerBasic: { ...state.customerBasic, ...fields },
    })),

  /** 고객 보험 정보 일괄 업데이트 */
  updateCustomerInsurance: (fields) =>
    set((state) => ({
      customerInsurance: { ...state.customerInsurance, ...fields },
    })),

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 상태: 달력 이벤트
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  calendarEvents: INITIAL_CALENDAR_EVENTS,

  /** 특정 이벤트를 동기화 완료 상태로 표시 */
  markEventSynced: (eventId) =>
    set((state) => ({
      calendarEvents: state.calendarEvents.map((ev) =>
        ev.id === eventId ? { ...ev, synced: true } : ev
      ),
    })),

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 파생 Selector (Computed Values)
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /** 달성률 0~100 (정수) */
  get progressPercent() {
    const tasks = get().tasks;
    if (tasks.length === 0) return 0;
    return Math.round((tasks.filter((t) => t.isDone).length / tasks.length) * 100);
  },
}));

// ── 외부에서 사용할 Selector 헬퍼 (불필요한 리렌더링 방지) ──────────────────
export const selectTasks          = (s) => s.tasks;
export const selectToggleTask     = (s) => s.toggleTask;
export const selectSilson         = (s) => ({ date: s.silsonDate, gen: s.silsonGeneration, calc: s.calculateSilson });
export const selectCustomerBasic  = (s) => ({ data: s.customerBasic,     update: s.updateCustomerBasic });
export const selectCustomerIns    = (s) => ({ data: s.customerInsurance, update: s.updateCustomerInsurance });
export const selectCalendar       = (s) => ({ events: s.calendarEvents,  markSynced: s.markEventSynced });
