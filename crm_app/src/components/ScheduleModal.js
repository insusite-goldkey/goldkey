/**
 * ScheduleModal.js — 일정 등록 / 수정 모달
 * 상담 예약, 갱신 안내, 생일/기념일 연락 등
 */
import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Modal, KeyboardAvoidingView, Platform, ScrollView,
} from 'react-native';
import { upsertSchedule } from '../services/supabaseService';

const SCHEDULE_TYPES = [
  { value: 'consult',  label: '상담', icon: '💬' },
  { value: 'renewal',  label: '갱신 안내', icon: '🔄' },
  { value: 'birthday', label: '생일 연락', icon: '🎂' },
  { value: 'followup', label: '팔로업', icon: '📞' },
  { value: 'visit',    label: '방문', icon: '🏢' },
  { value: 'other',    label: '기타', icon: '📌' },
];

const EMPTY = {
  title: '', date: '', time: '', type: 'consult', memo: '',
};

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function ScheduleModal({ visible, person, schedule, onClose }) {
  const [form, setForm]   = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (schedule) {
      setForm({ ...EMPTY, ...schedule });
    } else {
      setForm({
        ...EMPTY,
        date: todayStr(),
        title: person ? `${person.name} 상담` : '',
      });
    }
  }, [schedule, person, visible]);

  const set = (key) => (val) => setForm((f) => ({ ...f, [key]: val }));

  const handleSave = async () => {
    if (!form.title.trim() || !form.date) return;
    setSaving(true);
    try {
      const payload = {
        ...form,
        person_id: person?.person_id || schedule?.person_id || null,
        done: schedule?.done || false,
      };
      if (schedule?.id) payload.id = schedule.id;
      await upsertSchedule(payload);
      onClose();
    } catch (e) {
      console.error('일정 저장 오류:', e);
    } finally {
      setSaving(false);
    }
  };

  const selectedType = SCHEDULE_TYPES.find((t) => t.value === form.type) || SCHEDULE_TYPES[0];

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        style={styles.root}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* 헤더 */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose}>
            <Text style={styles.cancelText}>취소</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>
            {selectedType.icon} {schedule ? '일정 수정' : '일정 추가'}
          </Text>
          <TouchableOpacity
            onPress={handleSave}
            style={[styles.saveBtn, saving && { opacity: 0.5 }]}
            disabled={saving}
          >
            <Text style={styles.saveText}>{saving ? '저장 중...' : '저장'}</Text>
          </TouchableOpacity>
        </View>

        {/* 고객 표시 */}
        {person && (
          <View style={styles.personBadge}>
            <Text style={styles.personBadgeText}>👤 {person.name} 고객</Text>
          </View>
        )}

        <ScrollView style={styles.scroll} keyboardShouldPersistTaps="handled">

          {/* 일정 유형 */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>유형</Text>
            <View style={styles.typeGrid}>
              {SCHEDULE_TYPES.map((t) => (
                <TouchableOpacity
                  key={t.value}
                  style={[styles.typeBtn, form.type === t.value && styles.typeBtnActive]}
                  onPress={() => set('type')(t.value)}
                >
                  <Text style={styles.typeIcon}>{t.icon}</Text>
                  <Text style={[styles.typeLabel, form.type === t.value && styles.typeLabelActive]}>
                    {t.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* 제목 */}
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>제목 *</Text>
            <TextInput
              style={styles.input}
              value={form.title}
              onChangeText={set('title')}
              placeholder="일정 제목을 입력하세요"
              placeholderTextColor="#9ca3af"
            />
          </View>

          {/* 날짜 */}
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>날짜 *</Text>
            <TextInput
              style={styles.input}
              value={form.date}
              onChangeText={set('date')}
              placeholder="YYYY-MM-DD"
              placeholderTextColor="#9ca3af"
              keyboardType="numbers-and-punctuation"
            />
          </View>

          {/* 시간 */}
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>시간</Text>
            <TextInput
              style={styles.input}
              value={form.time}
              onChangeText={set('time')}
              placeholder="10:30 (선택)"
              placeholderTextColor="#9ca3af"
              keyboardType="numbers-and-punctuation"
            />
          </View>

          {/* 메모 */}
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>메모</Text>
            <TextInput
              style={[styles.input, styles.inputMulti]}
              value={form.memo}
              onChangeText={set('memo')}
              placeholder="상담 내용, 준비사항 등..."
              placeholderTextColor="#9ca3af"
              multiline
              numberOfLines={4}
            />
          </View>

          {/* 빠른 날짜 선택 */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>빠른 날짜 선택</Text>
            <View style={styles.quickDateRow}>
              {[
                { label: '오늘', days: 0 },
                { label: '내일', days: 1 },
                { label: '3일 후', days: 3 },
                { label: '1주 후', days: 7 },
                { label: '2주 후', days: 14 },
                { label: '1달 후', days: 30 },
              ].map((q) => (
                <TouchableOpacity
                  key={q.label}
                  style={styles.quickBtn}
                  onPress={() => {
                    const d = new Date();
                    d.setDate(d.getDate() + q.days);
                    set('date')(d.toISOString().slice(0, 10));
                  }}
                >
                  <Text style={styles.quickBtnText}>{q.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={{ height: 40 }} />
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
  headerTitle: { fontSize: 15, fontWeight: '900', color: '#1e3a5f' },
  cancelText:  { fontSize: 14, color: '#6b7280' },
  saveBtn:     { backgroundColor: '#1e3a5f', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 6 },
  saveText:    { color: '#fff', fontWeight: '800', fontSize: 13 },
  personBadge: {
    backgroundColor: '#eff6ff', paddingHorizontal: 16, paddingVertical: 6,
    borderBottomWidth: 1, borderBottomColor: '#bfdbfe',
  },
  personBadgeText: { fontSize: 12, color: '#1d4ed8', fontWeight: '700' },
  scroll: { flex: 1 },
  section: {
    backgroundColor: '#fff', padding: 16,
    borderBottomWidth: 1, borderBottomColor: '#f3f4f6', marginTop: 8,
  },
  sectionLabel: { fontSize: 12, fontWeight: '700', color: '#374151', marginBottom: 10 },
  typeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  typeBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 16, borderWidth: 1, borderColor: '#d1d5db',
    backgroundColor: '#fff',
  },
  typeBtnActive: { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  typeIcon:      { fontSize: 14 },
  typeLabel:     { fontSize: 12, color: '#374151' },
  typeLabelActive:{ color: '#fff', fontWeight: '700' },
  field: {
    backgroundColor: '#fff', paddingHorizontal: 16, paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: '#f3f4f6',
  },
  fieldLabel: { fontSize: 12, fontWeight: '600', color: '#6b7280', marginBottom: 6 },
  input: {
    borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 8, fontSize: 14, color: '#111',
  },
  inputMulti: { minHeight: 80, textAlignVertical: 'top' },
  quickDateRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  quickBtn: {
    paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 12, backgroundColor: '#f0fdf4',
    borderWidth: 1, borderColor: '#86efac',
  },
  quickBtnText: { fontSize: 12, color: '#16a34a', fontWeight: '600' },
});
