/**
 * PolicyScanModal.js — 보험증권 스캔 & 등록 모달
 * 흐름: 이미지 선택(카메라/갤러리) → AI 파싱(Supabase Edge Function 호출) → 결과 확인 → gk_policies 저장
 * 폴백: AI 파싱 실패 시 수동 입력 모드로 전환
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Modal,
  ScrollView, TextInput, ActivityIndicator,
  KeyboardAvoidingView, Platform, Alert,
} from 'react-native';
import { createPolicy } from '../services/supabaseService';

const STEPS = {
  SELECT:  'SELECT',   // 이미지 소스 선택
  PARSING: 'PARSING',  // AI 파싱 중
  REVIEW:  'REVIEW',   // 파싱 결과 확인 + 수정
  MANUAL:  'MANUAL',   // 수동 입력
  DONE:    'DONE',     // 저장 완료
};

const EMPTY_POLICY = {
  insurance_company: '',
  product_name:      '',
  policy_number:     '',
  contract_date:     '',
  expiry_date:       '',
  premium:           '',
  status:            'active',
};

function StepIndicator({ step }) {
  const steps = ['선택', '분석', '확인', '완료'];
  const idx = { SELECT: 0, PARSING: 1, REVIEW: 2, MANUAL: 2, DONE: 3 }[step] ?? 0;
  return (
    <View style={si.row}>
      {steps.map((s, i) => (
        <View key={s} style={si.item}>
          <View style={[si.dot, i <= idx && si.dotActive]}>
            <Text style={[si.dotNum, i <= idx && si.dotNumActive]}>{i + 1}</Text>
          </View>
          <Text style={[si.label, i <= idx && si.labelActive]}>{s}</Text>
          {i < steps.length - 1 && <View style={[si.line, i < idx && si.lineActive]} />}
        </View>
      ))}
    </View>
  );
}

const si = StyleSheet.create({
  row:          { flexDirection: 'row', justifyContent: 'center', paddingVertical: 12, backgroundColor: '#f9fafb' },
  item:         { alignItems: 'center', flexDirection: 'row' },
  dot:          { width: 24, height: 24, borderRadius: 12, backgroundColor: '#e5e7eb', alignItems: 'center', justifyContent: 'center' },
  dotActive:    { backgroundColor: '#1e3a5f' },
  dotNum:       { fontSize: 11, color: '#9ca3af', fontWeight: '700' },
  dotNumActive: { color: '#fff' },
  label:        { fontSize: 10, color: '#9ca3af', marginHorizontal: 4 },
  labelActive:  { color: '#1e3a5f', fontWeight: '700' },
  line:         { width: 20, height: 2, backgroundColor: '#e5e7eb' },
  lineActive:   { backgroundColor: '#1e3a5f' },
});

function PolicyField({ label, value, onChange, placeholder, keyboardType = 'default' }) {
  return (
    <View style={styles.policyField}>
      <Text style={styles.policyFieldLabel}>{label}</Text>
      <TextInput
        style={styles.policyInput}
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor="#9ca3af"
        keyboardType={keyboardType}
      />
    </View>
  );
}

export default function PolicyScanModal({ visible, person, onClose, onSaved }) {
  const [step,       setStep]       = useState(STEPS.SELECT);
  const [form,       setForm]       = useState(EMPTY_POLICY);
  const [saving,     setSaving]     = useState(false);
  const [parseError, setParseError] = useState('');

  const set = (key) => (val) => setForm((f) => ({ ...f, [key]: val }));

  const reset = () => {
    setStep(STEPS.SELECT);
    setForm(EMPTY_POLICY);
    setParseError('');
  };

  const handleClose = () => { reset(); onClose(); };

  // ── AI 파싱 시뮬레이션 (실제: Supabase Edge Function 또는 Google Vision API) ─
  const simulateParsing = async (sourceType) => {
    setStep(STEPS.PARSING);
    setParseError('');
    try {
      // TODO: 실제 구현 시 아래를 Edge Function 호출로 교체
      // const result = await callScanEdgeFunction(imageBase64);
      await new Promise((r) => setTimeout(r, 1800)); // 파싱 시뮬레이션

      // 시뮬레이션: 파싱 결과 예시
      setForm({
        insurance_company: '삼성화재',
        product_name:      '애니카 자동차보험',
        policy_number:     'AU-2025-' + Math.floor(Math.random() * 900000 + 100000),
        contract_date:     '2025-03-13',
        expiry_date:       '2026-03-12',
        premium:           '85000',
        status:            'active',
      });
      setStep(STEPS.REVIEW);
    } catch (e) {
      setParseError('AI 분석에 실패했습니다. 수동으로 입력해주세요.');
      setForm(EMPTY_POLICY);
      setStep(STEPS.MANUAL);
    }
  };

  const handleSave = async () => {
    if (!form.insurance_company || !form.product_name) {
      Alert.alert('필수 항목', '보험사와 상품명은 필수입니다.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        premium: form.premium ? parseInt(form.premium) : null,
        person_id: person?.person_id || null,
      };
      await createPolicy(payload);
      setStep(STEPS.DONE);
      onSaved && onSaved();
    } catch (e) {
      Alert.alert('저장 오류', e.message || '저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const renderContent = () => {
    switch (step) {

      // ── [1] 소스 선택 ──────────────────────────────────────────────────────
      case STEPS.SELECT:
        return (
          <View style={styles.selectBox}>
            <Text style={styles.selectTitle}>증권 이미지를 불러오세요</Text>
            <Text style={styles.selectSub}>AI가 자동으로 보험 정보를 인식합니다</Text>

            <TouchableOpacity
              style={styles.sourceBtn}
              onPress={() => simulateParsing('camera')}
            >
              <Text style={styles.sourceIcon}>📷</Text>
              <View>
                <Text style={styles.sourceName}>카메라 촬영</Text>
                <Text style={styles.sourceSub}>새 사진을 찍어서 분석</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.sourceBtn}
              onPress={() => simulateParsing('gallery')}
            >
              <Text style={styles.sourceIcon}>🖼️</Text>
              <View>
                <Text style={styles.sourceName}>갤러리에서 선택</Text>
                <Text style={styles.sourceSub}>저장된 이미지에서 선택</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.sourceBtn, styles.sourceBtnSecondary]}
              onPress={() => setStep(STEPS.MANUAL)}
            >
              <Text style={styles.sourceIcon}>✏️</Text>
              <View>
                <Text style={styles.sourceName}>직접 입력</Text>
                <Text style={styles.sourceSub}>증권 정보를 수동으로 입력</Text>
              </View>
            </TouchableOpacity>
          </View>
        );

      // ── [2] AI 파싱 중 ─────────────────────────────────────────────────────
      case STEPS.PARSING:
        return (
          <View style={styles.parsingBox}>
            <ActivityIndicator size="large" color="#1e3a5f" />
            <Text style={styles.parsingText}>AI가 증권을 분석하고 있습니다...</Text>
            <Text style={styles.parsingSub}>보험사 · 상품명 · 만기일을 자동 인식합니다</Text>
          </View>
        );

      // ── [3] 파싱 결과 확인 + 수정 (REVIEW / MANUAL 공용) ───────────────────
      case STEPS.REVIEW:
      case STEPS.MANUAL:
        return (
          <ScrollView keyboardShouldPersistTaps="handled">
            {step === STEPS.REVIEW && (
              <View style={styles.aiResultBanner}>
                <Text style={styles.aiResultText}>✅ AI 분석 완료 — 내용을 확인하고 수정하세요</Text>
              </View>
            )}
            {parseError ? (
              <View style={styles.errorBanner}>
                <Text style={styles.errorText}>⚠️ {parseError}</Text>
              </View>
            ) : null}

            <PolicyField label="보험사 *"    value={form.insurance_company} onChange={set('insurance_company')} placeholder="삼성화재 / DB손해보험..." />
            <PolicyField label="상품명 *"    value={form.product_name}      onChange={set('product_name')}      placeholder="애니카 자동차보험..." />
            <PolicyField label="증권번호"    value={form.policy_number}     onChange={set('policy_number')}     placeholder="AU-2025-XXXXXX" />
            <PolicyField label="계약일"      value={form.contract_date}     onChange={set('contract_date')}     placeholder="YYYY-MM-DD" keyboardType="numbers-and-punctuation" />
            <PolicyField label="만기일"      value={form.expiry_date}       onChange={set('expiry_date')}       placeholder="YYYY-MM-DD" keyboardType="numbers-and-punctuation" />
            <PolicyField label="월 보험료"   value={form.premium}           onChange={set('premium')}           placeholder="85000" keyboardType="number-pad" />

            <View style={styles.policyField}>
              <Text style={styles.policyFieldLabel}>상태</Text>
              <View style={styles.statusRow}>
                {[{ v: 'active', l: '유효' }, { v: 'lapsed', l: '실효' }, { v: 'terminated', l: '해지' }].map((s) => (
                  <TouchableOpacity
                    key={s.v}
                    style={[styles.statusBtn, form.status === s.v && styles.statusBtnActive]}
                    onPress={() => set('status')(s.v)}
                  >
                    <Text style={[styles.statusBtnText, form.status === s.v && styles.statusBtnTextActive]}>
                      {s.l}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <TouchableOpacity
              style={[styles.saveBtn, saving && { opacity: 0.5 }]}
              onPress={handleSave}
              disabled={saving}
            >
              {saving
                ? <ActivityIndicator color="#fff" />
                : <Text style={styles.saveBtnText}>💾 계약 저장</Text>}
            </TouchableOpacity>

            <View style={{ height: 40 }} />
          </ScrollView>
        );

      // ── [4] 저장 완료 ──────────────────────────────────────────────────────
      case STEPS.DONE:
        return (
          <View style={styles.doneBox}>
            <Text style={styles.doneIcon}>🎉</Text>
            <Text style={styles.doneTitle}>계약 등록 완료!</Text>
            <Text style={styles.doneSub}>{form.insurance_company} {form.product_name}</Text>
            <Text style={styles.doneSub2}>만기일: {form.expiry_date}</Text>

            <TouchableOpacity style={styles.doneBtn} onPress={handleClose}>
              <Text style={styles.doneBtnText}>확인</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.doneBtnSecondary} onPress={reset}>
              <Text style={styles.doneBtnSecondaryText}>+ 추가 등록</Text>
            </TouchableOpacity>
          </View>
        );

      default:
        return null;
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={handleClose}>
      <KeyboardAvoidingView
        style={styles.root}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* 헤더 */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleClose}>
            <Text style={styles.cancelText}>닫기</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>📄 증권 스캔</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* 고객 뱃지 */}
        {person && (
          <View style={styles.personBadge}>
            <Text style={styles.personBadgeText}>👤 {person.name} 고객의 보험 계약</Text>
          </View>
        )}

        {/* 스텝 인디케이터 */}
        <StepIndicator step={step} />

        {/* 본문 */}
        <View style={styles.body}>{renderContent()}</View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1, backgroundColor: '#f9fafb' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e5e7eb',
  },
  headerTitle:  { fontSize: 15, fontWeight: '900', color: '#1e3a5f' },
  cancelText:   { fontSize: 14, color: '#6b7280' },
  personBadge:  { backgroundColor: '#eff6ff', paddingHorizontal: 16, paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: '#bfdbfe' },
  personBadgeText: { fontSize: 12, color: '#1d4ed8', fontWeight: '700' },
  body:         { flex: 1 },

  // 소스 선택
  selectBox:    { padding: 24 },
  selectTitle:  { fontSize: 18, fontWeight: '900', color: '#1e3a5f', textAlign: 'center', marginBottom: 6 },
  selectSub:    { fontSize: 13, color: '#6b7280', textAlign: 'center', marginBottom: 28 },
  sourceBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 16,
    backgroundColor: '#fff', borderRadius: 12,
    padding: 16, marginBottom: 12,
    borderWidth: 1, borderColor: '#e5e7eb',
    elevation: 1,
  },
  sourceBtnSecondary: { backgroundColor: '#f9fafb', borderStyle: 'dashed' },
  sourceIcon:   { fontSize: 32 },
  sourceName:   { fontSize: 15, fontWeight: '800', color: '#111' },
  sourceSub:    { fontSize: 12, color: '#6b7280', marginTop: 2 },

  // 파싱 중
  parsingBox:   { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  parsingText:  { fontSize: 16, fontWeight: '800', color: '#1e3a5f', marginTop: 20, textAlign: 'center' },
  parsingSub:   { fontSize: 13, color: '#6b7280', marginTop: 8, textAlign: 'center' },

  // AI 결과 + 수동 입력 공용
  aiResultBanner: { backgroundColor: '#dcfce7', padding: 12, marginBottom: 4 },
  aiResultText:   { fontSize: 13, color: '#16a34a', fontWeight: '700' },
  errorBanner:    { backgroundColor: '#fef3c7', padding: 12, marginBottom: 4 },
  errorText:      { fontSize: 13, color: '#d97706', fontWeight: '600' },
  policyField: {
    backgroundColor: '#fff', paddingHorizontal: 16, paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: '#f3f4f6',
  },
  policyFieldLabel: { fontSize: 12, fontWeight: '600', color: '#6b7280', marginBottom: 6 },
  policyInput: {
    borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 8, fontSize: 14, color: '#111',
  },
  statusRow:    { flexDirection: 'row', gap: 8 },
  statusBtn: {
    paddingHorizontal: 16, paddingVertical: 6, borderRadius: 16,
    borderWidth: 1, borderColor: '#d1d5db', backgroundColor: '#fff',
  },
  statusBtnActive:    { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  statusBtnText:      { fontSize: 13, color: '#374151' },
  statusBtnTextActive:{ color: '#fff', fontWeight: '700' },
  saveBtn: {
    margin: 16, backgroundColor: '#1e3a5f',
    borderRadius: 12, paddingVertical: 14, alignItems: 'center',
  },
  saveBtnText: { color: '#fff', fontWeight: '900', fontSize: 15 },

  // 완료
  doneBox:           { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  doneIcon:          { fontSize: 60, marginBottom: 16 },
  doneTitle:         { fontSize: 22, fontWeight: '900', color: '#1e3a5f', marginBottom: 8 },
  doneSub:           { fontSize: 15, color: '#374151', fontWeight: '700' },
  doneSub2:          { fontSize: 13, color: '#6b7280', marginTop: 4, marginBottom: 28 },
  doneBtn: {
    backgroundColor: '#1e3a5f', borderRadius: 12,
    paddingHorizontal: 40, paddingVertical: 12, marginBottom: 12,
  },
  doneBtnText:          { color: '#fff', fontWeight: '900', fontSize: 15 },
  doneBtnSecondary:     { borderWidth: 1, borderColor: '#1e3a5f', borderRadius: 12, paddingHorizontal: 40, paddingVertical: 12 },
  doneBtnSecondaryText: { color: '#1e3a5f', fontWeight: '700', fontSize: 15 },
});
