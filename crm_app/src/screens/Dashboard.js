/**
 * Dashboard — 골드키 CRM 메인 대시보드 (v2)
 *
 * 폰:     단일 컬럼, 탭 전환
 * 태블릿: 2컬럼 (좌: 보장분석+Todo / 우: AI 리포트 사이드바)
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useCustomerStore, selCustomerList, selIsAgent } from '../store/customerStore';
import AvatarImage from '../components/AvatarImage';
import ExportPanel from '../components/ExportPanel';
import usePaginatedList from '../hooks/usePaginatedList';
import {
  Alert,
  Animated,
  FlatList,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  useCrmStore,
  selectTasks,
  selectSilson,
  selectCoverage,
  selectCustomer,
  selectAiReport,
  FEATURE_FLAGS,
} from '../store/crmStore';
import TaskCard from '../components/TaskCard';
import SilsonBadge from '../components/SilsonBadge';
import { useDeviceLayout } from '../utils/deviceCheck';
import { runWatchdog } from '../utils/SystemWatchdog';
import TermsScreen from './TermsScreen';
import { _openGkCustomerScreen } from '../../App';

const TAB = { TODO: 'todo', CUSTOMER: 'customer', CUSTOMERS: 'customers', EXPORT: 'export', GK: 'gk' };
const CUSTOMER_TAB = { BASIC: 'basic', COVERAGE: 'coverage' };

// ── Toast 컴포넌트 (다크 네이비, 100% 달성용) ─────────────────────────────────
const SuccessToast = ({ visible }) => {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(opacity,     { toValue: 1, duration: 300, useNativeDriver: true }),
        Animated.timing(translateY,  { toValue: 0, duration: 300, useNativeDriver: true }),
      ]).start(() => {
        setTimeout(() => {
          Animated.parallel([
            Animated.timing(opacity,    { toValue: 0, duration: 400, useNativeDriver: true }),
            Animated.timing(translateY, { toValue: 30, duration: 400, useNativeDriver: true }),
          ]).start();
        }, 2200);
      });
    }
  }, [visible]);

  return (
    <Animated.View style={[styles.toast, { opacity, transform: [{ translateY }] }]}>
      <Text style={styles.toastText}>가벼운 TO-DO 성공을 축하합니다 🎉</Text>
    </Animated.View>
  );
};

// ── Progress Bar ──────────────────────────────────────────────────────────────
const ProgressBar = ({ percent }) => {
  const barWidth = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.spring(barWidth, { toValue: percent, useNativeDriver: false, friction: 7 }).start();
  }, [percent]);
  const color = percent === 100 ? '#22c55e' : percent >= 60 ? '#f59e0b' : '#3b82f6';
  return (
    <View style={styles.progressWrap}>
      <View style={styles.progressTrack}>
        <Animated.View style={[styles.progressFill, {
          width: barWidth.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] }),
          backgroundColor: color,
        }]} />
      </View>
      <Text style={[styles.progressLabel, { color }]}>{percent}%</Text>
    </View>
  );
};

// ── AI 리포트 패널 (태블릿 사이드바 / 폰 인라인 공통) ────────────────────────
const AiReportPanel = ({ isSidebar }) => {
  const { report, loading, generate, share, clear } = useCrmStore(selectAiReport);
  if (!FEATURE_FLAGS.ENABLE_AI_REPORT) return null;
  return (
    <View style={[styles.reportPanel, isSidebar && styles.reportPanelSidebar]}>
      <Text style={styles.reportTitle}>✨ AI 상담 리포트</Text>
      {report ? (
        <>
          <ScrollView style={styles.reportScroll} showsVerticalScrollIndicator={false}>
            <Text style={styles.reportText}>{report}</Text>
          </ScrollView>
          <View style={styles.reportBtnRow}>
            <TouchableOpacity style={styles.shareBtn} onPress={share}>
              <Text style={styles.shareBtnText}>📤 카카오/문자 공유</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.clearBtn} onPress={clear}>
              <Text style={styles.clearBtnText}>✕</Text>
            </TouchableOpacity>
          </View>
        </>
      ) : (
        <TouchableOpacity
          style={[styles.generateBtn, loading && styles.generateBtnDisabled]}
          onPress={generate}
          disabled={loading}
        >
          <Text style={styles.generateBtnText}>
            {loading ? '생성 중...' : '✨ AI 상담 리포트 생성'}
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

// ── 메인 대시보드 ─────────────────────────────────────────────────────────────
const Dashboard = () => {
  const [activeTab, setActiveTab]             = useState(TAB.TODO);
  const [activeCustomerTab, setActiveCustTab] = useState(CUSTOMER_TAB.BASIC);
  const [showToast, setShowToast]             = useState(false);
  const [termsOpen, setTermsOpen]             = useState(false);
  const prevProgress                          = useRef(0);

  const { isTablet, isLegacyDevice, contentPadding, sidebarWidth, mainWidth } = useDeviceLayout();

  // ── SSOT 고객 목록 + 프로필 이동 ────────────────────────────────────────
  const customerList    = useCustomerStore(selCustomerList);
  const isAgent         = useCustomerStore(selIsAgent);
  const userRole        = useCustomerStore((s) => s.userRole);
  const openProfile  = useCustomerStore((s) => s.openProfile);
  const openScheduleModal = useCustomerStore((s) => s.openScheduleModal);

  // Zustand 슬라이스
  const tasks                                         = useCrmStore(selectTasks);
  const { date: silsonDate, gen: silsonGen, calc }    = useCrmStore(selectSilson);
  const { data: customer, update: updateCustomer }    = useCrmStore(selectCustomer);
  const { data: coverage, update: updateCoverage }    = useCrmStore(selectCoverage);
  const recoverState                                  = useCrmStore((s) => s.recoverState);

  // ── Watchdog 초기화 ──────────────────────────────────────────────────────
  useEffect(() => {
    recoverState();
  }, []);

  // ── 달성률 계산 + 100% Toast / Alert ─────────────────────────────────────
  const progress = tasks.length === 0
    ? 0
    : Math.round((tasks.filter((t) => t.isDone).length / tasks.length) * 100);

  useEffect(() => {
    if (progress === 100 && prevProgress.current < 100) {
      if (isLegacyDevice) {
        Alert.alert('🎉 축하합니다!', '오늘의 TO-DO를 모두 완료했습니다!');
      } else {
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
      }
    }
    prevProgress.current = progress;
  }, [progress]);

  // ── 고객 목록 페이징 (20개씩, usePaginatedList) ────────────────────────
  const [custSearch, setCustSearch] = useState('');
  const custPager = usePaginatedList(customerList, {
    pageSize: 20,
    filterFn: custSearch
      ? (c) => c.name?.includes(custSearch) || c.phone?.includes(custSearch)
      : null,
    key: custSearch,
  });

  // ── 렌더: 고객 카드 (FlatList renderItem) ───────────────────────────────
  const renderCustItem = useCallback(({ item: c }) => (
    <TouchableOpacity
      style={styles.custRow}
      onPress={() => openProfile(c.id)}
      activeOpacity={0.75}
    >
      <AvatarImage
        mode="initial"
        size={44}
        initial={c.name?.charAt(0) || '?'}
        registered={c.registered}
      />
      <View style={{ flex: 1 }}>
        <Text style={styles.custName}>{c.name}</Text>
        <Text style={styles.custSub} numberOfLines={1}>
          {[c.job, c.phone].filter(Boolean).join('  ·  ') || '정보 없음'}
        </Text>
        {(c.tags || []).length > 0 && (
          <View style={styles.custTagRow}>
            {c.tags.slice(0, 2).map((t, i) => (
              <View key={i} style={styles.custTag}>
                <Text style={styles.custTagText}>{t}</Text>
              </View>
            ))}
            {c.tags.length > 2 && (
              <Text style={styles.custTagMore}>+{c.tags.length - 2}</Text>
            )}
          </View>
        )}
      </View>
      <View style={styles.custActions}>
        <TouchableOpacity
          style={styles.custSchedBtn}
          onPress={() => openScheduleModal(c.id)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Text style={styles.custSchedBtnText}>📅</Text>
        </TouchableOpacity>
        <Text style={styles.custChevron}>›</Text>
      </View>
    </TouchableOpacity>
  ), [openProfile, openScheduleModal]);

  // ── 렌더: 고객 목록 탭 ──────────────────────────────────────────────────
  const renderCustomersTab = () => (
    <FlatList
      data={custPager.items}
      keyExtractor={(c) => c.id}
      renderItem={renderCustItem}
      onEndReached={custPager.loadMore}
      onEndReachedThreshold={0.3}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{ paddingBottom: 16 }}
      ListHeaderComponent={
        <>
          <View style={styles.custListHeader}>
            <Text style={styles.custListTitle}>� 담당 고객 목록</Text>
            <Text style={styles.custListSub}>
              {custPager.totalCount}명{custSearch ? ' (검색 중)' : ' 등록'}
            </Text>
          </View>
          <View style={styles.custSearchRow}>
            <TextInput
              style={styles.custSearchInput}
              value={custSearch}
              onChangeText={(v) => { setCustSearch(v); custPager.reset(); }}
              placeholder="이름 또는 연락처 검색..."
              placeholderTextColor="#94a3b8"
              clearButtonMode="while-editing"
            />
          </View>
          {custPager.isInitializing && (
            <Text style={styles.emptyText}>불러오는 중...</Text>
          )}
          {!custPager.isInitializing && custPager.totalCount === 0 && (
            <Text style={styles.emptyText}>
              {custSearch ? '검색 결과가 없습니다.' : '등록된 고객이 없습니다.'}
            </Text>
          )}
        </>
      }
      ListFooterComponent={
        <>
          {custPager.hasMore && (
            <TouchableOpacity
              style={styles.loadMoreBtn}
              onPress={custPager.loadMore}
              disabled={custPager.isLoadingMore}
            >
              <Text style={styles.loadMoreText}>
                {custPager.isLoadingMore
                  ? '불러오는 중...'
                  : `더 보기 (${custPager.totalCount - custPager.items.length}명 남음)`}
              </Text>
            </TouchableOpacity>
          )}
          <View style={{ height: 16 }} />
          <ExportPanel userRole={userRole} />
          <TouchableOpacity
            onPress={() => setTermsOpen(true)}
            style={styles.termsLink}
          >
            <Text style={styles.termsLinkText}>이용약관 및 개인정보처리방침</Text>
          </TouchableOpacity>
        </>
      }
    />
  );

  // ── 렌더: Task 탭 ────────────────────────────────────────────────────────
  const renderTodoTab = () => (
    <View style={{ flex: 1 }}>
      <View style={styles.progressSection}>
        <Text style={styles.progressTitle}>오늘의 달성률</Text>
        <ProgressBar percent={progress} />
        <Text style={styles.progressSub}>
          {tasks.filter((t) => t.isDone).length} / {tasks.length} 건 완료
        </Text>
      </View>
      <FlatList
        data={tasks}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <TaskCard taskId={item.id} />}
        contentContainerStyle={styles.taskList}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        ListEmptyComponent={
          <Text style={styles.emptyText}>오늘 할 일이 없습니다 😊</Text>
        }
      />
      {/* AI 리포트 버튼 (폰: 보장분석 탭 아래 인라인) */}
      {!isTablet && <AiReportPanel isSidebar={false} />}
    </View>
  );

  // ── 렌더: 고객 기본 정보 ─────────────────────────────────────────────────
  const renderBasicInfo = () => (
    <View style={styles.formSection}>
      <InputField label="고객 성함" value={customer.name}
        onChangeText={(v) => updateCustomer({ name: v })} placeholder="홍길동" />
      <InputField label="직업" value={customer.job}
        onChangeText={(v) => updateCustomer({ job: v })} placeholder="회사원" />
      <InputField label="연락처" value={customer.phone}
        onChangeText={(v) => updateCustomer({ phone: v })} placeholder="010-0000-0000"
        keyboardType="phone-pad" />
      <Text style={styles.inputLabel}>성별</Text>
      <View style={styles.genderRow}>
        {['남성', '여성'].map((g) => (
          <TouchableOpacity key={g}
            onPress={() => updateCustomer({ gender: g })}
            style={[styles.genderBtn, customer.gender === g && styles.genderBtnActive]}
          >
            <Text style={[styles.genderBtnText, customer.gender === g && styles.genderBtnTextActive]}>
              {g === '남성' ? '👨 남성' : '👩 여성'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  // ── 렌더: 보장 공백 탭 (호프만 + 실손) ──────────────────────────────────
  const renderCoverageTab = () => (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.formSection}>
        {/* 실손 세대 */}
        <Text style={styles.inputLabel}>실손보험 가입 연월 <Text style={styles.hint}>(YYYY-MM)</Text></Text>
        <View style={styles.silsonRow}>
          <TextInput
            style={[styles.input, { flex: 1 }]}
            placeholder="예: 2018-05"
            value={silsonDate}
            onChangeText={calc}
            maxLength={7}
            keyboardType="numbers-and-punctuation"
          />
          {!!silsonGen && <SilsonBadge generation={silsonGen} />}
        </View>
        {!!silsonGen && (
          <View style={styles.silsonInfo}>
            <Text style={styles.silsonInfoText}>
              {silsonGen === '1세대 구실손' && '⚠️ 면책 조항 없음 — 갱신 시 보험료 급등 주의.'}
              {silsonGen === '2세대 표준화실손' && '📋 표준화 약관 적용 — 항목별 보장 한도 존재.'}
              {silsonGen === '3세대 착한실손' && '💡 비급여 특약 분리 — 자기부담금 상향.'}
              {silsonGen === '4세대 실손' && '🔄 비급여 실적 연동 — 비급여 지출 많으면 갱신료 급상승.'}
            </Text>
          </View>
        )}

        {/* 호프만 계산 */}
        <Text style={[styles.sectionLabel, { marginTop: 20 }]}>📐 호프만 보장 공백 계산</Text>
        <InputField label="연간 소득(원)" value={String(coverage.annualIncome || '')}
          onChangeText={(v) => updateCoverage({ annualIncome: Number(v.replace(/[^0-9]/g, '')) })}
          placeholder="40000000" keyboardType="numeric" />
        <InputField label="보장 공백 비율 (%)" value={String(coverage.coverageGapPercent || '')}
          onChangeText={(v) => updateCoverage({ coverageGapPercent: Number(v.replace(/[^0-9]/g, '')) })}
          placeholder="30" keyboardType="numeric" />
        <InputField label="잔여 경제활동 연수" value={String(coverage.yearsRemaining || '')}
          onChangeText={(v) => updateCoverage({ yearsRemaining: Number(v.replace(/[^0-9]/g, '')) })}
          placeholder="30" keyboardType="numeric" />

        {coverage.hoffmannGap > 0 && (
          <View style={styles.hoffmannResult}>
            <Text style={styles.hoffmannLabel}>호프만 보장 공백 현가</Text>
            <Text style={styles.hoffmannValue}>
              {coverage.hoffmannGap.toLocaleString('ko-KR')} 만원
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );

  // ── 렌더: 고객 탭 전체 ──────────────────────────────────────────────────
  const renderCustomerTab = () => (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1 }}
      keyboardVerticalOffset={90}
    >
      <View style={styles.subTabRow}>
        {[
          { key: CUSTOMER_TAB.BASIC,    label: '👤 기본 정보' },
          { key: CUSTOMER_TAB.COVERAGE, label: '📐 보장 분석' },
        ].map(({ key, label }) => (
          <TouchableOpacity key={key}
            onPress={() => setActiveCustTab(key)}
            style={[styles.subTab, activeCustomerTab === key && styles.subTabActive]}
          >
            <Text style={[styles.subTabText, activeCustomerTab === key && styles.subTabTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      {activeCustomerTab === CUSTOMER_TAB.BASIC ? renderBasicInfo() : renderCoverageTab()}
    </KeyboardAvoidingView>
  );

  // ── 태블릿 2컬럼 레이아웃 ────────────────────────────────────────────────
  if (isTablet) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <View style={styles.headerRow}>
            <View style={styles.headerBrand}>
              <AvatarImage mode="logo" size={36} />
              <Text style={styles.headerTitle}>골드키 CRM</Text>
            </View>
            {/* 설계사 전용: 백업 버튼 compact */}
            {isAgent && (
              <ExportPanel userRole={userRole} compact />
            )}
          </View>
          <Text style={styles.headerSub}>AI 보험 영업 대시보드 · 태블릿 모드</Text>
        </View>
        <View style={styles.tabletBody}>
          {/* 좌측: 탭 + 콘텐츠 */}
          <View style={[styles.tabletMain, { width: mainWidth, paddingHorizontal: contentPadding }]}>
            <View style={styles.tabRow}>
              {[
                { key: TAB.TODO,      label: '📋 업무' },
                { key: TAB.CUSTOMERS, label: '👥 고객' },
                { key: TAB.CUSTOMER,  label: '📐 분석' },
                { key: TAB.GK,        label: '🗂️ 3단계' },
              ].map(({ key, label }) => (
                <TouchableOpacity key={key}
                  onPress={() => {
                    if (key === TAB.GK) { _openGkCustomerScreen && _openGkCustomerScreen(); return; }
                    setActiveTab(key); Keyboard.dismiss();
                  }}
                  style={[styles.tab, activeTab === key && styles.tabActive]}
                >
                  <Text style={[styles.tabText, activeTab === key && styles.tabTextActive]}>{label}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <View style={{ flex: 1, paddingTop: 14 }}>
              {activeTab === TAB.TODO      && renderTodoTab()}
              {activeTab === TAB.CUSTOMERS && renderCustomersTab()}
              {activeTab === TAB.CUSTOMER  && renderCustomerTab()}
            </View>
          </View>
          {/* 우측 사이드바: AI 리포트 */}
          <View style={[styles.tabletSidebar, { width: sidebarWidth }]}>
            <AiReportPanel isSidebar />
          </View>
        </View>
        <SuccessToast visible={showToast} />
      </SafeAreaView>
    );
  }

  // ── 폰 단일 컬럼 레이아웃 ────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <View style={styles.headerBrand}>
            <AvatarImage mode="logo" size={34} />
            <Text style={styles.headerTitle}>골드키 CRM</Text>
          </View>
          {/* 설계사 전용: 백업 버튼 compact */}
          {isAgent && (
            <ExportPanel userRole={userRole} compact />
          )}
        </View>
        <Text style={styles.headerSub}>AI 보험 영업 대시보드</Text>
      </View>
      <View style={styles.tabRow}>
        {[
          { key: TAB.TODO,      label: '📋 업무' },
          { key: TAB.CUSTOMERS, label: '👥 고객' },
          { key: TAB.CUSTOMER,  label: '📐 분석' },
          { key: TAB.GK,        label: '🗂️ 3단계' },
          ...(isAgent ? [{ key: TAB.EXPORT, label: '☁️ 백업' }] : []),
        ].map(({ key, label }) => (
          <TouchableOpacity key={key}
            onPress={() => {
              if (key === TAB.GK) { _openGkCustomerScreen && _openGkCustomerScreen(); return; }
              setActiveTab(key); Keyboard.dismiss();
            }}
            style={[styles.tab, activeTab === key && styles.tabActive]}
          >
            <Text style={[styles.tabText, activeTab === key && styles.tabTextActive]}>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={[styles.content, { paddingHorizontal: contentPadding }]}>
        {activeTab === TAB.TODO      && renderTodoTab()}
        {activeTab === TAB.CUSTOMERS && renderCustomersTab()}
        {activeTab === TAB.CUSTOMER  && renderCustomerTab()}
        {activeTab === TAB.EXPORT    && isAgent && (
          <ScrollView showsVerticalScrollIndicator={false}>
            <ExportPanel userRole={userRole} />
          </ScrollView>
        )}
      </View>
      <SuccessToast visible={showToast} />
      {termsOpen && (
        <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 300 }}>
          <TermsScreen onClose={() => setTermsOpen(false)} />
        </View>
      )}
    </SafeAreaView>
  );
};

// ── InputField 공용 컴포넌트 ──────────────────────────────────────────────────
const InputField = ({ label, value, onChangeText, placeholder, keyboardType, multiline }) => (
  <View style={styles.fieldWrap}>
    <Text style={styles.inputLabel}>{label}</Text>
    <TextInput
      style={[styles.input, multiline && styles.inputMulti]}
      value={String(value ?? '')}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor="#94a3b8"
      keyboardType={keyboardType || 'default'}
      multiline={!!multiline}
      numberOfLines={multiline ? 3 : 1}
    />
  </View>
);

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safeArea:    { flex: 1, backgroundColor: '#f8fafc' },
  header: {
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 20, paddingTop: 14, paddingBottom: 14,
  },
  headerRow:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 },
  headerBrand: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerTitle: { fontSize: 20, fontWeight: '900', color: '#ffd700', letterSpacing: 0.5 },
  headerSub:   { fontSize: 12, color: '#93c5fd', marginTop: 2 },

  // 탭 네비
  tabRow: {
    flexDirection: 'row', backgroundColor: '#fff',
    borderBottomWidth: 1, borderBottomColor: '#e2e8f0',
  },
  tab: {
    flex: 1, paddingVertical: 14, alignItems: 'center',
    borderBottomWidth: 3, borderBottomColor: 'transparent',
  },
  tabActive:     { borderBottomColor: '#2563eb' },
  tabText:       { fontSize: 14, fontWeight: '600', color: '#94a3b8' },
  tabTextActive: { color: '#2563eb', fontWeight: '800' },

  content: { flex: 1, paddingTop: 14 },

  // 태블릿 2컬럼
  tabletBody:    { flex: 1, flexDirection: 'row' },
  tabletMain:    { flex: 1 },
  tabletSidebar: {
    backgroundColor: '#f1f5f9',
    borderLeftWidth: 1, borderLeftColor: '#e2e8f0',
    paddingHorizontal: 16, paddingTop: 16,
  },

  // Progress
  progressSection: { marginBottom: 16 },
  progressTitle:   { fontSize: 15, fontWeight: '800', color: '#1e293b', marginBottom: 8 },
  progressSub:     { fontSize: 12, color: '#64748b', marginTop: 4 },
  progressWrap:    { flexDirection: 'row', alignItems: 'center', gap: 10 },
  progressTrack: {
    flex: 1, height: 10, backgroundColor: '#e2e8f0',
    borderRadius: 5, overflow: 'hidden',
  },
  progressFill:  { height: '100%', borderRadius: 5 },
  progressLabel: { fontSize: 14, fontWeight: '800', minWidth: 38, textAlign: 'right' },

  taskList:  { paddingBottom: 20 },
  emptyText: { textAlign: 'center', color: '#94a3b8', marginTop: 40, fontSize: 14 },

  // Sub-Tab
  subTabRow: {
    flexDirection: 'row', backgroundColor: '#f1f5f9',
    borderRadius: 10, padding: 4, marginBottom: 16,
  },
  subTab:           { flex: 1, paddingVertical: 9, alignItems: 'center', borderRadius: 8 },
  subTabActive:     { backgroundColor: '#fff', shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 4, elevation: 2 },
  subTabText:       { fontSize: 13, fontWeight: '600', color: '#64748b' },
  subTabTextActive: { color: '#1e293b', fontWeight: '800' },

  // 폼
  formSection: { paddingBottom: 40 },
  fieldWrap:   { marginBottom: 14 },
  inputLabel:  { fontSize: 13, fontWeight: '700', color: '#374151', marginBottom: 5 },
  hint:        { fontSize: 11, color: '#94a3b8', fontWeight: '400' },
  sectionLabel:{ fontSize: 14, fontWeight: '800', color: '#1e3a5f', marginBottom: 10 },
  input: {
    backgroundColor: '#fff', borderWidth: 1.5, borderColor: '#e2e8f0',
    borderRadius: 10, paddingHorizontal: 13, paddingVertical: 11,
    fontSize: 14, color: '#1e293b',
  },
  inputMulti: { height: 80, textAlignVertical: 'top' },

  // 성별
  genderRow: { flexDirection: 'row', gap: 10 },
  genderBtn: {
    flex: 1, paddingVertical: 11, alignItems: 'center',
    borderRadius: 10, borderWidth: 1.5, borderColor: '#e2e8f0', backgroundColor: '#fff',
  },
  genderBtnActive:     { backgroundColor: '#eff6ff', borderColor: '#2563eb' },
  genderBtnText:       { fontSize: 14, fontWeight: '600', color: '#64748b' },
  genderBtnTextActive: { color: '#2563eb', fontWeight: '800' },

  // 실손
  silsonRow:      { flexDirection: 'row', alignItems: 'center', gap: 10 },
  silsonInfo: {
    backgroundColor: '#f0fdf4', borderRadius: 8, padding: 10,
    marginTop: 8, borderLeftWidth: 3, borderLeftColor: '#22c55e',
  },
  silsonInfoText: { fontSize: 12, color: '#15803d', lineHeight: 18 },

  // 호프만 결과
  hoffmannResult: {
    backgroundColor: '#1e3a5f', borderRadius: 12,
    padding: 16, marginTop: 16, alignItems: 'center',
  },
  hoffmannLabel: { fontSize: 12, color: '#93c5fd', marginBottom: 4 },
  hoffmannValue: { fontSize: 24, fontWeight: '900', color: '#ffd700' },

  // AI 리포트 패널
  reportPanel: {
    backgroundColor: '#fff', borderRadius: 12,
    padding: 14, marginTop: 12,
    borderWidth: 1.5, borderColor: '#e2e8f0',
  },
  reportPanelSidebar: { marginTop: 0, flex: 1 },
  reportTitle: { fontSize: 14, fontWeight: '800', color: '#1e3a5f', marginBottom: 10 },
  reportScroll:{ maxHeight: 340, marginBottom: 10 },
  reportText:  { fontSize: 13, color: '#374151', lineHeight: 20 },
  reportBtnRow:{ flexDirection: 'row', gap: 8 },
  shareBtn: {
    flex: 1, backgroundColor: '#2563eb', borderRadius: 8,
    paddingVertical: 10, alignItems: 'center',
  },
  shareBtnText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  clearBtn: {
    backgroundColor: '#f1f5f9', borderRadius: 8,
    paddingVertical: 10, paddingHorizontal: 14, alignItems: 'center',
  },
  clearBtnText: { color: '#64748b', fontWeight: '700', fontSize: 13 },
  generateBtn: {
    backgroundColor: '#1e3a5f', borderRadius: 10,
    paddingVertical: 13, alignItems: 'center', marginTop: 4,
  },
  generateBtnDisabled: { backgroundColor: '#94a3b8' },
  generateBtnText: { color: '#ffd700', fontWeight: '800', fontSize: 14 },

  // Toast
  // ── 고객 목록 탭
  custListHeader: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 },
  custListTitle:  { fontSize: 15, fontWeight: '800', color: '#1e293b' },
  custListSub:    { fontSize: 12, color: '#94a3b8' },
  custSearchRow:  { marginBottom: 10 },
  custSearchInput: {
    backgroundColor: '#fff', borderWidth: 1.5, borderColor: '#e2e8f0',
    borderRadius: 10, paddingHorizontal: 13, paddingVertical: 10,
    fontSize: 14, color: '#1e293b',
  },
  loadMoreBtn: {
    alignItems: 'center', paddingVertical: 13,
    marginHorizontal: 4, marginBottom: 8,
    borderRadius: 10, backgroundColor: '#f1f5f9',
    borderWidth: 1, borderColor: '#e2e8f0',
  },
  loadMoreText: { fontSize: 13, fontWeight: '700', color: '#2563eb' },
  custRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: '#ffffff', borderRadius: 12,
    paddingVertical: 13, paddingHorizontal: 14,
    marginBottom: 8, borderWidth: 1, borderColor: '#e2e8f0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
  },
  custAvatar: {
    width: 44, height: 44, borderRadius: 22,
    alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  custAvatarReg:   { backgroundColor: '#1e3a5f' },
  custAvatarUnreg: { backgroundColor: '#94a3b8' },
  custAvatarText:  { fontSize: 18, fontWeight: '900', color: '#ffffff' },
  custName:    { fontSize: 15, fontWeight: '800', color: '#1e293b', marginBottom: 2 },
  custSub:     { fontSize: 12, color: '#64748b' },
  custTagRow:  { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 5 },
  custTag: {
    paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10,
    backgroundColor: '#eff6ff', borderWidth: 1, borderColor: '#bfdbfe',
  },
  custTagText: { fontSize: 10, fontWeight: '700', color: '#1d4ed8' },
  custTagMore: { fontSize: 10, color: '#94a3b8', alignSelf: 'center' },
  custActions: { alignItems: 'center', gap: 6 },
  custSchedBtn: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: '#f1f5f9', alignItems: 'center', justifyContent: 'center',
  },
  custSchedBtnText: { fontSize: 15 },
  custChevron: { fontSize: 20, color: '#94a3b8', fontWeight: '300' },

  toast: {
    position: 'absolute', bottom: 36, alignSelf: 'center',
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 24, paddingVertical: 14,
    borderRadius: 14,
    shadowColor: '#000', shadowOpacity: 0.18, shadowRadius: 8, elevation: 8,
  },
  toastText: { color: '#ffd700', fontWeight: '800', fontSize: 15 },
  termsLink: {
    alignItems: 'center',
    paddingVertical: 16,
    marginTop: 4,
  },
  termsLinkText: {
    fontSize: 12,
    color: '#6b7280',
    textDecorationLine: 'underline',
  },
});

// TermsScreen 오버레이 래퍼 — Dashboard 외부에서 Modal처럼 렌더
Dashboard.TermsOverlay = ({ termsOpen, setTermsOpen }) => {
  if (!termsOpen) return null;
  return (
    <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 300 }}>
      <TermsScreen onClose={() => setTermsOpen(false)} />
    </View>
  );
};

export default Dashboard;
