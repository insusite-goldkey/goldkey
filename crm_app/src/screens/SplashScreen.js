/**
 * SplashScreen — 골드키 CRM 초경량 스플래시
 *
 * ┌ 동작 흐름 ─────────────────────────────────────────────┐
 * │ 1. 마운트 즉시 스플래시 이미지 fullscreen 표시          │
 * │ 2. 동시에 백그라운드에서 Zustand 스토어 초기화(prefetch) │
 * │ 3. 4300ms 후 fadeOut 시작 (700ms 소요)                  │
 * │ 4. fadeOut 완료(5000ms) → onFinish() 호출 → 앱 진입    │
 * └──────────────────────────────────────────────────────────┘
 *
 * Props:
 *   onFinish {function} — 스플래시 종료 후 호출할 콜백 (App.js에서 주입)
 */

import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Dimensions,
  Image,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useCrmStore } from '../store/crmStore'; // getState() 전용 — hook 미사용
import AvatarImage from '../components/AvatarImage';

// ── 스플래시 이미지 경로 ─────────────────────────────────────────────────────
// assets/splash_goldkey.png 또는 .jpg 를 프로젝트 루트 기준으로 배치하세요.
// 없을 경우 순백 + 골드 로고 텍스트 fallback으로 자동 대체됩니다.
const SPLASH_IMAGE = (() => {
  try {
    // eslint-disable-next-line import/no-unresolved
    return require('../../assets/splash_goldkey.png');
  } catch {
    try {
      // eslint-disable-next-line import/no-unresolved
      return require('../../assets/splash_goldkey.jpg');
    } catch {
      return null;
    }
  }
})();

const FADE_START_MS = 4300; // fadeOut 시작 시각
const FADE_DURATION = 700;  // fadeOut 지속 시간 (총 5000ms)

const { width: SW, height: SH } = Dimensions.get('window');

// ── 컴포넌트 ─────────────────────────────────────────────────────────────────
const SplashScreen = ({ onFinish }) => {
  const opacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // ① 즉시 상태 복구 — hook 대신 getState()로 안전하게 호출
    try {
      useCrmStore.getState().recoverState();
    } catch (e) {
      // 스토어 복구 실패 시 스플래시는 정상 진행
      console.warn('[SplashScreen] recoverState 실패:', e);
    }

    // ② 필요 시 비동기 prefetch 확장 예시:
    // (async () => {
    //   await fetchUserProfile();       // Firebase Auth 확인
    //   await loadRemoteConfig();       // Remote Config
    //   useAppStore.getState().setUser(user);
    // })();

    // ③ 4.3초 후 fadeOut → 총 5초
    const fadeTimer = setTimeout(() => {
      Animated.timing(opacity, {
        toValue:        0,
        duration:       FADE_DURATION,
        useNativeDriver: true,
      }).start(() => {
        if (typeof onFinish === 'function') onFinish();
      });
    }, FADE_START_MS);

    return () => clearTimeout(fadeTimer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Animated.View style={[styles.container, { opacity }]}>
      <StatusBar
        barStyle="light-content"
        backgroundColor="#1e3a5f"
        translucent={Platform.OS === 'android'}
      />

      {SPLASH_IMAGE ? (
        /* ── 이미지 있을 때: object-cover 전체화면 ── */
        <Image
          source={SPLASH_IMAGE}
          style={styles.image}
          resizeMode="cover"
          fadeDuration={0}
        />
      ) : (
        /* ── 이미지 없을 때: 순백 + 골드 로고 텍스트 fallback ── */
        <View style={styles.fallbackBg}>
          <View style={styles.logoWrap}>
            <AvatarImage
              mode="ai"
              size={100}
              borderColor="#f0c040"
              borderWidth={3}
              style={styles.splashAvatar}
            />
            <Text style={styles.logoTitle}>GOLDKEY</Text>
            <Text style={styles.logoSubText}>AI 보험컨설팅 플랫폼</Text>
          </View>
          <View style={styles.taglineWrap}>
            <Text style={styles.tagline}>설계사의 성공을 설계합니다.</Text>
          </View>
        </View>
      )}

      {/* ── 하단 버전 텍스트 (이미지 위에 오버레이) ── */}
      <View style={styles.versionWrap} pointerEvents="none">
        <Text style={styles.versionText}>v1.0.0</Text>
      </View>
    </Animated.View>
  );
};

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    position:        'absolute',
    top:             0,
    left:            0,
    width:           SW,
    height:          SH,
    backgroundColor: '#ffffff',   // 이미지 로드 틈새 순백 처리
    zIndex:          9999,
  },

  // 이미지 — 전체 화면 꽉 채움
  image: {
    width:  '100%',
    height: '100%',
  },

  // Fallback — 순백 배경 + 골드 로고
  fallbackBg: {
    flex:            1,
    backgroundColor: '#ffffff',
    alignItems:      'center',
    justifyContent:  'center',
  },
  logoWrap: {
    alignItems: 'center',
    marginBottom: 60,
  },
  splashAvatar: {
    marginBottom: 20,
    shadowColor:  '#f0c040',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius:  16,
    elevation:     10,
  },
  logoTitle: {
    fontSize:    36,
    fontWeight:  '900',
    color:       '#1e3a5f',
    letterSpacing: 6,
  },
  logoSub: {
    fontSize:   14,
    fontWeight: '600',
    color:      '#64748b',
    marginTop:  8,
    letterSpacing: 1,
  },
  logoSubText: {
    fontSize:   14,
    fontWeight: '600',
    color:      '#64748b',
    marginTop:  8,
    letterSpacing: 1,
  },
  taglineWrap: {
    marginTop: 24,
  },
  tagline: {
    fontSize:   13,
    color:      '#94a3b8',
    fontWeight: '500',
    letterSpacing: 0.5,
  },

  // 하단 버전
  versionWrap: {
    position:   'absolute',
    bottom:     Platform.OS === 'ios' ? 44 : 24,
    alignSelf:  'center',
  },
  versionText: {
    fontSize:   11,
    color:      'rgba(255,255,255,0.55)',
    fontWeight: '600',
    letterSpacing: 1,
  },
});

export default SplashScreen;
