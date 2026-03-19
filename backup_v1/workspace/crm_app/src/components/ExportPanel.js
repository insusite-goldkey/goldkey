/**
 * ExportPanel — 설계사 전용 데이터 백업 패널
 *
 * ┌ 기능 ──────────────────────────────────────────────────────────┐
 * │  • AGENT 권한일 때만 렌더링 (고객 화면에서 완전 숨김)           │
 * │  • [☁️ 고객 명부] [📅 일정 명부] [🗂️ 전체 백업] 3버튼         │
 * │  • 클릭 → 1~2초 로딩 스피너 → CSV Share sheet 오픈            │
 * │  • 완료/취소 후 토스트 알림                                     │
 * │  • 프리미엄 라이트 테마 (흰 배경 + 골드 액센트)                │
 * └────────────────────────────────────────────────────────────────┘
 *
 * Props:
 *   userRole  {'AGENT' | 'CLIENT' | string}  — 권한 (기본 'AGENT')
 *   compact   {boolean}                       — 헤더바에 삽입 시 compact 모드
 */

import React, { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useCustomerStore } from '../store/customerStore';
import {
  exportAll,
  exportCustomersOnly,
  exportSchedulesOnly,
} from '../utils/exportUtils';

// ── 토스트 ────────────────────────────────────────────────────────────────────
const ExportToast = ({ visible, message, isError }) => {
  const opacity = useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    if (visible) {
      Animated.sequence([
        Animated.timing(opacity, { toValue: 1, duration: 250, useNativeDriver: true }),
        Animated.delay(2200),
        Animated.timing(opacity, { toValue: 0, duration: 350, useNativeDriver: true }),
      ]).start();
    }
  }, [visible]);

  if (!visible) return null;
  return (
    <Animated.View style={[styles.toast, isError && styles.toastError, { opacity }]}>
      <Text style={styles.toastText}>{message}</Text>
    </Animated.View>
  );
};

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
const ExportPanel = ({ userRole = 'AGENT', compact = false }) => {
  // ── 보안: AGENT 아닐 때 완전 null 반환 ─────────────────────────────────────
  if (userRole !== 'AGENT') return null;

  const customers    = useCustomerStore((s) => s.customers);
  const schedules    = useCustomerStore((s) => s.schedules);
  const scanResults  = useCustomerStore((s) => s.scanResults);

  const [loading,  setLoading]  = useState(null); // null | 'customers' | 'schedules' | 'all'
  const [toast,    setToast]    = useState({ visible: false, message: '', isError: false });

  // ── 토스트 트리거 ────────────────────────────────────────────────────────
  const showToast = (message, isError = false) => {
    setToast({ visible: true, message, isError });
    setTimeout(() => setToast((t) => ({ ...t, visible: false })), 3000);
  };

  // ── 내보내기 핸들러 ──────────────────────────────────────────────────────
  const handleExport = async (type) => {
    if (loading) return;
    setLoading(type);

    // 최소 1.2초 로딩 표시 (UX)
    const minDelay = new Promise((r) => setTimeout(r, 1200));

    try {
      let shared = false;
      if (type === 'customers') {
        await minDelay;
        shared = await exportCustomersOnly(customers, scanResults);
      } else if (type === 'schedules') {
        await minDelay;
        shared = await exportSchedulesOnly(schedules, customers);
      } else {
        await minDelay;
        const result = await exportAll({ customers, schedules, scanResults });
        shared = result.customersShared || result.schedulesShared;
      }

      showToast(shared ? '✅ 안전하게 백업되었습니다!' : '내보내기가 취소되었습니다.');
    } catch (e) {
      console.error('[ExportPanel]', e);
      showToast('⚠️ 내보내기 중 오류가 발생했습니다.', true);
    } finally {
      setLoading(null);
    }
  };

  // ── compact 모드: 헤더바 아이콘 단일 버튼 ───────────────────────────────
  if (compact) {
    return (
      <View>
        <TouchableOpacity
          style={styles.compactBtn}
          onPress={() => handleExport('all')}
          disabled={!!loading}
          activeOpacity={0.75}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#f0c040" />
          ) : (
            <Text style={styles.compactBtnText}>☁️</Text>
          )}
        </TouchableOpacity>
        <ExportToast
          visible={toast.visible}
          message={toast.message}
          isError={toast.isError}
        />
      </View>
    );
  }

  // ── 풀 패널 모드 ────────────────────────────────────────────────────────
  const activeCount   = Object.values(customers).filter((c) => !c.isDeleted).length;
  const scheduleCount = Object.values(schedules).filter((s) => !s.isDeleted).length;

  return (
    <View style={styles.panel}>
      {/* 헤더 */}
      <View style={styles.panelHeader}>
        <Text style={styles.panelTitle}>☁️ 데이터 백업</Text>
        <View style={styles.agentBadge}>
          <Text style={styles.agentBadgeText}>설계사 전용</Text>
        </View>
      </View>
      <Text style={styles.panelSub}>
        CSV 파일로 내보내어 저장·이메일·클라우드로 백업할 수 있습니다.
      </Text>

      {/* 통계 요약 */}
      <View style={styles.statsRow}>
        <View style={styles.statChip}>
          <Text style={styles.statNum}>{activeCount}</Text>
          <Text style={styles.statLabel}>고객</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statChip}>
          <Text style={styles.statNum}>{scheduleCount}</Text>
          <Text style={styles.statLabel}>일정</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statChip}>
          <Text style={styles.statNum}>
            {Object.values(useCustomerStore.getState().scanResults).filter((r) => !r.isDeleted).length}
          </Text>
          <Text style={styles.statLabel}>스캔</Text>
        </View>
      </View>

      {/* 버튼 3개 */}
      <View style={styles.btnGroup}>
        {/* 고객 명부 */}
        <ExportBtn
          label="고객 명부"
          icon="👥"
          sub={`${activeCount}명 CSV`}
          loading={loading === 'customers'}
          disabled={!!loading}
          onPress={() => handleExport('customers')}
          accent="#2563eb"
        />

        {/* 일정 명부 */}
        <ExportBtn
          label="일정 명부"
          icon="📅"
          sub={`${scheduleCount}건 CSV`}
          loading={loading === 'schedules'}
          disabled={!!loading}
          onPress={() => handleExport('schedules')}
          accent="#059669"
        />

        {/* 전체 백업 */}
        <ExportBtn
          label="전체 백업"
          icon="🗂️"
          sub="고객 + 일정"
          loading={loading === 'all'}
          disabled={!!loading}
          onPress={() => handleExport('all')}
          accent="#b45309"
          highlight
        />
      </View>

      {/* 로딩 안내 */}
      {loading && (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color="#2563eb" style={{ marginRight: 8 }} />
          <Text style={styles.loadingText}>데이터를 CSV로 변환 중입니다...</Text>
        </View>
      )}

      {/* 보안 안내 */}
      <Text style={styles.secureNote}>
        🔒 이 기능은 설계사 권한에서만 접근 가능합니다.{'\n'}
        내보내진 파일에는 고객 개인정보가 포함됩니다. 안전하게 관리하세요.
      </Text>

      {/* 토스트 */}
      <ExportToast
        visible={toast.visible}
        message={toast.message}
        isError={toast.isError}
      />
    </View>
  );
};

// ── ExportBtn 서브 컴포넌트 ───────────────────────────────────────────────────
const ExportBtn = ({ label, icon, sub, loading, disabled, onPress, accent, highlight }) => (
  <TouchableOpacity
    style={[
      styles.exportBtn,
      highlight && styles.exportBtnHighlight,
      disabled && styles.exportBtnDisabled,
    ]}
    onPress={onPress}
    disabled={disabled}
    activeOpacity={0.75}
  >
    {loading ? (
      <ActivityIndicator size="small" color={highlight ? '#ffffff' : accent} />
    ) : (
      <Text style={styles.exportBtnIcon}>{icon}</Text>
    )}
    <View style={{ flex: 1 }}>
      <Text style={[
        styles.exportBtnLabel,
        highlight && styles.exportBtnLabelLight,
      ]}>
        {label}
      </Text>
      <Text style={[
        styles.exportBtnSub,
        highlight && styles.exportBtnSubLight,
      ]}>
        {sub}
      </Text>
    </View>
    <Text style={[
      styles.exportBtnArrow,
      highlight && styles.exportBtnArrowLight,
    ]}>›</Text>
  </TouchableOpacity>
);

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  // 풀 패널
  panel: {
    backgroundColor: '#ffffff',
    borderRadius:    16,
    marginHorizontal: 16,
    marginVertical:  12,
    padding:         18,
    borderWidth:     1,
    borderColor:     '#e2e8f0',
    shadowColor:     '#000',
    shadowOffset:    { width: 0, height: 2 },
    shadowOpacity:   0.07,
    shadowRadius:    8,
    elevation:       3,
  },
  panelHeader: {
    flexDirection:  'row',
    alignItems:     'center',
    gap:             10,
    marginBottom:    6,
  },
  panelTitle: {
    fontSize:    17,
    fontWeight:  '900',
    color:       '#1e293b',
    letterSpacing: 0.3,
  },
  agentBadge: {
    paddingHorizontal: 10,
    paddingVertical:    3,
    borderRadius:      20,
    backgroundColor:   '#fef3c7',
    borderWidth:       1,
    borderColor:       '#f59e0b',
  },
  agentBadgeText: { fontSize: 10, fontWeight: '800', color: '#92400e' },
  panelSub: {
    fontSize:     12,
    color:        '#64748b',
    marginBottom: 14,
    lineHeight:   18,
  },

  // 통계 요약
  statsRow: {
    flexDirection:   'row',
    backgroundColor: '#f8fafc',
    borderRadius:    10,
    padding:         12,
    marginBottom:    16,
    alignItems:      'center',
    justifyContent:  'center',
  },
  statChip:    { flex: 1, alignItems: 'center' },
  statNum:     { fontSize: 20, fontWeight: '900', color: '#1e3a5f' },
  statLabel:   { fontSize: 11, color: '#64748b', fontWeight: '600', marginTop: 2 },
  statDivider: { width: 1, height: 32, backgroundColor: '#e2e8f0' },

  // 버튼 그룹
  btnGroup: { gap: 8, marginBottom: 14 },
  exportBtn: {
    flexDirection:  'row',
    alignItems:     'center',
    gap:             12,
    paddingVertical:  13,
    paddingHorizontal: 14,
    borderRadius:    12,
    backgroundColor: '#f8fafc',
    borderWidth:     1,
    borderColor:     '#e2e8f0',
  },
  exportBtnHighlight: {
    backgroundColor: '#1e3a5f',
    borderColor:     '#f0c040',
    borderWidth:     1.5,
  },
  exportBtnDisabled: { opacity: 0.5 },
  exportBtnIcon:     { fontSize: 22 },
  exportBtnLabel:    { fontSize: 14, fontWeight: '800', color: '#1e293b' },
  exportBtnLabelLight: { color: '#ffffff' },
  exportBtnSub:      { fontSize: 11, color: '#64748b', marginTop: 1 },
  exportBtnSubLight: { color: '#93c5fd' },
  exportBtnArrow:    { fontSize: 20, color: '#94a3b8', fontWeight: '300' },
  exportBtnArrowLight: { color: '#f0c040' },

  // 로딩 행
  loadingRow: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'center',
    paddingVertical: 10,
    marginBottom:    8,
  },
  loadingText: { fontSize: 13, color: '#2563eb', fontWeight: '600' },

  // 보안 안내
  secureNote: {
    fontSize:   11,
    color:      '#94a3b8',
    lineHeight: 17,
    textAlign:  'center',
    marginTop:   4,
  },

  // 토스트
  toast: {
    position:      'absolute',
    bottom:        -56,
    alignSelf:     'center',
    paddingHorizontal: 20,
    paddingVertical:    11,
    backgroundColor:   '#1e3a5f',
    borderRadius:      28,
    shadowColor:       '#000',
    shadowOffset:      { width: 0, height: 4 },
    shadowOpacity:     0.2,
    shadowRadius:      8,
    elevation:         8,
  },
  toastError: { backgroundColor: '#dc2626' },
  toastText:  { fontSize: 13, fontWeight: '700', color: '#ffffff' },

  // compact 헤더 버튼
  compactBtn: {
    width:           40,
    height:          40,
    borderRadius:    20,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems:      'center',
    justifyContent:  'center',
  },
  compactBtnText: { fontSize: 18 },
});

export default ExportPanel;
