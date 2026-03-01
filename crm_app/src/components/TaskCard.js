/**
 * TaskCard — 할 일 카드 컴포넌트
 * - Zustand Selector 패턴: 이 카드가 관심 있는 task 하나만 구독
 * - 완료 시 취소선 + 배경색 변경
 * - priority 배지 (high/medium/low)
 */

import React, { memo, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';
import { useCrmStore } from '../store/crmStore';

const PRIORITY_STYLES = {
  high:   { bg: '#fef2f2', border: '#ef4444', label: '긴급', labelColor: '#ef4444' },
  medium: { bg: '#fffbeb', border: '#f59e0b', label: '보통', labelColor: '#d97706' },
  low:    { bg: '#f0fdf4', border: '#22c55e', label: '여유', labelColor: '#16a34a' },
};

// ── memo로 감싸 부모 리렌더링 시 불필요한 재렌더링 차단 ─────────────────────
const TaskCard = memo(({ taskId, onAllDone }) => {
  // Selector: 해당 task 하나만 구독 (다른 task 변경 시 이 컴포넌트 리렌더 안 됨)
  const task       = useCrmStore(useCallback((s) => s.tasks.find((t) => t.id === taskId), [taskId]));
  const toggleTask = useCrmStore((s) => s.toggleTask);
  const tasks      = useCrmStore((s) => s.tasks);

  if (!task) return null;

  const pStyle = PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium;

  const handlePress = () => {
    // Haptic: 완료/취소 시 즉각적인 촉각 피드백
    ReactNativeHapticFeedback.trigger('impactLight', { enableVibrateFallback: true, ignoreAndroidSystemSettings: false });

    toggleTask(taskId);

    // 이 task를 완료로 바꿨을 때 전체 100% 달성 여부 체크
    if (!task.isDone) {
      const doneCnt = tasks.filter((t) => t.isDone).length + 1; // 토글 후 예상값
      if (doneCnt === tasks.length) {
        // 약간 지연 후 confetti (애니메이션이 겹치지 않게)
        ReactNativeHapticFeedback.trigger('notificationSuccess', { enableVibrateFallback: true });
        setTimeout(() => onAllDone?.(), 300);
      }
    }
  };

  return (
    <TouchableOpacity
      activeOpacity={0.75}
      onPress={handlePress}
      style={[
        styles.card,
        {
          backgroundColor: task.isDone ? '#f1f5f9' : pStyle.bg,
          borderLeftColor: task.isDone ? '#94a3b8' : pStyle.border,
          opacity: task.isDone ? 0.72 : 1,
        },
      ]}
    >
      <View style={styles.row}>
        {/* 완료 아이콘 */}
        <Text style={styles.icon}>{task.isDone ? '✅' : '⏳'}</Text>

        <View style={styles.info}>
          {/* 제목 */}
          <Text
            style={[
              styles.title,
              task.isDone && styles.titleDone,
            ]}
            numberOfLines={2}
          >
            {task.title}
          </Text>

          {/* 하단 메타: 우선순위 배지 + 마감일 */}
          <View style={styles.meta}>
            <View style={[styles.badge, { backgroundColor: pStyle.bg, borderColor: pStyle.border }]}>
              <Text style={[styles.badgeText, { color: pStyle.labelColor }]}>{pStyle.label}</Text>
            </View>
            {!!task.dueDate && (
              <Text style={styles.dueDate}>📅 {task.dueDate}</Text>
            )}
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
});

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderLeftWidth: 4,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  row: { flexDirection: 'row', alignItems: 'flex-start' },
  icon: { fontSize: 20, marginRight: 12, marginTop: 1 },
  info: { flex: 1 },
  title: { fontSize: 15, fontWeight: '600', color: '#1e293b', lineHeight: 22 },
  titleDone: { textDecorationLine: 'line-through', color: '#94a3b8' },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 6, gap: 8 },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 20,
    borderWidth: 1,
  },
  badgeText: { fontSize: 11, fontWeight: '700' },
  dueDate: { fontSize: 12, color: '#64748b' },
});

export default TaskCard;
