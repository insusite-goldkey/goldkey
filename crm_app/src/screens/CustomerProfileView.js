/**
 * CustomerProfileView — 고객 상세 프로필 화면
 *
 * - 조회 모드 / 편집 모드 전환
 * - 이 고객의 과거/예정 일정 리스트
 * - [+ 새 일정 추가] → ScheduleInputModal (고객 기본값 자동세팅)
 * - 정보 수정 저장 시 useCustomerStore 해당 id만 patch
 *   → 앱 전체(달력, 검색창, 대시보드) 즉시 동기화
 */

import React, { useState } from 'react';
import {
  Alert,
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
  useCustomerStore,
  selCustomer,
  selSchedules,
} from '../store/customerStore';

// ── 카테고리 메타 ─────────────────────────────────────────────────────────────
const CAT_META = {
  consult:     { label: '상담',    color: '#ef4444', bg: '#fee2e2' },
  appointment: { label: '약속',    color: '#3b82f6', bg: '#dbeafe' },
  todo:        { label: '할 일',   color: '#f59e0b', bg: '#fef9c3' },
  personal:    { label: '개인',    color: '#22c55e', bg: '#dcfce7' },
};

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
const CustomerProfileView = () => {
  const activeId         = useCustomerStore((s) => s.activeProfileId);
  const customer         = useCustomerStore(selCustomer(activeId));
  const schedules        = useCustomerStore(selSchedules(activeId));
  const updateCustomer   = useCustomerStore((s) => s.updateCustomer);
  const closeProfile     = useCustomerStore((s) => s.closeProfile);
  const openScheduleModal= useCustomerStore((s) => s.openScheduleModal);
  const toggleDone       = useCustomerStore((s) => s.toggleScheduleDone);
  const openEditSchedule = useCustomerStore((s) => s.openScheduleModal);

  const [editMode, setEditMode] = useState(false);
  const [draft, setDraft]       = useState({});

  if (!customer) return null;

  // ── 편집 시작 ──────────────────────────────────────────────────────────────
  const startEdit = () => {
    setDraft({
      name:    customer.name    || '',
      age:     String(customer.age || ''),
      job:     customer.job     || '',
      phone:   customer.phone   || '',
      gender:  customer.gender  || '',
      company: customer.company || '',
      title:   customer.title   || '',
      memo:    customer.memo    || '',
      tags:    (customer.tags   || []).join(', '),
    });
    setEditMode(true);
  };

  // ── 저장 — id 하나만 patch → 전체 동기화 ──────────────────────────────────
  const handleSave = () => {
    if (!draft.name.trim()) {
      Alert.alert('오류', '고객 이름을 입력하세요.');
      return;
    }
    updateCustomer(activeId, {
      name:    draft.name.trim(),
      age:     parseInt(draft.age, 10) || 0,
      job:     draft.job.trim(),
      phone:   draft.phone.trim(),
      gender:  draft.gender,
      company: draft.company.trim(),
      title:   draft.title.trim(),
      memo:    draft.memo.trim(),
      tags:    draft.tags.split(',').map((t) => t.trim()).filter(Boolean),
    });
    setEditMode(false);
  };

  const pd = (key, val) => setDraft((d) => ({ ...d, [key]: val }));

  // ── 일정 분리: 예정 / 완료 ────────────────────────────────────────────────
  const today = new Date().toISOString().slice(0, 10);
  const upcoming = schedules.filter((s) => !s.done && s.date >= today);
  const past     = schedules.filter((s) =>  s.done || s.date < today);

  // ── 렌더 ──────────────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.safeArea}>
      {/* 상단 헤더 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={closeProfile} style={styles.backBtn}>
          <Text style={styles.backBtnText}>← 뒤로</Text>
        </TouchableOpacity>
        <Text style={styles.topBarTitle} numberOfLines={1}>
          {customer.name} 프로필
        </Text>
        {editMode ? (
          <TouchableOpacity onPress={handleSave} style={styles.saveTopBtn}>
            <Text style={styles.saveTopBtnText}>저장</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity onPress={startEdit} style={styles.editTopBtn}>
            <Text style={styles.editTopBtnText}>편집</Text>
          </TouchableOpacity>
        )}
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={90}
      >
        <ScrollView
          style={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* ── 프로필 카드 ── */}
          <View style={styles.profileCard}>
            {/* 아바타 + 이름 */}
            <View style={styles.avatarRow}>
              <View style={[
                styles.avatar,
                customer.registered ? styles.avatarReg : styles.avatarUnreg,
              ]}>
                <Text style={styles.avatarText}>
                  {customer.name?.charAt(0) || '?'}
                </Text>
              </View>
              <View style={{ flex: 1 }}>
                {editMode ? (
                  <TextInput
                    style={[styles.editInput, styles.editInputName]}
                    value={draft.name}
                    onChangeText={(v) => pd('name', v)}
                    placeholder="고객 성함"
                    placeholderTextColor="#94a3b8"
                  />
                ) : (
                  <Text style={styles.profileName}>{customer.name}</Text>
                )}
                <View style={styles.regBadge}>
                  <View style={[
                    styles.regDot,
                    { backgroundColor: customer.registered ? '#22c55e' : '#f59e0b' },
                  ]} />
                  <Text style={styles.regText}>
                    {customer.registered ? '등록 고객' : '미등록 고객'}
                  </Text>
                </View>
              </View>
            </View>

            <Divider />

            {/* 기본 정보 그리드 */}
            {editMode ? (
              <View>
                <InfoRow2
                  label1="나이" val1={draft.age}     onChange1={(v) => pd('age', v)}
                  label2="직업" val2={draft.job}     onChange2={(v) => pd('job', v)}
                  keyboardType1="numeric"
                />
                <InfoRow2
                  label1="연락처" val1={draft.phone}   onChange1={(v) => pd('phone', v)}
                  label2="성별"   val2={draft.gender}  onChange2={(v) => pd('gender', v)}
                  keyboardType1="phone-pad"
                />
                <InfoRow2
                  label1="법인명" val1={draft.company} onChange1={(v) => pd('company', v)}
                  label2="직위"   val2={draft.title}   onChange2={(v) => pd('title', v)}
                />
              </View>
            ) : (
              <View>
                <InfoRow2View
                  label1="나이"   val1={customer.age ? `${customer.age}세` : '—'}
                  label2="직업"   val2={customer.job   || '—'}
                />
                <InfoRow2View
                  label1="연락처" val1={customer.phone || '—'}
                  label2="성별"   val2={customer.gender|| '—'}
                />
                <InfoRow2View
                  label1="법인명" val1={customer.company || '—'}
                  label2="직위"   val2={customer.title   || '—'}
                />
              </View>
            )}

            <Divider />

            {/* 특이사항 태그 */}
            <Text style={styles.sectionLabel}>🏷 특이사항 태그</Text>
            {editMode ? (
              <TextInput
                style={styles.editInput}
                value={draft.tags}
                onChangeText={(v) => pd('tags', v)}
                placeholder="쉼표(,)로 구분 예: 위암 보장 부족, 4세대 실손"
                placeholderTextColor="#94a3b8"
                multiline
              />
            ) : (
              <View style={styles.tagWrap}>
                {(customer.tags || []).length > 0
                  ? customer.tags.map((tag, i) => (
                    <View key={i} style={styles.tag}>
                      <Text style={styles.tagText}>{tag}</Text>
                    </View>
                  ))
                  : <Text style={styles.emptyText}>태그 없음</Text>
                }
              </View>
            )}

            <Divider />

            {/* 메모 */}
            <Text style={styles.sectionLabel}>📝 메모</Text>
            {editMode ? (
              <TextInput
                style={[styles.editInput, styles.editInputMulti]}
                value={draft.memo}
                onChangeText={(v) => pd('memo', v)}
                placeholder="상담 특이사항, 연락 선호 시간 등..."
                placeholderTextColor="#94a3b8"
                multiline
                numberOfLines={4}
                textAlignVertical="top"
              />
            ) : (
              <Text style={styles.memoText}>
                {customer.memo || '메모 없음'}
              </Text>
            )}

            {/* 편집 모드 취소 버튼 */}
            {editMode && (
              <TouchableOpacity
                style={styles.cancelEditBtn}
                onPress={() => setEditMode(false)}
              >
                <Text style={styles.cancelEditBtnText}>취소</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* ── 일정 섹션 ── */}
          <View style={styles.scheduleSection}>
            <View style={styles.scheduleSectionHeader}>
              <Text style={styles.scheduleSectionTitle}>📅 이 고객의 일정</Text>
              <TouchableOpacity
                style={styles.addSchedBtn}
                onPress={() => openScheduleModal(activeId)}
              >
                <Text style={styles.addSchedBtnText}>+ 새 일정</Text>
              </TouchableOpacity>
            </View>

            {/* 예정 일정 */}
            {upcoming.length > 0 && (
              <>
                <Text style={styles.schedGroupLabel}>⏳ 예정</Text>
                {upcoming.map((sc) => (
                  <ScheduleRow
                    key={sc.id}
                    schedule={sc}
                    onToggle={() => toggleDone(sc.id)}
                    onEdit={() => openEditSchedule(activeId, sc.id)}
                  />
                ))}
              </>
            )}

            {/* 과거/완료 일정 */}
            {past.length > 0 && (
              <>
                <Text style={[styles.schedGroupLabel, { color: '#94a3b8' }]}>✅ 완료 / 과거</Text>
                {past.map((sc) => (
                  <ScheduleRow
                    key={sc.id}
                    schedule={sc}
                    onToggle={() => toggleDone(sc.id)}
                    onEdit={() => openEditSchedule(activeId, sc.id)}
                    dimmed
                  />
                ))}
              </>
            )}

            {upcoming.length === 0 && past.length === 0 && (
              <View style={styles.emptyScheduleWrap}>
                <Text style={styles.emptyScheduleText}>
                  등록된 일정이 없습니다.{'\n'}[+ 새 일정] 버튼으로 추가하세요.
                </Text>
              </View>
            )}
          </View>

          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// ── 서브 컴포넌트들 ───────────────────────────────────────────────────────────

const Divider = () => <View style={styles.divider} />;

const InfoRow2View = ({ label1, val1, label2, val2 }) => (
  <View style={styles.infoRow}>
    <View style={styles.infoCell}>
      <Text style={styles.infoLabel}>{label1}</Text>
      <Text style={styles.infoValue}>{val1}</Text>
    </View>
    <View style={styles.infoCell}>
      <Text style={styles.infoLabel}>{label2}</Text>
      <Text style={styles.infoValue}>{val2}</Text>
    </View>
  </View>
);

const InfoRow2 = ({
  label1, val1, onChange1, keyboardType1,
  label2, val2, onChange2, keyboardType2,
}) => (
  <View style={styles.infoRow}>
    <View style={styles.infoCell}>
      <Text style={styles.infoLabel}>{label1}</Text>
      <TextInput
        style={styles.editInput}
        value={val1}
        onChangeText={onChange1}
        keyboardType={keyboardType1 || 'default'}
        placeholderTextColor="#94a3b8"
        placeholder="—"
      />
    </View>
    <View style={[styles.infoCell, { marginLeft: 10 }]}>
      <Text style={styles.infoLabel}>{label2}</Text>
      <TextInput
        style={styles.editInput}
        value={val2}
        onChangeText={onChange2}
        keyboardType={keyboardType2 || 'default'}
        placeholderTextColor="#94a3b8"
        placeholder="—"
      />
    </View>
  </View>
);

const ScheduleRow = ({ schedule, onToggle, onEdit, dimmed }) => {
  const meta = CAT_META[schedule.category] || CAT_META.consult;
  return (
    <TouchableOpacity
      style={[styles.schedRow, dimmed && styles.schedRowDimmed]}
      onPress={onEdit}
      activeOpacity={0.75}
    >
      <TouchableOpacity
        style={[styles.schedDot, { backgroundColor: schedule.done ? '#e2e8f0' : meta.color }]}
        onPress={onToggle}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        {schedule.done && <Text style={styles.schedDotCheck}>✓</Text>}
      </TouchableOpacity>
      <View style={{ flex: 1 }}>
        <Text style={[styles.schedTitle, dimmed && styles.schedTitleDimmed]}
          numberOfLines={1}>
          {schedule.title}
        </Text>
        <Text style={styles.schedMeta}>
          {schedule.date}  {schedule.startTime}–{schedule.endTime}
        </Text>
      </View>
      <View style={[styles.schedCatBadge, { backgroundColor: meta.bg }]}>
        <Text style={[styles.schedCatText, { color: meta.color }]}>{meta.label}</Text>
      </View>
    </TouchableOpacity>
  );
};

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safeArea:   { flex: 1, backgroundColor: '#f8fafc' },

  topBar: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 16, paddingTop: 14, paddingBottom: 14,
    gap: 10,
  },
  backBtn:        { paddingHorizontal: 4 },
  backBtnText:    { fontSize: 14, fontWeight: '700', color: '#93c5fd' },
  topBarTitle:    { flex: 1, fontSize: 16, fontWeight: '900', color: '#ffffff', textAlign: 'center' },
  editTopBtn: {
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  editTopBtnText: { fontSize: 13, fontWeight: '700', color: '#ffd700' },
  saveTopBtn: {
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: 8,
    backgroundColor: '#ffd700',
  },
  saveTopBtnText: { fontSize: 13, fontWeight: '800', color: '#1e3a5f' },

  scroll: { flex: 1 },

  // ── 프로필 카드
  profileCard: {
    backgroundColor: '#ffffff',
    margin: 16,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1.5, borderColor: '#e2e8f0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07, shadowRadius: 10, elevation: 4,
  },

  avatarRow:   { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: 16 },
  avatar: {
    width: 60, height: 60, borderRadius: 30,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarReg:   { backgroundColor: '#1e3a5f' },
  avatarUnreg: { backgroundColor: '#64748b' },
  avatarText:  { fontSize: 24, fontWeight: '900', color: '#ffffff' },

  profileName:  { fontSize: 22, fontWeight: '900', color: '#1e293b', marginBottom: 4 },
  regBadge:     { flexDirection: 'row', alignItems: 'center', gap: 5 },
  regDot:       { width: 8, height: 8, borderRadius: 4 },
  regText:      { fontSize: 12, fontWeight: '600', color: '#64748b' },

  divider: { height: 1, backgroundColor: '#f1f5f9', marginVertical: 14 },

  // 정보 행
  infoRow:  { flexDirection: 'row', marginBottom: 10 },
  infoCell: { flex: 1 },
  infoLabel:{ fontSize: 11, fontWeight: '700', color: '#94a3b8', marginBottom: 3, textTransform: 'uppercase', letterSpacing: 0.5 },
  infoValue:{ fontSize: 15, fontWeight: '700', color: '#1e293b' },

  sectionLabel: { fontSize: 13, fontWeight: '800', color: '#374151', marginBottom: 10 },

  // 태그
  tagWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  tag: {
    paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20,
    backgroundColor: '#eff6ff', borderWidth: 1, borderColor: '#bfdbfe',
  },
  tagText: { fontSize: 12, fontWeight: '700', color: '#1d4ed8' },

  // 메모
  memoText: { fontSize: 14, color: '#475569', lineHeight: 22 },

  // 편집 인풋
  editInput: {
    backgroundColor: '#f8fafc', borderWidth: 1.5, borderColor: '#e2e8f0',
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10,
    fontSize: 14, fontWeight: '600', color: '#1e293b',
  },
  editInputName: { fontSize: 20, fontWeight: '900' },
  editInputMulti:{ height: 90, textAlignVertical: 'top' },

  cancelEditBtn: {
    marginTop: 16, paddingVertical: 12, borderRadius: 10,
    backgroundColor: '#f1f5f9', alignItems: 'center',
    borderWidth: 1, borderColor: '#e2e8f0',
  },
  cancelEditBtnText: { fontSize: 14, fontWeight: '700', color: '#475569' },

  emptyText: { fontSize: 13, color: '#94a3b8' },

  // ── 일정 섹션
  scheduleSection: {
    marginHorizontal: 16, marginBottom: 16,
    backgroundColor: '#ffffff', borderRadius: 16, padding: 16,
    borderWidth: 1.5, borderColor: '#e2e8f0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07, shadowRadius: 10, elevation: 4,
  },
  scheduleSectionHeader: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 12,
  },
  scheduleSectionTitle: { fontSize: 14, fontWeight: '900', color: '#1e293b' },
  addSchedBtn: {
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20,
    backgroundColor: '#1e3a5f',
  },
  addSchedBtnText: { fontSize: 12, fontWeight: '800', color: '#ffd700' },

  schedGroupLabel: {
    fontSize: 11, fontWeight: '800', color: '#475569',
    textTransform: 'uppercase', letterSpacing: 0.5,
    marginTop: 10, marginBottom: 6,
  },

  schedRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingVertical: 11, paddingHorizontal: 12,
    backgroundColor: '#f8fafc', borderRadius: 10,
    marginBottom: 6, borderWidth: 1, borderColor: '#f1f5f9',
  },
  schedRowDimmed: { opacity: 0.55 },
  schedDot: {
    width: 22, height: 22, borderRadius: 11,
    alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  schedDotCheck: { fontSize: 11, color: '#fff', fontWeight: '900' },
  schedTitle:      { fontSize: 14, fontWeight: '700', color: '#1e293b' },
  schedTitleDimmed:{ textDecorationLine: 'line-through', color: '#94a3b8' },
  schedMeta:       { fontSize: 11, color: '#94a3b8', marginTop: 2 },
  schedCatBadge:   { paddingHorizontal: 9, paddingVertical: 4, borderRadius: 12 },
  schedCatText:    { fontSize: 11, fontWeight: '700' },

  emptyScheduleWrap: { paddingVertical: 24, alignItems: 'center' },
  emptyScheduleText: { fontSize: 13, color: '#94a3b8', textAlign: 'center', lineHeight: 20 },
});

export default CustomerProfileView;
