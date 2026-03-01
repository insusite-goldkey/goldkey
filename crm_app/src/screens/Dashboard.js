/**
 * Dashboard — 골드키 CRM 메인 대시보드
 *
 * 구조:
 *  ┌─────────────────────────┐
 *  │   헤더 (달성률 Progress) │
 *  ├──────────┬──────────────┤
 *  │ 📋 업무  │ 👤 고객 등록 │  ← Tab UI (Progressive Disclosure)
 *  └──────────┴──────────────┘
 *
 * 탭 1 — 업무 대시보드: TaskCard 리스트 + 달성률 Progress Bar
 * 탭 2 — 고객 등록:    기본 정보 / 보험 정보 Sub-Tab + 실손 세대 자동 산출 + CalendarSync
 */

import React, { useCallback, useRef, useState } from 'react';
import {
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
import ConfettiCannon from 'react-native-confetti-cannon';
import { useCrmStore, selectTasks, selectSilson, selectCustomerBasic, selectCustomerIns } from '../store/crmStore';
import TaskCard from '../components/TaskCard';
import SilsonBadge from '../components/SilsonBadge';
import CalendarSync from '../components/CalendarSync';

// ── 탭 상수 ──────────────────────────────────────────────────────────────────
const TAB = { TODO: 'todo', CUSTOMER: 'customer' };
const CUSTOMER_TAB = { BASIC: 'basic', INSURANCE: 'insurance' };

// ── Progress Bar (달성률 시각화) ──────────────────────────────────────────────
const ProgressBar = ({ percent }) => {
  const barWidth = useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.spring(barWidth, {
      toValue: percent,
      useNativeDriver: false,
      friction: 7,
    }).start();
  }, [percent]);

  const color = percent === 100 ? '#22c55e' : percent >= 60 ? '#f59e0b' : '#3b82f6';

  return (
    <View style={styles.progressWrap}>
      <View style={styles.progressTrack}>
        <Animated.View
          style={[
            styles.progressFill,
            {
              width: barWidth.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] }),
              backgroundColor: color,
            },
          ]}
        />
      </View>
      <Text style={[styles.progressLabel, { color }]}>{percent}%</Text>
    </View>
  );
};

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
const Dashboard = () => {
  const [activeTab, setActiveTab]           = useState(TAB.TODO);
  const [activeCustomerTab, setActiveCustTab] = useState(CUSTOMER_TAB.BASIC);
  const confettiRef = useRef(null);

  // Zustand Selector — 필요한 슬라이스만 구독
  const tasks      = useCrmStore(selectTasks);
  const { date: silsonDate, gen: silsonGen, calc: calculateSilson } = useCrmStore(selectSilson);
  const { data: basicData,  update: updateBasic }   = useCrmStore(selectCustomerBasic);
  const { data: insData,    update: updateIns }     = useCrmStore(selectCustomerIns);

  // 달성률 계산
  const progress = tasks.length === 0
    ? 0
    : Math.round((tasks.filter((t) => t.isDone).length / tasks.length) * 100);

  // Confetti 트리거 (TaskCard에서 100% 달성 시 호출)
  const handleAllDone = useCallback(() => {
    confettiRef.current?.start();
  }, []);

  // ── 렌더: Task 탭 ──────────────────────────────────────────────────────────
  const renderTodoTab = () => (
    <View style={{ flex: 1 }}>
      {/* 달성률 Progress Bar */}
      <View style={styles.progressSection}>
        <Text style={styles.progressTitle}>
          오늘의 달성률 {progress === 100 ? '🎉' : ''}
        </Text>
        <ProgressBar percent={progress} />
        <Text style={styles.progressSub}>
          {tasks.filter((t) => t.isDone).length} / {tasks.length} 건 완료
        </Text>
      </View>

      {/* Task 카드 리스트 */}
      <FlatList
        data={tasks}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <TaskCard taskId={item.id} onAllDone={handleAllDone} />
        )}
        contentContainerStyle={styles.taskList}
        showsVerticalScrollIndicator={false}
        // 키보드가 올라와도 스크롤 유지
        keyboardShouldPersistTaps="handled"
        ListEmptyComponent={
          <Text style={styles.emptyText}>오늘 할 일이 없습니다. 여유롭게 쉬어가세요! 😊</Text>
        }
      />
    </View>
  );

  // ── 렌더: 고객 탭 — 기본 정보 ─────────────────────────────────────────────
  const renderBasicInfo = () => (
    <View style={styles.formSection}>
      <InputField label="고객 성함" value={basicData.name}
        onChangeText={(v) => updateBasic({ name: v })} placeholder="홍길동" />
      <InputField label="연락처" value={basicData.phone}
        onChangeText={(v) => updateBasic({ phone: v })} placeholder="010-0000-0000"
        keyboardType="phone-pad" />
      <InputField label="생년월일" value={basicData.birthDate}
        onChangeText={(v) => updateBasic({ birthDate: v })} placeholder="1985-03-15" />

      {/* 성별 선택 */}
      <Text style={styles.inputLabel}>성별</Text>
      <View style={styles.genderRow}>
        {['남성', '여성'].map((g) => (
          <TouchableOpacity
            key={g}
            onPress={() => updateBasic({ gender: g })}
            style={[
              styles.genderBtn,
              basicData.gender === g && styles.genderBtnActive,
            ]}
          >
            <Text style={[
              styles.genderBtnText,
              basicData.gender === g && styles.genderBtnTextActive,
            ]}>
              {g === '남성' ? '👨 남성' : '👩 여성'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  // ── 렌더: 고객 탭 — 보험 정보 ─────────────────────────────────────────────
  const renderInsuranceInfo = () => (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.formSection}>
        {/* 실손 세대 자동 산출 — Smart Logic */}
        <Text style={styles.inputLabel}>실손보험 가입 연월 <Text style={styles.hint}>(YYYY-MM)</Text></Text>
        <View style={styles.silsonRow}>
          <TextInput
            style={[styles.input, { flex: 1 }]}
            placeholder="예: 2018-05"
            value={silsonDate}
            onChangeText={calculateSilson}
            maxLength={7}
            keyboardType="numbers-and-punctuation"
          />
          {/* 세대 배지 — 입력 즉시 표시 */}
          {!!silsonGen && (
            <View style={styles.silsonBadgeWrap}>
              <SilsonBadge generation={silsonGen} />
            </View>
          )}
        </View>

        {/* 세대 안내 텍스트 */}
        {!!silsonGen && (
          <View style={styles.silsonInfo}>
            <Text style={styles.silsonInfoText}>
              {silsonGen === '1세대 구실손' && '⚠️ 면책 조항 없음 — 보장 가장 넓음. 갱신 시 보험료 급등 주의.'}
              {silsonGen === '2세대 표준화실손' && '📋 표준화 약관 적용 — 항목별 보장 한도 존재.'}
              {silsonGen === '3세대 착한실손' && '💡 비급여 특약 분리 — 도수치료 등 자기부담금 상향.'}
              {silsonGen === '4세대 실손' && '🔄 비급여 실적 연동 보험료 — 비급여 지출 많으면 갱신료 급상승.'}
            </Text>
          </View>
        )}

        <InputField label="자동차보험 만기일" value={insData.carInsuranceExpiry}
          onChangeText={(v) => updateIns({ carInsuranceExpiry: v })} placeholder="2026-04-15" />
        <InputField label="종신/건강 월 보험료(원)" value={insData.lifeInsurancePremium}
          onChangeText={(v) => updateIns({ lifeInsurancePremium: v })} placeholder="150000"
          keyboardType="numeric" />
        <InputField label="메모" value={insData.memo}
          onChangeText={(v) => updateIns({ memo: v })} placeholder="특이사항 입력"
          multiline />

        {/* 달력 동기화 */}
        <CalendarSync />
      </View>
    </ScrollView>
  );

  // ── 렌더: 고객 탭 전체 ────────────────────────────────────────────────────
  const renderCustomerTab = () => (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1 }}
      keyboardVerticalOffset={90}
    >
      {/* Sub-Tab: 기본 정보 / 보험 정보 */}
      <View style={styles.subTabRow}>
        {[
          { key: CUSTOMER_TAB.BASIC,      label: '기본 정보' },
          { key: CUSTOMER_TAB.INSURANCE,  label: '보험 정보' },
        ].map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            onPress={() => setActiveCustTab(key)}
            style={[styles.subTab, activeCustomerTab === key && styles.subTabActive]}
          >
            <Text style={[styles.subTabText, activeCustomerTab === key && styles.subTabTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {activeCustomerTab === CUSTOMER_TAB.BASIC
        ? renderBasicInfo()
        : renderInsuranceInfo()}
    </KeyboardAvoidingView>
  );

  // ── 메인 렌더 ─────────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.safeArea}>
      {/* 헤더 */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🔑 골드키 CRM</Text>
        <Text style={styles.headerSub}>AI 보험 영업 대시보드</Text>
      </View>

      {/* 메인 탭 네비게이션 */}
      <View style={styles.tabRow}>
        {[
          { key: TAB.TODO,     label: '📋 오늘의 업무' },
          { key: TAB.CUSTOMER, label: '👤 고객 등록' },
        ].map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            onPress={() => { setActiveTab(key); Keyboard.dismiss(); }}
            style={[styles.tab, activeTab === key && styles.tabActive]}
          >
            <Text style={[styles.tabText, activeTab === key && styles.tabTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 탭 콘텐츠 */}
      <View style={styles.content}>
        {activeTab === TAB.TODO ? renderTodoTab() : renderCustomerTab()}
      </View>

      {/* 🎉 Confetti — 100% 달성 시 발사. fadeOut으로 잔잔하게 마무리 */}
      <ConfettiCannon
        ref={confettiRef}
        count={120}
        origin={{ x: -10, y: 0 }}
        autoStart={false}
        fadeOut
        explosionSpeed={350}
        fallSpeed={3000}
        colors={['#ffd700', '#2563eb', '#22c55e', '#f59e0b', '#a855f7']}
      />
    </SafeAreaView>
  );
};

// ── 재사용 InputField 컴포넌트 ────────────────────────────────────────────────
const InputField = ({ label, hint, value, onChangeText, placeholder, keyboardType, multiline }) => (
  <View style={styles.fieldWrap}>
    <Text style={styles.inputLabel}>
      {label}{hint ? <Text style={styles.hint}> {hint}</Text> : null}
    </Text>
    <TextInput
      style={[styles.input, multiline && styles.inputMulti]}
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor="#94a3b8"
      keyboardType={keyboardType || 'default'}
      multiline={multiline}
      numberOfLines={multiline ? 3 : 1}
    />
  </View>
);

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f8fafc' },

  // 헤더
  header: {
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 20,
    paddingTop: 14,
    paddingBottom: 14,
  },
  headerTitle: { fontSize: 20, fontWeight: '900', color: '#ffd700', letterSpacing: 0.5 },
  headerSub:   { fontSize: 12, color: '#93c5fd', marginTop: 2 },

  // 메인 탭
  tabRow: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
  },
  tabActive:     { borderBottomColor: '#2563eb' },
  tabText:       { fontSize: 14, fontWeight: '600', color: '#94a3b8' },
  tabTextActive: { color: '#2563eb', fontWeight: '800' },

  // 콘텐츠 영역
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 14 },

  // Progress
  progressSection: { marginBottom: 16 },
  progressTitle:   { fontSize: 15, fontWeight: '800', color: '#1e293b', marginBottom: 8 },
  progressSub:     { fontSize: 12, color: '#64748b', marginTop: 4 },
  progressWrap:    { flexDirection: 'row', alignItems: 'center', gap: 10 },
  progressTrack: {
    flex: 1,
    height: 10,
    backgroundColor: '#e2e8f0',
    borderRadius: 5,
    overflow: 'hidden',
  },
  progressFill:  { height: '100%', borderRadius: 5 },
  progressLabel: { fontSize: 14, fontWeight: '800', minWidth: 38, textAlign: 'right' },

  // Task 리스트
  taskList:  { paddingBottom: 20 },
  emptyText: { textAlign: 'center', color: '#94a3b8', marginTop: 40, fontSize: 14 },

  // Sub-Tab (기본/보험)
  subTabRow: {
    flexDirection: 'row',
    backgroundColor: '#f1f5f9',
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
  },
  subTab: {
    flex: 1,
    paddingVertical: 9,
    alignItems: 'center',
    borderRadius: 8,
  },
  subTabActive:     { backgroundColor: '#fff', shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 4, elevation: 2 },
  subTabText:       { fontSize: 13, fontWeight: '600', color: '#64748b' },
  subTabTextActive: { color: '#1e293b', fontWeight: '800' },

  // 폼
  formSection: { paddingBottom: 40 },
  fieldWrap:   { marginBottom: 14 },
  inputLabel:  { fontSize: 13, fontWeight: '700', color: '#374151', marginBottom: 5 },
  hint:        { fontSize: 11, color: '#94a3b8', fontWeight: '400' },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1.5,
    borderColor: '#e2e8f0',
    borderRadius: 10,
    paddingHorizontal: 13,
    paddingVertical: 11,
    fontSize: 14,
    color: '#1e293b',
  },
  inputMulti: { height: 80, textAlignVertical: 'top' },

  // 성별 버튼
  genderRow: { flexDirection: 'row', gap: 10 },
  genderBtn: {
    flex: 1,
    paddingVertical: 11,
    alignItems: 'center',
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: '#e2e8f0',
    backgroundColor: '#fff',
  },
  genderBtnActive:     { backgroundColor: '#eff6ff', borderColor: '#2563eb' },
  genderBtnText:       { fontSize: 14, fontWeight: '600', color: '#64748b' },
  genderBtnTextActive: { color: '#2563eb', fontWeight: '800' },

  // 실손 세대
  silsonRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  silsonBadgeWrap: { flexShrink: 0 },
  silsonInfo: {
    backgroundColor: '#f0fdf4',
    borderRadius: 8,
    padding: 10,
    marginTop: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#22c55e',
  },
  silsonInfoText: { fontSize: 12, color: '#15803d', lineHeight: 18 },
});

export default Dashboard;
