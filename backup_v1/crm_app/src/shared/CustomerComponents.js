'use strict';
/**
 * src/shared/CustomerComponents.js — Goldkey AI Masters 2026
 *
 * [GP 마스터-그림자 원칙 §1] 공통 고객 UI 컴포넌트
 * 모 앱 구조가 바뀌면 이 파일만 수정하면 자 앱도 자동 반영된다.
 *
 * export:
 *   CustomerCard       — 고객 1행 카드 (FlatList renderItem용)
 *   CustomerListHeader — 검색 + 타이틀 헤더
 *   CustomerForm       — 고객 입력/수정 폼 (양방향 공통)
 *   TierBadge          — 관리 등급 배지
 *   StatusBadge        — 고객 상태 배지
 *   DeepLinkButton     — 모 앱으로 쏘는 딥링크 발사대 버튼
 */

import React, { useState, useCallback } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ActivityIndicator, Alert, Linking, ScrollView,
} from 'react-native';
import {
  MANAGEMENT_TIER_LABELS,
  CUSTOMER_STATUS_LABELS,
  PROSPECTING_STAGE_LABELS,
  createEmptyCustomer,
  buildMotherDeepLink,
} from './customerSchema';

// ── TierBadge ─────────────────────────────────────────────────────────────────
export function TierBadge({ tier }) {
  const t = MANAGEMENT_TIER_LABELS[tier] || MANAGEMENT_TIER_LABELS[3];
  return (
    <View style={[badgeStyles.base, { backgroundColor: t.bg, borderColor: t.color }]}>
      <Text style={[badgeStyles.text, { color: t.color }]}>{t.icon} {t.label}</Text>
    </View>
  );
}

// ── StatusBadge ───────────────────────────────────────────────────────────────
export function StatusBadge({ status }) {
  const s = CUSTOMER_STATUS_LABELS[status] || CUSTOMER_STATUS_LABELS['potential'];
  return (
    <View style={[badgeStyles.base, { backgroundColor: s.bg, borderColor: s.color }]}>
      <Text style={[badgeStyles.text, { color: s.color }]}>{s.label}</Text>
    </View>
  );
}

const badgeStyles = StyleSheet.create({
  base: {
    borderWidth: 1, borderStyle: 'dashed', borderRadius: 6,
    paddingHorizontal: 6, paddingVertical: 2, alignSelf: 'flex-start',
  },
  text: { fontSize: 11, fontWeight: '700' },
});

// ── CustomerCard ──────────────────────────────────────────────────────────────
/**
 * @param {{ customer: object, onPress: () => void,
 *           onSchedule?: () => void, showTier?: boolean }} props
 */
export function CustomerCard({ customer: c, onPress, onSchedule, showTier = true }) {
  return (
    <TouchableOpacity style={cardStyles.row} onPress={onPress} activeOpacity={0.75}>
      {/* 아바타 이니셜 */}
      <View style={[cardStyles.avatar, { backgroundColor: _tierColor(c.management_tier) }]}>
        <Text style={cardStyles.avatarText}>{(c.name || '?').charAt(0)}</Text>
      </View>

      {/* 정보 */}
      <View style={{ flex: 1 }}>
        <View style={cardStyles.nameRow}>
          <Text style={cardStyles.name}>{c.name}</Text>
          {c.is_favorite && <Text style={cardStyles.star}>★</Text>}
        </View>
        <Text style={cardStyles.sub} numberOfLines={1}>
          {[c.job, c.contact].filter(Boolean).join('  ·  ') || '정보 없음'}
        </Text>
        <View style={cardStyles.badgeRow}>
          {showTier && <TierBadge tier={c.management_tier} />}
          <StatusBadge status={c.status} />
        </View>
        {/* 만기 월 알림 */}
        {(c.auto_renewal_month || c.fire_renewal_month) && (
          <Text style={cardStyles.renewal}>
            🔔 만기: {[
              c.auto_renewal_month && `자동차 ${c.auto_renewal_month}월`,
              c.fire_renewal_month && `화재 ${c.fire_renewal_month}월`,
            ].filter(Boolean).join(' · ')}
          </Text>
        )}
      </View>

      {/* 액션 버튼 */}
      <View style={cardStyles.actions}>
        {onSchedule && (
          <TouchableOpacity
            style={cardStyles.schedBtn}
            onPress={onSchedule}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={cardStyles.schedBtnText}>📅</Text>
          </TouchableOpacity>
        )}
        <Text style={cardStyles.chevron}>›</Text>
      </View>
    </TouchableOpacity>
  );
}

function _tierColor(tier) {
  const map = { 1: '#fef3c7', 2: '#dbeafe', 3: '#f3f4f6' };
  return map[tier] || map[3];
}

const cardStyles = StyleSheet.create({
  row: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#ffffff',
    borderWidth: 1, borderStyle: 'dashed', borderColor: '#000000',
    borderRadius: 10, padding: 12, marginBottom: 8,
  },
  avatar: {
    width: 44, height: 44, borderRadius: 22,
    alignItems: 'center', justifyContent: 'center', marginRight: 12,
    borderWidth: 1, borderStyle: 'dashed', borderColor: '#000',
  },
  avatarText:  { fontSize: 18, fontWeight: '900', color: '#1e293b' },
  nameRow:     { flexDirection: 'row', alignItems: 'center', gap: 4 },
  name:        { fontSize: 15, fontWeight: '900', color: '#1e293b' },
  star:        { fontSize: 13, color: '#f59e0b' },
  sub:         { fontSize: 12, color: '#6b7280', marginTop: 2 },
  badgeRow:    { flexDirection: 'row', gap: 4, marginTop: 4 },
  renewal:     { fontSize: 11, color: '#d97706', marginTop: 3 },
  actions:     { alignItems: 'center', gap: 6, paddingLeft: 8 },
  schedBtn:    { padding: 4 },
  schedBtnText: { fontSize: 18 },
  chevron:     { fontSize: 20, color: '#94a3b8', fontWeight: '900' },
});

// ── CustomerListHeader ────────────────────────────────────────────────────────
/**
 * @param {{ totalCount: number, search: string, onSearch: (v: string) => void,
 *           onAdd: () => void }} props
 */
export function CustomerListHeader({ totalCount, search, onSearch, onAdd }) {
  return (
    <View style={listHStyles.wrap}>
      <View style={listHStyles.titleRow}>
        <Text style={listHStyles.title}>👥 담당 고객 목록</Text>
        <View style={listHStyles.right}>
          <Text style={listHStyles.count}>{totalCount}명</Text>
          {onAdd && (
            <TouchableOpacity style={listHStyles.addBtn} onPress={onAdd}>
              <Text style={listHStyles.addBtnText}>+ 고객 추가</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
      <TextInput
        style={listHStyles.input}
        value={search}
        onChangeText={onSearch}
        placeholder="이름 또는 연락처 검색..."
        placeholderTextColor="#94a3b8"
        clearButtonMode="while-editing"
      />
    </View>
  );
}

const listHStyles = StyleSheet.create({
  wrap:      { paddingBottom: 8 },
  titleRow:  { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  title:     { fontSize: 16, fontWeight: '900', color: '#1e293b' },
  right:     { flexDirection: 'row', alignItems: 'center', gap: 8 },
  count:     { fontSize: 13, color: '#6b7280' },
  addBtn:    {
    backgroundColor: '#1d4ed8', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 5,
  },
  addBtnText: { fontSize: 12, fontWeight: '700', color: '#ffffff' },
  input: {
    height: 40, borderWidth: 1.5, borderColor: '#000000', borderRadius: 8,
    paddingHorizontal: 12, fontSize: 14, color: '#111827', backgroundColor: '#f9fafb',
  },
});

// ── CustomerForm ──────────────────────────────────────────────────────────────
/**
 * [GP §2] 고객 정보 입력/수정 폼 — 모/자 앱 양방향 공통
 *
 * @param {{ initial?: object, agentId: string,
 *           onSave: (data: object) => Promise<void>,
 *           onCancel: () => void }} props
 */
export function CustomerForm({ initial, agentId, onSave, onCancel }) {
  const [form, setForm]       = useState(initial || createEmptyCustomer(agentId));
  const [saving, setSaving]   = useState(false);
  const [errors, setErrors]   = useState({});

  const set = useCallback((key, val) => {
    setForm((prev) => ({ ...prev, [key]: val }));
    setErrors((prev) => { const e = { ...prev }; delete e[key]; return e; });
  }, []);

  const handleSave = async () => {
    if (!form.name?.trim())    { setErrors({ name: '이름을 입력해 주세요.' });    return; }
    if (!form.contact?.trim()) { setErrors({ contact: '연락처를 입력해 주세요.' }); return; }
    setSaving(true);
    try {
      await onSave({ ...form, agent_id: agentId, updated_at: new Date().toISOString() });
    } catch (e) {
      Alert.alert('저장 오류', e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={formStyles.scroll} keyboardShouldPersistTaps="handled">
      <View style={formStyles.wrap}>
        <Text style={formStyles.title}>
          {initial?.person_id ? '✏️ 고객 정보 수정' : '➕ 신규 고객 등록'}
        </Text>

        {/* 필수 */}
        <FormField label="이름 *" error={errors.name}>
          <TextInput style={[formStyles.input, errors.name && formStyles.inputErr]}
            value={form.name} onChangeText={(v) => set('name', v)}
            placeholder="홍길동" placeholderTextColor="#9ca3af" />
        </FormField>

        <FormField label="연락처 *" error={errors.contact}>
          <TextInput style={[formStyles.input, errors.contact && formStyles.inputErr]}
            value={form.contact} onChangeText={(v) => set('contact', v)}
            placeholder="010-0000-0000" placeholderTextColor="#9ca3af"
            keyboardType="phone-pad" />
        </FormField>

        {/* 선택 */}
        <FormField label="직업">
          <TextInput style={formStyles.input} value={form.job || ''}
            onChangeText={(v) => set('job', v)}
            placeholder="회사원, 자영업 등" placeholderTextColor="#9ca3af" />
        </FormField>

        <FormField label="주소">
          <TextInput style={formStyles.input} value={form.address || ''}
            onChangeText={(v) => set('address', v)}
            placeholder="서울 강남구" placeholderTextColor="#9ca3af" />
        </FormField>

        <FormField label="자동차보험 만기월">
          <TextInput style={formStyles.input}
            value={form.auto_renewal_month ? String(form.auto_renewal_month) : ''}
            onChangeText={(v) => set('auto_renewal_month', parseInt(v) || null)}
            placeholder="1~12" placeholderTextColor="#9ca3af" keyboardType="number-pad" />
        </FormField>

        <FormField label="화재보험 만기월">
          <TextInput style={formStyles.input}
            value={form.fire_renewal_month ? String(form.fire_renewal_month) : ''}
            onChangeText={(v) => set('fire_renewal_month', parseInt(v) || null)}
            placeholder="1~12" placeholderTextColor="#9ca3af" keyboardType="number-pad" />
        </FormField>

        <FormField label="메모">
          <TextInput style={[formStyles.input, formStyles.inputMulti]}
            value={form.memo || ''} onChangeText={(v) => set('memo', v)}
            placeholder="상담 메모, 특이사항 등" placeholderTextColor="#9ca3af"
            multiline numberOfLines={3} />
        </FormField>

        {/* 관리 등급 선택 */}
        <FormField label="관리 등급">
          <View style={formStyles.optionRow}>
            {[1, 2, 3].map((tier) => {
              const t = MANAGEMENT_TIER_LABELS[tier];
              return (
                <TouchableOpacity
                  key={tier}
                  style={[formStyles.optionBtn,
                    form.management_tier === tier && { backgroundColor: t.bg, borderColor: t.color }]}
                  onPress={() => set('management_tier', tier)}
                >
                  <Text style={[formStyles.optionText,
                    form.management_tier === tier && { color: t.color, fontWeight: '900' }]}>
                    {t.icon} {t.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </FormField>

        {/* 버튼 */}
        <View style={formStyles.btnRow}>
          <TouchableOpacity style={formStyles.cancelBtn} onPress={onCancel} disabled={saving}>
            <Text style={formStyles.cancelText}>취소</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[formStyles.saveBtn, saving && formStyles.saveBtnDisabled]}
            onPress={handleSave} disabled={saving}>
            {saving
              ? <ActivityIndicator color="#fff" />
              : <Text style={formStyles.saveText}>💾 저장</Text>
            }
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

function FormField({ label, error, children }) {
  return (
    <View style={formStyles.field}>
      <Text style={formStyles.label}>{label}</Text>
      {children}
      {error && <Text style={formStyles.errorText}>{error}</Text>}
    </View>
  );
}

const formStyles = StyleSheet.create({
  scroll:      { flex: 1 },
  wrap:        { padding: 16 },
  title:       { fontSize: 18, fontWeight: '900', color: '#1e293b', marginBottom: 20 },
  field:       { marginBottom: 14 },
  label:       { fontSize: 13, fontWeight: '700', color: '#374151', marginBottom: 5 },
  input: {
    borderWidth: 1.5, borderColor: '#000000', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 10,
    fontSize: 15, color: '#111827', backgroundColor: '#f9fafb',
  },
  inputErr:    { borderColor: '#dc2626' },
  inputMulti:  { height: 80, textAlignVertical: 'top' },
  errorText:   { fontSize: 12, color: '#dc2626', marginTop: 4 },
  optionRow:   { flexDirection: 'row', gap: 8 },
  optionBtn: {
    flex: 1, paddingVertical: 8, alignItems: 'center',
    borderWidth: 1, borderStyle: 'dashed', borderColor: '#000', borderRadius: 8,
    backgroundColor: '#f9fafb',
  },
  optionText:  { fontSize: 13, color: '#374151' },
  btnRow:      { flexDirection: 'row', gap: 10, marginTop: 24 },
  cancelBtn: {
    flex: 1, height: 48, borderWidth: 1.5, borderColor: '#000',
    borderRadius: 10, alignItems: 'center', justifyContent: 'center',
  },
  cancelText:  { fontSize: 15, fontWeight: '700', color: '#374151' },
  saveBtn: {
    flex: 2, height: 48, backgroundColor: '#1d4ed8',
    borderRadius: 10, alignItems: 'center', justifyContent: 'center',
  },
  saveBtnDisabled: { opacity: 0.55 },
  saveText:    { fontSize: 15, fontWeight: '900', color: '#ffffff' },
});

// ── DeepLinkButton ────────────────────────────────────────────────────────────
/**
 * [GP §3] 모 앱으로 쏘는 딥링크 발사대 버튼
 *
 * @param {{ action: string, params?: object, label: string,
 *           icon?: string, style?: object }} props
 */
export function DeepLinkButton({ action, params = {}, label, icon = '🚀', style }) {
  const [loading, setLoading] = useState(false);

  const handlePress = async () => {
    setLoading(true);
    try {
      const url = buildMotherDeepLink(action, params);
      const ok  = await Linking.canOpenURL(url);
      if (ok) {
        await Linking.openURL(url);
      } else {
        Alert.alert('알림', 'Goldkey AI 앱을 설치해 주세요.');
      }
    } catch (e) {
      Alert.alert('오류', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <TouchableOpacity
      style={[deepStyles.btn, style]}
      onPress={handlePress}
      disabled={loading}
      activeOpacity={0.8}
    >
      {loading
        ? <ActivityIndicator color="#fff" size="small" />
        : <Text style={deepStyles.text}>{icon} {label}</Text>
      }
    </TouchableOpacity>
  );
}

const deepStyles = StyleSheet.create({
  btn: {
    height: 44, backgroundColor: '#1e3a8a',
    borderRadius: 10, flexDirection: 'row',
    alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: 16,
    borderWidth: 1, borderStyle: 'dashed', borderColor: '#93c5fd',
  },
  text: { fontSize: 14, fontWeight: '900', color: '#ffffff' },
});
