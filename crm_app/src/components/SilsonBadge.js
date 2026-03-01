/**
 * SilsonBadge — 실손 세대 배지 컴포넌트
 * 세대별 색상 체계로 즉시 식별 가능하게 표시
 */

import React, { memo } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { SILSON_BADGE_COLORS } from '../store/crmStore';

const SilsonBadge = memo(({ generation }) => {
  if (!generation) return null;

  const colors = SILSON_BADGE_COLORS[generation] || {
    bg: '#f1f5f9', text: '#475569', border: '#94a3b8',
  };

  return (
    <View style={[styles.badge, { backgroundColor: colors.bg, borderColor: colors.border }]}>
      <Text style={[styles.label, { color: colors.text }]}>{generation}</Text>
    </View>
  );
});

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1.5,
    alignSelf: 'flex-start',
  },
  label: {
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
});

export default SilsonBadge;
