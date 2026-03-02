/**
 * 골드키 CRM 앱 진입점 (App.js)
 * React Native CLI 기준
 *
 * ┌ 라우팅 흐름 ─────────────────────────────────────────────────────────┐
 * │  앱 시작                                                              │
 * │    └─▶ <SplashScreen onFinish={handleSplashDone} />                  │
 * │          │  (5초 + 백그라운드 prefetch)                               │
 * │          └─▶ showSplash = false                                      │
 * │                └─▶ <RoutingGuard />                                  │
 * │                      ├─ <Dashboard />              (기본 화면)       │
 * │                      ├─ <CustomerProfileView />    (activeProfileId) │
 * │                      ├─ <MedicalScanResultView />  (activeScanId)    │
 * │                      └─ <ScheduleInputModal />     (전역 오버레이)   │
 * └──────────────────────────────────────────────────────────────────────┘
 *
 * 전역 데이터 동기화 헌법 (SSOT Constitution):
 *   제1장 — 모든 화면은 useCustomerStore 단 하나만 구독.
 *            수정 시 해당 id 하나만 patch → 앱 전역 0.1초 즉시 동기화.
 *   제2장 — analyzeMedicalDocument() 단일 AI 파이프라인.
 *            PII 2중 마스킹(클라이언트 정규식 + Gemini System Prompt).
 *            삭제 시 2중 확인 팝업 + audit_log 영구 기록.
 *   제3장 — MedicalScanResultView 듀얼뷰(설계사/고객).
 *            [일정 추가] → openScheduleModal → 메인 달력 즉시 반영.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { StyleSheet, View } from 'react-native';
import { useCustomerStore }    from './src/store/customerStore';
import SplashScreen            from './src/screens/SplashScreen';
import Dashboard               from './src/screens/Dashboard';
import CustomerProfileView     from './src/screens/CustomerProfileView';
import MedicalScanResultView   from './src/screens/MedicalScanResultView';
import ScheduleInputModal      from './src/components/ScheduleInputModal';
import PremiumLoadingUI        from './src/components/PremiumLoadingUI';
import TrashScreen             from './src/screens/TrashScreen';

/**
 * RoutingGuard — 인증/권한 분기 문지기.
 *
 * activeProfileId 가 있으면 CustomerProfileView 를 전면에 렌더.
 * 없으면 Dashboard 유지. ScheduleInputModal 은 항상 전역 오버레이.
 *
 * 추후 Firebase Auth 결과에 따라 LoginScreen / AdminDashboard 분기 가능.
 */
const RoutingGuard = () => {
  const activeProfileId = useCustomerStore((s) => s.activeProfileId);
  const activeScanId    = useCustomerStore((s) => s.activeScanId);
  const scanLoading     = useCustomerStore((s) => s.scanLoading);
  const loadingCustomer = useCustomerStore(
    (s) => (scanLoading.customerId ? s.customers[scanLoading.customerId] : null),
  );
  const avatarUri = loadingCustomer?.avatarUri ?? null;

  // 3단계: 휴지통 오버레이 상태 (로컬 — persist 불필요)
  const [trashOpen, setTrashOpen] = React.useState(false);

  // Dashboard 등 하위 컴포넌트에서 openTrash() 로 휴지통 오픈 가능
  useEffect(() => {
    _openTrashScreen = () => setTrashOpen(true);
    return () => { _openTrashScreen = null; };
  }, []);

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

      {/* 3단계: 휴지통 오버레이 */}
      {trashOpen && (
        <View style={[styles.fullOverlay, styles.trashOverlay]}>
          <TrashScreen onClose={() => setTrashOpen(false)} />
        </View>
      )}

      {/* 제1장 일정 입력 모달 */}
      <ScheduleInputModal />

      {/*
        제2장: PremiumLoadingUI — AI 분석 대기 전체화면 오버레이 (z:999, 최상단)
        scanLoading.active 가 true 인 동안 다른 모든 버튼 조작 불가
        Modal(transparent) 방식으로 구현되어 있어 별도 zIndex 불필요
      */}
      <PremiumLoadingUI
        isVisible={scanLoading.active}
        avatarUri={avatarUri}
      />
    </View>
  );
};

// ── App 루트 ──────────────────────────────────────────────────────────────────
const App = () => {
  const [showSplash, setShowSplash] = useState(true);

  const handleSplashDone = useCallback(() => {
    setShowSplash(false);
  }, []);

  return (
    <View style={styles.root}>
      {showSplash
        ? <SplashScreen onFinish={handleSplashDone} />
        : <RoutingGuard />
      }
    </View>
  );
};

// openTrash 전역 접근을 위한 ref (Dashboard → TrashScreen 연결)
export let _openTrashScreen = null;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#ffffff' },
  fullOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f8fafc',
    zIndex: 100,
  },
  scanOverlay:  { zIndex: 200 },
  trashOverlay: { zIndex: 150 },
});

export default App;
