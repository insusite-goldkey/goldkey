/**
 * firebase.js — Firebase 초기화 + Firestore 오프라인 지속성
 *
 * ☁️ 2단계: Firestore Offline Persistence
 * ─────────────────────────────────────────────────────────────────
 * enableIndexedDbPersistence (Web SDK) ↔ React Native Firebase는
 * 기본적으로 오프라인 캐시가 활성화되어 있으며,
 * settings({ persistence: true }) 로 명시적 보장.
 *
 * 동작:
 *  - 오프라인 상태에서 write → 로컬 큐에 저장
 *  - 네트워크 복구 즉시 → 백그라운드 자동 sync
 *  - 사용자에게 에러 없이 투명하게 처리
 *
 * 사용:
 *   import { db, COLLECTIONS } from '../utils/firebase';
 *   import { doc, setDoc } from '@react-native-firebase/firestore';
 */

import firestore from '@react-native-firebase/firestore';

// ── Firestore 오프라인 지속성 설정 ─────────────────────────────────────────
// React Native Firebase는 기본적으로 오프라인 캐시가 내장되어 있음.
// settings()로 캐시 사이즈를 명시적으로 100MB로 확장.
firestore().settings({
  persistence:    true,          // 오프라인 데이터 영속화 (기본값 true)
  cacheSizeBytes: 100 * 1024 * 1024, // 100MB (기본 40MB → 확장)
});

// ── Firestore 인스턴스 ──────────────────────────────────────────────────────
export const db = firestore();

// ── 컬렉션 이름 상수 (오타 방지 SSOT) ──────────────────────────────────────
export const COLLECTIONS = Object.freeze({
  CUSTOMERS:  'customers',
  SCHEDULES:  'schedules',
  SCAN_RESULTS: 'scan_results',
  AUDIT_LOGS: 'audit_logs',
  TRASH:      'trash',
});

// ── Firestore 헬퍼 함수들 ───────────────────────────────────────────────────

/**
 * upsertDoc — 문서 생성 또는 전체 갱신 (merge:true → 일부 필드만 갱신)
 * 오프라인 상태에서도 로컬 큐에 저장 후 자동 sync.
 */
export const upsertDoc = async (collectionName, docId, data) => {
  try {
    await db.collection(collectionName).doc(docId).set(data, { merge: true });
  } catch (e) {
    // Firestore 오프라인 큐가 처리하므로 에러 숨김 (큐에 쌓임)
    console.warn(`[firebase] upsertDoc(${collectionName}/${docId}) 오프라인 큐 저장:`, e?.code);
  }
};

/**
 * softDeleteDoc — Soft Delete: isDeleted:true + deletedAt 필드 추가
 * deleteDoc() 절대 금지. 이 함수만 사용할 것.
 *
 * @param {string} collectionName
 * @param {string} docId
 * @param {string} [deletedBy]  — 삭제한 사용자 ID (audit용)
 */
export const softDeleteDoc = async (collectionName, docId, deletedBy = 'unknown') => {
  const deletedAt = new Date().toISOString();
  try {
    await db.collection(collectionName).doc(docId).update({
      isDeleted: true,
      deletedAt,
      deletedBy,
    });
    // audit_log 기록
    await db.collection(COLLECTIONS.AUDIT_LOGS).add({
      action:     'SOFT_DELETE',
      collection: collectionName,
      docId,
      deletedBy,
      deletedAt,
    });
  } catch (e) {
    console.warn(`[firebase] softDeleteDoc(${collectionName}/${docId}) 오프라인 큐 저장:`, e?.code);
  }
};

/**
 * restoreDoc — 휴지통에서 복구: isDeleted:false + 관련 필드 제거
 */
export const restoreDoc = async (collectionName, docId, restoredBy = 'unknown') => {
  try {
    await db.collection(collectionName).doc(docId).update({
      isDeleted:  false,
      deletedAt:  null,
      deletedBy:  null,
    });
    await db.collection(COLLECTIONS.AUDIT_LOGS).add({
      action:     'RESTORE',
      collection: collectionName,
      docId,
      restoredBy,
      restoredAt: new Date().toISOString(),
    });
  } catch (e) {
    console.warn(`[firebase] restoreDoc(${collectionName}/${docId}):`, e?.code);
  }
};

/**
 * getActiveQuery — isDeleted:false 필터가 적용된 컬렉션 쿼리
 * 모든 목록 조회는 반드시 이 함수를 통해 isDeleted:false 필터 적용.
 */
export const getActiveQuery = (collectionName) =>
  db.collection(collectionName).where('isDeleted', '==', false);

/**
 * getTrashQuery — 휴지통 쿼리: isDeleted:true AND deletedAt 최근 30일 이내
 * 30일 경과 데이터는 Cloud Functions에서 자동 하드 삭제 권장.
 */
export const getTrashQuery = (collectionName) => {
  const cutoff = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
  return db
    .collection(collectionName)
    .where('isDeleted', '==', true)
    .where('deletedAt', '>=', cutoff);
};
