/**
 * CustomerListScreen.js — 고객 목록 메인 화면
 * 이번 달 갱신 대상자 상단 하이라이트 + 3단계 계층 필터
 */
import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  TextInput, SafeAreaView,
} from 'react-native';
import { useCustomerStore } from '../store/customerStore';
import { MANAGEMENT_TIER, PROSPECTING_STAGE } from '../config';
import PersonFormModal from '../components/PersonFormModal';

function PersonCard({ person, onPress, onLongPress }) {
  const tier  = MANAGEMENT_TIER[person.management_tier] || MANAGEMENT_TIER[3];
  const month = new Date().getMonth() + 1;
  const needsRenewal =
    person.auto_renewal_month === month || person.fire_renewal_month === month;

  return (
    <TouchableOpacity
      style={[styles.card, needsRenewal && styles.cardRenewal]}
      onPress={() => onPress(person.person_id)}
      onLongPress={() => onLongPress && onLongPress(person)}
      activeOpacity={0.75}
    >
      <View style={styles.cardLeft}>
        {person.is_favorite && <Text style={styles.star}>★ </Text>}
        <View>
          <Text style={styles.cardName}>{person.name}</Text>
          <Text style={styles.cardSub}>
            {person.contact || '연락처 미등록'}
            {person.job ? `  ·  ${person.job}` : ''}
          </Text>
          {needsRenewal && (
            <Text style={styles.renewalAlert}>
              🔴 {person.auto_renewal_month === month ? '자동차' : '화재'}보험 이번 달 갱신
            </Text>
          )}
        </View>
      </View>
      <View style={styles.cardRight}>
        <View style={[styles.tierBadge, { backgroundColor: tier.bg }]}>
          <Text style={[styles.tierText, { color: tier.color }]}>{tier.label}</Text>
        </View>
        {person.community_tags?.slice(0, 1).map((tag) => (
          <Text key={tag} style={styles.tagChip}>{tag}</Text>
        ))}
      </View>
    </TouchableOpacity>
  );
}

export default function CustomerListScreen() {
  const [query,    setQuery]    = useState('');
  const [filter,   setFilter]   = useState({});
  const [showForm, setShowForm] = useState(false);
  const [editPerson, setEditPerson] = useState(null);

  const people       = useCustomerStore((s) => s.people);
  const isLoading    = useCustomerStore((s) => s.isLoading);
  const loadPeople   = useCustomerStore((s) => s.loadPeople);
  const openProfile  = useCustomerStore((s) => s.openProfile);
  const renewalList  = useCustomerStore((s) => s.getRenewalThisMonth());

  const handleOpenForm = (person = null) => {
    setEditPerson(person);
    setShowForm(true);
  };

  useEffect(() => { loadPeople(); }, []);

  const filtered = people.filter((p) =>
    !query || p.name.includes(query) || (p.contact || '').includes(query)
  );

  const FILTER_TIERS = [
    { label: '전체', value: null },
    { label: 'VVIP', value: 1 },
    { label: '핵심', value: 2 },
    { label: '일반', value: 3 },
  ];

  return (
    <SafeAreaView style={styles.root} key="customer-list">
      {/* 헤더 */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>👥 고객 관리</Text>
        <Text style={styles.headerCount}>{people.length}명</Text>
      </View>

      {/* 이번 달 갱신 배너 */}
      {renewalList.length > 0 && (
        <View style={styles.renewalBanner}>
          <Text style={styles.renewalBannerText}>
            🔴 이번 달 갱신 대상: {renewalList.map((p) => p.name).join(', ')}
          </Text>
        </View>
      )}

      {/* 검색 */}
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          value={query}
          onChangeText={setQuery}
          placeholder="이름 또는 연락처 검색..."
          placeholderTextColor="#9ca3af"
        />
      </View>

      {/* 등급 필터 */}
      <View style={styles.filterRow}>
        {FILTER_TIERS.map((f) => (
          <TouchableOpacity
            key={String(f.value)}
            style={[styles.filterBtn, filter.management_tier === f.value && styles.filterBtnActive]}
            onPress={() => {
              const next = { ...filter, management_tier: f.value };
              setFilter(next);
              loadPeople(next);
            }}
          >
            <Text style={[
              styles.filterText,
              filter.management_tier === f.value && styles.filterTextActive,
            ]}>{f.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 목록 */}
      <PersonFormModal
        visible={showForm}
        person={editPerson}
        onClose={() => { setShowForm(false); setEditPerson(null); loadPeople(filter); }}
      />
      <FlatList
        data={filtered}
        keyExtractor={(item) => item.person_id}
        renderItem={({ item }) => (
          <PersonCard
            person={item}
            onPress={openProfile}
            onLongPress={() => handleOpenForm(item)}
          />
        )}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            {isLoading ? '불러오는 중...' : '등록된 고객이 없습니다.'}
          </Text>
        }
      />

      {/* FAB — 고객 등록 */}
      <TouchableOpacity style={styles.fab} onPress={() => handleOpenForm(null)}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root:          { flex: 1, backgroundColor: '#f9fafb' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    padding: 16, backgroundColor: '#fff',
    borderBottomWidth: 1, borderBottomColor: '#e5e7eb',
  },
  headerTitle:   { fontSize: 18, fontWeight: '900', color: '#1e3a5f' },
  headerCount:   { fontSize: 14, color: '#6b7280', fontWeight: '600' },
  renewalBanner: {
    backgroundColor: '#fff1f2', padding: 10,
    borderBottomWidth: 1, borderBottomColor: '#fecaca',
  },
  renewalBannerText: { fontSize: 12, color: '#dc2626', fontWeight: '700' },
  searchRow:     { padding: 12, backgroundColor: '#fff' },
  searchInput: {
    borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    borderRadius: 8, padding: 10, fontSize: 14, color: '#111',
    backgroundColor: '#f9fafb',
  },
  filterRow: {
    flexDirection: 'row', paddingHorizontal: 12, paddingBottom: 8,
    backgroundColor: '#fff', gap: 6,
  },
  filterBtn: {
    paddingHorizontal: 12, paddingVertical: 5,
    borderRadius: 12, borderWidth: 1, borderColor: '#d1d5db',
    backgroundColor: '#fff',
  },
  filterBtnActive: { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  filterText:      { fontSize: 12, color: '#374151' },
  filterTextActive:{ color: '#fff', fontWeight: '700' },
  list:          { padding: 12, gap: 8 },
  card: {
    backgroundColor: '#fff', borderRadius: 10,
    borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    padding: 12, flexDirection: 'row', justifyContent: 'space-between',
  },
  cardRenewal:   { borderColor: '#dc2626', backgroundColor: '#fff9f9' },
  cardLeft:      { flexDirection: 'row', alignItems: 'flex-start', flex: 1 },
  star:          { fontSize: 14, color: '#f59e0b', marginTop: 2 },
  cardName:      { fontSize: 16, fontWeight: '900', color: '#111' },
  cardSub:       { fontSize: 12, color: '#6b7280', marginTop: 2 },
  renewalAlert:  { fontSize: 11, color: '#dc2626', fontWeight: '700', marginTop: 3 },
  cardRight:     { alignItems: 'flex-end', gap: 4 },
  tierBadge:     { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
  tierText:      { fontSize: 11, fontWeight: '700' },
  tagChip:       { fontSize: 10, color: '#0369a1', backgroundColor: '#f0f9ff', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6 },
  emptyText:     { textAlign: 'center', color: '#9ca3af', marginTop: 40, fontSize: 14 },
  fab: {
    position: 'absolute', right: 20, bottom: 24,
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: '#1e3a5f', alignItems: 'center', justifyContent: 'center',
    elevation: 6,
  },
  fabText:       { color: '#fff', fontSize: 26, fontWeight: '300', lineHeight: 30 },
});
