/**
 * AnnualCycleTab.js — [1차 라인] 연간 계약 보드
 * 자동차/화재 보험 갱신월 D-Day + 체크리스트
 */
import React, { useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

function getDday(renewalMonth) {
  if (!renewalMonth) return null;
  const now   = new Date();
  const year  = renewalMonth <= now.getMonth() + 1
    ? now.getFullYear() + 1
    : now.getFullYear();
  const target = new Date(year, renewalMonth - 1, 1);
  const diff   = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
  return diff;
}

function RenewalCard({ label, month, carrier, urgent }) {
  const dday = useMemo(() => getDday(month), [month]);
  const isThisMonth = month && month === new Date().getMonth() + 1;

  return (
    <View style={[styles.renewalCard, isThisMonth && styles.renewalCardUrgent]}>
      <Text style={styles.renewalLabel}>{label}</Text>
      {month ? (
        <>
          <Text style={styles.renewalMonth}>{month}월 갱신</Text>
          {dday !== null && (
            <Text style={[styles.dday, isThisMonth && styles.ddayUrgent]}>
              D-{dday}
            </Text>
          )}
          {carrier && <Text style={styles.carrier}>{carrier}</Text>}
        </>
      ) : (
        <Text style={styles.notRegistered}>미등록</Text>
      )}
    </View>
  );
}

export default function AnnualCycleTab({ person, onEdit }) {
  if (!person) return null;

  return (
    <View style={styles.root}>
      <Text style={styles.sectionTitle}>📅 1차 라인 — 연간 계약 관리</Text>

      {/* 갱신 카드 2열 */}
      <View style={styles.cardRow}>
        <RenewalCard
          label="자동차 보험"
          month={person.auto_renewal_month}
          carrier={person.last_auto_carrier}
        />
        <RenewalCard
          label="화재 보험"
          month={person.fire_renewal_month}
        />
      </View>

      {/* 체크리스트 */}
      <View style={styles.checklistBox}>
        <Text style={styles.checklistTitle}>갱신 진행 현황</Text>
        <View style={styles.checkRow}>
          <Text style={styles.checkIcon}>☐</Text>
          <Text style={styles.checkText}>갱신 안내 문자 발송</Text>
        </View>
        <View style={styles.checkRow}>
          <Text style={styles.checkIcon}>☐</Text>
          <Text style={styles.checkText}>견적 비교 완료</Text>
        </View>
        <View style={styles.checkRow}>
          <Text style={styles.checkIcon}>☐</Text>
          <Text style={styles.checkText}>갱신 계약 완료</Text>
        </View>
      </View>

      {/* 갱신 메모 */}
      {person.renewal_memo && (
        <View style={styles.memoBox}>
          <Text style={styles.memoLabel}>📝 갱신 메모</Text>
          <Text style={styles.memoText}>{person.renewal_memo}</Text>
        </View>
      )}

      <TouchableOpacity style={styles.editBtn} onPress={() => onEdit && onEdit(person)}>
        <Text style={styles.editBtnText}>갱신 정보 수정</Text>
      </TouchableOpacity>
    </View>
  );
}

const URGENT_COLOR = '#dc2626';

const styles = StyleSheet.create({
  root: { flex: 1, padding: 16 },
  sectionTitle: {
    fontSize: 15, fontWeight: '900', color: '#1e3a5f', marginBottom: 12,
  },
  cardRow: {
    flexDirection: 'row', gap: 12, marginBottom: 16,
  },
  renewalCard: {
    flex: 1, borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    borderRadius: 10, padding: 12, backgroundColor: '#f9fafb',
  },
  renewalCardUrgent: {
    borderColor: URGENT_COLOR, backgroundColor: '#fff1f2',
  },
  renewalLabel:   { fontSize: 11, color: '#6b7280', marginBottom: 4 },
  renewalMonth:   { fontSize: 16, fontWeight: '900', color: '#111' },
  dday:           { fontSize: 22, fontWeight: '900', color: '#1d4ed8', marginTop: 2 },
  ddayUrgent:     { color: URGENT_COLOR },
  carrier:        { fontSize: 11, color: '#6b7280', marginTop: 4 },
  notRegistered:  { fontSize: 13, color: '#9ca3af', marginTop: 4 },
  checklistBox: {
    borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 10,
    padding: 12, backgroundColor: '#fff', marginBottom: 12,
  },
  checklistTitle: { fontSize: 12, fontWeight: '700', color: '#374151', marginBottom: 8 },
  checkRow:       { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  checkIcon:      { fontSize: 16, marginRight: 8, color: '#6b7280' },
  checkText:      { fontSize: 13, color: '#374151' },
  memoBox: {
    backgroundColor: '#fffbeb', borderWidth: 1, borderColor: '#fcd34d',
    borderRadius: 8, padding: 10, marginBottom: 12,
  },
  memoLabel: { fontSize: 11, fontWeight: '700', color: '#92400e', marginBottom: 4 },
  memoText:  { fontSize: 13, color: '#78350f' },
  editBtn: {
    backgroundColor: '#1e3a5f', borderRadius: 8,
    paddingVertical: 10, alignItems: 'center',
  },
  editBtnText: { color: '#fff', fontWeight: '700', fontSize: 13 },
});
