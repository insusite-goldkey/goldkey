'use strict';
/**
 * src/screens/OtpAuthScreen.js — Goldkey AI Masters 2026
 *
 * 2단계 인증 화면:
 *   STAGE 1 — 이름 + 연락처 끝 4자리 입력 → personId 조회 (Supabase)
 *   STAGE 2 — Google Authenticator 6자리 입력 → verifyOTP 서버 검증
 *
 * 인증 성공 시 onSuccess(personId, personName) 콜백 호출 → App.js에서 화면 전환.
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { verifyOtp }                 from '../services/otpService';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '../config';

// ── 상수 ─────────────────────────────────────────────────────────────────────
const MAX_ATTEMPTS = 5;

/**
 * Supabase gk_people 테이블에서 이름 + 연락처 끝 4자리로 person 검색.
 * @param {string} name
 * @param {string} contactTail - 연락처 끝 4자리
 * @returns {Promise<{ id: string, name: string, contact: string }|null>}
 */
async function findPerson(name, contactTail) {
  try {
    // Supabase REST API 직접 호출 (supabase-js 없어도 동작)
    const encodedName = encodeURIComponent(`%${name.trim()}%`);
    const query = `name=ilike.${encodedName}`;
    const resp = await fetch(
      `${SUPABASE_URL}/rest/v1/gk_people?${query}&select=person_id,name,contact`,
      {
        headers: {
          apikey:        SUPABASE_ANON_KEY,
          Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        },
      },
    );
    console.log('[findPerson] status:', resp.status, resp.ok);
    if (!resp.ok) {
      const errText = await resp.text();
      console.log('[findPerson] error body:', errText);
      return null;
    }
    const rows = await resp.json();
    console.log('[findPerson] rows:', JSON.stringify(rows));
    const tail  = contactTail.replace(/\D/g, '').slice(-4);
    console.log('[findPerson] tail:', tail);
    const match = (rows || []).find((r) =>
      (r.contact || '').replace(/\D/g, '').endsWith(tail),
    );
    console.log('[findPerson] match:', JSON.stringify(match));
    return match || null;
  } catch (e) {
    console.log('[findPerson] exception:', e?.message);
    return null;
  }
}

// ── 컴포넌트 ─────────────────────────────────────────────────────────────────
/**
 * @param {{ onSuccess: (personId: string, personName: string) => void }} props
 */
export default function OtpAuthScreen({ onSuccess }) {
  // ── 스테이지 상태 ─────────────────────────────────────────────────────────
  const [stage, setStage]           = useState('lookup'); // 'lookup' | 'totp'
  const [person, setPerson]         = useState(null);

  // ── 폼 값 ─────────────────────────────────────────────────────────────────
  const [name, setName]             = useState('');
  const [contactTail, setContactTail] = useState('');
  const [otpToken, setOtpToken]     = useState('');

  // ── UI 상태 ───────────────────────────────────────────────────────────────
  const [loading, setLoading]       = useState(false);
  const [attempts, setAttempts]     = useState(0);

  const otpInputRef = useRef(null);

  // ────────────────────────────────────────────────────────────────────────
  // STAGE 1: 이름 + 연락처 조회
  // ────────────────────────────────────────────────────────────────────────
  const handleLookup = useCallback(async () => {
    console.log('[handleLookup] called, name:', name, 'contactTail:', contactTail);
    const trimName    = name.trim();
    const trimContact = contactTail.replace(/\D/g, '').slice(-4);

    if (!trimName) {
      Alert.alert('입력 오류', '이름을 입력해 주세요.');
      return;
    }
    if (trimContact.length !== 4) {
      Alert.alert('입력 오류', '연락처 끝 4자리를 입력해 주세요.');
      return;
    }

    setLoading(true);
    try {
      const found = await findPerson(trimName, trimContact);
      if (!found) {
        Alert.alert(
          '⚠️ 조회 실패',
          '일치하는 고객 정보를 찾을 수 없습니다.\n이름 또는 연락처를 다시 확인해 주세요.',
          [{ text: '확인' }],
        );
        return;
      }
      setPerson(found);
      setStage('totp');
      // 자동 포커스
      setTimeout(() => otpInputRef.current?.focus(), 200);
    } catch (e) {
      Alert.alert('오류', `조회 중 오류가 발생했습니다: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [name, contactTail]);

  // ────────────────────────────────────────────────────────────────────────
  // STAGE 2: TOTP 검증
  // ────────────────────────────────────────────────────────────────────────
  const handleVerify = useCallback(async () => {
    const trimToken = otpToken.trim();
    console.log('[handleVerify] called, token:', trimToken, 'person_id:', person?.person_id);

    if (!/^\d{6}$/.test(trimToken)) {
      Alert.alert('입력 오류', '인증 앱에서 보이는 6자리 숫자를 입력해 주세요.');
      return;
    }
    if (attempts >= MAX_ATTEMPTS) {
      Alert.alert(
        '⛔ 잠금',
        `시도 횟수(${MAX_ATTEMPTS}회)를 초과했습니다.\n처음부터 다시 시작해 주세요.`,
        [{ text: '다시 시작', onPress: _resetAll }],
      );
      return;
    }

    setLoading(true);
    try {
      const result = await verifyOtp(person.person_id, trimToken);
      console.log('[handleVerify] result:', JSON.stringify(result));

      if (result.valid) {
        // ── 인증 성공 ──────────────────────────────────────────────────
        Alert.alert(
          '✅ 인증 완료',
          `${person.name}님, 환영합니다!`,
          [{
            text: '입장',
            onPress: () => onSuccess(person.person_id, person.name),
          }],
        );
      } else {
        // ── 인증 실패 — 서버 message 그대로 표시 ──────────────────────
        const newAttempts = attempts + 1;
        setAttempts(newAttempts);
        setOtpToken('');

        if (newAttempts >= MAX_ATTEMPTS) {
          Alert.alert(
            '⛔ 인증 잠금',
            `${result.message}\n\n시도 횟수를 초과했습니다. 처음부터 다시 시작해 주세요.`,
            [{ text: '다시 시작', onPress: _resetAll }],
          );
        } else {
          Alert.alert('❌ 인증 실패', result.message, [{ text: '다시 입력' }]);
        }
      }
    } catch (e) {
      Alert.alert('오류', `인증 중 문제가 발생했습니다: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [otpToken, person, attempts, onSuccess]);

  // ── 전체 초기화 ────────────────────────────────────────────────────────
  const _resetAll = useCallback(() => {
    setStage('lookup');
    setPerson(null);
    setName('');
    setContactTail('');
    setOtpToken('');
    setAttempts(0);
  }, []);

  // ── 뒤로가기 (STAGE 2 → 1) ─────────────────────────────────────────────
  const handleBack = useCallback(() => {
    setStage('lookup');
    setOtpToken('');
    setAttempts(0);
  }, []);

  // ────────────────────────────────────────────────────────────────────────
  // 렌더
  // ────────────────────────────────────────────────────────────────────────
  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        {/* 헤더 */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>🔐 Goldkey AI Masters 2026</Text>
          <Text style={styles.headerSub}>고객 본인 확인 — TOTP (RFC 6238)</Text>
        </View>

        {/* 스테이지 인디케이터 */}
        <View style={styles.stepsRow}>
          <StepDot active={stage === 'lookup'} done={stage === 'totp'} label="1 조회" />
          <View style={styles.stepLine} />
          <StepDot active={stage === 'totp'}   done={false}            label="2 인증" />
        </View>

        {/* ══════════════════════════════════════════════════════
            STAGE 1 — 이름 + 연락처
        ══════════════════════════════════════════════════════ */}
        {stage === 'lookup' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>등록된 고객 정보로 조회합니다</Text>
            <Text style={styles.label}>이름</Text>
            <TextInput
              style={styles.input}
              placeholder="예) 홍길동"
              placeholderTextColor="#9ca3af"
              value={name}
              onChangeText={setName}
              autoCorrect={false}
              returnKeyType="next"
              editable={!loading}
            />
            <Text style={styles.label}>연락처 끝 4자리</Text>
            <TextInput
              style={styles.input}
              placeholder="예) 1234"
              placeholderTextColor="#9ca3af"
              value={contactTail}
              onChangeText={(v) => setContactTail(v.replace(/\D/g, '').slice(0, 4))}
              keyboardType="number-pad"
              maxLength={4}
              returnKeyType="done"
              onSubmitEditing={handleLookup}
              editable={!loading}
            />
            <TouchableOpacity
              style={[styles.btn, loading && styles.btnDisabled]}
              onPress={handleLookup}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading
                ? <ActivityIndicator color="#fff" />
                : <Text style={styles.btnText}>🔍 조회</Text>
              }
            </TouchableOpacity>
          </View>
        )}

        {/* ══════════════════════════════════════════════════════
            STAGE 2 — TOTP 6자리 입력
        ══════════════════════════════════════════════════════ */}
        {stage === 'totp' && person && (
          <View style={styles.card}>
            {/* 인물 확인 배지 */}
            <View style={styles.personBadge}>
              <Text style={styles.personBadgeText}>
                👤 {person.name} 님으로 확인되었습니다
              </Text>
            </View>

            <Text style={styles.cardTitle}>Google Authenticator 앱을 열어{'\n'}6자리 코드를 입력하세요</Text>

            <Text style={styles.guideText}>
              ⏱ 코드는 30초마다 갱신됩니다.{'\n'}
              앱에 표시된 번호를 그대로 입력하세요.
            </Text>

            <Text style={styles.label}>TOTP 6자리</Text>
            <TextInput
              ref={otpInputRef}
              style={[styles.input, styles.inputOtp]}
              placeholder="예) 123456"
              placeholderTextColor="#9ca3af"
              value={otpToken}
              onChangeText={(v) => setOtpToken(v.replace(/\D/g, '').slice(0, 6))}
              keyboardType="number-pad"
              maxLength={6}
              returnKeyType="done"
              onSubmitEditing={handleVerify}
              editable={!loading}
            />

            {attempts > 0 && (
              <Text style={styles.attemptsText}>
                시도 횟수: {attempts} / {MAX_ATTEMPTS}
              </Text>
            )}

            <TouchableOpacity
              style={[styles.btn, loading && styles.btnDisabled]}
              onPress={handleVerify}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading
                ? <ActivityIndicator color="#fff" />
                : <Text style={styles.btnText}>✅ 인증 확인</Text>
              }
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.btnBack}
              onPress={handleBack}
              disabled={loading}
              activeOpacity={0.7}
            >
              <Text style={styles.btnBackText}>← 뒤로</Text>
            </TouchableOpacity>

            {/* Google Authenticator 미등록 안내 */}
            <View style={styles.infoBox}>
              <Text style={styles.infoBoxTitle}>🔑 처음 등록하는 경우</Text>
              <Text style={styles.infoBoxText}>
                1. Google Authenticator 앱 설치{'\n'}
                2. <Text style={styles.bold}>+</Text> → <Text style={styles.bold}>키 직접 입력</Text>{'\n'}
                3. 계정 이름: <Text style={styles.mono}>{person.name}</Text>{'\n'}
                4. 유형: <Text style={styles.bold}>시간 기반</Text> 선택{'\n'}
                5. Secret 키는 담당 설계사에게 문의하세요.
              </Text>
            </View>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ── 스텝 닷 컴포넌트 ──────────────────────────────────────────────────────────
function StepDot({ active, done, label }) {
  return (
    <View style={styles.stepDotWrapper}>
      <View style={[
        styles.stepDot,
        active && styles.stepDotActive,
        done   && styles.stepDotDone,
      ]}>
        <Text style={[
          styles.stepDotText,
          (active || done) && styles.stepDotTextActive,
        ]}>
          {done ? '✓' : label[0]}
        </Text>
      </View>
      <Text style={[styles.stepLabel, active && styles.stepLabelActive]}>
        {label}
      </Text>
    </View>
  );
}

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  flex:          { flex: 1, backgroundColor: '#f8fafc' },
  container:     { flexGrow: 1, padding: 20, paddingTop: 48 },

  header:        { alignItems: 'center', marginBottom: 24 },
  headerTitle:   { fontSize: 20, fontWeight: '900', color: '#1d4ed8' },
  headerSub:     { fontSize: 13, color: '#6b7280', marginTop: 4 },

  stepsRow:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginBottom: 24 },
  stepDotWrapper:{ alignItems: 'center', gap: 4 },
  stepDot:       {
    width: 36, height: 36, borderRadius: 18,
    borderWidth: 2, borderColor: '#d1d5db',
    backgroundColor: '#ffffff',
    alignItems: 'center', justifyContent: 'center',
  },
  stepDotActive: { borderColor: '#1d4ed8', backgroundColor: '#1d4ed8' },
  stepDotDone:   { borderColor: '#16a34a', backgroundColor: '#16a34a' },
  stepDotText:   { fontSize: 14, fontWeight: '700', color: '#9ca3af' },
  stepDotTextActive: { color: '#ffffff' },
  stepLine:      { width: 48, height: 2, backgroundColor: '#e5e7eb', marginHorizontal: 8 },
  stepLabel:     { fontSize: 11, color: '#6b7280', marginTop: 4 },
  stepLabelActive: { color: '#1d4ed8', fontWeight: '700' },

  card: {
    backgroundColor: '#ffffff',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#dbeafe',
    borderStyle: 'dashed',
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardTitle:     { fontSize: 15, fontWeight: '700', color: '#1e293b', marginBottom: 16, lineHeight: 22 },

  label:         { fontSize: 13, fontWeight: '600', color: '#374151', marginBottom: 6, marginTop: 12 },
  input: {
    height: 48, borderWidth: 1.5, borderColor: '#d1d5db', borderRadius: 10,
    paddingHorizontal: 14, fontSize: 16, color: '#111827', backgroundColor: '#f9fafb',
  },
  inputOtp: {
    fontSize: 24, fontWeight: '900', textAlign: 'center',
    letterSpacing: 8, color: '#1d4ed8',
  },

  btn: {
    height: 50, backgroundColor: '#1d4ed8', borderRadius: 12,
    alignItems: 'center', justifyContent: 'center', marginTop: 20,
  },
  btnDisabled:   { opacity: 0.55 },
  btnText:       { fontSize: 16, fontWeight: '900', color: '#ffffff' },

  btnBack: {
    height: 40, alignItems: 'center', justifyContent: 'center', marginTop: 10,
  },
  btnBackText:   { fontSize: 14, color: '#6b7280' },

  personBadge: {
    backgroundColor: '#f0fdf4', borderWidth: 1, borderColor: '#86efac',
    borderRadius: 8, padding: 10, marginBottom: 16,
  },
  personBadgeText: { fontSize: 14, fontWeight: '700', color: '#15803d' },

  guideText:     { fontSize: 13, color: '#6b7280', marginBottom: 8, lineHeight: 20 },
  attemptsText:  { fontSize: 12, color: '#dc2626', marginTop: 8, textAlign: 'right' },

  infoBox: {
    marginTop: 20, backgroundColor: '#eff6ff',
    borderWidth: 1, borderColor: '#93c5fd', borderStyle: 'dashed',
    borderRadius: 10, padding: 14,
  },
  infoBoxTitle:  { fontSize: 13, fontWeight: '700', color: '#1d4ed8', marginBottom: 8 },
  infoBoxText:   { fontSize: 12, color: '#374151', lineHeight: 20 },
  bold:          { fontWeight: '700' },
  mono:          { fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace', fontSize: 12 },
});
