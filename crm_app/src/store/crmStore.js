/**
 * CRM 전역 상태 스토어 (Zustand)
 * - Task 관리 + 달성률
 * - 실손 세대 자동 산출
 * - 고객 기본/보험/보장공백 정보
 * - AI 리포트 생성 (generateReport)
 * - 피처 플래그
 */

import { create } from 'zustand';
import { Share } from 'react-native';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 피처 플래그
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export const FEATURE_FLAGS = {
  ENABLE_CALENDAR_SYNC: false,   // 안드로이드 네이티브 권한 이슈 차단
  ENABLE_AI_REPORT:     true,
  ENABLE_HOFFMANN:      true,
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 순수 함수
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const _getSilsonGeneration = (dateString) => {
  if (!dateString || !/^\d{4}-\d{2}$/.test(dateString)) return '';
  const [y, m] = dateString.split('-').map(Number);
  const d = new Date(y, m - 1, 28);
  if (d <= new Date(2009, 8, 30))  return '1세대 구실손';
  if (d <= new Date(2017, 2, 31))  return '2세대 표준화실손';
  if (d <= new Date(2021, 5, 30))  return '3세대 착한실손';
  return '4세대 실손';
};

/** 호프만 계산 — 연수익 기준 보장 공백 현가(만원) */
const _calcHoffmann = (annualIncome, coverageGap, yearsRemaining) => {
  if (!annualIncome || !yearsRemaining) return 0;
  const rate = 0.05;
  const pv = annualIncome * ((1 - Math.pow(1 + rate, -yearsRemaining)) / rate);
  return Math.round((pv * (coverageGap / 100)) / 10000);
};

/** AI 상담 리포트 스크립트 생성 */
const _generateReportText = ({ name, job, hoffmannGap, silsonGen }) => {
  const jobStr  = job  || '고객';
  const genStr  = silsonGen || '미확인';
  const gapStr  = hoffmannGap > 0 ? `약 ${hoffmannGap.toLocaleString('ko-KR')}만원` : '추가 확인 필요';
  return (
    `[골드키 AI 맞춤 상담 리포트]\n\n` +
    `안녕하세요, ${name || '고객'}님.\n\n` +
    `📋 직업: ${jobStr}\n` +
    `🏥 실손 세대: ${genStr}\n` +
    `⚠️ 보장 공백(호프만 현가): ${gapStr}\n\n` +
    `현재 가입하신 ${genStr} 실손보험은 보장 범위와 자기부담금 구조가 다릅니다.\n` +
    `보장 공백 ${gapStr}을 고려하면, 지금 추가 설계가 필요한 시점입니다.\n\n` +
    `✅ 권장 조치:\n` +
    `1. 실손 전환 또는 보완 상품 검토\n` +
    `2. 소득 대비 보험료 적정성 재점검\n` +
    `3. 추가 진단 보장 공백 확인\n\n` +
    `문의: 골드키 파트너 설계사\n` +
    `──────────────────────`
  );
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Badge 색상 맵
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export const SILSON_BADGE_COLORS = {
  '1세대 구실손':     { bg: '#fef3c7', text: '#92400e', border: '#f59e0b' },
  '2세대 표준화실손': { bg: '#dbeafe', text: '#1e40af', border: '#3b82f6' },
  '3세대 착한실손':   { bg: '#dcfce7', text: '#166534', border: '#22c55e' },
  '4세대 실손':       { bg: '#f3e8ff', text: '#6b21a8', border: '#a855f7' },
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 초기 데이터
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const INITIAL_TASKS = [
  { id: 1, title: '자동차보험 만기 안내 (D-30)',  isDone: false, priority: 'high',   dueDate: '2026-03-15' },
  { id: 2, title: '신규 고객 실손 청구 접수',      isDone: false, priority: 'high',   dueDate: '2026-03-10' },
  { id: 3, title: '박○○ 고객 종신보험 설계 전달', isDone: false, priority: 'medium', dueDate: '2026-03-12' },
  { id: 4, title: '월별 영업 실적 보고서 제출',    isDone: false, priority: 'low',    dueDate: '2026-03-31' },
];

const INITIAL_CUSTOMER = {
  name: '', job: '', phone: '', birthYear: '', gender: '',
  subscriptionDate: '',
};

const INITIAL_COVERAGE = {
  annualIncome: 0,
  coverageGapPercent: 30,
  yearsRemaining: 30,
  hoffmannGap: 0,
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Zustand 스토어
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export const useCrmStore = create((set, get) => ({

  // ── Tasks ──────────────────────────────────────────
  tasks: INITIAL_TASKS,

  toggleTask: (taskId) =>
    set((s) => ({ tasks: s.tasks.map((t) => t.id === taskId ? { ...t, isDone: !t.isDone } : t) })),

  addTask: (title, priority = 'medium', dueDate = '') =>
    set((s) => ({ tasks: [...s.tasks, { id: Date.now(), title, isDone: false, priority, dueDate }] })),

  removeTask: (taskId) =>
    set((s) => ({ tasks: s.tasks.filter((t) => t.id !== taskId) })),

  getProgressPercent: () => {
    const { tasks } = get();
    if (!tasks.length) return 0;
    return Math.round((tasks.filter((t) => t.isDone).length / tasks.length) * 100);
  },

  // ── 고객 정보 ──────────────────────────────────────
  customer: { ...INITIAL_CUSTOMER },

  updateCustomer: (fields) =>
    set((s) => ({ customer: { ...s.customer, ...fields } })),

  // ── 실손 세대 ──────────────────────────────────────
  silsonDate: '',
  silsonGeneration: '',

  calculateSilson: (dateString) =>
    set({ silsonDate: dateString, silsonGeneration: _getSilsonGeneration(dateString) }),

  // ── 보장 공백 (호프만) ─────────────────────────────
  coverage: { ...INITIAL_COVERAGE },

  updateCoverage: (fields) => {
    const next = { ...get().coverage, ...fields };
    next.hoffmannGap = _calcHoffmann(
      next.annualIncome, next.coverageGapPercent, next.yearsRemaining
    );
    set({ coverage: next });
  },

  // ── AI 리포트 ──────────────────────────────────────
  aiReport: null,
  isGeneratingReport: false,

  generateReport: () => {
    if (!FEATURE_FLAGS.ENABLE_AI_REPORT) return;
    set({ isGeneratingReport: true });
    const { customer, silsonGeneration, coverage } = get();
    const text = _generateReportText({
      name:       customer.name,
      job:        customer.job,
      hoffmannGap: coverage.hoffmannGap,
      silsonGen:  silsonGeneration,
    });
    setTimeout(() => {
      set({ aiReport: text, isGeneratingReport: false });
    }, 600);
  },

  clearReport: () => set({ aiReport: null }),

  shareReport: async () => {
    const { aiReport } = get();
    if (!aiReport) return;
    try {
      await Share.share({ message: aiReport, title: '골드키 AI 상담 리포트' });
    } catch (_) {}
  },

  // ── Watchdog 자가복구 진입점 ───────────────────────
  recoverState: () => {
    const s = get();
    if (!Array.isArray(s.tasks))      set({ tasks: INITIAL_TASKS });
    if (typeof s.customer !== 'object' || s.customer === null)
      set({ customer: { ...INITIAL_CUSTOMER } });
    if (typeof s.coverage !== 'object' || s.coverage === null)
      set({ coverage: { ...INITIAL_COVERAGE } });
  },
}));

// ── Selector 헬퍼 ─────────────────────────────────────
export const selectTasks         = (s) => s.tasks;
export const selectToggleTask    = (s) => s.toggleTask;
export const selectProgress      = (s) => s.getProgressPercent;
export const selectCustomer      = (s) => ({ data: s.customer, update: s.updateCustomer });
export const selectSilson        = (s) => ({ date: s.silsonDate, gen: s.silsonGeneration, calc: s.calculateSilson });
export const selectCoverage      = (s) => ({ data: s.coverage, update: s.updateCoverage });
export const selectAiReport      = (s) => ({ report: s.aiReport, loading: s.isGeneratingReport, generate: s.generateReport, share: s.shareReport, clear: s.clearReport });
