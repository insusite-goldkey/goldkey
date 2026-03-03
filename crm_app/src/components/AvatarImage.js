/**
 * AvatarImage — 골드키 CRM 단일 아바타 시스템 (SSOT)
 *
 * ┌ 설계 원칙 ──────────────────────────────────────────────────────┐
 * │  • 앱 전체에서 이 컴포넌트 하나만 아바타로 사용                  │
 * │  • 이모지(🔑 등) 아바타 완전 대체                               │
 * │  • SVG를 Base64 data URI로 내장 → 패키지/파일 의존성 0          │
 * │  • ~2KB, 모든 해상도에서 선명 (SVG 벡터)                        │
 * │  • 3가지 모드:                                                   │
 * │    1. mode="ai"      골드키 AI 전용 아바타 (여성 비즈니스)       │
 * │    2. mode="initial" 고객 이니셜 원형 (이름 첫 글자)             │
 * │    3. mode="logo"    브랜드 로고 (GK 텍스트)                    │
 * └────────────────────────────────────────────────────────────────┘
 *
 * Props:
 *   mode        {'ai' | 'initial' | 'logo'}  기본값 'ai'
 *   size        {number}                      기본값 64
 *   initial     {string}                      mode='initial' 일 때 표시할 글자
 *   registered  {boolean}                     mode='initial' 색상 분기
 *   style       {object}                      추가 스타일 오버라이드
 *   borderColor {string}                      테두리 색상 (기본값 '#f0c040')
 *   borderWidth {number}                      테두리 두께 (기본값 0)
 */

import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';

// ── 골드키 AI 아바타 SVG (Base64 data URI) ────────────────────────────────────
// 비즈니스 여성 아바타 / 딥네이비 배경 / 골드 귀걸이 + GK 뱃지
// SVG → btoa() 변환값 (순수 ASCII SVG)
const GK_AVATAR_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
<circle cx="64" cy="64" r="64" fill="#1e3a5f"/>
<circle cx="64" cy="64" r="60" fill="none" stroke="#f0c040" stroke-width="1.5" opacity="0.5"/>
<ellipse cx="64" cy="110" rx="36" ry="26" fill="#152d4a"/>
<path d="M64 90 L50 78 L46 110 L64 100 L82 110 L78 78 Z" fill="#0f2238"/>
<path d="M64 90 L58 82 L61 110 L64 98 L67 110 L70 82 Z" fill="#e8edf2"/>
<rect x="59" y="70" width="10" height="15" rx="5" fill="#f4c49a"/>
<ellipse cx="64" cy="55" rx="22" ry="24" fill="#f4c49a"/>
<path d="M42 50 Q41 28 64 26 Q87 28 86 50 Q86 36 64 34 Q42 36 42 50Z" fill="#1a0e08"/>
<path d="M42 50 Q37 62 40 74 Q45 68 47 60Z" fill="#1a0e08"/>
<path d="M86 50 Q91 62 88 74 Q83 68 81 60Z" fill="#1a0e08"/>
<ellipse cx="55" cy="53" rx="4" ry="4.5" fill="white"/>
<ellipse cx="73" cy="53" rx="4" ry="4.5" fill="white"/>
<circle cx="56" cy="54" r="2.8" fill="#1a0e08"/>
<circle cx="74" cy="54" r="2.8" fill="#1a0e08"/>
<circle cx="57.2" cy="52.5" r="1" fill="white"/>
<circle cx="75.2" cy="52.5" r="1" fill="white"/>
<path d="M51 50 Q55 48 59 50" fill="none" stroke="#1a0e08" stroke-width="1.4" stroke-linecap="round"/>
<path d="M69 50 Q73 48 77 50" fill="none" stroke="#1a0e08" stroke-width="1.4" stroke-linecap="round"/>
<path d="M62 60 Q64 63 66 60" fill="none" stroke="#cc8855" stroke-width="1" stroke-linecap="round"/>
<path d="M57 68 Q64 73 71 68" fill="#d97070"/>
<path d="M57 68 Q64 65 71 68" fill="#b85555"/>
<ellipse cx="50" cy="61" rx="5" ry="3" fill="#f4a0a0" opacity="0.3"/>
<ellipse cx="78" cy="61" rx="5" ry="3" fill="#f4a0a0" opacity="0.3"/>
<circle cx="42" cy="62" r="3" fill="#f0c040"/>
<circle cx="86" cy="62" r="3" fill="#f0c040"/>
<circle cx="96" cy="96" r="18" fill="#f0c040"/>
<circle cx="96" cy="96" r="15" fill="#e6b800"/>
<text x="96" y="102" font-size="13" text-anchor="middle" fill="#1e3a5f" font-weight="900" font-family="sans-serif">GK</text>
</svg>`;

// SVG → Base64 data URI 변환 (순수 JS, btoa 사용)
const svgToDataUri = (svg) => {
  // RN 환경에서 btoa가 없을 경우를 위한 순수 JS 구현
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  const bytes = [];
  for (let i = 0; i < svg.length; i++) {
    const code = svg.charCodeAt(i);
    if (code > 127) {
      // UTF-8 인코딩 (ASCII만 사용하므로 해당 없음)
      bytes.push(0xef, 0xbf, 0xbd);
    } else {
      bytes.push(code);
    }
  }
  let result = '';
  for (let i = 0; i < bytes.length; i += 3) {
    const b0 = bytes[i], b1 = bytes[i + 1] ?? 0, b2 = bytes[i + 2] ?? 0;
    result += chars[b0 >> 2];
    result += chars[((b0 & 3) << 4) | (b1 >> 4)];
    result += i + 1 < bytes.length ? chars[((b1 & 15) << 2) | (b2 >> 6)] : '=';
    result += i + 2 < bytes.length ? chars[b2 & 63] : '=';
  }
  return `data:image/svg+xml;base64,${result}`;
};

// 모듈 레벨에서 1회만 계산 (재렌더 비용 0)
export const GK_AVATAR_URI = svgToDataUri(GK_AVATAR_SVG);

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
const AvatarImage = ({
  mode        = 'ai',
  size        = 64,
  initial     = '?',
  registered  = true,
  style,
  borderColor = 'transparent',
  borderWidth = 0,
}) => {
  const radius     = size / 2;
  const frameStyle = {
    width:        size,
    height:       size,
    borderRadius: radius,
    borderWidth,
    borderColor,
    overflow:     'hidden',
  };

  // ── mode: ai — 골드키 AI 아바타 이미지 ──────────────────────────────────
  if (mode === 'ai') {
    return (
      <View style={[frameStyle, style]}>
        <Image
          source={{ uri: GK_AVATAR_URI }}
          style={{ width: size, height: size }}
          resizeMode="cover"
          fadeDuration={0}
        />
      </View>
    );
  }

  // ── mode: logo — GK 텍스트 로고 ─────────────────────────────────────────
  if (mode === 'logo') {
    return (
      <View style={[frameStyle, styles.logoBg, style]}>
        <Text style={[styles.logoText, { fontSize: size * 0.35 }]}>GK</Text>
        <Text style={[styles.logoSub, { fontSize: size * 0.14 }]}>AI</Text>
      </View>
    );
  }

  // ── mode: initial — 고객 이니셜 원형 ────────────────────────────────────
  const bgColor = registered ? '#1e3a5f' : '#64748b';
  return (
    <View style={[frameStyle, { backgroundColor: bgColor, alignItems: 'center', justifyContent: 'center' }, style]}>
      <Text style={[styles.initialText, { fontSize: size * 0.38 }]}>
        {(initial || '?').charAt(0).toUpperCase()}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  logoBg: {
    backgroundColor: '#1e3a5f',
    alignItems:      'center',
    justifyContent:  'center',
  },
  logoText: {
    color:      '#f0c040',
    fontWeight: '900',
    letterSpacing: 1,
    lineHeight: undefined,
  },
  logoSub: {
    color:      '#f0c040',
    fontWeight: '700',
    opacity:    0.7,
    marginTop:  -2,
  },
  initialText: {
    color:      '#ffffff',
    fontWeight: '900',
  },
});

export default AvatarImage;
