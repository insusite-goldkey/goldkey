/**
 * MedicalScanResultView — 제3장 권한별 맞춤형 듀얼뷰
 *
 * ┌ 뷰 모드 ────────────────────────────────────────────────────┐
 * │  AGENT (설계사): KCD코드·장해율·수술명·업셀링 포인트 강조     │
 * │                  [일정 추가] [카톡 멘트 복사] 버튼 연동       │
 * │  CLIENT (고객): 전문용어 배제, 예상 수령금 차트, 안심 요약    │
 * └────────────────────────────────────────────────────────────┘
 *
 * SSOT 동기화:
 *   useCustomerStore.activeScanId 구독 → 스캔 결과 한 곳에서 관리
 *   [일정 추가] → openScheduleModal(customerId) → 메인 달력 즉시 반영
 */

import React, { useState } from 'react';
import {
  Alert,
  Clipboard,
  SafeAreaView,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  useCustomerStore,
  selScan,
  selCustomer,
} from '../store/customerStore';

// ── 문서 유형 레이블 ──────────────────────────────────────────────────────────
const DOC_TYPE_LABEL = {
  diagnosis:           { label: '진단서',       color: '#3b82f6', bg: '#dbeafe' },
  surgery:             { label: '수술확인서',    color: '#ef4444', bg: '#fee2e2' },
  disability:          { label: '장해진단서',    color: '#f59e0b', bg: '#fef3c7' },
  medical_certificate: { label: '진료확인서',    color: '#22c55e', bg: '#dcfce7' },
  other:               { label: '기타문서',      color: '#6b7280', bg: '#f3f4f6' },
};

// ── 뷰 모드 상수 ──────────────────────────────────────────────────────────────
const VIEW_MODE = { AGENT: 'agent', CLIENT: 'client' };

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
const MedicalScanResultView = () => {
  const activeScanId      = useCustomerStore((s) => s.activeScanId);
  const scan              = useCustomerStore(selScan(activeScanId));
  const customer          = useCustomerStore(selCustomer(scan?.customerId));
  const closeScanView     = useCustomerStore((s) => s.closeScanView);
  const openScheduleModal = useCustomerStore((s) => s.openScheduleModal);
  const removeScanResult  = useCustomerStore((s) => s.removeScanResult);

  const [viewMode, setViewMode] = useState(VIEW_MODE.AGENT);

  if (!scan || !scan.analysis) return null;

  const { analysis, docType, scannedAt, status } = scan;
  const docMeta = DOC_TYPE_LABEL[docType] || DOC_TYPE_LABEL.other;
  const custName = customer?.name || '고객';

  // ── 삭제 — 2중 확인 필수 ─────────────────────────────────────────────────
  const handleDelete = () => {
    Alert.alert(
      '⚠️ 스캔 결과 삭제',
      `"${custName}" 고객의 스캔 결과를 영구 삭제합니다.\n삭제 후 복구가 불가능합니다. 계속하시겠습니까?`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제 확인',
          style: 'destructive',
          onPress: () => {
            // 2차 확인
            Alert.alert(
              '최종 확인',
              '정말로 삭제하시겠습니까? 이 작업은 되돌릴 수 없으며 감사 로그에 기록됩니다.',
              [
                { text: '취소', style: 'cancel' },
                {
                  text: '최종 삭제',
                  style: 'destructive',
                  onPress: () => {
                    removeScanResult(activeScanId, 'AGENT_ID'); // TODO: 실제 agentId 주입
                    closeScanView();
                  },
                },
              ],
            );
          },
        },
      ],
    );
  };

  // ── 카톡 멘트 복사 ─────────────────────────────────────────────────────────
  const handleKakao = async () => {
    const script = analysis.kakaoScript || '';
    try {
      await Share.share({ message: script, title: '카카오톡 상담 멘트' });
    } catch {
      Clipboard.setString(script);
      Alert.alert('복사 완료', '카톡 멘트가 클립보드에 복사되었습니다.');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* ── 헤더 ── */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={closeScanView} style={styles.backBtn}>
          <Text style={styles.backBtnText}>← 뒤로</Text>
        </TouchableOpacity>
        <Text style={styles.topBarTitle} numberOfLines={1}>
          {custName} · 스캔 결과
        </Text>
        <TouchableOpacity onPress={handleDelete} style={styles.deleteTopBtn}>
          <Text style={styles.deleteTopBtnText}>삭제</Text>
        </TouchableOpacity>
      </View>

      {/* ── 뷰 모드 토글 ── */}
      <View style={styles.modeRow}>
        {[
          { key: VIEW_MODE.AGENT,  label: '🔬 설계사 뷰' },
          { key: VIEW_MODE.CLIENT, label: '😊 고객 뷰' },
        ].map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            onPress={() => setViewMode(key)}
            style={[styles.modeBtn, viewMode === key && styles.modeBtnActive]}
          >
            <Text style={[styles.modeBtnText, viewMode === key && styles.modeBtnTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* ── 문서 정보 헤더 카드 ── */}
        <View style={styles.docCard}>
          <View style={styles.docCardRow}>
            <View style={[styles.docTypeBadge, { backgroundColor: docMeta.bg }]}>
              <Text style={[styles.docTypeBadgeText, { color: docMeta.color }]}>
                {docMeta.label}
              </Text>
            </View>
            <View style={[styles.statusBadge, status === 'done' ? styles.statusDone : styles.statusPending]}>
              <Text style={styles.statusText}>
                {status === 'done' ? '✅ 분석완료' : status === 'error' ? '⚠️ 오류' : '⏳ 분석중'}
              </Text>
            </View>
          </View>
          <Text style={styles.docCardName}>{custName}</Text>
          <Text style={styles.docCardDate}>
            스캔일시: {new Date(scannedAt).toLocaleString('ko-KR')}
            {scan.masked ? '  ·  🛡️ PII 마스킹 완료' : ''}
          </Text>
        </View>

        {/* ══════════════════════════════════════════════════════ */}
        {/* ── 설계사 뷰 ── */}
        {/* ══════════════════════════════════════════════════════ */}
        {viewMode === VIEW_MODE.AGENT && (
          <>
            {/* AI 정밀 요약 */}
            <SectionCard title="🔬 AI 정밀 분석 요약" accent="#1e3a5f">
              <Text style={styles.summaryText}>{analysis.summary || '—'}</Text>
            </SectionCard>

            {/* KCD 코드 */}
            {(analysis.kcdCodes || []).length > 0 && (
              <SectionCard title="🏷 KCD 질병분류 코드" accent="#1e3a5f">
                {analysis.kcdCodes.map((k, i) => (
                  <View key={i} style={styles.kcdRow}>
                    <View style={styles.kcdBadge}>
                      <Text style={styles.kcdCode}>{k.code}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.kcdName}>{k.name}</Text>
                      {!!k.note && <Text style={styles.kcdNote}>{k.note}</Text>}
                    </View>
                  </View>
                ))}
              </SectionCard>
            )}

            {/* 장해율 */}
            {analysis.disabilityRate != null && (
              <SectionCard title="📐 장해율" accent="#f59e0b">
                <View style={styles.disabilityWrap}>
                  <Text style={styles.disabilityRate}>
                    {analysis.disabilityRate}%
                  </Text>
                  <Text style={styles.disabilityLabel}>맥브라이드/ABI 판정 기준</Text>
                </View>
              </SectionCard>
            )}

            {/* 수술 목록 */}
            {(analysis.surgeries || []).length > 0 && (
              <SectionCard title="🔪 수술 이력" accent="#ef4444">
                {analysis.surgeries.map((s, i) => (
                  <View key={i} style={styles.surgeryRow}>
                    <View style={styles.surgeryDot} />
                    <Text style={styles.surgeryText}>{s}</Text>
                  </View>
                ))}
              </SectionCard>
            )}

            {/* AI 업셀링 추천 포인트 */}
            {(analysis.upsellPoints || []).length > 0 && (
              <SectionCard title="⭐ AI 업셀링 추천 포인트" accent="#7c3aed">
                {analysis.upsellPoints.map((p, i) => (
                  <View key={i} style={styles.upsellRow}>
                    <View style={styles.upsellBadge}>
                      <Text style={styles.upsellNum}>{i + 1}</Text>
                    </View>
                    <Text style={styles.upsellText}>{p}</Text>
                  </View>
                ))}
              </SectionCard>
            )}

            {/* 설계사 액션 버튼 */}
            <View style={styles.actionRow}>
              <TouchableOpacity
                style={styles.actionBtnPrimary}
                onPress={() => openScheduleModal(scan.customerId)}
              >
                <Text style={styles.actionBtnPrimaryText}>📅 이 고객 일정 추가</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionBtnSecondary}
                onPress={handleKakao}
              >
                <Text style={styles.actionBtnSecondaryText}>💬 카톡 멘트</Text>
              </TouchableOpacity>
            </View>
          </>
        )}

        {/* ══════════════════════════════════════════════════════ */}
        {/* ── 고객 뷰 ── */}
        {/* ══════════════════════════════════════════════════════ */}
        {viewMode === VIEW_MODE.CLIENT && (
          <>
            {/* 안심 요약 */}
            <SectionCard title="😊 분석 결과 안내" accent="#22c55e">
              <Text style={styles.clientSummaryText}>
                {analysis.clientSummary || '분석이 완료되었습니다. 담당 설계사에게 문의해 주세요.'}
              </Text>
            </SectionCard>

            {/* 예상 수령 보험금 */}
            {analysis.expectedPayout > 0 && (
              <SectionCard title="💰 예상 수령 보험금" accent="#1e3a5f">
                <View style={styles.payoutWrap}>
                  <Text style={styles.payoutLabel}>예상 수령액</Text>
                  <Text style={styles.payoutAmount}>
                    {analysis.expectedPayout.toLocaleString('ko-KR')}
                    <Text style={styles.payoutUnit}> 만원</Text>
                  </Text>
                  <Text style={styles.payoutNote}>
                    ※ 실제 수령액은 보험사 심사 결과에 따라 다를 수 있습니다.
                  </Text>
                </View>
              </SectionCard>
            )}

            {/* 간단 바 차트 — 보험금 직관적 표시 */}
            {analysis.expectedPayout > 0 && (
              <SectionCard title="📊 보험금 구성 미리보기" accent="#3b82f6">
                <PayoutChart payout={analysis.expectedPayout} />
              </SectionCard>
            )}

            {/* 안심 메시지 */}
            <View style={styles.reassureCard}>
              <Text style={styles.reassureIcon}>🛡️</Text>
              <Text style={styles.reassureText}>
                고객님의 개인정보는 철저히 보호됩니다.{'\n'}
                주민등록번호 뒷자리, 상세 주소는 자동으로 가려져 저장됩니다.
              </Text>
            </View>
          </>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
};

// ── 섹션 카드 래퍼 ────────────────────────────────────────────────────────────
const SectionCard = ({ title, accent, children }) => (
  <View style={[styles.sectionCard, { borderLeftColor: accent }]}>
    <Text style={[styles.sectionCardTitle, { color: accent }]}>{title}</Text>
    {children}
  </View>
);

// ── 간단 바 차트 ──────────────────────────────────────────────────────────────
const CHART_ITEMS = [
  { label: '수술비',    ratio: 0.45, color: '#3b82f6' },
  { label: '입원비',    ratio: 0.30, color: '#22c55e' },
  { label: '진단비',    ratio: 0.15, color: '#f59e0b' },
  { label: '기타',      ratio: 0.10, color: '#94a3b8' },
];

const PayoutChart = ({ payout }) => (
  <View style={styles.chartWrap}>
    {CHART_ITEMS.map((item) => {
      const amt = Math.round(payout * item.ratio);
      return (
        <View key={item.label} style={styles.chartRow}>
          <Text style={styles.chartLabel}>{item.label}</Text>
          <View style={styles.chartBarTrack}>
            <View style={[styles.chartBarFill, {
              width: `${item.ratio * 100}%`,
              backgroundColor: item.color,
            }]} />
          </View>
          <Text style={[styles.chartAmt, { color: item.color }]}>
            {amt.toLocaleString('ko-KR')}만
          </Text>
        </View>
      );
    })}
  </View>
);

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f8fafc' },

  topBar: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 16, paddingTop: 14, paddingBottom: 14, gap: 10,
  },
  backBtn:          { paddingHorizontal: 4 },
  backBtnText:      { fontSize: 14, fontWeight: '700', color: '#93c5fd' },
  topBarTitle:      { flex: 1, fontSize: 15, fontWeight: '900', color: '#ffffff', textAlign: 'center' },
  deleteTopBtn:     { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6, backgroundColor: 'rgba(239,68,68,0.22)' },
  deleteTopBtnText: { fontSize: 12, fontWeight: '700', color: '#fca5a5' },

  // 뷰 모드 토글
  modeRow: {
    flexDirection: 'row', backgroundColor: '#ffffff',
    paddingHorizontal: 16, paddingVertical: 10, gap: 10,
    borderBottomWidth: 1, borderBottomColor: '#e2e8f0',
  },
  modeBtn: {
    flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center',
    backgroundColor: '#f1f5f9', borderWidth: 1.5, borderColor: '#e2e8f0',
  },
  modeBtnActive:     { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  modeBtnText:       { fontSize: 13, fontWeight: '700', color: '#64748b' },
  modeBtnTextActive: { color: '#ffd700', fontWeight: '900' },

  scroll: { flex: 1, paddingHorizontal: 16, paddingTop: 12 },

  // 문서 정보 헤더
  docCard: {
    backgroundColor: '#ffffff', borderRadius: 14, padding: 16,
    marginBottom: 12, borderWidth: 1.5, borderColor: '#e2e8f0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06, shadowRadius: 6, elevation: 3,
  },
  docCardRow:       { flexDirection: 'row', gap: 8, marginBottom: 10 },
  docTypeBadge:     { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20 },
  docTypeBadgeText: { fontSize: 12, fontWeight: '800' },
  statusBadge:      { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 20 },
  statusDone:       { backgroundColor: '#dcfce7' },
  statusPending:    { backgroundColor: '#fef9c3' },
  statusText:       { fontSize: 11, fontWeight: '700', color: '#374151' },
  docCardName:      { fontSize: 18, fontWeight: '900', color: '#1e293b', marginBottom: 4 },
  docCardDate:      { fontSize: 11, color: '#94a3b8' },

  // 섹션 카드
  sectionCard: {
    backgroundColor: '#ffffff', borderRadius: 14, padding: 16,
    marginBottom: 12, borderLeftWidth: 4, borderWidth: 1, borderColor: '#e2e8f0',
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05, shadowRadius: 5, elevation: 2,
  },
  sectionCardTitle: { fontSize: 13, fontWeight: '900', marginBottom: 12, letterSpacing: 0.3 },

  summaryText:      { fontSize: 14, color: '#374151', lineHeight: 22 },

  // KCD
  kcdRow:   { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 10 },
  kcdBadge: { backgroundColor: '#dbeafe', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 8, flexShrink: 0 },
  kcdCode:  { fontSize: 13, fontWeight: '900', color: '#1d4ed8' },
  kcdName:  { fontSize: 14, fontWeight: '700', color: '#1e293b' },
  kcdNote:  { fontSize: 11, color: '#3b82f6', marginTop: 2 },

  // 장해율
  disabilityWrap:  { alignItems: 'center', paddingVertical: 8 },
  disabilityRate:  { fontSize: 48, fontWeight: '900', color: '#1e3a5f' },
  disabilityLabel: { fontSize: 12, color: '#64748b', marginTop: 4 },

  // 수술
  surgeryRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  surgeryDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#ef4444', flexShrink: 0 },
  surgeryText:{ fontSize: 14, fontWeight: '600', color: '#1e293b' },

  // 업셀링
  upsellRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 10 },
  upsellBadge: {
    width: 24, height: 24, borderRadius: 12,
    backgroundColor: '#7c3aed', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  upsellNum:  { fontSize: 11, fontWeight: '900', color: '#ffffff' },
  upsellText: { flex: 1, fontSize: 13, color: '#374151', lineHeight: 20 },

  // 액션 버튼
  actionRow: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  actionBtnPrimary: {
    flex: 2, backgroundColor: '#1e3a5f', borderRadius: 12,
    paddingVertical: 14, alignItems: 'center',
    shadowColor: '#1e3a5f', shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25, shadowRadius: 6, elevation: 4,
  },
  actionBtnPrimaryText:   { fontSize: 14, fontWeight: '900', color: '#ffd700' },
  actionBtnSecondary: {
    flex: 1, backgroundColor: '#f0fdf4', borderRadius: 12,
    paddingVertical: 14, alignItems: 'center',
    borderWidth: 1.5, borderColor: '#bbf7d0',
  },
  actionBtnSecondaryText: { fontSize: 13, fontWeight: '800', color: '#15803d' },

  // 고객뷰 — 안심 요약
  clientSummaryText: { fontSize: 15, color: '#374151', lineHeight: 24, fontWeight: '500' },

  // 예상 수령금
  payoutWrap:   { alignItems: 'center', paddingVertical: 8 },
  payoutLabel:  { fontSize: 13, color: '#64748b', marginBottom: 6 },
  payoutAmount: { fontSize: 44, fontWeight: '900', color: '#1e3a5f' },
  payoutUnit:   { fontSize: 18, fontWeight: '700' },
  payoutNote:   { fontSize: 11, color: '#94a3b8', marginTop: 8, textAlign: 'center' },

  // 바 차트
  chartWrap: { gap: 10 },
  chartRow:  { flexDirection: 'row', alignItems: 'center', gap: 10 },
  chartLabel:{ width: 36, fontSize: 11, fontWeight: '700', color: '#374151', textAlign: 'right' },
  chartBarTrack: {
    flex: 1, height: 12, backgroundColor: '#f1f5f9',
    borderRadius: 6, overflow: 'hidden',
  },
  chartBarFill: { height: '100%', borderRadius: 6 },
  chartAmt: { width: 52, fontSize: 11, fontWeight: '700', textAlign: 'right' },

  // 안심 카드
  reassureCard: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 12,
    backgroundColor: '#f0fdf4', borderRadius: 12, padding: 16,
    borderWidth: 1, borderColor: '#bbf7d0', marginBottom: 12,
  },
  reassureIcon: { fontSize: 24 },
  reassureText: { flex: 1, fontSize: 13, color: '#166534', lineHeight: 20 },
});

export default MedicalScanResultView;
