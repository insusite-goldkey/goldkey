# iOS Info.plist 설정 가이드

## App Store 심사 통과를 위한 필수 권한 설정

### 달력 접근 권한 (iOS 17 이상 대응)

`ios/GoldkeyCRM/Info.plist` 파일에 아래 키를 추가하세요.
iOS 17부터 쓰기 전용(WriteOnly) 권한이 분리되었습니다. **두 키 모두** 추가해야 합니다.

```xml
<!-- Info.plist -->
<dict>
  <!-- ... 기존 설정 ... -->

  <!-- iOS 17+ 필수: 쓰기 전용 달력 접근 -->
  <key>NSCalendarsWriteOnlyAccessUsageDescription</key>
  <string>고객 보험 만기일 및 갱신일 알림을 달력에 등록하기 위해 접근 권한이 필요합니다.</string>

  <!-- iOS 17 미만 + 읽기 필요 시 (하위 호환) -->
  <key>NSCalendarsUsageDescription</key>
  <string>고객 보험 일정 확인 및 만기일 관리를 위해 달력 접근 권한이 필요합니다.</string>

</dict>
```

### 권한 정책 요약

| iOS 버전 | 필요 키 | 비고 |
|----------|---------|------|
| iOS 17 이상 | `NSCalendarsWriteOnlyAccessUsageDescription` | 필수 — 없으면 앱스토어 리젝 |
| iOS 17 미만 | `NSCalendarsUsageDescription` | 하위 호환용 |
| 모든 버전 권장 | **두 키 모두 추가** | 버전 무관 안전 통과 |

### 권한 설명문 작성 원칙 (앱스토어 리젝 방지)

Apple 심사팀은 권한 설명문이 **구체적 목적**을 명시하지 않으면 리젝합니다.

❌ 리젝 사유가 되는 예시:
```
"달력 접근이 필요합니다."
```

✅ 통과되는 예시:
```
"고객 보험 만기일 및 갱신일 알림을 달력에 자동으로 등록하여
영업 담당자가 고객 관리 일정을 놓치지 않도록 돕기 위해 접근 권한이 필요합니다."
```

---

## react-native-calendar-events Pod 설치

```bash
cd ios
pod install
```

`Podfile`에 자동으로 추가되지 않을 경우 수동 추가:

```ruby
# ios/Podfile
pod 'RNCalendarEvents', :path => '../node_modules/react-native-calendar-events'
```

---

## 기타 권한 (필요 시)

```xml
<!-- 알림 권한 (만기일 푸시 알림 사용 시) -->
<key>NSUserNotificationUsageDescription</key>
<string>보험 만기일 및 갱신 알림을 전송하기 위해 권한이 필요합니다.</string>
```
