/**
 * PersonFormModal.js — 고객 등록 / 수정 풀스크린 모달
 * 3단계 계층 전체 필드 입력 지원
 */
import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Modal, Switch, KeyboardAvoidingView, Platform,
} from 'react-native';
import { MANAGEMENT_TIER, PROSPECTING_STAGE } from '../config';
import { upsertPerson } from '../services/supabaseService';

const MONTHS = ['1','2','3','4','5','6','7','8','9','10','11','12'];

function SectionTitle({ label }) {
  return <Text style={styles.sectionTitle}>{label}</Text>;
}

function Field({ label, children }) {
  return (
    <View style={styles.fieldRow}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.fieldInput}>{children}</View>
    </View>
  );
}

function TextF({ value, onChange, placeholder, keyboardType = 'default', multiline = false }) {
  return (
    <TextInput
      style={[styles.input, multiline && styles.inputMulti]}
      value={value || ''}
      onChangeText={onChange}
      placeholder={placeholder}
      placeholderTextColor="#9ca3af"
      keyboardType={keyboardType}
      multiline={multiline}
      numberOfLines={multiline ? 3 : 1}
    />
  );
}

function SelectRow({ options, value, onChange }) {
  return (
    <View style={styles.selectRow}>
      {options.map((opt) => (
        <TouchableOpacity
          key={String(opt.value)}
          style={[styles.selectBtn, value === opt.value && styles.selectBtnActive]}
          onPress={() => onChange(opt.value)}
        >
          <Text style={[styles.selectText, value === opt.value && styles.selectTextActive]}>
            {opt.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

function MonthPicker({ label, value, onChange }) {
  return (
    <Field label={label}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.monthRow}>
          <TouchableOpacity
            style={[styles.monthBtn, value == null && styles.monthBtnActive]}
            onPress={() => onChange(null)}
          >
            <Text style={[styles.monthText, value == null && styles.monthTextActive]}>없음</Text>
          </TouchableOpacity>
          {MONTHS.map((m) => (
            <TouchableOpacity
              key={m}
              style={[styles.monthBtn, value === parseInt(m) && styles.monthBtnActive]}
              onPress={() => onChange(parseInt(m))}
            >
              <Text style={[styles.monthText, value === parseInt(m) && styles.monthTextActive]}>
                {m}월
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </Field>
  );
}

const EMPTY_FORM = {
  name: '', birth_date: '', gender: '', contact: '', address: '', job: '',
  is_real_client: true, is_favorite: false, memo: '',
  status: 'potential',
  auto_renewal_month: null, fire_renewal_month: null, last_auto_carrier: '',
  management_tier: 3, wedding_anniversary: '', driving_status: '', risk_note: '',
  lead_source: '', referrer_id: '', referrer_relation: '', prospecting_stage: 'lead',
  community_tags_raw: '',
};

export default function PersonFormModal({ visible, person, onClose }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (person) {
      setForm({
        ...EMPTY_FORM,
        ...person,
        community_tags_raw: (person.community_tags || []).join(', '),
      });
    } else {
      setForm(EMPTY_FORM);
    }
  }, [person, visible]);

  const set = (key) => (val) => setForm((f) => ({ ...f, [key]: val }));

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const tags = form.community_tags_raw
        ? form.community_tags_raw.split(',').map((t) => t.trim()).filter(Boolean)
        : [];
      const payload = { ...form, community_tags: tags };
      delete payload.community_tags_raw;
      if (person?.person_id) payload.person_id = person.person_id;
      await upsertPerson(payload);
      onClose();
    } catch (e) {
      console.error('저장 오류:', e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView
        style={styles.root}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* 헤더 */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.cancelBtn}>
            <Text style={styles.cancelText}>취소</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>
            {person ? '고객 수정' : '고객 등록'}
          </Text>
          <TouchableOpacity
            onPress={handleSave}
            style={[styles.saveBtn, saving && styles.saveBtnDisabled]}
            disabled={saving}
          >
            <Text style={styles.saveText}>{saving ? '저장 중...' : '저장'}</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.scroll} keyboardShouldPersistTaps="handled">

          {/* ── Core 기본 정보 ─────────────────────────────── */}
          <SectionTitle label="기본 정보" />

          <Field label="이름 *">
            <TextF value={form.name} onChange={set('name')} placeholder="홍길동" />
          </Field>
          <Field label="생년월일">
            <TextF value={form.birth_date} onChange={set('birth_date')}
              placeholder="1985-06-15" keyboardType="numbers-and-punctuation" />
          </Field>
          <Field label="성별">
            <SelectRow
              value={form.gender}
              onChange={set('gender')}
              options={[{ label: '남', value: 'male' }, { label: '여', value: 'female' }]}
            />
          </Field>
          <Field label="연락처">
            <TextF value={form.contact} onChange={set('contact')}
              placeholder="010-0000-0000" keyboardType="phone-pad" />
          </Field>
          <Field label="주소">
            <TextF value={form.address} onChange={set('address')} placeholder="서울시 강남구..." />
          </Field>
          <Field label="직업">
            <TextF value={form.job} onChange={set('job')} placeholder="회사원 / 자영업..." />
          </Field>
          <Field label="실제 고객">
            <Switch value={form.is_real_client} onValueChange={set('is_real_client')} />
          </Field>
          <Field label="중요 고객 ★">
            <Switch value={form.is_favorite} onValueChange={set('is_favorite')} />
          </Field>

          {/* ── Core 관리 상태 ──────────────────────────────── */}
          <SectionTitle label="관리 상태" />

          <Field label="관리 등급">
            <SelectRow
              value={form.management_tier}
              onChange={set('management_tier')}
              options={Object.entries(MANAGEMENT_TIER).map(([v, t]) => ({
                value: parseInt(v), label: t.label,
              }))}
            />
          </Field>
          <Field label="고객 상태">
            <SelectRow
              value={form.status}
              onChange={set('status')}
              options={[
                { label: '가망', value: 'potential' },
                { label: '진행', value: 'active' },
                { label: '계약', value: 'contracted' },
                { label: '종료', value: 'closed' },
              ]}
            />
          </Field>

          {/* ── 1차 라인: 연간 계약 ────────────────────────── */}
          <SectionTitle label="📅 1차 라인 — 연간 계약" />

          <MonthPicker label="자동차 갱신월" value={form.auto_renewal_month}
            onChange={set('auto_renewal_month')} />
          <MonthPicker label="화재 갱신월" value={form.fire_renewal_month}
            onChange={set('fire_renewal_month')} />
          <Field label="마지막 자동차보험사">
            <TextF value={form.last_auto_carrier} onChange={set('last_auto_carrier')}
              placeholder="삼성화재 / DB손해보험..." />
          </Field>

          {/* ── 2차 라인: 전략 케어 ────────────────────────── */}
          <SectionTitle label="💎 2차 라인 — 전략 케어" />

          <Field label="결혼기념일">
            <TextF value={form.wedding_anniversary} onChange={set('wedding_anniversary')}
              placeholder="2010-05-22" keyboardType="numbers-and-punctuation" />
          </Field>
          <Field label="운전 상태">
            <SelectRow
              value={form.driving_status}
              onChange={set('driving_status')}
              options={[
                { label: '자가용', value: 'personal' },
                { label: '영업용', value: 'commercial' },
                { label: '이륜차', value: 'motorcycle' },
                { label: '미운전', value: 'none' },
              ]}
            />
          </Field>
          <Field label="위험 메모">
            <TextF value={form.risk_note} onChange={set('risk_note')}
              placeholder="고혈압, 스카이다이빙 취미..." multiline />
          </Field>

          {/* ── 3차 라인: 인맥 & 활동 ─────────────────────── */}
          <SectionTitle label="🏟️ 3차 라인 — 인맥 & 활동" />

          <Field label="개척 단계">
            <SelectRow
              value={form.prospecting_stage}
              onChange={set('prospecting_stage')}
              options={Object.entries(PROSPECTING_STAGE).map(([v, s]) => ({
                value: v, label: s.label,
              }))}
            />
          </Field>
          <Field label="유입 경로">
            <TextF value={form.lead_source} onChange={set('lead_source')}
              placeholder="지인 소개 / SNS / 세미나..." />
          </Field>
          <Field label="소개 관계">
            <TextF value={form.referrer_relation} onChange={set('referrer_relation')}
              placeholder="친구 / 직장동료..." />
          </Field>
          <Field label="소속 모임">
            <TextF value={form.community_tags_raw} onChange={set('community_tags_raw')}
              placeholder="골프모임, 동창회, 교회 (쉼표 구분)" />
          </Field>

          {/* ── 메모 ───────────────────────────────────────── */}
          <SectionTitle label="메모" />
          <Field label="상담 메모">
            <TextF value={form.memo} onChange={set('memo')}
              placeholder="감성 포인트, 선호 연락 시간..." multiline />
          </Field>

          <View style={styles.bottomPad} />
        </ScrollView>
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
  headerTitle: { fontSize: 16, fontWeight: '900', color: '#1e3a5f' },
  cancelBtn:   { paddingHorizontal: 4 },
  cancelText:  { fontSize: 14, color: '#6b7280' },
  saveBtn:     { backgroundColor: '#1e3a5f', borderRadius: 8, paddingHorizontal: 16, paddingVertical: 6 },
  saveBtnDisabled: { opacity: 0.5 },
  saveText:    { color: '#fff', fontWeight: '800', fontSize: 14 },
  scroll:      { flex: 1 },
  sectionTitle: {
    fontSize: 13, fontWeight: '900', color: '#1e3a5f',
    backgroundColor: '#eff6ff', paddingHorizontal: 16, paddingVertical: 8,
    marginTop: 8,
  },
  fieldRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 10,
    backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#f3f4f6',
  },
  fieldLabel: { fontSize: 13, color: '#374151', width: 100, fontWeight: '600' },
  fieldInput: { flex: 1 },
  input: {
    borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 6,
    paddingHorizontal: 10, paddingVertical: 6, fontSize: 13, color: '#111',
  },
  inputMulti: { minHeight: 60, textAlignVertical: 'top' },
  selectRow:  { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  selectBtn: {
    paddingHorizontal: 12, paddingVertical: 5, borderRadius: 16,
    borderWidth: 1, borderColor: '#d1d5db', backgroundColor: '#fff',
  },
  selectBtnActive: { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  selectText:      { fontSize: 12, color: '#374151' },
  selectTextActive:{ color: '#fff', fontWeight: '700' },
  monthRow:   { flexDirection: 'row', gap: 4 },
  monthBtn: {
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 12, borderWidth: 1, borderColor: '#d1d5db', backgroundColor: '#fff',
  },
  monthBtnActive: { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  monthText:      { fontSize: 12, color: '#374151' },
  monthTextActive:{ color: '#fff', fontWeight: '700' },
  bottomPad: { height: 60 },
});
