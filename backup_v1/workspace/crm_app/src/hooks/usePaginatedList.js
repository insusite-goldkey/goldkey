/**
 * usePaginatedList — 커서 기반 페이징 훅
 *
 * ┌ 설계 원칙 ──────────────────────────────────────────────────────┐
 * │  • Zustand SSOT 데이터를 기반으로 클라이언트 사이드 페이징       │
 * │  • 현재: Zustand 로컬 스토어에서 페이징 (Firebase 연동 전 단계) │
 * │  • Firebase 연동 시: fetchNextPage()를 Firestore 쿼리로 교체    │
 * │                                                                  │
 * │  흐름:                                                           │
 * │    전체 데이터 배열 → 20개씩 슬라이싱 → FlatList에 주입         │
 * │    "더 보기" / onEndReached → 다음 20개 추가 (누적 방식)        │
 * │                                                                  │
 * │  Firebase 연동 시 교체할 부분:                                   │
 * │    fetchNextPage 내부의 localFetch → Firestore 쿼리로 swap       │
 * └────────────────────────────────────────────────────────────────┘
 *
 * 사용법:
 *   const {
 *     items,          // 현재까지 로드된 아이템 배열
 *     hasMore,        // 더 로드할 항목 있음 여부
 *     isLoadingMore,  // 추가 로딩 중 여부
 *     isInitializing, // 첫 로드 중 여부
 *     loadMore,       // 다음 페이지 로드 (onEndReached에 연결)
 *     reset,          // 필터 변경 시 처음으로 리셋
 *     totalCount,     // 전체 항목 수 (필터 포함)
 *   } = usePaginatedList(allItems, { pageSize: 20, filterFn, sortFn });
 */

import { useCallback, useEffect, useRef, useState } from 'react';

const DEFAULT_PAGE_SIZE = 20;

/**
 * @param {Array}    allItems   — Zustand에서 가져온 전체 정렬/필터된 배열
 * @param {object}   options
 * @param {number}   [options.pageSize=20]   — 한 번에 로드할 항목 수
 * @param {Function} [options.filterFn]      — 추가 필터 함수 (item) => bool
 * @param {Function} [options.sortFn]        — 정렬 함수 (a, b) => number
 * @param {string}   [options.key]           — 필터/정렬 변경 감지 키 (선택)
 */
const usePaginatedList = (allItems = [], options = {}) => {
  const {
    pageSize  = DEFAULT_PAGE_SIZE,
    filterFn  = null,
    sortFn    = null,
    key       = '',
  } = options;

  const [page,           setPage]           = useState(1);
  const [isLoadingMore,  setIsLoadingMore]  = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const prevKeyRef = useRef(key);

  // ── key(필터/정렬) 변경 시 자동 리셋 ─────────────────────────────────────
  useEffect(() => {
    if (prevKeyRef.current !== key) {
      prevKeyRef.current = key;
      setPage(1);
      setIsInitializing(true);
    }
  }, [key]);

  // ── allItems 최초 수신 시 초기화 완료 표시 ────────────────────────────────
  useEffect(() => {
    if (allItems.length >= 0) {
      const timer = setTimeout(() => setIsInitializing(false), 50);
      return () => clearTimeout(timer);
    }
  }, [allItems]);

  // ── 필터 + 정렬 적용 ─────────────────────────────────────────────────────
  const processedItems = (() => {
    let result = allItems;
    if (filterFn)  result = result.filter(filterFn);
    if (sortFn)    result = [...result].sort(sortFn);
    return result;
  })();

  const totalCount  = processedItems.length;
  const slicedItems = processedItems.slice(0, page * pageSize);
  const hasMore     = slicedItems.length < totalCount;

  // ── 다음 페이지 로드 ──────────────────────────────────────────────────────
  const loadMore = useCallback(() => {
    if (isLoadingMore || !hasMore) return;
    setIsLoadingMore(true);
    // 실제 네트워크 요청 흉내 (Firestore 연동 전: 즉시 처리)
    // Firebase 연동 시: 여기서 Firestore 커서 쿼리 실행 후 setPage
    requestAnimationFrame(() => {
      setPage((p) => p + 1);
      setIsLoadingMore(false);
    });
  }, [isLoadingMore, hasMore]);

  // ── 리셋 (검색어/필터 변경 시 호출) ──────────────────────────────────────
  const reset = useCallback(() => {
    setPage(1);
    setIsInitializing(true);
    setTimeout(() => setIsInitializing(false), 50);
  }, []);

  return {
    items:          slicedItems,
    hasMore,
    isLoadingMore,
    isInitializing,
    loadMore,
    reset,
    totalCount,
    currentPage:    page,
    pageSize,
  };
};

export default usePaginatedList;

// ── Firebase 연동용 커서 페이징 훅 (Firestore 사용 시 교체) ─────────────────
/**
 * useFirestorePaginatedList — Firestore 커서 기반 페이징
 *
 * 현재 미사용 (Zustand 로컬 모드). Firebase 연동 시 usePaginatedList를
 * 이 훅으로 swap하면 됩니다.
 *
 * 쿼리 예시 (고객 목록):
 *   db.collection('customers')
 *     .where('isDeleted', '==', false)
 *     .where('agentId', '==', agentId)
 *     .orderBy('createdAt', 'desc')
 *     .limit(20)
 *     .startAfter(lastDoc)   ← 커서 (이전 페이지 마지막 문서)
 *
 * firestore.indexes.json에 정의된 복합 인덱스 적용:
 *   [agentId ASC, isDeleted ASC, createdAt DESC]
 */
export const useFirestorePaginatedList = ({
  collectionName,
  baseQuery,
  pageSize = DEFAULT_PAGE_SIZE,
  enabled  = false,
}) => {
  const [items,          setItems]          = useState([]);
  const [lastDoc,        setLastDoc]        = useState(null);
  const [hasMore,        setHasMore]        = useState(true);
  const [isLoadingMore,  setIsLoadingMore]  = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  const loadPage = useCallback(async (cursor = null) => {
    if (!enabled || !baseQuery) return;
    setIsLoadingMore(true);
    try {
      let q = baseQuery.orderBy('createdAt', 'desc').limit(pageSize);
      if (cursor) q = q.startAfter(cursor);

      const snap = await q.get();
      const newDocs = snap.docs.map((d) => ({ id: d.id, ...d.data() }));

      setItems((prev) => cursor ? [...prev, ...newDocs] : newDocs);
      setLastDoc(snap.docs[snap.docs.length - 1] ?? null);
      setHasMore(newDocs.length === pageSize);
    } catch (e) {
      console.error('[useFirestorePaginatedList]', e);
    } finally {
      setIsLoadingMore(false);
      setIsInitializing(false);
    }
  }, [baseQuery, pageSize, enabled]);

  useEffect(() => { loadPage(null); }, []);

  const loadMore = useCallback(() => {
    if (!isLoadingMore && hasMore && lastDoc) loadPage(lastDoc);
  }, [isLoadingMore, hasMore, lastDoc, loadPage]);

  const reset = useCallback(() => {
    setItems([]);
    setLastDoc(null);
    setHasMore(true);
    setIsInitializing(true);
    loadPage(null);
  }, [loadPage]);

  return { items, hasMore, isLoadingMore, isInitializing, loadMore, reset, totalCount: items.length };
};
