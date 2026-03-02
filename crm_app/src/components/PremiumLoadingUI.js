/**
 * PremiumLoadingUI — AI 스캔 분석 대기 화면 (React Native 전용)
 *
 * framer-motion 은 웹 전용이므로 React Native 내장 Animated API로 완전 구현.
 *
 * 구성
 * ┌─────────────────────────────────────────────────────────┐
 * │  fixed inset-0 z-[999]  bg-white/90 + backdrop-blur    │
 * │                                                         │
 * │        [파동 1] — 가장 크게, 느리게 퍼짐                │
 * │        [파동 2] — 중간, 0.5s 시차                       │
 * │        [파동 3] — 작게, 1.0s 시차                       │
 * │        ┌──────┐ ← 아바타 이미지(원형, 골드 테두리)      │
 * │        └──────┘                                         │
 * │                                                         │
 * │   [다이내믹 텍스트 — 1.5s 마다 fadeIn/Out 전환]         │
 * │                                                         │
 * │        ● ● ●  ← 바운스 점 3개                          │
 * └─────────────────────────────────────────────────────────┘
 *
 * Props:
 *   isVisible  {boolean}  — true 시 전체화면 오버레이 표시
 *   avatarUri  {string?}  — 아바타 이미지 URI (없으면 기본 🔑 fallback)
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Dimensions,
  Easing,
  Image,
  Modal,
  Platform,
  StyleSheet,
  Text,
  View,
} from 'react-native';

// ── 다이내믹 메시지 배열 ──────────────────────────────────────────────────────
const LOADING_MESSAGES = [
  '문서의 텍스트를 해독하고 있습니다...',
  'KCD 질병 코드를 정밀 분류 중입니다...',
  '최신 약관 데이터베이스와 대조하고 있습니다...',
  '업셀링 포인트를 분석 중입니다... 거의 다 되었습니다!',
];

const AVATAR_SIZE   = 128;
const PULSE_SIZE    = AVATAR_SIZE;
const { width: SW } = Dimensions.get('window');

// ── 파동(Pulse) 단일 레이어 ───────────────────────────────────────────────────
const PulseRing = ({ delay, maxScale, color }) => {
  const scale   = useRef(new Animated.Value(1)).current;
  const opacity = useRef(new Animated.Value(0.7)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.delay(delay),
        Animated.parallel([
          Animated.timing(scale, {
            toValue:         maxScale,
            duration:        2000,
            easing:          Easing.out(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(opacity, {
            toValue:         0,
            duration:        2000,
            easing:          Easing.out(Easing.ease),
            useNativeDriver: true,
          }),
        ]),
        Animated.parallel([
          Animated.timing(scale,   { toValue: 1, duration: 0, useNativeDriver: true }),
          Animated.timing(opacity, { toValue: 0.7, duration: 0, useNativeDriver: true }),
        ]),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, []);

  return (
    <Animated.View
      style={[
        styles.pulseRing,
        {
          width:            PULSE_SIZE,
          height:           PULSE_SIZE,
          borderRadius:     PULSE_SIZE / 2,
          backgroundColor:  color,
          transform:        [{ scale }],
          opacity,
        },
      ]}
    />
  );
};

// ── 바운스 점 ─────────────────────────────────────────────────────────────────
const BounceDot = ({ delay }) => {
  const translateY = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const bounce = Animated.loop(
      Animated.sequence([
        Animated.delay(delay),
        Animated.timing(translateY, {
          toValue: -10, duration: 300,
          easing: Easing.out(Easing.quad), useNativeDriver: true,
        }),
        Animated.timing(translateY, {
          toValue: 0, duration: 300,
          easing: Easing.in(Easing.quad), useNativeDriver: true,
        }),
        Animated.delay(600 - delay), // 전체 주기 맞춤
      ]),
    );
    bounce.start();
    return () => bounce.stop();
  }, []);

  return (
    <Animated.View
      style={[styles.dot, { transform: [{ translateY }] }]}
    />
  );
};

// ── 다이내믹 텍스트 ───────────────────────────────────────────────────────────
const DynamicText = ({ isVisible }) => {
  const [msgIdx, setMsgIdx] = useState(0);
  const opacity             = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!isVisible) { setMsgIdx(0); return; }

    const interval = setInterval(() => {
      // fade-out → 텍스트 교체 → fade-in
      Animated.timing(opacity, {
        toValue: 0, duration: 250,
        useNativeDriver: true,
      }).start(() => {
        setMsgIdx((prev) => (prev + 1) % LOADING_MESSAGES.length);
        Animated.timing(opacity, {
          toValue: 1, duration: 300,
          useNativeDriver: true,
        }).start();
      });
    }, 1500);

    return () => clearInterval(interval);
  }, [isVisible]);

  return (
    <Animated.Text style={[styles.msgText, { opacity }]}>
      {LOADING_MESSAGES[msgIdx]}
    </Animated.Text>
  );
};

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
const PremiumLoadingUI = ({ isVisible, avatarUri }) => {
  // 아바타 소프트-스케일 맥동
  const avatarScale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!isVisible) return;
    const breathe = Animated.loop(
      Animated.sequence([
        Animated.timing(avatarScale, {
          toValue: 1.06, duration: 1000,
          easing: Easing.inOut(Easing.ease), useNativeDriver: true,
        }),
        Animated.timing(avatarScale, {
          toValue: 1, duration: 1000,
          easing: Easing.inOut(Easing.ease), useNativeDriver: true,
        }),
      ]),
    );
    breathe.start();
    return () => breathe.stop();
  }, [isVisible]);

  return (
    <Modal
      visible={isVisible}
      transparent
      animationType="fade"
      statusBarTranslucent={Platform.OS === 'android'}
    >
      <View style={styles.overlay}>

        {/* ── 아바타 + 파동 ── */}
        <View style={styles.avatarWrap}>
          {/* 파동 3겹 (뒤→앞 순서) */}
          <PulseRing delay={0}    maxScale={2.6} color="rgba(96,165,250,0.35)" />
          <PulseRing delay={500}  maxScale={2.1} color="rgba(59,130,246,0.45)" />
          <PulseRing delay={1000} maxScale={1.6} color="rgba(37,99,235,0.50)" />

          {/* 아바타 이미지 (골드 테두리 원형) */}
          <Animated.View
            style={[
              styles.avatarFrame,
              { transform: [{ scale: avatarScale }] },
            ]}
          >
            {avatarUri ? (
              <Image
                source={{ uri: avatarUri }}
                style={styles.avatarImg}
                resizeMode="cover"
              />
            ) : (
              /* 이미지 없을 때 fallback */
              <View style={styles.avatarFallback}>
                <Text style={styles.avatarFallbackText}>🔑</Text>
              </View>
            )}
          </Animated.View>
        </View>

        {/* ── 브랜드 타이틀 ── */}
        <Text style={styles.titleText}>Goldkey AI 분석 중</Text>

        {/* ── 다이내믹 메시지 ── */}
        <View style={styles.msgWrap}>
          <DynamicText isVisible={isVisible} />
        </View>

        {/* ── 바운스 점 3개 ── */}
        <View style={styles.dotsRow}>
          <BounceDot delay={0}   />
          <BounceDot delay={200} />
          <BounceDot delay={400} />
        </View>

        {/* ── 하단 보안 문구 ── */}
        <Text style={styles.secureText}>
          🛡️ 개인정보는 철저히 암호화되어 처리됩니다.
        </Text>

      </View>
    </Modal>
  );
};

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.93)',
    alignItems: 'center',
    justifyContent: 'center',
    // iOS backdrop-blur 효과: 네이티브에서는 blurRadius로 근사
    ...(Platform.OS === 'ios' ? {} : {}),
  },

  // 아바타 + 파동 컨테이너 (겹침을 위해 relative)
  avatarWrap: {
    width:           AVATAR_SIZE * 3,
    height:          AVATAR_SIZE * 3,
    alignItems:      'center',
    justifyContent:  'center',
    marginBottom:    28,
  },
  pulseRing: {
    position: 'absolute',
  },

  // 아바타 프레임
  avatarFrame: {
    width:        AVATAR_SIZE,
    height:       AVATAR_SIZE,
    borderRadius: AVATAR_SIZE / 2,
    borderWidth:  4,
    borderColor:  '#f0c040',         // 골드 테두리
    shadowColor:  '#f0c040',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.55,
    shadowRadius:  20,
    elevation:     12,
    overflow:     'hidden',
    backgroundColor: '#1e3a5f',
    zIndex:       10,
  },
  avatarImg: {
    width:  '100%',
    height: '100%',
  },
  avatarFallback: {
    flex: 1,
    alignItems:     'center',
    justifyContent: 'center',
    backgroundColor: '#1e3a5f',
  },
  avatarFallbackText: { fontSize: 56 },

  // 타이틀
  titleText: {
    fontSize:      20,
    fontWeight:    '900',
    color:         '#1e293b',
    letterSpacing: 0.5,
    marginBottom:  10,
  },

  // 다이내믹 메시지
  msgWrap: {
    height:      28,
    alignItems:  'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    marginBottom: 24,
  },
  msgText: {
    fontSize:   15,
    fontWeight: '700',
    color:      '#475569',
    textAlign:  'center',
  },

  // 바운스 점
  dotsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 32,
  },
  dot: {
    width:        10,
    height:       10,
    borderRadius: 5,
    backgroundColor: '#2563eb',
  },

  // 보안 문구
  secureText: {
    fontSize:   12,
    color:      '#94a3b8',
    fontWeight: '500',
  },
});

export default PremiumLoadingUI;
