# 🔥 Firebase 연동 설정 가이드 (골드키 CRM)

## ✅ 현재 완료 상태
- [x] `npm install` 완료 (879 패키지)
- [x] `@react-native-firebase/app` v20 설치
- [x] `@react-native-firebase/firestore` v20 설치
- [x] `@react-native-async-storage/async-storage` v1.23 설치
- [x] `src/utils/firebase.js` 초기화 코드 완성
- [x] `firestore.indexes.json` 복합 인덱스 19개 정의

## 🔧 남은 필수 작업 (수동 진행)

---

### STEP 1 — Firebase 콘솔에서 프로젝트 생성

1. https://console.firebase.google.com 접속
2. [프로젝트 추가] → 이름: `goldkey-crm`
3. Google Analytics 활성화 (선택)
4. [계속] → 프로젝트 생성 완료

---

### STEP 2 — Android 앱 등록 + google-services.json 다운로드

1. Firebase 콘솔 → 프로젝트 홈 → [앱 추가] → Android 아이콘 클릭
2. Android 패키지 이름 입력:
   ```
   com.goldkeycrm
   ```
3. [앱 등록] 클릭
4. `google-services.json` 다운로드
5. 다운로드한 파일을 아래 경로에 복사:
   ```
   crm_app/android/app/google-services.json
   ```

---

### STEP 3 — iOS 앱 등록 + GoogleService-Info.plist 다운로드

1. Firebase 콘솔 → [앱 추가] → iOS 아이콘 클릭
2. iOS 번들 ID 입력:
   ```
   com.goldkeycrm
   ```
3. [앱 등록] 클릭
4. `GoogleService-Info.plist` 다운로드
5. Xcode에서 `ios/GoldKeyCRM/` 폴더에 파일 추가 (드래그 앤 드롭)
   - ✅ "Copy items if needed" 체크
   - ✅ Target Membership: GoldKeyCRM 체크

---

### STEP 4 — Android 빌드 설정

#### 4-1. `android/build.gradle` (프로젝트 레벨)
```groovy
buildscript {
    dependencies {
        // 기존 코드 아래에 추가
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

#### 4-2. `android/app/build.gradle` (앱 레벨) 파일 맨 마지막 줄에 추가:
```groovy
apply plugin: 'com.google.gms.google-services'
```

---

### STEP 5 — iOS 빌드 설정

터미널에서 실행:
```bash
cd ios
pod install
cd ..
```

---

### STEP 6 — Firestore 데이터베이스 생성

1. Firebase 콘솔 → Firestore Database → [데이터베이스 만들기]
2. **프로덕션 모드** 선택
3. 위치: `asia-northeast3` (서울) 선택
4. [완료]

---

### STEP 7 — Firestore 보안 규칙 배포

프로젝트 루트의 `firestore.rules` 파일이 이미 작성되어 있습니다.

```bash
# Firebase CLI 설치 (최초 1회)
npm install -g firebase-tools

# 로그인
firebase login

# 프로젝트 연결
firebase use --add

# 규칙 + 인덱스 배포
firebase deploy --only firestore
```

---

### STEP 8 — 인덱스 배포

```bash
firebase deploy --only firestore:indexes
```

`firestore.indexes.json` 파일의 19개 복합 인덱스가 자동으로 생성됩니다.
(인덱스 빌드: 약 5~10분 소요)

---

## 🚀 앱 실행

```bash
# Android
npx react-native run-android

# iOS
npx react-native run-ios
```

---

## 🔒 보안 주의사항

- `google-services.json` / `GoogleService-Info.plist` 는 **절대 Git에 커밋하지 마세요**
- `.gitignore`에 다음을 추가하세요:
  ```
  android/app/google-services.json
  ios/GoldKeyCRM/GoogleService-Info.plist
  ```

---

## 📂 최종 프로젝트 구조

```
crm_app/
├── android/
│   └── app/
│       └── google-services.json       ← STEP 2에서 추가
├── ios/
│   └── GoldKeyCRM/
│       └── GoogleService-Info.plist   ← STEP 3에서 추가 (Xcode 통해서)
├── src/
│   └── utils/
│       └── firebase.js                ✅ 완성 (초기화 + 헬퍼 함수)
├── firestore.indexes.json             ✅ 완성 (복합 인덱스 19개)
├── firestore.rules                    ✅ 완성 (보안 규칙)
└── package.json                       ✅ 패키지 설치 완료
```
