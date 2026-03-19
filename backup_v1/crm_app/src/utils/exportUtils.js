/**
 * exportUtils.js — 고객/일정 데이터 CSV 내보내기 유틸리티
 *
 * ┌ 전략 ───────────────────────────────────────────────────────────┐
 * │  React Native 환경 → 브라우저 Blob/Download API 없음           │
 * │  대신 RN 내장 Share.share() API로 CSV 텍스트 공유/저장         │
 * │  외부 패키지 의존성 0 (xlsx 라이브러리 불필요)                  │
 * │                                                                  │
 * │  흐름:                                                           │
 * │    SSOT 데이터 → CSV 문자열 생성 → Share.share() 호출          │
 * │    → iOS: 파일 앱 저장 / 이메일 전송 / AirDrop 가능            │
 * │    → Android: 파일 저장 / Google Drive / 이메일 가능           │
 * └────────────────────────────────────────────────────────────────┘
 *
 * 함수:
 *   exportCustomers(customers, scanResults) — 고객 명부 CSV
 *   exportSchedules(schedules, customers)   — 일정 명부 CSV
 *   exportAll(store)                        — 고객+일정 통합 (2회 Share)
 */

import { Share } from 'react-native';

// ── 날짜 포맷 헬퍼 ────────────────────────────────────────────────────────────
const formatDate = (iso) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('ko-KR', {
      year: 'numeric', month: '2-digit', day: '2-digit',
    }).replace(/\. /g, '-').replace('.', '');
  } catch {
    return iso;
  }
};

const formatDateTime = (iso) => {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  } catch {
    return iso;
  }
};

// ── 파일명 생성 ───────────────────────────────────────────────────────────────
const makeFilename = (type) => {
  const today = new Date().toISOString().slice(0, 10);
  return `GoldKey_${type}_${today}.csv`;
};

// ── CSV 이스케이프 (쉼표·줄바꿈·큰따옴표 처리) ───────────────────────────────
const escapeCell = (val) => {
  if (val === null || val === undefined) return '';
  const str = String(val);
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
};

const toCsvRow = (cells) => cells.map(escapeCell).join(',');

// ── BOM 헤더 (엑셀 한글 인식) ─────────────────────────────────────────────────
const BOM = '\uFEFF';

// ── 고객 명부 CSV 생성 ────────────────────────────────────────────────────────
/**
 * @param {object} customers   — customerStore.customers HashMap
 * @param {object} scanResults — customerStore.scanResults HashMap
 * @returns {string} CSV 문자열 (BOM 포함)
 */
export const buildCustomersCsv = (customers, scanResults = {}) => {
  const header = toCsvRow([
    '고객ID', '이름', '나이', '성별', '직업',
    '연락처', '회사', '직위', '등록여부',
    '태그', '메모', '등록일', '최근수정일', '스캔기록수',
  ]);

  // 스캔 카운트 사전 계산 (isDeleted:false 만)
  const scanCountMap = {};
  Object.values(scanResults).forEach((r) => {
    if (!r.isDeleted) {
      scanCountMap[r.customerId] = (scanCountMap[r.customerId] || 0) + 1;
    }
  });

  const rows = Object.values(customers)
    .filter((c) => !c.isDeleted)
    .sort((a, b) => a.name.localeCompare(b.name, 'ko'))
    .map((c) => toCsvRow([
      c.id,
      c.name,
      c.age || '',
      c.gender || '',
      c.job || '',
      c.phone || '',
      c.company || '',
      c.title || '',
      c.registered ? '등록' : '미등록',
      (c.tags || []).join(' | '),
      c.memo || '',
      formatDate(c.createdAt),
      formatDate(c.updatedAt),
      scanCountMap[c.id] || 0,
    ]));

  return BOM + [header, ...rows].join('\n');
};

// ── 일정 명부 CSV 생성 ────────────────────────────────────────────────────────
const CATEGORY_LABEL = {
  consult:     '상담',
  appointment: '약속',
  todo:        '할 일',
  personal:    '개인',
};

/**
 * @param {object} schedules — customerStore.schedules HashMap
 * @param {object} customers — customerStore.customers HashMap
 * @returns {string} CSV 문자열 (BOM 포함)
 */
export const buildSchedulesCsv = (schedules, customers = {}) => {
  const header = toCsvRow([
    '일정ID', '고객명', '고객ID', '일정분류',
    '날짜', '시작시간', '종료시간', '완료여부',
    '메모', '등록일',
  ]);

  const rows = Object.values(schedules)
    .filter((sc) => !sc.isDeleted)
    .sort((a, b) => (a.date > b.date ? 1 : -1))
    .map((sc) => {
      const cust = customers[sc.customerId];
      return toCsvRow([
        sc.id,
        cust?.name || '(고객 없음)',
        sc.customerId || '',
        CATEGORY_LABEL[sc.category] || sc.category || '',
        sc.date || '',
        sc.startTime || '',
        sc.endTime || '',
        sc.done ? '완료' : '예정',
        sc.memo || '',
        formatDateTime(sc.createdAt || ''),
      ]);
    });

  return BOM + [header, ...rows].join('\n');
};

// ── 공유 실행 ─────────────────────────────────────────────────────────────────
/**
 * shareFile — CSV 텍스트를 Share.share()로 공유
 * iOS: 파일 앱 저장 / 이메일 / AirDrop
 * Android: 파일 저장 / Google Drive / 이메일
 *
 * @param {string} csvContent  — CSV 문자열
 * @param {string} filename    — 권장 파일명 (메시지에 포함)
 * @param {string} title       — 공유 시트 타이틀
 * @returns {Promise<boolean>} — 공유 완료 여부
 */
export const shareFile = async (csvContent, filename, title) => {
  const result = await Share.share(
    {
      message: csvContent,   // Android: 텍스트 공유
      title,                 // Android 공유 시트 타이틀
    },
    {
      dialogTitle: `${filename} 저장/공유`,
      subject:     title,    // 이메일 제목
    },
  );
  return result.action !== Share.dismissedAction;
};

// ── 통합 내보내기 (고객 + 일정) ───────────────────────────────────────────────
/**
 * exportAll — 고객 명부와 일정 명부를 순차적으로 공유
 *
 * @param {{customers, schedules, scanResults}} storeState
 * @returns {Promise<{customersShared: boolean, schedulesShared: boolean}>}
 */
export const exportAll = async (storeState) => {
  const { customers, schedules, scanResults } = storeState;

  // ① 고객 명부
  const customersCsv = buildCustomersCsv(customers, scanResults);
  const customersFile = makeFilename('고객백업');
  const customersShared = await shareFile(
    customersCsv,
    customersFile,
    `GoldKey 고객 명부 (${Object.values(customers).filter(c => !c.isDeleted).length}명)`,
  );

  if (!customersShared) {
    return { customersShared: false, schedulesShared: false };
  }

  // ② 일정 명부
  const schedulesCsv = buildSchedulesCsv(schedules, customers);
  const schedulesFile = makeFilename('일정백업');
  const schedulesShared = await shareFile(
    schedulesCsv,
    schedulesFile,
    `GoldKey 일정 명부 (${Object.values(schedules).filter(s => !s.isDeleted).length}건)`,
  );

  return { customersShared, schedulesShared };
};

// ── 개별 내보내기 ─────────────────────────────────────────────────────────────
export const exportCustomersOnly = async (customers, scanResults) => {
  const csv  = buildCustomersCsv(customers, scanResults);
  const file = makeFilename('고객백업');
  return shareFile(
    csv,
    file,
    `GoldKey 고객 명부 (${Object.values(customers).filter(c => !c.isDeleted).length}명)`,
  );
};

export const exportSchedulesOnly = async (schedules, customers) => {
  const csv  = buildSchedulesCsv(schedules, customers);
  const file = makeFilename('일정백업');
  return shareFile(
    csv,
    file,
    `GoldKey 일정 명부 (${Object.values(schedules).filter(s => !s.isDeleted).length}건)`,
  );
};
