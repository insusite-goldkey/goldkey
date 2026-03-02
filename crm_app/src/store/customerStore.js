/**
 * useCustomerStore — SSOT(Single Source of Truth) 고객 전역 상태
 *
 * ┌ 데이터 구조 ──────────────────────────────────────────────────┐
 * │  customers: {                                                  │
 * │    [customerId: string]: {                                     │
 * │      id, name, age, job, phone, gender,                       │
 * │      tags, memo, company, title, registered,                  │
 * │      createdAt, updatedAt                                      │
 * │    }                                                           │
 * │  }                                                             │
 * │  schedules: {                                                  │
 * │    [scheduleId: string]: {                                     │
 * │      id, customerId, title, category,                         │
 * │      date, startTime, endTime, memo, done                     │
 * │    }                                                           │
 * │  }                                                             │
 * └───────────────────────────────────────────────────────────────┘
 *
 * 모든 컴포넌트는 customerId / scheduleId 만 보유하고,
 * 실제 데이터는 이 Store에서 실시간 구독(lookup)합니다.
 */

import { create } from 'zustand';

// ── 유틸 ─────────────────────────────────────────────────────────────────────
const uid = () => `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
const now = () => new Date().toISOString();

// ── 목업 초기 데이터 ──────────────────────────────────────────────────────────
const MOCK_CUSTOMERS = {
  'CUST_101': {
    id: 'CUST_101', name: '김민준', age: 42, job: '회사원',
    phone: '010-1234-5678', gender: '남성',
    company: '(주)한국물산', title: '부장',
    tags: ['위암 보장 부족', '4세대 실손', '종신 미가입'],
    memo: '자녀 2명, 배우자 암보험 필요. 매월 15일 연락 선호.',
    registered: true, createdAt: '2025-01-10T09:00:00.000Z', updatedAt: now(),
  },
  'CUST_102': {
    id: 'CUST_102', name: '이서연', age: 35, job: '자영업',
    phone: '010-9876-5432', gender: '여성',
    company: '이서연 카페', title: '대표',
    tags: ['실손 1세대', '갱신료 급등 위험'],
    memo: '카페 운영 중. 오전 상담 선호.',
    registered: true, createdAt: '2025-02-05T10:00:00.000Z', updatedAt: now(),
  },
  'CUST_103': {
    id: 'CUST_103', name: '박도현', age: 28, job: '프리랜서',
    phone: '010-5555-1234', gender: '남성',
    company: '', title: '',
    tags: ['신규 고객', '보장 공백 큼'],
    memo: '디자이너, 소득 불규칙. 실손 상담 필요.',
    registered: false, createdAt: '2025-03-01T11:00:00.000Z', updatedAt: now(),
  },
};

const MOCK_SCHEDULES = {
  'SCH_001': {
    id: 'SCH_001', customerId: 'CUST_101',
    title: '김민준 종신보험 설계 전달',
    category: 'consult',
    date: new Date().toISOString().slice(0, 10),
    startTime: '10:00', endTime: '11:00',
    memo: '종신 설계서 2종 준비', done: false,
  },
  'SCH_002': {
    id: 'SCH_002', customerId: 'CUST_101',
    title: '김민준 자동차보험 만기 안내',
    category: 'appointment',
    date: new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10),
    startTime: '14:00', endTime: '14:30',
    memo: 'D-30 만기 안내 콜', done: false,
  },
  'SCH_003': {
    id: 'SCH_003', customerId: 'CUST_102',
    title: '이서연 실손 전환 상담',
    category: 'consult',
    date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10),
    startTime: '09:30', endTime: '10:30',
    memo: '1세대→4세대 전환 비교표 지참', done: false,
  },
};

// ── 스토어 ────────────────────────────────────────────────────────────────────
export const useCustomerStore = create((set, get) => ({

  // ── 고객 해시맵 (SSOT) ──────────────────────────────────────────────────
  customers: { ...MOCK_CUSTOMERS },

  /** 고객 단건 조회 */
  getCustomer: (id) => get().customers[id] ?? null,

  /** 고객 배열 반환 (검색/목록용) */
  getCustomerList: () => Object.values(get().customers),

  /** 고객 추가 */
  addCustomer: (fields) => {
    const id = fields.id || `CUST_${uid()}`;
    const customer = {
      id, name: '', age: 0, job: '', phone: '', gender: '',
      company: '', title: '', tags: [], memo: '',
      registered: false, createdAt: now(), updatedAt: now(),
      ...fields,
      id,
    };
    set((s) => ({ customers: { ...s.customers, [id]: customer } }));
    return id;
  },

  /** 고객 단건 수정 — customerId 하나만 갱신 → 전체 동기화 */
  updateCustomer: (id, fields) => {
    set((s) => {
      const prev = s.customers[id];
      if (!prev) return s;
      return {
        customers: {
          ...s.customers,
          [id]: { ...prev, ...fields, id, updatedAt: now() },
        },
      };
    });
    // TODO: Firebase upsert 연동 시 여기에 추가
    // firebaseUpdateCustomer(id, fields);
  },

  /** 고객 삭제 */
  removeCustomer: (id) =>
    set((s) => {
      const next = { ...s.customers };
      delete next[id];
      return { customers: next };
    }),

  // ── 일정 해시맵 (SSOT) ──────────────────────────────────────────────────
  schedules: { ...MOCK_SCHEDULES },

  /** 특정 고객의 일정 배열 */
  getSchedulesByCustomer: (customerId) =>
    Object.values(get().schedules)
      .filter((s) => s.customerId === customerId)
      .sort((a, b) => (a.date > b.date ? 1 : -1)),

  /** 특정 날짜의 일정 배열 */
  getSchedulesByDate: (date) =>
    Object.values(get().schedules).filter((s) => s.date === date),

  /** 일정 추가 */
  addSchedule: (fields) => {
    const id = `SCH_${uid()}`;
    const schedule = {
      id, customerId: '', title: '', category: 'consult',
      date: new Date().toISOString().slice(0, 10),
      startTime: '09:00', endTime: '10:00',
      memo: '', done: false,
      ...fields,
      id,
    };
    set((s) => ({ schedules: { ...s.schedules, [id]: schedule } }));
    return id;
  },

  /** 일정 수정 */
  updateSchedule: (id, fields) =>
    set((s) => {
      const prev = s.schedules[id];
      if (!prev) return s;
      return { schedules: { ...s.schedules, [id]: { ...prev, ...fields, id } } };
    }),

  /** 일정 삭제 */
  removeSchedule: (id) =>
    set((s) => {
      const next = { ...s.schedules };
      delete next[id];
      return { schedules: next };
    }),

  /** 일정 완료 토글 */
  toggleScheduleDone: (id) =>
    set((s) => {
      const prev = s.schedules[id];
      if (!prev) return s;
      return { schedules: { ...s.schedules, [id]: { ...prev, done: !prev.done } } };
    }),

  // ── 스캔 결과 해시맵 (SSOT) ─────────────────────────────────────────────
  /**
   * scanResults: {
   *   [scanId]: {
   *     id, customerId, agentId,
   *     docType,        // 'medical_certificate' | 'diagnosis' | 'surgery' | 'disability' | 'other'
   *     rawText,        // 원본 OCR 텍스트 (마스킹 전)
   *     masked,         // PII 마스킹 완료 여부
   *     analysis: {
   *       summary,      // AI 요약 (설계사용)
   *       clientSummary,// 고객용 안심 요약
   *       kcdCodes,     // [{code, name, note}]
   *       disabilityRate,
   *       surgeries,    // [string]
   *       expectedPayout,  // 예상 수령 보험금(만원)
   *       upsellPoints, // AI 업셀링 추천 포인트 [string]
   *       kakaoScript,  // 카톡 멘트 초안
   *     },
   *     scannedAt, status // 'pending'|'done'|'error'
   *   }
   * }
   */
  scanResults: {},

  /** 스캔 결과 upsert (신규 추가 또는 수정) — Firestore stub 포함 */
  upsertScanResult: (customerId, agentId, scanData) => {
    const id = scanData.id || `SCAN_${uid()}`;
    const record = {
      id, customerId, agentId,
      docType: 'other', rawText: '', masked: false,
      analysis: {
        summary: '', clientSummary: '', kcdCodes: [],
        disabilityRate: null, surgeries: [], expectedPayout: 0,
        upsellPoints: [], kakaoScript: '',
      },
      scannedAt: now(), status: 'pending',
      ...scanData,
      id,
    };
    set((s) => ({ scanResults: { ...s.scanResults, [id]: record } }));
    // TODO: Firestore upsert
    // firebaseUpsertScan(customerId, agentId, record);
    return id;
  },

  /** 스캔 분석 완료 후 결과 patch */
  completeScanResult: (scanId, analysis, docType) =>
    set((s) => {
      const prev = s.scanResults[scanId];
      if (!prev) return s;
      return {
        scanResults: {
          ...s.scanResults,
          [scanId]: { ...prev, analysis, docType, masked: true, status: 'done' },
        },
      };
    }),

  /** 스캔 삭제 — 2중 확인은 UI 레이어에서 처리, 여기서는 audit_log 기록 후 삭제 */
  removeScanResult: (scanId, agentId) => {
    const record = get().scanResults[scanId];
    if (!record) return;
    // audit_log stub
    const log = {
      action: 'DELETE_SCAN', scanId, agentId,
      customerId: record.customerId, at: now(),
    };
    console.info('[audit_log]', JSON.stringify(log));
    // TODO: Firestore audit_logs 컬렉션에 저장
    // firebaseAddAuditLog(log);
    set((s) => {
      const next = { ...s.scanResults };
      delete next[scanId];
      return { scanResults: next };
    });
  },

  /** 고객별 스캔 결과 배열 (최신순) */
  getScansByCustomer: (customerId) =>
    Object.values(get().scanResults)
      .filter((r) => r.customerId === customerId)
      .sort((a, b) => (a.scannedAt < b.scannedAt ? 1 : -1)),

  // ── 내비게이션 상태 ──────────────────────────────────────────────────────
  /** 현재 열려있는 프로필 고객 ID */
  activeProfileId: null,
  openProfile: (id) => set({ activeProfileId: id }),
  closeProfile: ()  => set({ activeProfileId: null }),

  /** 스캔 결과 뷰 상태 */
  activeScanId: null,
  openScanView:  (scanId) => set({ activeScanId: scanId }),
  closeScanView: ()       => set({ activeScanId: null }),

  /** 일정 모달 상태 */
  scheduleModal: { open: false, prefillCustomerId: null, editScheduleId: null },
  openScheduleModal:  (prefillCustomerId = null, editScheduleId = null) =>
    set({ scheduleModal: { open: true, prefillCustomerId, editScheduleId } }),
  closeScheduleModal: () =>
    set({ scheduleModal: { open: false, prefillCustomerId: null, editScheduleId: null } }),
}));

// ── Selector 헬퍼 ──────────────────────────────────────────────────────────
export const selCustomer      = (id) => (s) => s.customers[id] ?? null;
export const selCustomerList  = (s) => Object.values(s.customers);
export const selSchedules     = (customerId) => (s) =>
  Object.values(s.schedules)
    .filter((sc) => sc.customerId === customerId)
    .sort((a, b) => (a.date > b.date ? 1 : -1));
export const selDateSchedules = (date) => (s) =>
  Object.values(s.schedules).filter((sc) => sc.date === date);
export const selModal         = (s) => s.scheduleModal;
export const selActiveProfile = (s) => s.activeProfileId;
export const selActiveScan    = (s) => s.activeScanId;
export const selScan          = (id) => (s) => s.scanResults[id] ?? null;
export const selScansByCustomer = (customerId) => (s) =>
  Object.values(s.scanResults)
    .filter((r) => r.customerId === customerId)
    .sort((a, b) => (a.scannedAt < b.scannedAt ? 1 : -1));
