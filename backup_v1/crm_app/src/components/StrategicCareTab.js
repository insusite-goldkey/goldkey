/**
 * StrategicCareTab.js — [2차 라인] 전략 케어 & AI 리포트
 * 라이프사이클 타임라인 + 위험도 + AI 보장 분석 요약
 */
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { MANAGEMENT_TIER } from '../config';

function DdayBadge({ label, date }) {
  if (!date) return null;
  const target = new Date(date);
  const now    = new Date();
  target.setFullYear(now.getFullYear());
  if (target < now) target.setFullYear(now.getFullYear() + 1);
  const diff = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
  const urgent = diff <= 30;
  return (
    <View style={[styles.ddayBadge, urgent && styles.ddayBadgeUrgent]}>
      <Text style={[styles.ddayLabel, urgent && styles.ddayLabelUrgent]}>{label}</Text>
      <Text style={[styles.ddayVal, urgent && styles.ddayValUrgent]}>D-{diff}</Text>
    </View>
  );
}

function RiskLevel({ job, drivingStatus }) {
  let level = '저위험';
  let color  = '#16a34a';
  const highRiskJobs = ['건설', '운전', '어업', '광업', '화물', '소방', '경찰'];
  if (highRiskJobs.some((k) => (job || '').includes(k))) { level = '고위험'; color = '#dc2626'; }
  else if (drivingStatus === 'commercial' || drivingStatus === 'motorcycle') { level = '중위험'; color = '#d97706'; }
  return (
    <View style={[styles.riskBox, { borderColor: color }]}>
      <Text style={styles.riskLabel}>직업 위험도</Text>
      <Text style={[styles.riskLevel, { color }]}>{level}</Text>
      <Text style={styles.riskSub}>{job || '미등록'}{drivingStatus ? ` · ${drivingStatus}` : ''}</Text>
    </View>
  );
}

export default function StrategicCareTab({ person, scanResults = [], onViewReport }) {
  if (!person) return null;

  const tier     = MANAGEMENT_TIER[person.management_tier] || MANAGEMENT_TIER[3];
  const events   = person.lifecycle_events || [];
  const latestScan = scanResults[0] || null;

  return (
    <ScrollView style={styles.root} showsVerticalScrollIndicator={false}>
      <Text style={styles.sectionTitle}>💎 2차 라인 — 전략 케어</Text>

      {/* 관리 등급 + 핵심 포인트 */}
      <View style={styles.tierBox}>
        <View style={[styles.tierBadge, { backgroundColor: tier.bg }]}>
          <Text style={[styles.tierText, { color: tier.color }]}>{tier.label} 관리</Text>
        </View>
        {person.key_customer_note && (
          <Text style={styles.keyNote}>💡 {person.key_customer_note}</Text>
        )}
      </View>

      {/* 라이프사이클 타임라인 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>라이프사이클 이벤트</Text>
        <View style={styles.ddayRow}>
          {person.wedding_anniversary && (
            <DdayBadge label="결혼기념일" date={person.wedding_anniversary} />
          )}
          {events.length === 0 && !person.wedding_anniversary && (
            <Text style={styles.emptyText}>등록된 이벤트 없음</Text>
          )}
          {events.map((ev, i) => (
            <DdayBadge key={i} label={ev.type} date={ev.date} />
          ))}
        </View>
      </View>

      {/* 위험도 */}
      <RiskLevel job={person.job} drivingStatus={person.driving_status} />
      {person.risk_note && (
        <View style={styles.riskNote}>
          <Text style={styles.riskNoteText}>⚠️ {person.risk_note}</Text>
        </View>
      )}

      {/* AI 보장 분석 리포트 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>AI 보장 분석 리포트</Text>
        {latestScan ? (
          <>
            <Text style={styles.scanDate}>
              분석일: {latestScan.created_at?.slice(0, 10)}
            </Text>
            <Text style={styles.scanCompany}>
              {latestScan.insurance_co} · {latestScan.product_name}
            </Text>
            <TouchableOpacity
              style={styles.reportBtn}
              onPress={() => onViewReport && onViewReport(latestScan)}
            >
              <Text style={styles.reportBtnText}>리포트 전체 보기 →</Text>
            </TouchableOpacity>
          </>
        ) : (
          <Text style={styles.emptyText}>아직 분석 결과가 없습니다. 증권 스캔을 먼저 진행하세요.</Text>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:         { flex: 1, padding: 16 },
  sectionTitle: { fontSize: 15, fontWeight: '900', color: '#1e3a5f', marginBottom: 12 },
  tierBox:      { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  tierBadge:    { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  tierText:     { fontSize: 13, fontWeight: '700' },
  keyNote:      { fontSize: 12, color: '#374151', flex: 1 },
  card: {
    borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    borderRadius: 10, padding: 12, backgroundColor: '#f9fafb', marginBottom: 12,
  },
  cardTitle:  { fontSize: 12, fontWeight: '700', color: '#374151', marginBottom: 8 },
  ddayRow:    { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  ddayBadge: {
    borderWidth: 1, borderColor: '#93c5fd', backgroundColor: '#eff6ff',
    borderRadius: 8, padding: 8, alignItems: 'center', minWidth: 80,
  },
  ddayBadgeUrgent: { borderColor: '#fca5a5', backgroundColor: '#fff1f2' },
  ddayLabel:       { fontSize: 10, color: '#1d4ed8' },
  ddayLabelUrgent: { color: '#dc2626' },
  ddayVal:         { fontSize: 18, fontWeight: '900', color: '#1d4ed8' },
  ddayValUrgent:   { color: '#dc2626' },
  riskBox: {
    borderWidth: 1, borderRadius: 8, padding: 10,
    backgroundColor: '#fff', marginBottom: 8,
  },
  riskLabel: { fontSize: 11, color: '#6b7280' },
  riskLevel: { fontSize: 18, fontWeight: '900', marginVertical: 2 },
  riskSub:   { fontSize: 11, color: '#6b7280' },
  riskNote: {
    backgroundColor: '#fffbeb', borderWidth: 1, borderColor: '#fcd34d',
    borderRadius: 6, padding: 8, marginBottom: 12,
  },
  riskNoteText: { fontSize: 12, color: '#92400e' },
  emptyText:    { fontSize: 12, color: '#9ca3af' },
  scanDate:     { fontSize: 11, color: '#6b7280', marginBottom: 2 },
  scanCompany:  { fontSize: 13, fontWeight: '700', color: '#111', marginBottom: 8 },
  reportBtn: {
    backgroundColor: '#1e3a5f', borderRadius: 6,
    paddingVertical: 8, alignItems: 'center',
  },
  reportBtnText: { color: '#fff', fontWeight: '700', fontSize: 13 },
});
