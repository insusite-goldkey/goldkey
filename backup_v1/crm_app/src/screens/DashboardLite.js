'use strict';
/**
 * src/screens/DashboardLite.js — Goldkey AI Masters CRM 2026
 *
 * [GP 마스터-그림자 원칙 §3] 초경량 대시보드
 *
 * 자 앱은 오직 3가지 역할만 한다:
 *   1) shared 공통 모듈을 통한 고객 리스트 조회/입력
 *   2) 내보험다보여 기본 조회 (딥링크 발사)
 *   3) 모 앱으로 쏘는 딥링크 발사대
 *
 * 복잡한 계산식(호프만·KB7·KOSIS)은 모 앱에 위임한다 → DeepLinkButton.
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, FlatList, SafeAreaView,
  StyleSheet, TouchableOpacity, Modal, ActivityIndicator,
} from 'react-native';

// ── [GP §1] 공통 모듈 import (모 앱 구조 거울) ───────────────────────────────
import {
  CustomerCard,
  CustomerListHeader,
  CustomerForm,
  DeepLinkButton,
} from '../shared/CustomerComponents';
import { fetchCustomers, customerInputForm, toggleFavorite } from '../shared/supabaseCrud';
import { useAuthStore } from '../store/authStore';
import TaskCard     from '../components/TaskCard';
import { useCrmStore, selectTasks, FEATURE_FLAGS } from '../store/crmStore';

// ── 탭 상수 ───────────────────────────────────────────────────────────────────
const TAB = { TODAY: 'today', CUSTOMERS: 'customers', DEEPLINK: 'deeplink' };

// ── 메인 대시보드 (초경량) ─────────────────────────────────────────────────────
export default function DashboardLite() {
  const [activeTab, setActiveTab]   = useState(TAB.TODAY);
  const [customers, setCustomers]   = useState([]);
  const [loading, setLoading]       = useState(false);
  const [search, setSearch]         = useState('');
  const [formVisible, setFormVisible] = useState(false);
  const [editTarget, setEditTarget] = useState(null);

  const personId   = useAuthStore((s) => s.personId);
  const personName = useAuthStore((s) => s.personName);
  const tasks      = useCrmStore(selectTasks);

  // ── 고객 목록 로드 ────────────────────────────────────────────────────────
  const loadCustomers = useCallback(async (query = '') => {
    if (!personId) return;
    setLoading(true);
    try {
      const list = await fetchCustomers(personId, { query: query || undefined });
      setCustomers(list);
    } catch (e) {
      console.warn('[DashboardLite] fetchCustomers 오류:', e?.message);
    } finally {
      setLoading(false);
    }
  }, [personId]);

  useEffect(() => { loadCustomers(); }, [loadCustomers]);

  // ── 검색 ─────────────────────────────────────────────────────────────────
  const handleSearch = useCallback((v) => {
    setSearch(v);
    loadCustomers(v);
  }, [loadCustomers]);

  // ── 고객 저장 (양방향 공통 함수 사용) ──────────────────────────────────────
  const handleSave = useCallback(async (data) => {
    await customerInputForm(data, personId);
    setFormVisible(false);
    setEditTarget(null);
    loadCustomers(search);
  }, [personId, search, loadCustomers]);

  // ── 즐겨찾기 토글 ─────────────────────────────────────────────────────────
  const handleFavorite = useCallback(async (c) => {
    try {
      await toggleFavorite(c.person_id, c.is_favorite);
      loadCustomers(search);
    } catch (e) {
      console.warn('[DashboardLite] toggleFavorite 오류:', e?.message);
    }
  }, [search, loadCustomers]);

  // ── 렌더: 오늘의 업무 탭 ──────────────────────────────────────────────────
  const renderTodayTab = () => (
    <View style={{ flex: 1, paddingTop: 8 }}>
      <View style={s.sectionHeader}>
        <Text style={s.sectionTitle}>📋 오늘의 할 일</Text>
        <Text style={s.sectionSub}>{tasks.filter((t) => t.isDone).length}/{tasks.length} 완료</Text>
      </View>
      <FlatList
        data={tasks}
        keyExtractor={(t) => String(t.id)}
        renderItem={({ item }) => <TaskCard taskId={item.id} />}
        ListEmptyComponent={<Text style={s.empty}>오늘 할 일이 없습니다 😊</Text>}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );

  // ── 렌더: 고객 목록 탭 (공통 컴포넌트 사용) ──────────────────────────────
  const renderCustomersTab = () => (
    <View style={{ flex: 1 }}>
      {/* [GP §1] 공통 헤더 컴포넌트 */}
      <CustomerListHeader
        totalCount={customers.length}
        search={search}
        onSearch={handleSearch}
        onAdd={() => { setEditTarget(null); setFormVisible(true); }}
      />
      {loading ? (
        <ActivityIndicator style={{ marginTop: 40 }} color="#1d4ed8" />
      ) : (
        <FlatList
          data={customers}
          keyExtractor={(c) => c.person_id}
          /* [GP §1] 공통 카드 컴포넌트 */
          renderItem={({ item: c }) => (
            <CustomerCard
              customer={c}
              onPress={() => { setEditTarget(c); setFormVisible(true); }}
              showTier
            />
          )}
          ListEmptyComponent={<Text style={s.empty}>등록된 고객이 없습니다.</Text>}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 20 }}
        />
      )}
    </View>
  );

  // ── 렌더: 딥링크 발사대 탭 ────────────────────────────────────────────────
  const renderDeepLinkTab = () => (
    <View style={s.deepLinkTab}>
      <Text style={s.sectionTitle}>🚀 Goldkey AI 연결</Text>
      <Text style={s.deepLinkNote}>
        복잡한 분석은 모 앱(Goldkey AI)에서 처리합니다.{'\n'}
        아래 버튼을 누르면 해당 기능으로 바로 이동합니다.
      </Text>

      <View style={s.deepLinkList}>
        {/* [GP §3] 딥링크 발사대 버튼들 */}
        <DeepLinkButton
          action="kb7_analysis"
          label="KB 7대 보장 분석"
          icon="🛡️"
          style={s.dlBtn}
        />
        <DeepLinkButton
          action="insurance_scan"
          label="내보험다보여 조회"
          icon="📋"
          style={s.dlBtn}
        />
        <DeepLinkButton
          action="ai_report"
          label="AI 상담 리포트 생성"
          icon="✨"
          style={s.dlBtn}
        />
        <DeepLinkButton
          action="hoffmann_calc"
          label="호프만 보장공백 계산"
          icon="📐"
          style={s.dlBtn}
        />
        <DeepLinkButton
          action="customer_profile"
          params={{ agent_id: personId || '' }}
          label="고객 상세 프로필 열기"
          icon="👤"
          style={s.dlBtn}
        />
      </View>

      {/* 시스템 안내 */}
      <View style={s.systemNote}>
        <Text style={s.systemNoteText}>
          본 앱은 Goldkey AI Masters 2026의{'\n'}
          서브 애플리케이션(Shadow App)입니다.{'\n'}
          모든 AI 분석 및 정밀 상담 로직은{'\n'}
          모 앱의 보안 프로토콜을 따릅니다.
        </Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={s.safe}>
      {/* 헤더 */}
      <View style={s.header}>
        <Text style={s.headerTitle}>🔑 골드키 CRM</Text>
        <Text style={s.headerSub}>{personName || '설계사'} · Shadow App</Text>
      </View>

      {/* 탭 네비 */}
      <View style={s.tabRow}>
        {[
          { key: TAB.TODAY,     label: '📋 업무' },
          { key: TAB.CUSTOMERS, label: '👥 고객' },
          { key: TAB.DEEPLINK,  label: '🚀 AI 연결' },
        ].map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            style={[s.tab, activeTab === key && s.tabActive]}
            onPress={() => setActiveTab(key)}
          >
            <Text style={[s.tabText, activeTab === key && s.tabTextActive]}>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 컨텐츠 */}
      <View style={s.content}>
        {activeTab === TAB.TODAY     && renderTodayTab()}
        {activeTab === TAB.CUSTOMERS && renderCustomersTab()}
        {activeTab === TAB.DEEPLINK  && renderDeepLinkTab()}
      </View>

      {/* [GP §2] 고객 입력/수정 폼 모달 (공통 CustomerForm 사용) */}
      <Modal
        visible={formVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => { setFormVisible(false); setEditTarget(null); }}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: '#f8fafc' }}>
          <CustomerForm
            initial={editTarget}
            agentId={personId || ''}
            onSave={handleSave}
            onCancel={() => { setFormVisible(false); setEditTarget(null); }}
          />
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

// ── 스타일 (최소화) ───────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe:        { flex: 1, backgroundColor: '#f8fafc' },

  header: {
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 20, paddingTop: 14, paddingBottom: 14,
  },
  headerTitle: { fontSize: 20, fontWeight: '900', color: '#ffd700' },
  headerSub:   { fontSize: 12, color: '#93c5fd', marginTop: 2 },

  tabRow: {
    flexDirection: 'row', backgroundColor: '#fff',
    borderBottomWidth: 1, borderBottomColor: '#e2e8f0',
  },
  tab: {
    flex: 1, paddingVertical: 14, alignItems: 'center',
    borderBottomWidth: 3, borderBottomColor: 'transparent',
  },
  tabActive:     { borderBottomColor: '#1d4ed8' },
  tabText:       { fontSize: 13, fontWeight: '600', color: '#94a3b8' },
  tabTextActive: { color: '#1d4ed8', fontWeight: '900' },

  content: { flex: 1, paddingHorizontal: 16, paddingTop: 12 },

  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  sectionTitle:  { fontSize: 16, fontWeight: '900', color: '#1e293b' },
  sectionSub:    { fontSize: 12, color: '#6b7280' },
  empty:         { textAlign: 'center', color: '#94a3b8', marginTop: 40, fontSize: 14 },

  deepLinkTab:  { flex: 1, paddingTop: 8 },
  deepLinkNote: { fontSize: 13, color: '#6b7280', lineHeight: 20, marginBottom: 20 },
  deepLinkList: { gap: 10 },
  dlBtn:        { marginBottom: 0 },

  systemNote: {
    marginTop: 28, padding: 14,
    backgroundColor: '#eff6ff',
    borderWidth: 1, borderStyle: 'dashed', borderColor: '#000',
    borderRadius: 10,
  },
  systemNoteText: { fontSize: 11, color: '#374151', lineHeight: 18, textAlign: 'center' },
});
