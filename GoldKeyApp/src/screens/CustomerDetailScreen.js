/**
 * CustomerDetailScreen.js — 고객 상세 화면
 * 태블릿: 3-데크 (Core 사이드바 | 탭A/B/C | 상담 히스토리)
 * 핸드폰: 세로 1컬럼 스크롤
 */
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  SafeAreaView, ScrollView,
} from 'react-native';
import { isTablet, LAYOUT } from '../utils/deviceCheck';
import CustomerCoreSidebar    from '../components/CustomerCoreSidebar';
import AnnualCycleTab         from '../components/AnnualCycleTab';
import StrategicCareTab       from '../components/StrategicCareTab';
import SocialNetworkTab       from '../components/SocialNetworkTab';
import ConsultHistoryPanel    from '../components/ConsultHistoryPanel';
import { useCustomerStore }   from '../store/customerStore';
import { fetchScanResults }   from '../services/supabaseService';

const TABS = [
  { key: 'annual',    label: '📅 1차 갱신' },
  { key: 'strategic', label: '💎 2차 케어' },
  { key: 'social',    label: '🏟️ 3차 활동' },
];

export default function CustomerDetailScreen({ onBack }) {
  const [activeTab,   setActiveTab]   = useState('annual');
  const [scanResults, setScanResults] = useState([]);

  const person     = useCustomerStore((s) => s.getActivePerson());
  const allPeople  = useCustomerStore((s) => s.people);
  const schedules  = useCustomerStore((s) => s.schedules);
  const closeProfile = useCustomerStore((s) => s.closeProfile);

  useEffect(() => {
    if (person?.person_id) {
      fetchScanResults(person.person_id).then(setScanResults).catch(() => {});
    }
  }, [person?.person_id]);

  if (!person) return null;

  const handleBack = () => {
    closeProfile();
    onBack && onBack();
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'annual':
        return <AnnualCycleTab person={person} />;
      case 'strategic':
        return <StrategicCareTab person={person} scanResults={scanResults} />;
      case 'social':
        return (
          <SocialNetworkTab
            person={person}
            allPeople={allPeople}
            onOpenPerson={(pid) => useCustomerStore.getState().openProfile(pid)}
          />
        );
      default:
        return null;
    }
  };

  if (isTablet) {
    // ── 태블릿: 3-데크 가로 레이아웃 ─────────────────────────────────────
    return (
      <SafeAreaView style={styles.root}>
        {/* 헤더 */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
            <Text style={styles.backText}>← 목록</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{person.name} 고객 상세</Text>
        </View>

        <View style={styles.deckRow}>
          {/* 좌측: Core 사이드바 */}
          <View style={[styles.sidebar, { width: LAYOUT.sidebarWidth }]}>
            <CustomerCoreSidebar
              person={person}
              onStartConsult={() => setActiveTab('strategic')}
              onScanPolicy={() => {}}
            />
          </View>

          {/* 중앙: 탭 시스템 */}
          <View style={[styles.mainPanel, { width: LAYOUT.mainWidth }]}>
            <View style={styles.tabBar}>
              {TABS.map((t) => (
                <TouchableOpacity
                  key={t.key}
                  style={[styles.tabItem, activeTab === t.key && styles.tabItemActive]}
                  onPress={() => setActiveTab(t.key)}
                >
                  <Text style={[styles.tabText, activeTab === t.key && styles.tabTextActive]}>
                    {t.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <View style={styles.tabContent}>
              {renderTabContent()}
            </View>
          </View>

          {/* 우측: 상담 히스토리 */}
          <View style={[styles.subPanel, { width: LAYOUT.subWidth }]}>
            <ConsultHistoryPanel
              person={person}
              schedules={schedules}
              onAddSchedule={() => {}}
            />
          </View>
        </View>
      </SafeAreaView>
    );
  }

  // ── 핸드폰: 세로 1컬럼 ─────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Text style={styles.backText}>← 목록</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{person.name}</Text>
      </View>

      <ScrollView style={styles.scrollPhone} showsVerticalScrollIndicator={false}>
        {/* Core 카드 (축약형) */}
        <View style={styles.phoneSection}>
          <CustomerCoreSidebar
            person={person}
            onStartConsult={() => setActiveTab('strategic')}
            onScanPolicy={() => {}}
          />
        </View>

        {/* 탭 바 */}
        <View style={styles.tabBar}>
          {TABS.map((t) => (
            <TouchableOpacity
              key={t.key}
              style={[styles.tabItem, activeTab === t.key && styles.tabItemActive]}
              onPress={() => setActiveTab(t.key)}
            >
              <Text style={[styles.tabText, activeTab === t.key && styles.tabTextActive]}>
                {t.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* 탭 내용 */}
        <View style={styles.phoneSection}>
          {renderTabContent()}
        </View>

        {/* 상담 히스토리 */}
        <View style={styles.phoneSection}>
          <ConsultHistoryPanel
            person={person}
            schedules={schedules}
            onAddSchedule={() => {}}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root:       { flex: 1, backgroundColor: '#f9fafb' },
  header: {
    flexDirection: 'row', alignItems: 'center',
    padding: 12, borderBottomWidth: 1, borderBottomColor: '#e5e7eb',
    backgroundColor: '#fff',
  },
  backBtn:     { marginRight: 12 },
  backText:    { fontSize: 14, color: '#2563eb', fontWeight: '600' },
  headerTitle: { fontSize: 16, fontWeight: '900', color: '#1e3a5f' },

  // 태블릿 3-데크
  deckRow:   { flex: 1, flexDirection: 'row' },
  sidebar:   { padding: 12, borderRightWidth: 1, borderRightColor: '#e5e7eb' },
  mainPanel: { flex: 1, borderRightWidth: 1, borderRightColor: '#e5e7eb' },
  subPanel:  { padding: 4 },

  // 탭
  tabBar: {
    flexDirection: 'row',
    borderBottomWidth: 1, borderBottomColor: '#e5e7eb',
    backgroundColor: '#fff',
  },
  tabItem: {
    flex: 1, paddingVertical: 10, alignItems: 'center',
    borderBottomWidth: 2, borderBottomColor: 'transparent',
  },
  tabItemActive:  { borderBottomColor: '#1e3a5f' },
  tabText:        { fontSize: 12, color: '#6b7280', fontWeight: '600' },
  tabTextActive:  { color: '#1e3a5f', fontWeight: '800' },
  tabContent:     { flex: 1 },

  // 핸드폰
  scrollPhone:  { flex: 1 },
  phoneSection: { padding: 12 },
});
