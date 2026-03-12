/**
 * App.js — Goldkey AI Masters 2026
 * 라우팅: CustomerListScreen ↔ CustomerDetailScreen
 */
import React, { useEffect } from 'react';
import { View, StyleSheet, Linking, Alert } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import CustomerListScreen   from './src/screens/CustomerListScreen';
import CustomerDetailScreen from './src/screens/CustomerDetailScreen';
import { useCustomerStore } from './src/store/customerStore';
import { CRM_PLAY_STORE_URL } from './src/config';

// ── CRM 설치 유도 팝업 (Step A — 원클릭 생태계) ─────────────────────────────
function useCrmInstallPrompt() {
  useEffect(() => {
    const timer = setTimeout(() => {
      Alert.alert(
        '📱 현장 관리를 더 스마트하게!',
        'Goldkey AI Masters CRM을 설치하면\n핸드폰에서 고객 상담·일정·증권분석을\n언제 어디서나 관리할 수 있습니다.',
        [
          { text: '나중에', style: 'cancel' },
          {
            text: '지금 설치하기',
            onPress: () => Linking.openURL(CRM_PLAY_STORE_URL),
          },
        ],
        { cancelable: true }
      );
    }, 5000); // 앱 실행 5초 후 표시
    return () => clearTimeout(timer);
  }, []);
}

// ── 라우팅 가드 ──────────────────────────────────────────────────────────────
function RoutingGuard() {
  useCrmInstallPrompt();

  const activePersonId = useCustomerStore((s) => s.activePersonId);

  if (activePersonId) {
    return <CustomerDetailScreen />;
  }
  return <CustomerListScreen />;
}

// ── 앱 루트 ──────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <SafeAreaProvider>
      <View style={styles.root}>
        <RoutingGuard />
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f9fafb' },
});
