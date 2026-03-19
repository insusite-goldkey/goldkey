/**
 * TermsScreen.js — Goldkey AI Masters CRM
 * 이용약관 및 개인정보처리방침
 *
 * 본 앱은 Goldkey AI Masters 2026의 그림자 앱(Shadow App)입니다.
 * 모든 데이터·정보 관리 기준은 본앱(Goldkey AI Masters 2026)을 따릅니다.
 */

import React from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, SafeAreaView,
} from 'react-native';

export default function TermsScreen({ onClose }) {
  return (
    <SafeAreaView style={styles.root}>
      {/* 헤더 */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>이용약관 및 개인정보처리방침</Text>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
            <Text style={styles.closeTxt}>닫기</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>

        {/* 앱 정체성 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>제1조 (앱 정체성)</Text>
          <Text style={styles.body}>
            본 앱 <Text style={styles.bold}>Goldkey AI Masters CRM</Text>은
            {' '}<Text style={styles.bold}>Goldkey AI Masters 2026</Text>(이하 "본앱")의
            그림자 앱(Shadow App)입니다.{'\n\n'}
            본 앱에서 제공되는 모든 기능·데이터·분석 결과·리포트는
            본앱에서 파생되며, 본앱의 운영 기준 및 정책을 그대로 준수합니다.
          </Text>
        </View>

        {/* 서비스 범위 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>제2조 (서비스 범위)</Text>
          <Text style={styles.body}>
            본 앱은 다음 기능을 제공합니다:{'\n'}
            • 고객 상담 일정 관리{'\n'}
            • 보험 증권 분석 (내보험다보여){'\n'}
            • AI 상담 리포트 조회{'\n'}
            • 고객 정보 조회 및 메모{'\n\n'}
            위 기능의 실질적 처리·분석·AI 연산은 본앱(Goldkey AI Masters 2026)에서 수행됩니다.
          </Text>
        </View>

        {/* 고객정보 보관 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>제3조 (고객정보 보관 및 암호화)</Text>
          <Text style={styles.body}>
            고객 개인정보의 보관·암호화·관리는 본앱(Goldkey AI Masters 2026)의
            기준을 따릅니다:{'\n\n'}
            • 모든 고객 데이터는 Supabase(암호화 클라우드 DB)에 저장됩니다.{'\n'}
            • 전송 구간은 TLS/HTTPS로 암호화됩니다.{'\n'}
            • 본 앱은 고객 정보를 기기 내 로컬에 캐시할 수 있으나,
            원본 데이터의 관리 권한은 본앱에 있습니다.{'\n'}
            • 개인정보는 보험 상담 목적 외 제3자에게 제공되지 않습니다.
          </Text>
        </View>

        {/* 데이터 수집 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>제4조 (수집하는 정보)</Text>
          <Text style={styles.body}>
            본 앱이 처리하는 정보:{'\n'}
            • 성명, 연락처, 생년월일, 직업 (보험 상담 목적){'\n'}
            • 보험 증권 정보 (분석 목적){'\n'}
            • 상담 일정 및 메모{'\n\n'}
            수집된 정보는 설계사-고객 간 보험 상담 서비스 제공 목적으로만 사용됩니다.
          </Text>
        </View>

        {/* 사용 기준 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>제5조 (사용 기준)</Text>
          <Text style={styles.body}>
            본 앱의 사용 기준은 본앱(Goldkey AI Masters 2026)의 기준을 준수합니다.{'\n\n'}
            • 본 앱은 보험 설계사 전용 업무 도구입니다.{'\n'}
            • 무단 배포·상업적 재사용은 금지됩니다.{'\n'}
            • 고객 정보는 해당 설계사의 담당 고객에 한해 접근 가능합니다.
          </Text>
        </View>

        {/* 책임 한계 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>제6조 (책임 한계)</Text>
          <Text style={styles.body}>
            본 앱은 그림자 앱 특성상 본앱의 서비스 가용성에 종속됩니다.
            본앱 서비스 중단 시 일부 기능이 제한될 수 있습니다.{'\n\n'}
            AI 분석 결과는 참고용이며, 최종 보험 설계 결정은 전문 설계사의 판단을 따릅니다.
          </Text>
        </View>

        {/* 문의 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>제7조 (문의처)</Text>
          <Text style={styles.body}>
            본 앱 및 본앱(Goldkey AI Masters 2026) 관련 문의:{'\n'}
            • 운영사: Goldkey AI Masters 2026{'\n'}
            • 개인정보 관련 문의는 본앱 내 고객센터를 이용해 주세요.
          </Text>
        </View>

        <Text style={styles.footer}>
          본 약관은 2026년 3월 13일부터 적용됩니다.{'\n'}
          Goldkey AI Masters CRM v1.0.0
        </Text>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#ffffff' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    backgroundColor: '#1e3a5f',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#ffffff',
  },
  closeBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 6,
  },
  closeTxt: { color: '#ffffff', fontSize: 14, fontWeight: '600' },
  scroll: { flex: 1 },
  content: { padding: 20, paddingBottom: 40 },
  section: {
    marginBottom: 24,
    borderLeftWidth: 3,
    borderLeftColor: '#1e3a5f',
    paddingLeft: 12,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1e3a5f',
    marginBottom: 8,
  },
  body: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 22,
  },
  bold: { fontWeight: '700' },
  footer: {
    marginTop: 16,
    textAlign: 'center',
    fontSize: 12,
    color: '#9ca3af',
    lineHeight: 20,
  },
});
