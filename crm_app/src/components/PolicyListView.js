/**
 * PolicyListView.js — 고객 보험 계약 목록
 * 만기일 임박 순 정렬 + 상태 뱃지 + 신규 등록 버튼
 */
import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  FlatList, ActivityIndicator,
} from 'react-native';
import { fetchPolicies } from '../services/supabaseService';
import { isTablet } from '../utils/deviceCheck';

const STATUS_MAP = {
  active:     { label: '유효', color: '#16a34a', bg: '#dcfce7' },
  lapsed:     { label: '실효', color: '#d97706', bg: '#fef3c7' },
  terminated: { label: '해지', color: '#dc2626', bg: '#fee2e2' },
};

function daysUntilExpiry(expiryDate) {
  if (!expiryDate) return null;
  const diff = Math.ceil((new Date(expiryDate) - new Date()) / (1000 * 60 * 60 * 24));
  return diff;
}

function PolicyCard({ policy }) {
  const st   = STATUS_MAP[policy.status] || STATUS_MAP.active;
  const days = daysUntilExpiry(policy.expiry_date);
  const urgent = days != null && days <= 30 && days >= 0;

  return (
    <View style={[styles.card, urgent && styles.cardUrgent]}>
      <View style={styles.cardTop}>
        <View style={styles.cardLeft}>
          <Text style={styles.company}>{policy.insurance_company}</Text>
          <Text style={styles.productName} numberOfLines={1}>{policy.product_name}</Text>
          {policy.policy_number && (
            <Text style={styles.policyNum}>증권번호: {policy.policy_number}</Text>
          )}
        </View>
        <View style={styles.cardRight}>
          <View style={[styles.statusBadge, { backgroundColor: st.bg }]}>
            <Text style={[styles.statusText, { color: st.color }]}>{st.label}</Text>
          </View>
          {policy.premium && (
            <Text style={styles.premium}>
              {policy.premium.toLocaleString()}원/월
            </Text>
          )}
        </View>
      </View>

      {policy.expiry_date && (
        <View style={styles.cardBottom}>
          <Text style={styles.expiryLabel}>만기일</Text>
          <Text style={[styles.expiryDate, urgent && styles.expiryDateUrgent]}>
            {policy.expiry_date}
          </Text>
          {days != null && (
            <Text style={[styles.dday, days <= 0 && styles.ddayPast]}>
              {days > 0 ? `D-${days}` : days === 0 ? 'D-Day' : `D+${Math.abs(days)}`}
            </Text>
          )}
        </View>
      )}
    </View>
  );
}

export default function PolicyListView({ personId, onAddPolicy }) {
  const [policies, setPolicies] = useState([]);
  const [loading,  setLoading]  = useState(false);

  useEffect(() => {
    if (!personId) return;
    setLoading(true);
    fetchPolicies(personId)
      .then(setPolicies)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [personId]);

  if (loading) return <ActivityIndicator style={{ margin: 20 }} />;

  return (
    <View style={styles.root}>
      <View style={styles.headerRow}>
        <Text style={styles.sectionTitle}>📋 보험 계약 목록</Text>
        <TouchableOpacity style={styles.addBtn} onPress={onAddPolicy}>
          <Text style={styles.addBtnText}>+ 계약 등록</Text>
        </TouchableOpacity>
      </View>

      {policies.length === 0 ? (
        <View style={styles.emptyBox}>
          <Text style={styles.emptyText}>등록된 보험 계약이 없습니다.</Text>
          <Text style={styles.emptySubText}>증권 스캔 또는 직접 등록으로 추가하세요.</Text>
        </View>
      ) : (
        policies.map((p) => <PolicyCard key={p.id} policy={p} />)
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root:          { flex: 1, padding: isTablet ? 12 : 8 },
  headerRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: isTablet ? 10 : 6,
  },
  sectionTitle:  { fontSize: isTablet ? 14 : 13, fontWeight: '900', color: '#1e3a5f' },
  addBtn: {
    backgroundColor: '#1e3a5f', borderRadius: 8,
    paddingHorizontal: isTablet ? 12 : 10, paddingVertical: isTablet ? 5 : 4,
  },
  addBtnText:    { color: '#fff', fontWeight: '700', fontSize: isTablet ? 12 : 11 },
  card: {
    borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    borderRadius: 10, padding: isTablet ? 12 : 9, backgroundColor: '#fff', marginBottom: isTablet ? 8 : 6,
  },
  cardUrgent:    { borderColor: '#dc2626', backgroundColor: '#fff9f9' },
  cardTop:       { flexDirection: 'row', justifyContent: 'space-between' },
  cardLeft:      { flex: 1, marginRight: 8 },
  cardRight:     { alignItems: 'flex-end' },
  company:       { fontSize: isTablet ? 11 : 10, color: '#6b7280', marginBottom: 2 },
  productName:   { fontSize: isTablet ? 14 : 13, fontWeight: '900', color: '#111' },
  policyNum:     { fontSize: 10, color: '#9ca3af', marginTop: 2 },
  statusBadge:   { paddingHorizontal: isTablet ? 8 : 6, paddingVertical: 2, borderRadius: 8, marginBottom: 4 },
  statusText:    { fontSize: isTablet ? 11 : 10, fontWeight: '700' },
  premium:       { fontSize: isTablet ? 11 : 10, color: '#374151', fontWeight: '600' },
  cardBottom: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    marginTop: 8, paddingTop: 8,
    borderTopWidth: 1, borderTopColor: '#f3f4f6',
  },
  expiryLabel:    { fontSize: isTablet ? 11 : 10, color: '#9ca3af' },
  expiryDate:     { fontSize: isTablet ? 13 : 12, fontWeight: '700', color: '#374151' },
  expiryDateUrgent: { color: '#dc2626' },
  dday: {
    fontSize: 12, fontWeight: '900', color: '#1d4ed8',
    backgroundColor: '#eff6ff', paddingHorizontal: 6, paddingVertical: 1, borderRadius: 6,
  },
  ddayPast: { color: '#6b7280', backgroundColor: '#f3f4f6' },
  emptyBox: {
    borderWidth: 1, borderColor: '#e5e7eb', borderStyle: 'dashed',
    borderRadius: 10, padding: 20, alignItems: 'center', backgroundColor: '#f9fafb',
  },
  emptyText:    { fontSize: 13, color: '#6b7280', fontWeight: '600' },
  emptySubText: { fontSize: 11, color: '#9ca3af', marginTop: 4 },
});
