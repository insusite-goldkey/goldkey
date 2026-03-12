/**
 * ConsultHistoryPanel.js — 우측 상담 히스토리 패널
 * 상담 메모 + 퀵 메모 + 다음 할 일
 */
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  TextInput, ScrollView,
} from 'react-native';

export default function ConsultHistoryPanel({ person, schedules = [], onAddSchedule }) {
  const [quickMemo, setQuickMemo] = useState('');

  if (!person) return null;

  const upcoming = schedules
    .filter((s) => s.person_id === person.person_id && !s.done && s.date >= new Date().toISOString().slice(0, 10))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(0, 3);

  return (
    <ScrollView style={styles.root} showsVerticalScrollIndicator={false}>
      <Text style={styles.panelTitle}>📝 상담 히스토리</Text>

      {/* 마지막 상담 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>마지막 상담</Text>
        {person.last_consulted_at ? (
          <Text style={styles.consultDate}>
            {person.last_consulted_at.slice(0, 10)}
          </Text>
        ) : (
          <Text style={styles.emptyText}>상담 기록 없음</Text>
        )}
        {person.memo && (
          <Text style={styles.memoText} numberOfLines={4}>
            {person.memo}
          </Text>
        )}
      </View>

      {/* 퀵 메모 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>퀵 메모</Text>
        <TextInput
          style={styles.memoInput}
          value={quickMemo}
          onChangeText={setQuickMemo}
          placeholder="감성 포인트, 선호 연락 시간 등..."
          placeholderTextColor="#9ca3af"
          multiline
          numberOfLines={3}
        />
      </View>

      {/* 다음 할 일 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>다음 할 일</Text>
        {upcoming.length > 0 ? (
          upcoming.map((s) => (
            <View key={s.id} style={styles.scheduleRow}>
              <Text style={styles.scheduleDate}>📅 {s.date}</Text>
              <Text style={styles.scheduleTitle} numberOfLines={1}>{s.title}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>예정된 일정 없음</Text>
        )}
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => onAddSchedule && onAddSchedule(person)}
        >
          <Text style={styles.addBtnText}>+ 일정 추가</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:       { flex: 1, padding: 12 },
  panelTitle: { fontSize: 14, fontWeight: '900', color: '#1e3a5f', marginBottom: 10 },
  card: {
    borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    borderRadius: 10, padding: 10, backgroundColor: '#fff', marginBottom: 10,
  },
  cardTitle:    { fontSize: 11, fontWeight: '700', color: '#374151', marginBottom: 6 },
  consultDate:  { fontSize: 15, fontWeight: '900', color: '#111', marginBottom: 4 },
  memoText:     { fontSize: 12, color: '#374151', lineHeight: 18 },
  emptyText:    { fontSize: 11, color: '#9ca3af' },
  memoInput: {
    borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 6,
    padding: 8, fontSize: 12, color: '#374151',
    textAlignVertical: 'top', minHeight: 60,
  },
  scheduleRow:  { flexDirection: 'row', alignItems: 'center', marginBottom: 4, gap: 6 },
  scheduleDate: { fontSize: 11, color: '#6b7280', width: 80 },
  scheduleTitle:{ fontSize: 12, color: '#111', flex: 1, fontWeight: '600' },
  addBtn: {
    marginTop: 8, backgroundColor: '#f0fdf4',
    borderWidth: 1, borderColor: '#16a34a',
    borderRadius: 6, paddingVertical: 6, alignItems: 'center',
  },
  addBtnText: { color: '#16a34a', fontWeight: '700', fontSize: 12 },
});
