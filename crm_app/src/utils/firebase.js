/**
 * firebase.js — Firebase 초기화 + Firestore 오프라인 지속성
 *
 * ┌ 3중 데이터 안전망 2단계 ─────────────────────────────────────┐
 * │  1) Firestore 오프라인 캐시 (100MB, 자동 sync)               │
 * │  2) Soft Delete 아키텍처 (isDeleted + 30일 복구)             │
 * │  3) AsyncStorage 로컬 Zustand persist (앱 재시작 유지)       │
 * └────────────────────────────────────────────────────────────┘
 *
 * google-services.json (Android) / GoogleService-Info.plist (iOS)
 * 파일이 없으면 Firebase 기능은 비활성화되고 로컬 모드로만 동작.
 * FIREBASE_SETUP_GUIDE.md 참고.
 *
 * 사용:
 *   import { db, COLLECTIONS, isFirebaseReady } from '../utils/firebase';
 */

import firestore from '@react-native-firebase/firestore';
import app       from '@react-native-firebase/app';

// ── Firebase 초기화 상태 ──────────────────────────────────────────────────
// google-services.json / GoogleService-Info.plist 없으면 앱 초기화 자체가
// 실패하므로 try-catch로 감싸 로컬 모드 폴백 보장.
let _firestoreInstance = null;
let _isFirebaseReady   = false;

const initFirebase = () => {
  try {
    // 앱이 초기화되었는지 확인 (google-services.json 필요)
    if (!app().options?.projectId) {
      console.warn('[firebase] google-services.json 미설정 → 로컬 모드로 동작');
      return false;
    }

    // Firestore 오프라인 지속성 + 캐시 100MB 설정
    firestore().settings({
      persistence:    true,
      cacheSizeBytes: 100 * 1024 * 1024, // 100MB
    });

    _firestoreInstance = firestore();
    _isFirebaseReady   = true;
    console.info('[firebase] ✅ Firestore 연결 완료 | 프로젝트:', app().options.projectId);
    return true;
  } catch (e) {
    console.warn('[firebase] ⚠️ 초기화 실패 (로컬 모드):', e?.message ?? e?.code);
    return false;
  }
};

initFirebase();

// ── 공개 인스턴스 + 상태 ─────────────────────────────────────────────────
/** Firestore 인스턴스 (google-services.json 없으면 null) */
export const db = _firestoreInstance;

/** Firebase 연결 여부 — 조건부 렌더링에 활용 */
export const isFirebaseReady = () => _isFirebaseReady;

/** Firebase 연결 상태 재확인 (런타임 중 재시도용) */
export const retryFirebaseInit = () => initFirebase();

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
