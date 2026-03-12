'use strict';
/**
 * src/store/authStore.js — Goldkey AI Masters 2026
 * 인증 전용 Zustand 스토어 (persisted to AsyncStorage).
 *
 * 상태:
 *   personId   — 인증된 person UUID (null = 미인증)
 *   personName — 표시용 이름
 *   authedAt   — 인증 완료 ISO 시각
 *
 * SESSION_TTL_MS(기본 8시간) 초과 시 자동 만료.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SESSION_TTL_MS = 8 * 60 * 60 * 1000; // 8시간

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // ── 상태 ────────────────────────────────────────────────
      personId:   null,
      personName: '',
      authedAt:   null,

      // ── 인증 완료 ─────────────────────────────────────────
      setAuth: (personId, personName) =>
        set({
          personId,
          personName,
          authedAt: new Date().toISOString(),
        }),

      // ── 로그아웃 ──────────────────────────────────────────
      clearAuth: () =>
        set({ personId: null, personName: '', authedAt: null }),

      // ── 세션 유효 여부 확인 ───────────────────────────────
      isAuthenticated: () => {
        const { personId, authedAt } = get();
        if (!personId || !authedAt) return false;
        const elapsed = Date.now() - new Date(authedAt).getTime();
        return elapsed < SESSION_TTL_MS;
      },
    }),
    {
      name:    'goldkey-auth',
      storage: createJSONStorage(() => AsyncStorage),
      // personId, personName, authedAt 만 저장 (함수 제외)
      partialize: (s) => ({
        personId:   s.personId,
        personName: s.personName,
        authedAt:   s.authedAt,
      }),
    },
  ),
);

// ── Selector 헬퍼 ─────────────────────────────────────────────────────────
export const selectIsAuthenticated = (s) => s.isAuthenticated;
export const selectPersonId        = (s) => s.personId;
export const selectPersonName      = (s) => s.personName;
export const selectSetAuth         = (s) => s.setAuth;
export const selectClearAuth       = (s) => s.clearAuth;
