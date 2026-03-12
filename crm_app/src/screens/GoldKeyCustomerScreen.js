/**
 * GoldKeyCustomerScreen.js — CRM 앱의 Supabase 3단계 고객 관리 화면
 * Phase 2: GoldKeyApp 모 앱 컴포넌트 이식 통합 화면
 *
 * ┌ 데이터 흐름 ─────────────────────────────────────────────────────────────┐
 * │  authStore.personId → agent_id로 사용 (GP-IMMORTAL §2 격리)              │
 * │  supabaseService 직접 호출 (Firebase customerStore와 독립)               │
 * └──────────────────────────────────────────────────────────────────────────┘
 *
 * 진입: Dashboard → "3단계 고객 관리" 탭 or 버튼
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  FlatList, TouchableOpacity, TextInput, ActivityIndicator,
} from 'react-native';
import { useAuthStore }       from '../store/authStore';
import { isTablet, LAYOUT }   from '../utils/deviceCheck';
import { MANAGEMENT_TIER }    from '../config';
import {
  fetchPeople, fetchSchedules,
} from '../services/supabaseService';

import CustomerCoreSidebar  from '../components/CustomerCoreSidebar';
import AnnualCycleTab       from '../components/AnnualCycleTab';
import StrategicCareTab     from '../components/StrategicCareTab';
import SocialNetworkTab     from '../components/SocialNetworkTab';
import ConsultHistoryPanel  from '../components/ConsultHistoryPanel';
import PolicyListView       from '../components/PolicyListView';
import PolicyScanModal      from '../components/PolicyScanModal';
import PersonFormModal      from '../components/PersonFormModal';
import ScheduleModal        from '../components/ScheduleModal';

const TABS = [
  { key: 'annual',    label: '📅 1차 갱신' },
  { key: 'strategic', label: '💎 2차 케어' },
  { key: 'social',    label: '🏟️ 3차 활동' },
  { key: 'policies',  label: '📋 계약' },
];

const FILTER_TIERS = [
  { label: '전체', value: null },
  { label: 'VVIP', value: 1 },
  { label: '핵심', value: 2 },
  { label: '일반', value: 3 },
];

// ── 고객 목록 카드 ─────────────────────────────────────────────────────────
function PersonCard({ person, isActive, onPress, onLongPress }) {
  const tier  = MANAGEMENT_TIER[person.management_tier] || MANAGEMENT_TIER[3];
  const month = new Date().getMonth() + 1;
  const needsRenewal =
    person.auto_renewal_month === month || person.fire_renewal_month === month;

  return (
    <TouchableOpacity
      style={[styles.card, isActive && styles.cardActive, needsRenewal && styles.cardRenewal]}
      onPress={() => onPress(person)}
      onLongPress={() => onLongPress && onLongPress(person)}
      activeOpacity={0.75}
    >
      <View style={styles.cardLeft}>
        {person.is_favorite && <Text style={styles.star}>★ </Text>}
        <View style={{ flex: 1 }}>
          <Text style={styles.cardName}>{person.name}</Text>
          <Text style={styles.cardSub} numberOfLines={1}>
            {person.contact || '연락처 미등록'}
            {person.job ? `  ·  ${person.job}` : ''}
          </Text>
          {needsRenewal && (
            <Text style={styles.renewalAlert}>🔄 이번 달 갱신 대상</Text>
          )}
        </View>
      </View>
      <View style={[styles.tierBadge, { backgroundColor: tier.bg }]}>
        <Text style={[styles.tierText, { color: tier.color }]}>{tier.label}</Text>
      </View>
    </TouchableOpacity>
  );
}

// ── 상세 패널 (우측 또는 전체 화면) ──────────────────────────────────────
function DetailPanel({
  person, schedules, activeTab, onTabChange,
  onEdit, onAddSchedule, onScan, allPeople,
}) {
  const renderTab = () => {
    switch (activeTab) {
      case 'annual':
        return <AnnualCycleTab person={person} />;
      case 'strategic':
        return <StrategicCareTab person={person} scanResults={[]} />;
      case 'social':
        return (
          <SocialNetworkTab
            person={person}
            allPeople={allPeople}
            onOpenPerson={() => {}}
          />
        );
      case 'policies':
        return (
          <PolicyListView
            personId={person?.person_id}
            onAddPolicy={onScan}
          />
        );
      default:
        return null;
    }
  };

  return (
    <View style={{ flex: 1 }}>
      {/* 탭바 */}
      <View style={styles.tabBar}>
        {TABS.map((t) => (
          <TouchableOpacity
            key={t.key}
            style={[styles.tabItem, activeTab === t.key && styles.tabItemActive]}
            onPress={() => onTabChange(t.key)}
          >
            <Text style={[styles.tabText, activeTab === t.key && styles.tabTextActive]}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 탭 내용 */}
      <View style={styles.tabContent}>{renderTab()}</View>
    </View>
  );
}

// ── 메인 화면 ──────────────────────────────────────────────────────────────
export default function GoldKeyCustomerScreen({ onBack }) {
  const agentId = useAuthStore((s) => s.personId) || '';

  const [people,       setPeople]       = useState([]);
  const [schedules,    setSchedules]    = useState([]);
  const [activePerson, setActivePerson] = useState(null);
  const [activeTab,    setActiveTab]    = useState('annual');
  const [isLoading,    setIsLoading]    = useState(false);
  const [query,        setQuery]        = useState('');
  const [tierFilter,   setTierFilter]   = useState(null);

  const [showForm,     setShowForm]     = useState(false);
  const [editPerson,   setEditPerson]   = useState(null);
  const [showSchedule, setShowSchedule] = useState(false);
  const [showScan,     setShowScan]     = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const filters = {};
      if (tierFilter != null) filters.management_tier = tierFilter;
      if (query)              filters.query           = query;

      const [peopleData, scheduleData] = await Promise.all([
        fetchPeople(agentId, filters),
        fetchSchedules(agentId),
      ]);
      setPeople(peopleData);
      setSchedules(scheduleData);

      if (peopleData.length > 0 && !activePerson) {
        setActivePerson(peopleData[0]);
      }
    } catch (e) {
      console.error('데이터 로드 오류:', e);
    } finally {
      setIsLoading(false);
    }
  }, [agentId, query, tierFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  const personSchedules = schedules.filter(
    (s) => s.person_id === activePerson?.person_id,
  );

  const handleOpenForm = (person = null) => {
    setEditPerson(person);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditPerson(null);
    loadData();
  };

  const handleScheduleClose = () => {
    setShowSchedule(false);
    loadData();
  };

  const handleScanSaved = () => {
    setShowScan(false);
    setActiveTab('policies');
  };

  // ── 태블릿: 2컬럼 (목록 | 사이드바+탭+히스토리) ──────────────────────────
  if (isTablet) {
    return (
      <SafeAreaView style={styles.root}>
        <PersonFormModal  visible={showForm}     person={editPerson}   onClose={handleFormClose} />
        <ScheduleModal    visible={showSchedule} person={activePerson} onClose={handleScheduleClose} />
        <PolicyScanModal  visible={showScan}     person={activePerson} onClose={() => setShowScan(false)} onSaved={handleScanSaved} />

        {/* 헤더 */}
        <View style={styles.header}>
          {onBack && (
            <TouchableOpacity onPress={onBack} style={styles.backBtn}>
              <Text style={styles.backText}>← 대시보드</Text>
            </TouchableOpacity>
          )}
          <Text style={styles.headerTitle}>👥 3단계 고객 관리</Text>
          <TouchableOpacity style={styles.addBtn} onPress={() => handleOpenForm(null)}>
            <Text style={styles.addBtnText}>+ 고객 등록</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.tabletRow}>
          {/* 좌측: 고객 목록 */}
          <View style={[styles.listPanel, { width: LAYOUT.sidebarWidth + 40 }]}>
            {/* 검색 */}
            <TextInput
              style={styles.searchInput}
              value={query}
              onChangeText={setQuery}
              placeholder="이름 검색..."
              placeholderTextColor="#9ca3af"
            />
            {/* 등급 필터 */}
            <View style={styles.filterRow}>
              {FILTER_TIERS.map((f) => (
                <TouchableOpacity
                  key={String(f.value)}
                  style={[styles.filterBtn, tierFilter === f.value && styles.filterBtnActive]}
                  onPress={() => setTierFilter(f.value)}
                >
                  <Text style={[styles.filterText, tierFilter === f.value && styles.filterTextActive]}>
                    {f.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            {isLoading
              ? <ActivityIndicator style={{ margin: 20 }} />
              : (
                <FlatList
                  data={people}
                  keyExtractor={(item) => item.person_id}
                  renderItem={({ item }) => (
                    <PersonCard
                      person={item}
                      isActive={item.person_id === activePerson?.person_id}
                      onPress={setActivePerson}
                      onLongPress={handleOpenForm}
                    />
                  )}
                  showsVerticalScrollIndicator={false}
                  ListEmptyComponent={
                    <Text style={styles.emptyText}>등록된 고객이 없습니다.</Text>
                  }
                />
              )
            }
          </View>

          {/* 우측: 상세 */}
          {activePerson ? (
            <View style={styles.detailArea}>
              {/* Core 사이드바 + 수정 버튼 */}
              <View style={[styles.coreSidebar, { width: LAYOUT.sidebarWidth }]}>
                <TouchableOpacity
                  style={styles.editSmallBtn}
                  onPress={() => handleOpenForm(activePerson)}
                >
                  <Text style={styles.editSmallText}>✏️ 수정</Text>
                </TouchableOpacity>
                <CustomerCoreSidebar
                  person={activePerson}
                  onStartConsult={() => setActiveTab('strategic')}
                  onScanPolicy={() => setShowScan(true)}
                />
              </View>

              {/* 탭 + 히스토리 */}
              <View style={styles.mainAndSub}>
                <View style={{ flex: 1 }}>
                  <DetailPanel
                    person={activePerson}
                    schedules={personSchedules}
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    onEdit={() => handleOpenForm(activePerson)}
                    onAddSchedule={() => setShowSchedule(true)}
                    onScan={() => setShowScan(true)}
                    allPeople={people}
                  />
                </View>
                <View style={[styles.historyPanel, { width: LAYOUT.subWidth }]}>
                  <ConsultHistoryPanel
                    person={activePerson}
                    schedules={personSchedules}
                    onAddSchedule={() => setShowSchedule(true)}
                  />
                </View>
              </View>
            </View>
          ) : (
            <View style={styles.emptyDetail}>
              <Text style={styles.emptyDetailText}>← 좌측에서 고객을 선택하세요</Text>
            </View>
          )}
        </View>

        {/* FAB */}
        <TouchableOpacity style={styles.fab} onPress={() => handleOpenForm(null)}>
          <Text style={styles.fabText}>+</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  // ── 핸드폰: 목록 ↔ 상세 전환 ───────────────────────────────────────────
  if (activePerson && !isTablet) {
    return (
      <SafeAreaView style={styles.root}>
        <PersonFormModal  visible={showForm}     person={editPerson}   onClose={handleFormClose} />
        <ScheduleModal    visible={showSchedule} person={activePerson} onClose={handleScheduleClose} />
        <PolicyScanModal  visible={showScan}     person={activePerson} onClose={() => setShowScan(false)} onSaved={handleScanSaved} />

        <View style={styles.header}>
          <TouchableOpacity onPress={() => setActivePerson(null)} style={styles.backBtn}>
            <Text style={styles.backText}>← 목록</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle} numberOfLines={1}>{activePerson.name}</Text>
          <TouchableOpacity onPress={() => handleOpenForm(activePerson)} style={styles.addBtn}>
            <Text style={styles.addBtnText}>수정</Text>
          </TouchableOpacity>
        </View>

        <CustomerCoreSidebar
          person={activePerson}
          onStartConsult={() => setActiveTab('strategic')}
          onScanPolicy={() => setShowScan(true)}
        />

        <DetailPanel
          person={activePerson}
          schedules={personSchedules}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onEdit={() => handleOpenForm(activePerson)}
          onAddSchedule={() => setShowSchedule(true)}
          onScan={() => setShowScan(true)}
          allPeople={people}
        />

        <View style={styles.phoneHistoryWrap}>
          <ConsultHistoryPanel
            person={activePerson}
            schedules={personSchedules}
            onAddSchedule={() => setShowSchedule(true)}
          />
        </View>
      </SafeAreaView>
    );
  }

  // ── 핸드폰: 목록 화면 ──────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.root}>
      <PersonFormModal visible={showForm} person={editPerson} onClose={handleFormClose} />

      <View style={styles.header}>
        {onBack && (
          <TouchableOpacity onPress={onBack} style={styles.backBtn}>
            <Text style={styles.backText}>← 뒤로</Text>
          </TouchableOpacity>
        )}
        <Text style={styles.headerTitle}>👥 고객 관리</Text>
        <Text style={styles.headerCount}>{people.length}명</Text>
      </View>

      <TextInput
        style={styles.searchInput}
        value={query}
        onChangeText={setQuery}
        placeholder="이름 검색..."
        placeholderTextColor="#9ca3af"
      />

      <View style={styles.filterRow}>
        {FILTER_TIERS.map((f) => (
          <TouchableOpacity
            key={String(f.value)}
            style={[styles.filterBtn, tierFilter === f.value && styles.filterBtnActive]}
            onPress={() => setTierFilter(f.value)}
          >
            <Text style={[styles.filterText, tierFilter === f.value && styles.filterTextActive]}>
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {isLoading
        ? <ActivityIndicator style={{ margin: 40 }} />
        : (
          <FlatList
            data={people}
            keyExtractor={(item) => item.person_id}
            renderItem={({ item }) => (
              <PersonCard
                person={item}
                isActive={false}
                onPress={setActivePerson}
                onLongPress={handleOpenForm}
              />
            )}
            contentContainerStyle={{ paddingBottom: 80 }}
            showsVerticalScrollIndicator={false}
            ListEmptyComponent={
              <Text style={styles.emptyText}>등록된 고객이 없습니다.</Text>
            }
          />
        )
      }

      <TouchableOpacity style={styles.fab} onPress={() => handleOpenForm(null)}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root:          { flex: 1, backgroundColor: '#f9fafb' },
  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1, borderBottomColor: '#e5e7eb',
  },
  backBtn:       { marginRight: 10 },
  backText:      { fontSize: 14, color: '#2563eb', fontWeight: '600' },
  headerTitle:   { flex: 1, fontSize: 16, fontWeight: '900', color: '#1e3a5f' },
  headerCount:   { fontSize: 13, color: '#6b7280', fontWeight: '600' },
  addBtn: {
    backgroundColor: '#1e3a5f', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 5,
  },
  addBtnText:    { color: '#fff', fontWeight: '700', fontSize: 12 },

  // 검색 + 필터
  searchInput: {
    margin: 12, borderWidth: 1, borderColor: '#e5e7eb',
    borderRadius: 10, paddingHorizontal: 14, paddingVertical: 8,
    fontSize: 14, backgroundColor: '#fff', color: '#111',
  },
  filterRow:     { flexDirection: 'row', paddingHorizontal: 12, gap: 8, marginBottom: 4 },
  filterBtn: {
    paddingHorizontal: 12, paddingVertical: 5,
    borderRadius: 16, borderWidth: 1, borderColor: '#d1d5db', backgroundColor: '#fff',
  },
  filterBtnActive: { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  filterText:    { fontSize: 12, color: '#374151' },
  filterTextActive:{ color: '#fff', fontWeight: '700' },

  // 카드
  card: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#fff', marginHorizontal: 12, marginVertical: 3,
    padding: 12, borderRadius: 10,
    borderWidth: 1, borderColor: '#e5e7eb',
  },
  cardActive:    { borderColor: '#1e3a5f', backgroundColor: '#eff6ff' },
  cardRenewal:   { borderColor: '#f59e0b', backgroundColor: '#fffbeb' },
  cardLeft:      { flexDirection: 'row', alignItems: 'flex-start', flex: 1 },
  star:          { fontSize: 14, color: '#f59e0b', marginTop: 2 },
  cardName:      { fontSize: 15, fontWeight: '900', color: '#111' },
  cardSub:       { fontSize: 12, color: '#6b7280', marginTop: 2 },
  renewalAlert:  { fontSize: 11, color: '#d97706', fontWeight: '700', marginTop: 2 },
  tierBadge:     { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, marginLeft: 8 },
  tierText:      { fontSize: 11, fontWeight: '700' },
  emptyText:     { textAlign: 'center', color: '#9ca3af', marginTop: 40, fontSize: 14 },

  // 태블릿 레이아웃
  tabletRow:     { flex: 1, flexDirection: 'row' },
  listPanel: {
    borderRightWidth: 1, borderRightColor: '#e5e7eb',
    backgroundColor: '#f9fafb',
  },
  detailArea:    { flex: 1, flexDirection: 'row' },
  coreSidebar: {
    borderRightWidth: 1, borderRightColor: '#e5e7eb',
    paddingTop: 4,
  },
  editSmallBtn: {
    margin: 8, padding: 6,
    backgroundColor: '#f3f4f6', borderRadius: 6, alignSelf: 'flex-end',
  },
  editSmallText: { fontSize: 12, color: '#374151', fontWeight: '600' },
  mainAndSub:    { flex: 1, flexDirection: 'row' },
  historyPanel:  { borderLeftWidth: 1, borderLeftColor: '#e5e7eb' },
  emptyDetail: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
  },
  emptyDetailText: { fontSize: 14, color: '#9ca3af' },

  // 탭
  tabBar: {
    flexDirection: 'row', backgroundColor: '#fff',
    borderBottomWidth: 1, borderBottomColor: '#e5e7eb',
  },
  tabItem: {
    flex: 1, paddingVertical: 10, alignItems: 'center',
    borderBottomWidth: 2, borderBottomColor: 'transparent',
  },
  tabItemActive: { borderBottomColor: '#1e3a5f' },
  tabText:       { fontSize: 11, color: '#9ca3af', fontWeight: '600' },
  tabTextActive: { color: '#1e3a5f', fontWeight: '900' },
  tabContent:    { flex: 1 },

  // 핸드폰 히스토리
  phoneHistoryWrap: { maxHeight: 260, borderTopWidth: 1, borderTopColor: '#e5e7eb' },

  // FAB
  fab: {
    position: 'absolute', right: 20, bottom: 24,
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: '#1e3a5f', alignItems: 'center', justifyContent: 'center',
    elevation: 6,
  },
  fabText: { color: '#fff', fontSize: 26, fontWeight: '300', lineHeight: 30 },
});
