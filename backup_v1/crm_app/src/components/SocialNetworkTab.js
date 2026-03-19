/**
 * SocialNetworkTab.js — [3차 라인] 생활 활동 & 인맥 지도
 * 소속 모임 + 소개 계보 + 개척 단계
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { PROSPECTING_STAGE } from '../config';

function StageTracker({ stage }) {
  const stages = ['lead', 'contact', 'proposal', 'contracted'];
  const currentIdx = stages.indexOf(stage || 'lead');
  return (
    <View style={styles.stageRow}>
      {stages.map((s, i) => {
        const info    = PROSPECTING_STAGE[s];
        const active  = i === currentIdx;
        const done    = i < currentIdx;
        return (
          <React.Fragment key={s}>
            <View style={[
              styles.stageStep,
              done   && styles.stageStepDone,
              active && styles.stageStepActive,
            ]}>
              <Text style={[
                styles.stageStepText,
                (done || active) && styles.stageStepTextActive,
              ]}>{info.label}</Text>
            </View>
            {i < stages.length - 1 && (
              <View style={[styles.stageLine, done && styles.stageLineDone]} />
            )}
          </React.Fragment>
        );
      })}
    </View>
  );
}

export default function SocialNetworkTab({ person, allPeople = [], onOpenPerson }) {
  if (!person) return null;

  const referrer = person.referrer_id
    ? allPeople.find((p) => p.person_id === person.referrer_id)
    : null;

  const referredByMe = allPeople.filter(
    (p) => p.referrer_id === person.person_id
  );

  const tags = person.community_tags || [];

  return (
    <ScrollView style={styles.root} showsVerticalScrollIndicator={false}>
      <Text style={styles.sectionTitle}>🏟️ 3차 라인 — 생활 활동 & 개척</Text>

      {/* 소속 모임 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>소속 모임</Text>
        {tags.length > 0 ? (
          <View style={styles.tagWrap}>
            {tags.map((tag) => (
              <View key={tag} style={styles.tag}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.emptyText}>등록된 모임 없음</Text>
        )}
        {person.lead_source && (
          <Text style={styles.leadSource}>유입: {person.lead_source}</Text>
        )}
      </View>

      {/* 소개 계보 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>소개 계보</Text>
        <View style={styles.referralChain}>
          {referrer ? (
            <TouchableOpacity
              style={styles.referralNode}
              onPress={() => onOpenPerson && onOpenPerson(referrer.person_id)}
            >
              <Text style={styles.referralName}>{referrer.name}</Text>
              <Text style={styles.referralRelation}>
                {person.referrer_relation || '소개'}
              </Text>
            </TouchableOpacity>
          ) : (
            <View style={[styles.referralNode, styles.referralNodeEmpty]}>
              <Text style={styles.emptyText}>소개자 없음</Text>
            </View>
          )}

          <Text style={styles.arrow}> ──소개──▶ </Text>

          <View style={[styles.referralNode, styles.referralNodeSelf]}>
            <Text style={[styles.referralName, { color: '#1e3a5f' }]}>
              {person.name}
            </Text>
            <Text style={styles.referralRelation}>현재 고객</Text>
          </View>

          {referredByMe.length > 0 && (
            <>
              <Text style={styles.arrow}> ──소개──▶ </Text>
              <View style={styles.referralNode}>
                <Text style={styles.referralName}>
                  {referredByMe[0].name}
                  {referredByMe.length > 1 && ` 외 ${referredByMe.length - 1}명`}
                </Text>
              </View>
            </>
          )}
        </View>
      </View>

      {/* 개척 단계 */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>개척 단계 트래커</Text>
        <StageTracker stage={person.prospecting_stage} />
        <Text style={styles.currentStage}>
          현재: {PROSPECTING_STAGE[person.prospecting_stage || 'lead']?.label}
        </Text>
      </View>

      {/* 활동 그룹 */}
      {person.activity_group && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>생활 활동 그룹</Text>
          <Text style={styles.activityGroup}>{person.activity_group}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:         { flex: 1, padding: 16 },
  sectionTitle: { fontSize: 15, fontWeight: '900', color: '#1e3a5f', marginBottom: 12 },
  card: {
    borderWidth: 1, borderColor: '#000', borderStyle: 'dashed',
    borderRadius: 10, padding: 12, backgroundColor: '#f9fafb', marginBottom: 12,
  },
  cardTitle:  { fontSize: 12, fontWeight: '700', color: '#374151', marginBottom: 8 },
  tagWrap:    { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  tag: {
    backgroundColor: '#f0f9ff', borderWidth: 1, borderColor: '#bae6fd',
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12,
  },
  tagText:      { fontSize: 12, color: '#0369a1', fontWeight: '600' },
  leadSource:   { fontSize: 11, color: '#6b7280', marginTop: 6 },
  emptyText:    { fontSize: 12, color: '#9ca3af' },
  referralChain:{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap' },
  referralNode: {
    borderWidth: 1, borderColor: '#d1d5db',
    borderRadius: 8, padding: 8, alignItems: 'center', minWidth: 70,
  },
  referralNodeEmpty: { borderStyle: 'dashed' },
  referralNodeSelf:  { borderColor: '#1e3a5f', backgroundColor: '#eff6ff' },
  referralName:   { fontSize: 13, fontWeight: '700', color: '#111' },
  referralRelation:{ fontSize: 10, color: '#6b7280', marginTop: 2 },
  arrow:          { fontSize: 12, color: '#6b7280', paddingHorizontal: 2 },
  stageRow:       { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  stageStep: {
    flex: 1, paddingVertical: 6, alignItems: 'center',
    borderWidth: 1, borderColor: '#d1d5db',
    borderRadius: 6, backgroundColor: '#fff',
  },
  stageStepDone:   { backgroundColor: '#dcfce7', borderColor: '#16a34a' },
  stageStepActive: { backgroundColor: '#1e3a5f', borderColor: '#1e3a5f' },
  stageStepText:   { fontSize: 11, color: '#9ca3af' },
  stageStepTextActive: { color: '#fff', fontWeight: '700' },
  stageLine:       { width: 8, height: 1, backgroundColor: '#d1d5db' },
  stageLineDone:   { backgroundColor: '#16a34a' },
  currentStage:    { fontSize: 12, color: '#374151', fontWeight: '600' },
  activityGroup:   { fontSize: 14, color: '#374151', fontWeight: '600' },
});
