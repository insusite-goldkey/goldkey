'use strict';
/**
 * src/screens/OtpAuthScreen.js — Goldkey AI Masters 2026
 *
 * [GP-SSO §1] SSO 전용 화면 — 자체 로그인 폼 없음.
 * 세션이 없으면 모 앱(Goldkey AI) 로그인 URL로 자동 리다이렉트.
 * 모 앱 로그인 완료 → goldkeycrmapp://sso?token=...&user_id=...&name=... 딥링크 수신
 * → App.js Linking 핸들러가 setSsoAuth() 호출 → 인증 완료.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Linking,
} from 'react-native';

// ── SSO 설정 상수 ─────────────────────────────────────────────────────────────
const MOTHER_APP_URL      = 'https://goldkey-ai-817097913199.asia-northeast3.run.app';
const CRM_DEEPLINK_SCHEME = 'goldkeycrmapp://sso';

/**
 * [GP-SSO §1] SSO 로그인 화면
 * 세션 없음 → 모 앱으로 자동 리다이렉트 → 토큰 딥링크 수신은 App.js 처리
 * @param {{ onSsoSuccess?: () => void }} props
 */
export default function OtpAuthScreen({ onSsoSuccess }) {
  const [redirecting, setRedirecting] = useState(false);
  const [error, setError]             = useState(null);

  useEffect(() => { handleRedirectToMother(); }, []);

  const handleRedirectToMother = async () => {
    setRedirecting(true);
    setError(null);
    try {
      const returnTo = encodeURIComponent(CRM_DEEPLINK_SCHEME);
      const loginUrl = `${MOTHER_APP_URL}/?return_to=${returnTo}`;
      const canOpen  = await Linking.canOpenURL(loginUrl);
      if (canOpen) {
        await Linking.openURL(loginUrl);
      } else {
        setError('브라우저를 열 수 없습니다. 수동으로 접속해 주세요.');
      }
    } catch (e) {
      setError(`리다이렉트 오류: ${e.message}`);
    } finally {
      setRedirecting(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.logo}>🔑</Text>
        <Text style={styles.title}>Goldkey AI Masters CRM</Text>
        <Text style={styles.subtitle}>SSO 통합 인증</Text>
        <View style={styles.divider} />
        {redirecting ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color="#1d4ed8" />
            <Text style={styles.loadingText}>
              {'Goldkey AI 로그인 화면으로\n이동 중입니다...'}
            </Text>
          </View>
        ) : (
          <View style={styles.guideBox}>
            <Text style={styles.guideTitle}>📋 로그인 방법</Text>
            <Text style={styles.guideText}>
              {'1. 아래 버튼을 누르면 Goldkey AI 앱으로 이동합니다.\n'}
              {'2. Goldkey AI 앱에서 로그인을 완료하세요.\n'}
              {'3. 로그인 완료 후 자동으로 CRM 앱으로 돌아옵니다.'}
            </Text>
          </View>
        )}
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>⚠️ {error}</Text>
          </View>
        )}
        <TouchableOpacity
          style={[styles.btn, redirecting && styles.btnDisabled]}
          onPress={handleRedirectToMother}
          disabled={redirecting}
          activeOpacity={0.8}
        >
          {redirecting
            ? <ActivityIndicator color="#fff" />
            : <Text style={styles.btnText}>🚀 Goldkey AI로 로그인</Text>
          }
        </TouchableOpacity>
        <Text style={styles.ssoNote}>Powered by Goldkey AI SSO · GP-SSO §1</Text>
      </View>
    </View>
  );
}

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1, backgroundColor: '#f0f4ff',
    alignItems: 'center', justifyContent: 'center', padding: 24,
  },
  card: {
    backgroundColor: '#ffffff', borderRadius: 20, padding: 28,
    width: '100%', maxWidth: 400,
    shadowColor: '#000', shadowOpacity: 0.10, shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 }, elevation: 6,
    alignItems: 'center',
  },
  logo:        { fontSize: 48, marginBottom: 8 },
  title:       { fontSize: 20, fontWeight: '900', color: '#1e3a8a', textAlign: 'center' },
  subtitle:    { fontSize: 13, color: '#6b7280', marginTop: 4, marginBottom: 16 },
  divider:     { height: 1, backgroundColor: '#e5e7eb', width: '100%', marginBottom: 20 },
  loadingBox:  { alignItems: 'center', paddingVertical: 16, gap: 12 },
  loadingText: { fontSize: 14, color: '#4b5563', textAlign: 'center', lineHeight: 22 },
  guideBox: {
    backgroundColor: '#eff6ff', borderRadius: 12,
    borderWidth: 1, borderColor: '#bfdbfe',
    padding: 16, width: '100%', marginBottom: 20,
  },
  guideTitle:  { fontSize: 14, fontWeight: '700', color: '#1d4ed8', marginBottom: 8 },
  guideText:   { fontSize: 13, color: '#374151', lineHeight: 22 },
  errorBox: {
    backgroundColor: '#fef2f2', borderRadius: 10,
    borderWidth: 1, borderColor: '#fca5a5',
    padding: 12, width: '100%', marginBottom: 16,
  },
  errorText:   { fontSize: 13, color: '#dc2626' },
  btn: {
    height: 52, backgroundColor: '#1d4ed8', borderRadius: 14,
    alignItems: 'center', justifyContent: 'center',
    width: '100%', marginTop: 4,
  },
  btnDisabled: { opacity: 0.55 },
  btnText:     { fontSize: 16, fontWeight: '900', color: '#ffffff' },
  ssoNote:     { fontSize: 11, color: '#9ca3af', marginTop: 16, textAlign: 'center' },
});
