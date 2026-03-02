/**
 * useCustomerStore — SSOT(Single Source of Truth) 고객 전역 상태
 *
 * ┌ 3중 데이터 안전망 (3-Tier Data Safety Net) ───────────────────┐
 * │  1️⃣  Zustand persist (AsyncStorage) — 기기 로컬 영구 저장      │
 * │       앱 crash/강제종료 후 재시작해도 데이터 완전 복구          │
 * │  2️⃣  Firebase Offline Persistence — 오프라인 큐 자동 sync      │
 * │       지하/엘리베이터 등 무선 단절 시 로컬 큐 → 복구 시 sync   │
 * │  3️⃣  Soft Delete — isDeleted:true + 30일 휴지통 복구           │
 * │       deleteDoc() 완전 금지. 모든 삭제는 updateDoc만 허용.     │
 * └───────────────────────────────────────────────────────────────┘
 *
 * ┌ 데이터 구조 ──────────────────────────────────────────────────┐
 * │  customers / schedules / scanResults 모두 동일 패턴:           │
 * │  { id, ...fields, isDeleted: bool, deletedAt: iso|null }      │
 * │  UI는 항상 isDeleted:false 만 렌더링.                          │
 * └───────────────────────────────────────────────────────────────┘
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

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

// ── AsyncStorage 어댑터 (zustand persist용) ─────────────────────────────────
const asyncStorageAdapter = createJSONStorage(() => AsyncStorage);

// ── persist 제외 상태 키 (UI 상태는 영구 저장 불필요) ──────────────────────
const TRANSIENT_KEYS = [
  'activeProfileId', 'activeScanId',
  'scheduleModal', 'scanLoading',
];

// ── 스토어 ────────────────────────────────────────────────────────────────────
export const useCustomerStore = create(
 persist(
  (set, get) => ({

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
      // ── 3단계: Soft Delete 필드 ──
      isDeleted: false, deletedAt: null, deletedBy: null,
      ...fields,
      id,
    };
    set((s) => ({ customers: { ...s.customers, [id]: customer } }));
    // TODO: upsertDoc(COLLECTIONS.CUSTOMERS, id, customer);
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
    // TODO: upsertDoc(COLLECTIONS.CUSTOMERS, id, { ...fields, updatedAt: now() });
  },

  /**
   * ♻️ 고객 Soft Delete — Hard Delete 금지!
   * isDeleted:true + deletedAt 기록 → 휴지통에서 30일 내 복구 가능
   */
  removeCustomer: (id, deletedBy = 'agent') =>
    set((s) => {
      const prev = s.customers[id];
      if (!prev) return s;
      const deleted = { ...prev, isDeleted: true, deletedAt: now(), deletedBy };
      // TODO: softDeleteDoc(COLLECTIONS.CUSTOMERS, id, deletedBy);
      return { customers: { ...s.customers, [id]: deleted } };
    }),

  /** 휴지통에서 고객 복구 */
  restoreCustomer: (id) =>
    set((s) => {
      const prev = s.customers[id];
      if (!prev) return s;
      const restored = { ...prev, isDeleted: false, deletedAt: null, deletedBy: null };
      // TODO: restoreDoc(COLLECTIONS.CUSTOMERS, id);
      return { customers: { ...s.customers, [id]: restored } };
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
      // ── 3단계: Soft Delete 필드 ──
      isDeleted: false, deletedAt: null, deletedBy: null,
      ...fields,
      id,
    };
    set((s) => ({ schedules: { ...s.schedules, [id]: schedule } }));
    // TODO: upsertDoc(COLLECTIONS.SCHEDULES, id, schedule);
    return id;
  },

  /** 일정 수정 */
  updateSchedule: (id, fields) =>
    set((s) => {
      const prev = s.schedules[id];
      if (!prev) return s;
      return { schedules: { ...s.schedules, [id]: { ...prev, ...fields, id } } };
    }),

  /**
   * ♻️ 일정 Soft Delete
   */
  removeSchedule: (id, deletedBy = 'agent') =>
    set((s) => {
      const prev = s.schedules[id];
      if (!prev) return s;
      const deleted = { ...prev, isDeleted: true, deletedAt: now(), deletedBy };
      // TODO: softDeleteDoc(COLLECTIONS.SCHEDULES, id, deletedBy);
      return { schedules: { ...s.schedules, [id]: deleted } };
    }),

  /** 휴지통에서 일정 복구 */
  restoreSchedule: (id) =>
    set((s) => {
      const prev = s.schedules[id];
      if (!prev) return s;
      const restored = { ...prev, isDeleted: false, deletedAt: null, deletedBy: null };
      // TODO: restoreDoc(COLLECTIONS.SCHEDULES, id);
      return { schedules: { ...s.schedules, [id]: restored } };
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

  /**
   * ♻️ 스캔 결과 Soft Delete — 2중 확인은 UI 레이어에서 처리
   */
  removeScanResult: (scanId, agentId = 'agent') => {
    const record = get().scanResults[scanId];
    if (!record) return;
    const log = {
      action: 'SOFT_DELETE_SCAN', scanId, agentId,
      customerId: record.customerId, at: now(),
    };
    console.info('[audit_log]', JSON.stringify(log));
    // TODO: softDeleteDoc(COLLECTIONS.SCAN_RESULTS, scanId, agentId);
    set((s) => ({
      scanResults: {
        ...s.scanResults,
        [scanId]: { ...record, isDeleted: true, deletedAt: now(), deletedBy: agentId },
      },
    }));
  },

  /** 휴지통에서 스캔 결과 복구 */
  restoreScanResult: (scanId) =>
    set((s) => {
      const prev = s.scanResults[scanId];
      if (!prev) return s;
      // TODO: restoreDoc(COLLECTIONS.SCAN_RESULTS, scanId);
      return {
        scanResults: {
          ...s.scanResults,
          [scanId]: { ...prev, isDeleted: false, deletedAt: null, deletedBy: null },
        },
      };
    }),

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

  // ── AI 스캔 로딩 상태 (PremiumLoadingUI 제어) ────────────────────────────
  /**
   * scanLoading: {
   *   active:     bool   — 로딩 오버레이 표시 여부
   *   customerId: string — 분석 중인 고객 ID (avatarUri 조회용)
   * }
   */
  scanLoading: { active: false, customerId: null },

  /** AI 분석 시작 시 호출 → PremiumLoadingUI 표시 */
  startScanLoading: (customerId = null) =>
    set({ scanLoading: { active: true, customerId } }),

  /** AI 분석 완료/오류 시 호출 → PremiumLoadingUI 숨김 */
  stopScanLoading: () =>
    set({ scanLoading: { active: false, customerId: null } }),
  }),
  {
    name: 'goldkey-crm-store',          // AsyncStorage 키
    storage: asyncStorageAdapter,
    // UI 상태는 persist 제외 (기기 재시작 시 초기화)
    partialize: (s) =>
      Object.fromEntries(
        Object.entries(s).filter(([k]) => !TRANSIENT_KEYS.includes(k)),
      ),
    version: 1,                          // 스키마 버전 (migrate 대비)
    onRehydrateStorage: () => (state, error) => {
      if (error) {
        console.error('[persist] 복원 실패:', error);
      } else {
        console.info('[persist] AsyncStorage 복원 완료. 고객:', Object.keys(state?.customers ?? {}).length);
      }
    },
  },
));

// ── 휴지통 유틸: 30일 이내 여부 ──────────────────────────────────────────────
const TRASH_EXPIRE_MS = 30 * 24 * 60 * 60 * 1000; // 30일
const isWithinTrashWindow = (deletedAt) => {
  if (!deletedAt) return false;
  return Date.now() - new Date(deletedAt).getTime() < TRASH_EXPIRE_MS;
};

// ── Active Selector (isDeleted:false 만 반환) ─────────────────────────────
export const selCustomer      = (id) => (s) => {
  const c = s.customers[id];
  return c && !c.isDeleted ? c : null;
};
export const selCustomerList  = (s) =>
  Object.values(s.customers).filter((c) => !c.isDeleted);

export const selSchedules     = (customerId) => (s) =>
  Object.values(s.schedules)
    .filter((sc) => sc.customerId === customerId && !sc.isDeleted)
    .sort((a, b) => (a.date > b.date ? 1 : -1));

export const selDateSchedules = (date) => (s) =>
  Object.values(s.schedules).filter((sc) => sc.date === date && !sc.isDeleted);

export const selModal         = (s) => s.scheduleModal;
export const selActiveProfile = (s) => s.activeProfileId;
export const selActiveScan    = (s) => s.activeScanId;

export const selScan          = (id) => (s) => {
  const r = s.scanResults[id];
  return r && !r.isDeleted ? r : null;
};
export const selScansByCustomer = (customerId) => (s) =>
  Object.values(s.scanResults)
    .filter((r) => r.customerId === customerId && !r.isDeleted)
    .sort((a, b) => (a.scannedAt < b.scannedAt ? 1 : -1));

// ── Trash Selector (isDeleted:true AND 30일 이내) ─────────────────────────
/** 휴지통: 삭제된 고객 (30일 이내) */
export const selTrashCustomers = (s) =>
  Object.values(s.customers)
    .filter((c) => c.isDeleted && isWithinTrashWindow(c.deletedAt))
    .sort((a, b) => (a.deletedAt < b.deletedAt ? 1 : -1));

/** 휴지통: 삭제된 일정 (30일 이내) */
export const selTrashSchedules = (s) =>
  Object.values(s.schedules)
    .filter((sc) => sc.isDeleted && isWithinTrashWindow(sc.deletedAt))
    .sort((a, b) => (a.deletedAt < b.deletedAt ? 1 : -1));

/** 휴지통: 삭제된 스캔 결과 (30일 이내) */
export const selTrashScans = (s) =>
  Object.values(s.scanResults)
    .filter((r) => r.isDeleted && isWithinTrashWindow(r.deletedAt))
    .sort((a, b) => (a.deletedAt < b.deletedAt ? 1 : -1));

/** 휴지통 전체 카운트 (뱃지용) */
export const selTrashCount = (s) =>
  selTrashCustomers(s).length +
  selTrashSchedules(s).length +
  selTrashScans(s).length;
