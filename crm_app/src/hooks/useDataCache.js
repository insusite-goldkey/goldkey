/**
 * useDataCache — 30분 TTL 로컬 캐시 훅 (Stale-While-Revalidate)
 *
 * ┌ 설계 원칙 ──────────────────────────────────────────────────────┐
 * │  • 신규 패키지 0 (React Query / SWR 없이 순수 JS 구현)          │
 * │  • 동일 키 데이터를 TTL 내 재요청 시 → 서버 호출 완전 차단      │
 * │  • TTL 경과 후 → 캐시 데이터 즉시 반환(stale) + 백그라운드 갱신 │
 * │  • Zustand + 모듈 레벨 캐시 맵 조합                             │
 * │                                                                  │
 * │  캐시 저장소: 모듈 레벨 Map (앱 수명 동안 유지)                 │
 * │  TTL 기본값: 30분 (1_800_000 ms)                                 │
 * │  Firebase Read 비용 최소화 전략:                                 │
 * │    동일 고객 프로필 30분 내 재조회 → 0 Read (캐시 반환)          │
 * │    TTL 경과 → stale 즉시 표시 + 백그라운드 revalidate            │
 * └────────────────────────────────────────────────────────────────┘
 *
 * 사용법:
 *   const { data, isLoading, isStale, refresh } = useDataCache(
 *     `customer_${customerId}`,
 *     () => fetchCustomerFromFirestore(customerId),
 *     { ttl: 30 * 60 * 1000 }
 *   );
 */

import { useCallback, useEffect, useRef, useState } from 'react';

// ── 모듈 레벨 캐시 저장소 ─────────────────────────────────────────────────────
// Map<key, { data, fetchedAt, ttl, promise }>
const CACHE_STORE = new Map();

const DEFAULT_TTL        = 30 * 60 * 1000; // 30분
const BACKGROUND_DELAY   = 100;             // stale 반환 후 revalidate 대기 ms

// ── 캐시 유틸 ─────────────────────────────────────────────────────────────────
const isFresh = (entry) =>
  entry && (Date.now() - entry.fetchedAt) < entry.ttl;

const isStaleEntry = (entry) =>
  entry && !isFresh(entry);

/**
 * 캐시 수동 무효화 — 데이터 mutate(추가/수정/삭제) 후 반드시 호출
 * @param {string|RegExp} keyOrPattern — 정확한 키 또는 prefix 패턴
 */
export const invalidateCache = (keyOrPattern) => {
  if (typeof keyOrPattern === 'string') {
    CACHE_STORE.delete(keyOrPattern);
  } else if (keyOrPattern instanceof RegExp) {
    for (const k of CACHE_STORE.keys()) {
      if (keyOrPattern.test(k)) CACHE_STORE.delete(k);
    }
  }
};

/**
 * 캐시 전체 초기화 — 로그아웃 시 호출
 */
export const clearAllCache = () => CACHE_STORE.clear();

/**
 * 캐시 통계 조회 — 디버깅용
 */
export const getCacheStats = () => {
  const entries = [...CACHE_STORE.entries()];
  return {
    totalKeys:  entries.length,
    freshKeys:  entries.filter(([, v]) => isFresh(v)).length,
    staleKeys:  entries.filter(([, v]) => isStaleEntry(v)).length,
    keys:       entries.map(([k, v]) => ({
      key:      k,
      age:      Math.round((Date.now() - v.fetchedAt) / 1000) + 's',
      isFresh:  isFresh(v),
    })),
  };
};

// ── 메인 훅 ──────────────────────────────────────────────────────────────────
/**
 * useDataCache
 *
 * @param {string}   cacheKey    — 캐시 키 (예: `customer_${id}`, `scans_${id}`)
 * @param {Function} fetchFn     — 데이터를 가져오는 async 함수 () => Promise<data>
 * @param {object}   options
 * @param {number}   [options.ttl=1_800_000]   — TTL (ms), 기본 30분
 * @param {boolean}  [options.enabled=true]    — false이면 fetch 실행 안 함
 * @param {boolean}  [options.revalidateOnMount=false] — 마운트 시 항상 재검증
 * @param {Function} [options.onSuccess]       — 새 데이터 수신 시 콜백
 * @param {Function} [options.onError]         — 에러 발생 시 콜백
 *
 * @returns {{
 *   data:       any,       현재 데이터 (stale 포함)
 *   isLoading:  boolean,   최초 로딩 중 (캐시 없음)
 *   isFetching: boolean,   백그라운드 fetch 중
 *   isStale:    boolean,   TTL 경과 데이터 사용 중
 *   error:      Error|null,
 *   refresh:    Function,  수동 강제 갱신
 * }}
 */
const useDataCache = (cacheKey, fetchFn, options = {}) => {
  const {
    ttl               = DEFAULT_TTL,
    enabled           = true,
    revalidateOnMount = false,
    onSuccess         = null,
    onError           = null,
  } = options;

  const cached        = CACHE_STORE.get(cacheKey);
  const hasFreshCache = isFresh(cached);
  const hasStaleCache = isStaleEntry(cached);

  const [data,       setData]       = useState(cached?.data ?? null);
  const [isLoading,  setIsLoading]  = useState(!hasFreshCache && !hasStaleCache && enabled);
  const [isFetching, setIsFetching] = useState(false);
  const [error,      setError]      = useState(null);
  const [isStale,    setIsStale]    = useState(hasStaleCache);

  const mountedRef   = useRef(true);
  const fetchingRef  = useRef(false); // 동시 중복 요청 방지

  // ── 실제 fetch 실행 ────────────────────────────────────────────────────────
  const executeFetch = useCallback(async (force = false) => {
    if (!enabled || !fetchFn)       return;
    if (fetchingRef.current)        return; // 중복 요청 차단

    const entry = CACHE_STORE.get(cacheKey);
    if (!force && isFresh(entry))   return; // 신선한 캐시 있으면 skip

    fetchingRef.current = true;
    setIsFetching(true);
    setError(null);

    try {
      const result = await fetchFn();
      if (!mountedRef.current) return;

      const newEntry = { data: result, fetchedAt: Date.now(), ttl };
      CACHE_STORE.set(cacheKey, newEntry);

      setData(result);
      setIsStale(false);
      setIsLoading(false);
      onSuccess?.(result);
    } catch (e) {
      if (!mountedRef.current) return;
      setError(e);
      setIsLoading(false);
      onError?.(e);
      console.error(`[useDataCache] fetch error for key="${cacheKey}":`, e?.message);
    } finally {
      fetchingRef.current = false;
      if (mountedRef.current) setIsFetching(false);
    }
  }, [cacheKey, fetchFn, ttl, enabled, onSuccess, onError]);

  // ── 마운트 시 전략 ──────────────────────────────────────────────────────────
  useEffect(() => {
    mountedRef.current = true;

    if (!enabled) return;

    const entry = CACHE_STORE.get(cacheKey);

    if (isFresh(entry) && !revalidateOnMount) {
      // 신선한 캐시 → 즉시 사용, fetch 없음
      setData(entry.data);
      setIsLoading(false);
      setIsStale(false);
      return;
    }

    if (isStaleEntry(entry)) {
      // Stale-While-Revalidate: 즉시 stale 데이터 반환 후 백그라운드 재검증
      setData(entry.data);
      setIsLoading(false);
      setIsStale(true);
      const timer = setTimeout(() => executeFetch(), BACKGROUND_DELAY);
      return () => clearTimeout(timer);
    }

    // 캐시 없음: 첫 fetch
    setIsLoading(true);
    executeFetch();

    return () => { mountedRef.current = false; };
  }, [cacheKey, enabled, revalidateOnMount]);

  // ── 수동 강제 갱신 ────────────────────────────────────────────────────────
  const refresh = useCallback(() => {
    CACHE_STORE.delete(cacheKey);
    setIsStale(false);
    executeFetch(true);
  }, [cacheKey, executeFetch]);

  return { data, isLoading, isFetching, isStale, error, refresh };
};

export default useDataCache;

// ── 멀티 키 프리페치 유틸 ────────────────────────────────────────────────────
/**
 * prefetchData — 화면 진입 전 미리 캐시 워밍
 * 예: 고객 목록 화면에서 각 고객 프로필을 미리 로드
 *
 * @param {Array<{key: string, fetchFn: Function, ttl?: number}>} entries
 */
export const prefetchData = async (entries) => {
  const tasks = entries.map(async ({ key, fetchFn, ttl = DEFAULT_TTL }) => {
    if (isFresh(CACHE_STORE.get(key))) return; // 이미 신선한 캐시 있으면 skip
    try {
      const data = await fetchFn();
      CACHE_STORE.set(key, { data, fetchedAt: Date.now(), ttl });
    } catch (e) {
      console.warn(`[prefetchData] key="${key}" failed:`, e?.message);
    }
  });
  await Promise.allSettled(tasks);
};

// ── 캐시 키 네임스페이스 상수 (오타 방지 SSOT) ───────────────────────────────
export const CACHE_KEYS = Object.freeze({
  customer:     (id)         => `customer_${id}`,
  customerList: (agentId)    => `customer_list_${agentId}`,
  scans:        (customerId) => `scans_${customerId}`,
  schedules:    (date)       => `schedules_${date}`,
  scanDetail:   (scanId)     => `scan_detail_${scanId}`,
});
