/**
 * CalendarSync — 기기 달력 동기화 컴포넌트
 *
 * [iOS 17 보안 대응]
 * Info.plist에 반드시 아래 두 키를 추가해야 App Store 심사 통과:
 *
 *   <key>NSCalendarsWriteOnlyAccessUsageDescription</key>
 *   <string>고객 보험 만기일 갱신 알림을 달력에 등록하기 위해 접근 권한이 필요합니다.</string>
 *
 *   <key>NSCalendarsUsageDescription</key>
 *   <string>고객 일정 확인 및 보험 만기일 관리를 위해 달력 접근 권한이 필요합니다.</string>
 *
 * iOS 17 이상: NSCalendarsWriteOnlyAccessUsageDescription 추가 필수
 * iOS 17 미만: NSCalendarsUsageDescription 만으로도 통과되나, 둘 다 넣는 것을 권장
 *
 * react-native-calendar-events 설치:
 *   npm install react-native-calendar-events
 *   cd ios && pod install
 */

import React, { memo, useCallback, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Platform,
  ActivityIndicator,
} from 'react-native';
import RNCalendarEvents from 'react-native-calendar-events';
import { useCrmStore, selectCalendar } from '../store/crmStore';

const CalendarSync = memo(() => {
  const { events, markSynced } = useCrmStore(selectCalendar);
  const [loadingId, setLoadingId] = useState(null);

  // ── 권한 요청 헬퍼 ─────────────────────────────────────────────────────────
  const requestPermission = useCallback(async () => {
    try {
      // iOS 17+: 'readWrite' 대신 'restricted' 권한 분리 대응
      // 쓰기 전용 요청 시 사용자 경험이 더 부드러움
      const status = await RNCalendarEvents.requestPermissions(/* readOnly= */ false);
      return status === 'authorized';
    } catch (err) {
      console.warn('[CalendarSync] 권한 요청 오류:', err);
      return false;
    }
  }, []);

  // ── 이벤트 동기화 실행 ─────────────────────────────────────────────────────
  const handleSync = useCallback(async (event) => {
    if (event.synced) return; // 이미 동기화된 항목 중복 방지

    setLoadingId(event.id);

    try {
      const granted = await requestPermission();
      if (!granted) {
        Alert.alert(
          '달력 접근 권한 필요',
          Platform.OS === 'ios'
            ? '설정 → 개인 정보 보호 → 달력에서 권한을 허용해 주세요.'
            : '설정 → 앱 권한에서 달력 접근을 허용해 주세요.',
          [{ text: '확인' }],
        );
        return;
      }

      // 이벤트 날짜 파싱 (YYYY-MM-DD)
      const [y, m, d] = event.date.split('-').map(Number);
      const startDate = new Date(y, m - 1, d, 9, 0, 0);   // 당일 09:00
      const endDate   = new Date(y, m - 1, d, 10, 0, 0);  // 당일 10:00 (1시간)

      await RNCalendarEvents.saveEvent(event.title, {
        startDate: startDate.toISOString(),
        endDate:   endDate.toISOString(),
        notes:     `[골드키 CRM] 자동 등록 — ${event.title}`,
        alarms:    [
          { date: -1440 }, // D-1 (1일 전 알림, 분 단위 음수)
          { date: -60  },  // 1시간 전 알림
        ],
      });

      markSynced(event.id);
      Alert.alert('✅ 동기화 완료', `'${event.title}' 이(가) 기기 달력에 등록되었습니다.`);
    } catch (err) {
      console.error('[CalendarSync] 저장 오류:', err);
      Alert.alert('오류', `달력 등록 실패: ${err.message || '알 수 없는 오류'}`);
    } finally {
      setLoadingId(null);
    }
  }, [markSynced, requestPermission]);

  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>🗓️ 기기 달력 동기화</Text>
      <Text style={styles.sectionSub}>보험 만기일·갱신일을 달력에 자동 등록합니다.</Text>

      {events.map((ev) => (
        <View key={ev.id} style={styles.eventRow}>
          <View style={styles.eventInfo}>
            <Text style={styles.eventTitle}>{ev.title}</Text>
            <Text style={styles.eventDate}>{ev.date}</Text>
          </View>

          {ev.synced ? (
            <View style={styles.syncedBadge}>
              <Text style={styles.syncedText}>✅ 등록됨</Text>
            </View>
          ) : (
            <TouchableOpacity
              style={styles.syncBtn}
              onPress={() => handleSync(ev)}
              disabled={loadingId === ev.id}
            >
              {loadingId === ev.id ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={styles.syncBtnText}>달력에 추가</Text>
              )}
            </TouchableOpacity>
          )}
        </View>
      ))}
    </View>
  );
});

const styles = StyleSheet.create({
  container: { marginTop: 20 },
  sectionTitle: { fontSize: 16, fontWeight: '800', color: '#1e293b', marginBottom: 2 },
  sectionSub:   { fontSize: 12, color: '#64748b', marginBottom: 12 },
  eventRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  eventInfo: { flex: 1 },
  eventTitle: { fontSize: 14, fontWeight: '600', color: '#1e293b' },
  eventDate:  { fontSize: 12, color: '#64748b', marginTop: 2 },
  syncBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  syncBtnText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  syncedBadge: {
    backgroundColor: '#dcfce7',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  syncedText: { color: '#16a34a', fontSize: 12, fontWeight: '700' },
});

export default CalendarSync;
