/**
 * 골드키 CRM 앱 진입점 (App.js)
 * React Native CLI 기준
 *
 * ┌ 라우팅 흐름 ──────────────────────────────────────────────┐
 * │  앱 시작                                                   │
 * │    └─▶ <SplashScreen onFinish={handleSplashDone} />       │
 * │          │  (5초 + 백그라운드 prefetch)                    │
 * │          └─▶ showSplash = false                           │
 * │                └─▶ <RoutingGuard />  (Dashboard)          │
 * └───────────────────────────────────────────────────────────┘
 */

import React, { useState, useCallback } from 'react';
import { StyleSheet, View } from 'react-native';
import SplashScreen from './src/screens/SplashScreen';
import Dashboard    from './src/screens/Dashboard';

/**
 * RoutingGuard — 인증/권한 분기 문지기.
 * 현재는 단일 역할(설계사)만 존재하므로 Dashboard를 직접 렌더.
 * 추후 Firebase Auth 결과에 따라 LoginScreen / AdminDashboard 분기 가능.
 */
const RoutingGuard = () => <Dashboard />;

const App = () => {
  const [showSplash, setShowSplash] = useState(true);

  /** 스플래시 fadeOut 완료 시 호출 — 상태 전환만 담당 */
  const handleSplashDone = useCallback(() => {
    setShowSplash(false);
  }, []);

  return (
    <View style={styles.root}>
      {/* 스플래시가 끝나면 RoutingGuard를 즉시 마운트 */}
      {!showSplash && <RoutingGuard />}

      {/*
        SplashScreen은 absolute z:9999 오버레이로 동작.
        showSplash가 true인 동안만 렌더(fadeOut 완료 후 언마운트).
        이 순서 덕분에 RoutingGuard는 스플래시 뒤에서 미리 마운트되어
        prefetch가 끝나는 즉시 화면 전환이 0.1초 내에 완료됩니다.
      */}
      {showSplash && <SplashScreen onFinish={handleSplashDone} />}
    </View>
  );
};

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#ffffff' },
});

export default App;
