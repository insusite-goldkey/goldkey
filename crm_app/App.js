/**
 * 골드키 CRM 앱 진입점 (App.js)
 * React Native CLI 기준
 *
 * ┌ 라우팅 흐름 ────────────────────────────────────────────────────┐
 * │  앱 시작                                                         │
 * │    └─▶ <SplashScreen onFinish={handleSplashDone} />             │
 * │          │  (5초 + 백그라운드 prefetch)                          │
 * │          └─▶ showSplash = false                                 │
 * │                └─▶ <RoutingGuard />                             │
 * │                      ├─ <Dashboard />          (기본 화면)      │
 * │                      ├─ <CustomerProfileView /> (activeProfileId) │
 * │                      └─ <ScheduleInputModal />  (전역 오버레이) │
 * └─────────────────────────────────────────────────────────────────┘
 *
 * SSOT 동기화:
 *   모든 화면은 useCustomerStore(customerId) 구독 → 프로필 저장 시
 *   해당 id 하나만 patch → Dashboard·검색창·달력 즉시 일제 반영
 */

import React, { useState, useCallback } from 'react';
import { StyleSheet, View } from 'react-native';
import { useCustomerStore }    from './src/store/customerStore';
import SplashScreen            from './src/screens/SplashScreen';
import Dashboard               from './src/screens/Dashboard';
import CustomerProfileView     from './src/screens/CustomerProfileView';
import ScheduleInputModal      from './src/components/ScheduleInputModal';

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

  return (
    <View style={styles.root}>
      {/* 메인 대시보드 — 항상 마운트 유지 (unmount 없이 overlay로 가림) */}
      <Dashboard />

      {/* 고객 프로필 오버레이 — activeProfileId 있을 때만 표시 */}
      {activeProfileId && (
        <View style={styles.profileOverlay}>
          <CustomerProfileView />
        </View>
      )}

      {/* 일정 입력 모달 — 전역 단일 인스턴스 */}
      <ScheduleInputModal />
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
      {!showSplash && <RoutingGuard />}
      {showSplash  && <SplashScreen onFinish={handleSplashDone} />}
    </View>
  );
};

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#ffffff' },
  profileOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#f8fafc',
    zIndex: 100,
  },
});

export default App;
