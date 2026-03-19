'use strict';
/**
 * src/store/authStore.js — Goldkey AI Masters 2026
 * 인증 전용 Zustand 스토어 (persisted to AsyncStorage).
 *
 * 상태:
 *   personId     — 인증된 person UUID (null = 미인증)
 *   personName   — 표시용 이름
 *   userRole     — 'agent' | 'customer'
 *   authedAt     — 인증 완료 ISO 시각
 *   accessToken  — 모 앱 SSO로부터 수신한 토큰 (GP-SSO §2)
 *   ssoVerified  — SSO 딥링크로 인증된 여부
 *
 * SESSION_TTL_MS(기본 8시간) 초과 시 자동 만료.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getSupabase } from '../services/supabaseService';

const SESSION_TTL_MS = 8 * 60 * 60 * 1000; // 8시간

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // ── 상태 ────────────────────────────────────────────────
      personId:    null,
      personName:  '',
      userRole:    'customer',
      authedAt:    null,
      accessToken: null,
      ssoVerified: false,

      // ── 일반 인증 완료 (TOTP) ─────────────────────────────
      setAuth: (personId, personName, userRole = 'customer') =>
        set({
          personId,
          personName,
          userRole,
          authedAt:    new Date().toISOString(),
          ssoVerified: false,
        }),

      // ── [GP-SSO §2] 모 앱 딥링크 SSO 인증 ────────────────
      // token: 모 앱 _auto_login_token (HMAC-SHA256 32자)
      setSsoAuth: async (token, userId, name, role = 'customer') => {
        try {
          // Supabase 세션에 토큰 적용 (있는 경우)
          // 모 앱 토큰은 Supabase JWT가 아니므로 직접 세션 등록 대신
          // Supabase anon 상태로 두고 app-level 인증만 처리
          const sb = getSupabase();
          // Supabase access_token 형식(JWT)이면 setSession 시도
          if (token && token.split('.').length === 3) {
            await sb.auth.setSession({
              access_token:  token,
              refresh_token: token,
            }).catch(() => null);
          }
        } catch (_e) {
          // 토큰 형식 불일치 시 app-level 인증만 진행
        }
        set({
          personId:    userId,
          personName:  name,
          userRole:    role,
          authedAt:    new Date().toISOString(),
          accessToken: token,
          ssoVerified: true,
        });
      },

      // ── 로그아웃 ──────────────────────────────────────────
      clearAuth: () =>
        set({
          personId:    null,
          personName:  '',
          userRole:    'customer',
          authedAt:    null,
          accessToken: null,
          ssoVerified: false,
        }),

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
      partialize: (s) => ({
        personId:    s.personId,
        personName:  s.personName,
        userRole:    s.userRole,
        authedAt:    s.authedAt,
        accessToken: s.accessToken,
        ssoVerified: s.ssoVerified,
      }),
    },
  ),
);

// ── Selector 헬퍼 ─────────────────────────────────────────────────────────
export const selectIsAuthenticated = (s) => s.isAuthenticated;
export const selectPersonId        = (s) => s.personId;
export const selectPersonName      = (s) => s.personName;
export const selectUserRole        = (s) => s.userRole;
export const selectSsoVerified     = (s) => s.ssoVerified;
export const selectSetAuth         = (s) => s.setAuth;
export const selectSetSsoAuth      = (s) => s.setSsoAuth;
export const selectClearAuth       = (s) => s.clearAuth;
