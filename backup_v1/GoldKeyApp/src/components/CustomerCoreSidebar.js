/**
 * CustomerCoreSidebar.js — [Core] 주라인
 * 태블릿 좌측 고정 패널 / 폰에서는 상단 카드
 */
import React from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Linking,
} from 'react-native';
import { MANAGEMENT_TIER, CUSTOMER_STATUS } from '../config';

export default function CustomerCoreSidebar({ person, onStartConsult, onScanPolicy }) {
  if (!person) return null;

  const tier   = MANAGEMENT_TIER[person.management_tier] || MANAGEMENT_TIER[3];
  const status = CUSTOMER_STATUS[person.status] || CUSTOMER_STATUS.potential;

  const callPhone = () => {
    if (person.contact) Linking.openURL(`tel:${person.contact.replace(/-/g, '')}`);
  };

  return (
    <View style={styles.root}>
      {/* 이름 + 별표 + 등급 */}
      <View style={styles.nameRow}>
        {person.is_favorite && <Text style={styles.star}>★ </Text>}
        <Text style={styles.name}>{person.name}</Text>
        {person.birth_date && (
          <Text style={styles.age}>
            {' '}({new Date().getFullYear() - parseInt(person.birth_date.slice(0, 4), 10)}세
            /{person.gender === 'male' ? '남' : '여'})
          </Text>
        )}
      </View>

      {/* 관리 등급 + 모임 태그 */}
      <View style={styles.tagRow}>
        <View style={[styles.tierBadge, { backgroundColor: tier.bg }]}>
          <Text style={[styles.tierText, { color: tier.color }]}>{tier.label}</Text>
        </View>
        {(person.community_tags || []).slice(0, 2).map((tag) => (
          <View key={tag} style={styles.communityTag}>
            <Text style={styles.communityTagText}>{tag}</Text>
          </View>
        ))}
      </View>

      <View style={styles.divider} />

      {/* 연락처 */}
      <TouchableOpacity onPress={callPhone} style={styles.infoRow}>
        <Text style={styles.infoIcon}>📞</Text>
        <Text style={styles.infoText}>{person.contact || '미등록'}</Text>
      </TouchableOpacity>

      {/* 주소 */}
      {person.address && (
        <View style={styles.infoRow}>
          <Text style={styles.infoIcon}>🏠</Text>
          <Text style={styles.infoText}>{person.address}</Text>
        </View>
      )}

      {/* 직업 */}
      {person.job && (
        <View style={styles.infoRow}>
          <Text style={styles.infoIcon}>💼</Text>
          <Text style={styles.infoText}>{person.job}</Text>
        </View>
      )}

      <View style={styles.divider} />

      {/* 관리 상태 */}
      <View style={styles.infoRow}>
        <Text style={styles.infoLabel}>상태</Text>
        <View style={[styles.statusBadge, { borderColor: status.color }]}>
          <Text style={[styles.statusText, { color: status.color }]}>{status.label}</Text>
        </View>
      </View>

      {/* 최근 상담일 */}
      {person.last_consulted_at && (
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>최근상담</Text>
          <Text style={styles.infoText}>
            {person.last_consulted_at.slice(0, 10)}
          </Text>
        </View>
      )}

      <View style={styles.divider} />

      {/* 액션 버튼 */}
      <TouchableOpacity style={[styles.actionBtn, styles.primaryBtn]} onPress={onStartConsult}>
        <Text style={styles.primaryBtnText}>상담 시작</Text>
      </TouchableOpacity>
      <TouchableOpacity style={[styles.actionBtn, styles.secondaryBtn]} onPress={onScanPolicy}>
        <Text style={styles.secondaryBtnText}>증권 스캔</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    backgroundColor: '#fff',
    borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    borderRadius: 12, padding: 14,
  },
  nameRow:   { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', marginBottom: 6 },
  star:      { fontSize: 16, color: '#f59e0b' },
  name:      { fontSize: 18, fontWeight: '900', color: '#111' },
  age:       { fontSize: 13, color: '#6b7280', marginLeft: 2 },
  tagRow:    { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginBottom: 8 },
  tierBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  tierText:  { fontSize: 11, fontWeight: '700' },
  communityTag: {
    backgroundColor: '#f0f9ff', borderWidth: 1, borderColor: '#bae6fd',
    paddingHorizontal: 6, paddingVertical: 2, borderRadius: 8,
  },
  communityTagText: { fontSize: 10, color: '#0369a1' },
  divider:   { height: 1, backgroundColor: '#e5e7eb', marginVertical: 8 },
  infoRow:   { flexDirection: 'row', alignItems: 'center', marginBottom: 4 },
  infoIcon:  { fontSize: 13, marginRight: 6, width: 18 },
  infoLabel: { fontSize: 11, color: '#9ca3af', width: 50 },
  infoText:  { fontSize: 13, color: '#374151', flex: 1 },
  statusBadge: {
    borderWidth: 1, borderRadius: 8,
    paddingHorizontal: 8, paddingVertical: 1,
  },
  statusText: { fontSize: 11, fontWeight: '700' },
  actionBtn:  {
    borderRadius: 8, paddingVertical: 10,
    alignItems: 'center', marginTop: 6,
  },
  primaryBtn:      { backgroundColor: '#1e3a5f' },
  primaryBtnText:  { color: '#fff', fontWeight: '800', fontSize: 14 },
  secondaryBtn:    { backgroundColor: '#f0fdf4', borderWidth: 1, borderColor: '#16a34a' },
  secondaryBtnText: { color: '#16a34a', fontWeight: '700', fontSize: 14 },
});
