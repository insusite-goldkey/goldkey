/**
 * TrashScreen — 3단계 Soft Delete 휴지통
 *
 * ┌ 기능 ──────────────────────────────────────────────────────────┐
 * │  - 삭제된 고객 / 일정 / 스캔결과 를 탭으로 구분해서 표시       │
 * │  - 삭제 후 30일 이내 데이터만 표시 (만료 시 자동 숨김)         │
 * │  - [복구] 버튼: 원클릭으로 isDeleted:false 복원                │
 * │  - 남은 일수(D-30) 표시로 긴박감 전달                          │
 * │  - 빈 상태(0건)일 때 안심 메시지 표시                          │
 * └────────────────────────────────────────────────────────────────┘
 *
 * Props:
 *   onClose {function} — 닫기 콜백
 */

import React, { useState } from 'react';
import {
  Alert,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  useCustomerStore,
  selTrashCustomers,
  selTrashSchedules,
  selTrashScans,
  selTrashCount,
} from '../store/customerStore';

// ── 남은 일수 계산 ────────────────────────────────────────────────────────────
const daysLeft = (deletedAt) => {
  if (!deletedAt) return 0;
  const elapsed = Date.now() - new Date(deletedAt).getTime();
  return Math.max(0, 30 - Math.floor(elapsed / 86400000));
};

const formatDate = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  });
};

// ── 탭 정의 ───────────────────────────────────────────────────────────────────
const TABS = [
  { key: 'customers', label: '고객' },
  { key: 'schedules', label: '일정' },
  { key: 'scans',     label: '스캔' },
];

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
const TrashScreen = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('customers');

  const trashCustomers = useCustomerStore(selTrashCustomers);
  const trashSchedules = useCustomerStore(selTrashSchedules);
  const trashScans     = useCustomerStore(selTrashScans);
  const totalCount     = useCustomerStore(selTrashCount);

  const restoreCustomer   = useCustomerStore((s) => s.restoreCustomer);
  const restoreSchedule   = useCustomerStore((s) => s.restoreSchedule);
  const restoreScanResult = useCustomerStore((s) => s.restoreScanResult);

  // ── 복구 핸들러 ─────────────────────────────────────────────────────────────
  const handleRestore = (type, id, label) => {
    Alert.alert(
      '데이터 복구',
      `"${label}"을(를) 복구하시겠습니까?`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '복구',
          onPress: () => {
            if (type === 'customers') restoreCustomer(id);
            else if (type === 'schedules') restoreSchedule(id);
            else if (type === 'scans') restoreScanResult(id);
          },
        },
      ],
    );
  };

  // ── 현재 탭 데이터 ──────────────────────────────────────────────────────────
  const currentData = {
    customers: trashCustomers,
    schedules: trashSchedules,
    scans:     trashScans,
  }[activeTab] ?? [];

  // ── 아이템 렌더 ─────────────────────────────────────────────────────────────
  const renderItem = (item) => {
    const days = daysLeft(item.deletedAt);
    const isUrgent = days <= 7;

    let title = '';
    let sub   = '';
    if (activeTab === 'customers') {
      title = `${item.name} (${item.age}세)`;
      sub   = `${item.job || '직업 미기재'} · ${item.phone || '번호 없음'}`;
    } else if (activeTab === 'schedules') {
      title = item.title || '(제목 없음)';
      sub   = `${item.date} ${item.startTime}~${item.endTime}`;
    } else {
      title = item.analysis?.summary
        ? item.analysis.summary.slice(0, 40) + '…'
        : '분석 대기 중';
      sub = `스캔: ${formatDate(item.scannedAt)} · ${item.docType || 'other'}`;
    }

    return (
      <View key={item.id} style={styles.itemRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.itemTitle} numberOfLines={1}>{title}</Text>
          <Text style={styles.itemSub}>{sub}</Text>
          <View style={styles.itemMetaRow}>
            <Text style={styles.deleteDate}>
              삭제일: {formatDate(item.deletedAt)}
            </Text>
            <View style={[styles.daysLeftBadge, isUrgent && styles.daysLeftUrgent]}>
              <Text style={[styles.daysLeftText, isUrgent && styles.daysLeftTextUrgent]}>
                D-{days}
              </Text>
            </View>
          </View>
        </View>
        <TouchableOpacity
          style={styles.restoreBtn}
          onPress={() => handleRestore(activeTab, item.id, title)}
          activeOpacity={0.75}
        >
          <Text style={styles.restoreBtnText}>♻️ 복구</Text>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* ── 헤더 ── */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>🗑️ 휴지통</Text>
          <Text style={styles.headerSub}>
            삭제 후 30일 이내 데이터를 복구할 수 있습니다.
          </Text>
        </View>
        <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
          <Text style={styles.closeBtnText}>✕ 닫기</Text>
        </TouchableOpacity>
      </View>

      {/* ── 탭 ── */}
      <View style={styles.tabBar}>
        {TABS.map((tab) => {
          const count = {
            customers: trashCustomers.length,
            schedules: trashSchedules.length,
            scans:     trashScans.length,
          }[tab.key];
          const isActive = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={[styles.tab, isActive && styles.tabActive]}
              onPress={() => setActiveTab(tab.key)}
              activeOpacity={0.75}
            >
              <Text style={[styles.tabText, isActive && styles.tabTextActive]}>
                {tab.label}
              </Text>
              {count > 0 && (
                <View style={styles.tabBadge}>
                  <Text style={styles.tabBadgeText}>{count}</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* ── 리스트 ── */}
      <ScrollView
        style={styles.list}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      >
        {currentData.length === 0 ? (
          <View style={styles.emptyWrap}>
            <Text style={styles.emptyIcon}>✅</Text>
            <Text style={styles.emptyTitle}>휴지통이 비어있습니다</Text>
            <Text style={styles.emptySub}>
              삭제된 데이터가 없거나{'\n'}모두 30일이 경과되었습니다.
            </Text>
          </View>
        ) : (
          currentData.map(renderItem)
        )}
      </ScrollView>

      {/* ── 하단 안내 ── */}
      {totalCount > 0 && (
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            🛡️ 총 {totalCount}건의 데이터가 보호 중입니다. 30일 후 자동 만료됩니다.
          </Text>
        </View>
      )}
    </SafeAreaView>
  );
};

// ── 스타일 ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },

  // 헤더
  header: {
    flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1, borderBottomColor: '#f1f5f9',
  },
  headerTitle:  { fontSize: 22, fontWeight: '900', color: '#1e293b' },
  headerSub:    { fontSize: 12, color: '#94a3b8', marginTop: 2 },
  closeBtn: {
    paddingHorizontal: 14, paddingVertical: 8,
    backgroundColor: '#f1f5f9', borderRadius: 20,
  },
  closeBtnText: { fontSize: 13, fontWeight: '700', color: '#475569' },

  // 탭
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderBottomWidth: 1, borderBottomColor: '#f1f5f9',
    paddingHorizontal: 16,
  },
  tab: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingVertical: 12, paddingHorizontal: 16,
    borderBottomWidth: 2, borderBottomColor: 'transparent',
  },
  tabActive:     { borderBottomColor: '#1e3a5f' },
  tabText:       { fontSize: 14, fontWeight: '700', color: '#94a3b8' },
  tabTextActive: { color: '#1e3a5f' },
  tabBadge: {
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 10,
    backgroundColor: '#fee2e2',
  },
  tabBadgeText: { fontSize: 10, fontWeight: '800', color: '#ef4444' },

  // 리스트
  list:        { flex: 1 },
  listContent: { padding: 16, gap: 10 },

  // 아이템 행
  itemRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: '#ffffff', borderRadius: 14,
    padding: 14,
    borderWidth: 1, borderColor: '#f1f5f9',
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
  },
  itemTitle:    { fontSize: 14, fontWeight: '800', color: '#1e293b', marginBottom: 3 },
  itemSub:      { fontSize: 12, color: '#64748b', marginBottom: 6 },
  itemMetaRow:  { flexDirection: 'row', alignItems: 'center', gap: 8 },
  deleteDate:   { fontSize: 11, color: '#94a3b8' },
  daysLeftBadge: {
    paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10,
    backgroundColor: '#f1f5f9',
  },
  daysLeftUrgent: { backgroundColor: '#fee2e2' },
  daysLeftText:   { fontSize: 11, fontWeight: '800', color: '#64748b' },
  daysLeftTextUrgent: { color: '#ef4444' },

  // 복구 버튼
  restoreBtn: {
    paddingHorizontal: 14, paddingVertical: 9,
    backgroundColor: '#f0fdf4', borderRadius: 12,
    borderWidth: 1.5, borderColor: '#86efac',
    flexShrink: 0,
  },
  restoreBtnText: { fontSize: 12, fontWeight: '800', color: '#166534' },

  // 빈 상태
  emptyWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  emptyIcon:  { fontSize: 52, marginBottom: 16 },
  emptyTitle: { fontSize: 17, fontWeight: '900', color: '#1e293b', marginBottom: 8 },
  emptySub:   { fontSize: 13, color: '#94a3b8', textAlign: 'center', lineHeight: 20 },

  // 하단 안내
  footer: {
    paddingHorizontal: 20, paddingVertical: 14,
    backgroundColor: '#fff7ed',
    borderTopWidth: 1, borderTopColor: '#fed7aa',
  },
  footerText: { fontSize: 12, color: '#92400e', fontWeight: '600', textAlign: 'center' },
});

export default TrashScreen;
