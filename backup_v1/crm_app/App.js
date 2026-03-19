/**
 * 골드키 CRM 앱 진입점 (App.js) — Goldkey AI Masters 2026
 * React Native CLI 기준
 *
 * ┌ 마스터-그림자 아키텍처 (GP §1·§2·§3) ──────────────────────────────────┐
 * │  앱 시작 → SSO 인증(GP-SSO §3) → <RoutingGuard />                    │
 * │         ├─ [미인증]  OtpAuthScreen  → 모 앱 SSO 리다이렉트           │
 * │         └─ [인증됨]  DashboardLite  (초경량 메인 화면)                │
 * │              ├─ 오늘의 업무 탭 (TaskCard)                            │
 * │              ├─ 고객 목록/입력 탭 (shared/CustomerComponents)        │
 * │              └─ 딥링크 발사대 탭 → 모 앱 AI 기능 위임               │
 * └──────────────────────────────────────────────────────────────────────┘
 *
 * [GP §1] 공통 모듈: src/shared/customerSchema.js
 *                    src/shared/CustomerComponents.js
 * [GP §2] 양방향 CRUD: src/shared/supabaseCrud.js → customerInputForm()
 * [GP §3] 딥링크 발사대: DeepLinkButton → 모 앱 URL 전송
 */

import React, { useEffect, useCallback } from 'react';
import { StyleSheet, View, Linking }     from 'react-native';
import { useCustomerStore }              from './src/store/customerStore';
import { useAuthStore }                  from './src/store/authStore';
import Dashboard                         from './src/screens/DashboardLite';
import CustomerProfileView               from './src/screens/CustomerProfileView';
import MedicalScanResultView             from './src/screens/MedicalScanResultView';
import ScheduleInputModal                from './src/components/ScheduleInputModal';
import PremiumLoadingUI                  from './src/components/PremiumLoadingUI';
import TrashScreen                       from './src/screens/TrashScreen';
import GoldKeyCustomerScreen             from './src/screens/GoldKeyCustomerScreen';
import OtpAuthScreen                     from './src/screens/OtpAuthScreen';

// ── 메인 라우팅 가드 ─────────────────────────────────────────────────────────
/**
 * RoutingGuard — 인증 통과 후 CRM 메인 화면 분기.
 *
 * activeProfileId 가 있으면 CustomerProfileView 를 전면에 렌더.
 * 없으면 Dashboard 유지. ScheduleInputModal 은 항상 전역 오버레이.
 */
const RoutingGuard = () => {
  const activeProfileId = useCustomerStore((s) => s.activeProfileId);
  const activeScanId    = useCustomerStore((s) => s.activeScanId);
  const scanLoading     = useCustomerStore((s) => s.scanLoading);
  const loadingCustomer = useCustomerStore(
    (s) => (scanLoading.customerId ? s.customers[scanLoading.customerId] : null),
  );
  const avatarUri = loadingCustomer?.avatarUri ?? null;

  const [trashOpen,      setTrashOpen]      = React.useState(false);
  const [gkCustomerOpen, setGkCustomerOpen] = React.useState(false);

  const stopScanLoading = useCustomerStore((s) => s.stopScanLoading);

  // ── [GP-SSO §3] 인증 상태 ───────────────────────────────────────────────
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setSsoAuth      = useAuthStore((s) => s.setSsoAuth);

  // ── [GP-SSO §3] 딥링크 수신 핸들러 — goldkeycrmapp://sso?token=...&user_id=...&name=... ──
  const handleDeepLink = useCallback(async ({ url }) => {
    try {
      if (!url || !url.startsWith('goldkeycrmapp://sso')) return;
      const queryStr = url.includes('?') ? url.split('?')[1] : '';
      const params   = {};
      queryStr.split('&').forEach((pair) => {
        const [k, v] = pair.split('=');
        if (k) params[decodeURIComponent(k)] = decodeURIComponent(v || '');
      });
      const { token, user_id, name, role } = params;
      if (token && user_id && name) {
        await setSsoAuth(token, user_id, name, role || 'agent');
        console.log('[GP-SSO §3] SSO 인증 완료:', user_id, name);
      }
    } catch (e) {
      console.warn('[GP-SSO §3] 딥링크 처리 오류:', e?.message);
    }
  }, [setSsoAuth]);

  useEffect(() => {
    stopScanLoading();

    // [GP-SSO §3] 앱 실행 중 딥링크 수신
    const sub = Linking.addEventListener('url', handleDeepLink);

    // [GP-SSO §3] 앱이 닫혀있다가 딥링크로 열린 경우
    Linking.getInitialURL().then((url) => {
      if (url) handleDeepLink({ url });
    }).catch(() => null);

    const timer = setTimeout(() => {
      try {
        require('./src/utils/firebase');
      } catch (e) {
        console.warn('[App] Firebase lazy init 건너뜀:', e?.message);
      }
    }, 0);
    return () => {
      sub.remove();
      clearTimeout(timer);
    };
  }, [handleDeepLink]);

  useEffect(() => {
    _openTrashScreen      = () => setTrashOpen(true);
    _openGkCustomerScreen = () => setGkCustomerOpen(true);
    return () => { _openTrashScreen = null; _openGkCustomerScreen = null; };
  }, []);

  // ── [GP-SSO §3] 미인증 시 SSO 로그인 화면 표시 ───────────────────────────
  if (!isAuthenticated()) {
    return (
      <View style={styles.root}>
        <OtpAuthScreen />
      </View>
    );
  }

  return (
    <View style={styles.root}>
      {/* 제1장: 메인 대시보드 — 항상 마운트 유지 */}
      <Dashboard />

      {/* 제1장: 고객 프로필 오버레이 */}
      {activeProfileId && (
        <View style={styles.fullOverlay}>
          <CustomerProfileView />
        </View>
      )}

      {/* 제3장: 스캔 결과 듀얼뷰 (z:200) */}
      {activeScanId && (
        <View style={[styles.fullOverlay, styles.scanOverlay]}>
          <MedicalScanResultView />
        </View>
      )}

      {/* 휴지통 오버레이 */}
      {trashOpen && (
        <View style={[styles.fullOverlay, styles.trashOverlay]}>
          <TrashScreen onClose={() => setTrashOpen(false)} />
        </View>
      )}

      {/* 3단계 고객 관리 오버레이 (Phase 2 이식 컴포넌트) */}
      {gkCustomerOpen && (
        <View style={[styles.fullOverlay, styles.gkOverlay]}>
          <GoldKeyCustomerScreen onBack={() => setGkCustomerOpen(false)} />
        </View>
      )}

      {/* 일정 입력 모달 */}
      <ScheduleInputModal />

      {/*
        제2장: PremiumLoadingUI — AI 분석 대기 전체화면 오버레이 (z:999)
        scanLoading.active 가 true 인 동안 다른 모든 버튼 조작 불가
      */}
      <PremiumLoadingUI
        isVisible={scanLoading.active}
        avatarUri={avatarUri}
      />
    </View>
  );
};

// ── App 루트 ──────────────────────────────────────────────────────────────────
const App = () => (
  <View style={styles.root}>
    <RoutingGuard />
  </View>
);

// 전역 접근 핸들러
export let _openTrashScreen      = null;
export let _openGkCustomerScreen = null;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#ffffff' },
  fullOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f8fafc',
    zIndex: 100,
  },
  scanOverlay:  { zIndex: 200 },
  trashOverlay: { zIndex: 150 },
  gkOverlay:    { zIndex: 120 },
});

export default App;
