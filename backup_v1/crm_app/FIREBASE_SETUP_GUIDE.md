# 🔥 Firebase 연동 + 앱 빌드 완전 가이드 (골드키 CRM)

## ✅ 코드 작업 완료 상태 (Windsurf 처리 완료)
- [x] Firebase 동기 import 제거 → lazy init (앱 프리즈 완전 방지)
- [x] `firebase.js` 방어 코드 (google-services.json 없어도 크래시 없음)
- [x] AsyncStorage 타임아웃 10초 내장 (rehydration 무한 대기 방지)
- [x] `PremiumLoadingUI` 검은 박스 버그 수정
- [x] `npm install` 완료 (879 패키지)
- [x] `firestore.indexes.json` 복합 인덱스 19개 정의

## ⚠️ 현재 상황: android/ 폴더 없음
현재 프로젝트에 `android/`, `ios/` 네이티브 폴더가 없습니다.
아래 **STEP 0**을 먼저 실행해야 앱을 빌드할 수 있습니다.

---

## 🔧 남은 필수 작업 순서

---

### STEP 0 — 네이티브 폴더 생성 (최초 1회 필수) ⚠️

터미널(명령 프롬프트)에서 실행:

```bash
cd D:\CascadeProjects\crm_app
npx react-native@0.73.4 init GoldKeyCRM --directory . --skip-install
```

> 완료되면 `android/`, `ios/` 폴더가 생성됩니다.
> 이후 `android/app/build.gradle`을 열어 `applicationId` 값을 확인하세요.
> (기본값: `com.goldkeycrm` — 아래 STEP 2에서 그대로 사용)

---

### STEP 1 — Firebase 콘솔 프로젝트 생성 (설계사님 직접 진행)

1. https://console.firebase.google.com 접속 (구글 계정 로그인)
2. **[프로젝트 추가]** 클릭
3. 프로젝트 이름: `GoldKey CRM` 입력
4. Google 애널리틱스: 체크 해제해도 무방
5. **[프로젝트 만들기]** 클릭 → 완료까지 약 1분 대기

---

### STEP 2 — Android 앱 등록 + google-services.json 다운로드 (설계사님 직접 진행)

1. Firebase 콘솔 → 프로젝트 홈 화면 중앙 **안드로이드 로봇 아이콘** 클릭
2. **Android 패키지 이름** 입력 (아래 값을 정확히 복사하여 붙여넣기):
   ```
   com.goldkeycrm
   ```
   > ⚠️ 대소문자, 점(.) 하나라도 다르면 연동 실패합니다.
3. 앱 닉네임: `골드키 앱` (선택사항)
4. **[앱 등록]** 클릭
5. **`google-services.json` 다운로드** 버튼 클릭 → 컴퓨터에 저장
6. 다운받은 파일을 아래 경로로 이동 (드래그 앤 드롭):
   ```
   D:\CascadeProjects\crm_app\android\app\google-services.json
   ```
   > ⚠️ `android\app\` 폴더 안에 넣어야 합니다. `android\` 바로 밑이 아닙니다.

---

### STEP 3 — Android 빌드 설정 (STEP 0 완료 후 진행)

#### 3-1. `android/build.gradle` (프로젝트 레벨) 수정
`buildscript { dependencies { ... } }` 블록 안에 추가:
```groovy
classpath 'com.google.gms:google-services:4.4.0'
```

#### 3-2. `android/app/build.gradle` (앱 레벨) 파일 **맨 마지막 줄**에 추가:
```groovy
apply plugin: 'com.google.gms.google-services'
```

---

### STEP 4 — Firestore 데이터베이스 생성

1. Firebase 콘솔 좌측 메뉴 → **Firestore Database** → **[데이터베이스 만들기]**
2. **프로덕션 모드** 선택
3. 위치: **`asia-northeast3` (서울)** 선택
4. **[완료]**

---

### STEP 5 — Firestore 보안 규칙 + 인덱스 배포

터미널에서 실행:
```bash
# Firebase CLI 설치 (최초 1회)
npm install -g firebase-tools

# 구글 계정 로그인
firebase login

# 프로젝트 연결 (목록에서 GoldKey CRM 선택)
firebase use --add

# 규칙 + 인덱스 한 번에 배포
firebase deploy --only firestore
```

---

### STEP 6 — iOS 앱 등록 (Mac + Xcode 있는 경우만)

1. Firebase 콘솔 → **[앱 추가]** → iOS 아이콘
2. iOS 번들 ID:
   ```
   com.goldkeycrm
   ```
3. `GoogleService-Info.plist` 다운로드
4. Xcode → `ios/GoldKeyCRM/` 폴더에 드래그 앤 드롭
   - ✅ "Copy items if needed" 체크
   - ✅ Target Membership: GoldKeyCRM 체크
5. 터미널에서:
   ```bash
   cd ios && pod install && cd ..
   ```

---

## 🚀 앱 빌드 및 실행

```bash
# Metro 번들러 먼저 실행
npx react-native start

# 새 터미널에서 Android 빌드
npx react-native run-android

# iOS (Mac 전용)
npx react-native run-ios
```

---

## 🔒 보안 필수 사항

- `google-services.json` / `GoogleService-Info.plist` 는 **절대 Git에 커밋 금지**
- `.gitignore`에 이미 등록되어 있습니다 ✅

---

## 📂 완성 후 프로젝트 구조

```
crm_app/
├── android/                           ← STEP 0 후 생성
│   ├── build.gradle                   ← STEP 3-1 수정
│   └── app/
│       ├── build.gradle               ← STEP 3-2 수정
│       └── google-services.json       ← STEP 2에서 추가 (설계사님 직접)
├── ios/                               ← STEP 0 후 생성
│   └── GoldKeyCRM/
│       └── GoogleService-Info.plist   ← STEP 6에서 추가 (선택)
├── src/
│   └── utils/
│       └── firebase.js                ✅ 방어 코드 완성
├── firestore.indexes.json             ✅ 복합 인덱스 19개
├── firestore.rules                    ✅ 보안 규칙
├── .env.example                       ✅ 환경 변수 템플릿
└── package.json                       ✅ 패키지 설치 완료
```
