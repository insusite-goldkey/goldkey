/**
 * ScheduleInputModal — 일정 추가/수정 모달
 *
 * - useCustomerStore.scheduleModal.prefillCustomerId 가 있으면
 *   고객을 기본값으로 자동 세팅
 * - 신규/편집 공통 사용 (editScheduleId 유무로 분기)
 */

import React, { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useCustomerStore, selModal, selCustomerList } from '../store/customerStore';

const CATEGORIES = [
  { key: 'consult',     label: '🔴 상담',    color: '#ef4444' },
  { key: 'appointment', label: '🔵 약속',    color: '#3b82f6' },
  { key: 'todo',        label: '🟡 할 일',   color: '#f59e0b' },
  { key: 'personal',    label: '🟢 개인일정', color: '#22c55e' },
];

const EMPTY_FORM = {
  customerId: '',
  title:      '',
  category:   'consult',
  date:       new Date().toISOString().slice(0, 10),
  startTime:  '09:00',
  endTime:    '10:00',
  memo:       '',
};

const ScheduleInputModal = () => {
  const modal            = useCustomerStore(selModal);
  const customers        = useCustomerStore(selCustomerList);
  const addSchedule      = useCustomerStore((s) => s.addSchedule);
  const updateSchedule   = useCustomerStore((s) => s.updateSchedule);
  const removeSchedule   = useCustomerStore((s) => s.removeSchedule);
  const closeModal       = useCustomerStore((s) => s.closeScheduleModal);
  const schedules        = useCustomerStore((s) => s.schedules);

  const [form, setForm]  = useState({ ...EMPTY_FORM });

  // 모달 열릴 때 폼 초기화
  useEffect(() => {
    if (!modal.open) return;
    if (modal.editScheduleId && schedules[modal.editScheduleId]) {
      const sc = schedules[modal.editScheduleId];
      setForm({
        customerId: sc.customerId || '',
        title:      sc.title      || '',
        category:   sc.category   || 'consult',
        date:       sc.date       || EMPTY_FORM.date,
        startTime:  sc.startTime  || '09:00',
        endTime:    sc.endTime    || '10:00',
        memo:       sc.memo       || '',
      });
    } else {
      setForm({
        ...EMPTY_FORM,
        customerId: modal.prefillCustomerId || '',
        date: new Date().toISOString().slice(0, 10),
      });
    }
  }, [modal.open, modal.editScheduleId, modal.prefillCustomerId]);

  const patch = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const handleSave = () => {
    if (!form.title.trim()) return;
    if (modal.editScheduleId) {
      updateSchedule(modal.editScheduleId, form);
    } else {
      addSchedule(form);
    }
    closeModal();
  };

  const handleDelete = () => {
    if (modal.editScheduleId) {
      removeSchedule(modal.editScheduleId);
      closeModal();
    }
  };

  const isEdit = !!modal.editScheduleId;

  return (
    <Modal
      visible={modal.open}
      transparent
      animationType="slide"
      onRequestClose={closeModal}
    >
      <KeyboardAvoidingView
        style={styles.overlay}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <TouchableOpacity style={styles.backdrop} activeOpacity={1} onPress={closeModal} />
        <View style={styles.sheet}>
          {/* 헤더 */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>
              {isEdit ? '✏️ 일정 수정' : '📅 새 일정 추가'}
            </Text>
            <TouchableOpacity onPress={closeModal} style={styles.closeBtn}>
              <Text style={styles.closeBtnText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView
            style={styles.body}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            {/* 제목 */}
            <Field label="일정 제목 *">
              <TextInput
                style={styles.input}
                value={form.title}
                onChangeText={(v) => patch('title', v)}
                placeholder="예: 김민준 종신보험 설계 전달"
                placeholderTextColor="#94a3b8"
              />
            </Field>

            {/* 분류 */}
            <Field label="분류">
              <View style={styles.catRow}>
                {CATEGORIES.map((c) => (
                  <TouchableOpacity
                    key={c.key}
                    onPress={() => patch('category', c.key)}
                    style={[
                      styles.catBtn,
                      form.category === c.key && { borderColor: c.color, backgroundColor: `${c.color}14` },
                    ]}
                  >
                    <Text style={[styles.catBtnText, form.category === c.key && { color: c.color, fontWeight: '800' }]}>
                      {c.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </Field>

            {/* 날짜 */}
            <View style={styles.row2}>
              <Field label="날짜" flex>
                <TextInput
                  style={styles.input}
                  value={form.date}
                  onChangeText={(v) => patch('date', v)}
                  placeholder="YYYY-MM-DD"
                  placeholderTextColor="#94a3b8"
                  keyboardType="numbers-and-punctuation"
                  maxLength={10}
                />
              </Field>
              <View style={styles.row2Gap} />
              <Field label="시작" flex>
                <TextInput
                  style={styles.input}
                  value={form.startTime}
                  onChangeText={(v) => patch('startTime', v)}
                  placeholder="09:00"
                  placeholderTextColor="#94a3b8"
                  keyboardType="numbers-and-punctuation"
                  maxLength={5}
                />
              </Field>
              <View style={styles.row2Gap} />
              <Field label="종료" flex>
                <TextInput
                  style={styles.input}
                  value={form.endTime}
                  onChangeText={(v) => patch('endTime', v)}
                  placeholder="10:00"
                  placeholderTextColor="#94a3b8"
                  keyboardType="numbers-and-punctuation"
                  maxLength={5}
                />
              </Field>
            </View>

            {/* 관련 고객 */}
            <Field label="관련 고객">
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                style={styles.custScroll}
              >
                <TouchableOpacity
                  onPress={() => patch('customerId', '')}
                  style={[styles.custChip, !form.customerId && styles.custChipActive]}
                >
                  <Text style={[styles.custChipText, !form.customerId && styles.custChipTextActive]}>
                    선택 안 함
                  </Text>
                </TouchableOpacity>
                {customers.map((c) => (
                  <TouchableOpacity
                    key={c.id}
                    onPress={() => patch('customerId', c.id)}
                    style={[styles.custChip, form.customerId === c.id && styles.custChipActive]}
                  >
                    <Text style={[styles.custChipText, form.customerId === c.id && styles.custChipTextActive]}>
                      {c.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </Field>

            {/* 메모 */}
            <Field label="메모">
              <TextInput
                style={[styles.input, styles.inputMulti]}
                value={form.memo}
                onChangeText={(v) => patch('memo', v)}
                placeholder="상담 내용, 준비사항 등..."
                placeholderTextColor="#94a3b8"
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />
            </Field>
          </ScrollView>

          {/* 푸터 버튼 */}
          <View style={styles.footer}>
            {isEdit && (
              <TouchableOpacity style={styles.deleteBtn} onPress={handleDelete}>
                <Text style={styles.deleteBtnText}>삭제</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity style={styles.cancelBtn} onPress={closeModal}>
              <Text style={styles.cancelBtnText}>취소</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.saveBtn, !form.title.trim() && styles.saveBtnDisabled]}
              onPress={handleSave}
              disabled={!form.title.trim()}
            >
              <Text style={styles.saveBtnText}>저장</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

// ── Field 래퍼 ────────────────────────────────────────────────────────────────
const Field = ({ label, children, flex }) => (
  <View style={[styles.field, flex && { flex: 1 }]}>
    <Text style={styles.fieldLabel}>{label}</Text>
    {children}
  </View>
);

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  overlay: {
    flex: 1, justifyContent: 'flex-end',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(15,23,42,0.45)',
  },
  sheet: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    paddingBottom: Platform.OS === 'ios' ? 34 : 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.12, shadowRadius: 16, elevation: 24,
  },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 20, paddingBottom: 14,
    borderBottomWidth: 1, borderBottomColor: '#f1f5f9',
  },
  headerTitle: { fontSize: 16, fontWeight: '900', color: '#1e293b' },
  closeBtn: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: '#f1f5f9', alignItems: 'center', justifyContent: 'center',
  },
  closeBtnText: { fontSize: 14, color: '#64748b', fontWeight: '700' },

  body: { paddingHorizontal: 20, paddingTop: 4 },

  field: { marginTop: 14 },
  fieldLabel: { fontSize: 12, fontWeight: '700', color: '#374151', marginBottom: 6 },

  input: {
    backgroundColor: '#f8fafc', borderWidth: 1.5, borderColor: '#e2e8f0',
    borderRadius: 10, paddingHorizontal: 13, paddingVertical: 11,
    fontSize: 14, fontWeight: '600', color: '#1e293b',
  },
  inputMulti: { height: 80, textAlignVertical: 'top' },

  catRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  catBtn: {
    paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20,
    borderWidth: 1.5, borderColor: '#e2e8f0', backgroundColor: '#f8fafc',
  },
  catBtnText: { fontSize: 12, fontWeight: '600', color: '#64748b' },

  row2: { flexDirection: 'row', alignItems: 'flex-start' },
  row2Gap: { width: 8 },

  custScroll: { marginVertical: 2 },
  custChip: {
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20,
    borderWidth: 1.5, borderColor: '#e2e8f0', backgroundColor: '#f8fafc',
    marginRight: 8,
  },
  custChipActive:    { borderColor: '#2563eb', backgroundColor: '#eff6ff' },
  custChipText:      { fontSize: 13, fontWeight: '600', color: '#64748b' },
  custChipTextActive:{ color: '#2563eb', fontWeight: '800' },

  footer: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 20, paddingTop: 14, gap: 10,
    borderTopWidth: 1, borderTopColor: '#f1f5f9',
  },
  deleteBtn: {
    paddingHorizontal: 16, paddingVertical: 11, borderRadius: 10,
    backgroundColor: '#fee2e2', borderWidth: 1, borderColor: '#fca5a5',
  },
  deleteBtnText: { fontSize: 13, fontWeight: '700', color: '#b91c1c' },
  cancelBtn: {
    flex: 1, paddingVertical: 13, borderRadius: 10,
    backgroundColor: '#f1f5f9', alignItems: 'center',
    borderWidth: 1, borderColor: '#e2e8f0',
  },
  cancelBtnText: { fontSize: 14, fontWeight: '700', color: '#475569' },
  saveBtn: {
    flex: 2, paddingVertical: 13, borderRadius: 10,
    backgroundColor: '#1e3a5f', alignItems: 'center',
  },
  saveBtnDisabled: { backgroundColor: '#94a3b8' },
  saveBtnText: { fontSize: 14, fontWeight: '800', color: '#ffd700' },
});

export default ScheduleInputModal;
