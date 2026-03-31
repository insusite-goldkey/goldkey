# CRM 랜딩페이지 설치 가이드

> **작성일**: 2026-03-31  
> **대상**: Goldkey CRM 앱 (https://goldkey-crm-vje5ef5qka-du.a.run.app/)

---

## ✅ 완료된 작업

### 1. 랜딩페이지 코드 구현 완료
- ✅ `_crm_load_splash_b64()` 함수: 이미지 base64 인코딩 및 캐싱
- ✅ `_crm_render_landing_page()` 함수: 기기별 이미지 분기 렌더링
- ✅ 진입점 로직: 미인증 + 랜딩 미완료 시 자동 노출
- ✅ 타임아웃 보호: 랜딩페이지 노출 중 타임아웃 체크 건너뛰기
- ✅ 사이드바 지연: 랜딩페이지 완료 후 사이드바 렌더링
- ✅ 자동 전환: 2.5초 후 자동으로 로그인 화면 전환

---

## 📸 이미지 저장 방법

### Step 1: 이미지 다운로드

업로드하신 2개의 이미지를 다운로드하세요:
- **Image 1 (태블릿 가로)**: 16:9 비율, 전문 보험 컨설턴트 이미지
- **Image 2 (핸드폰 세로)**: 9:16 비율, 동일한 컨설턴트 이미지

### Step 2: 이미지 저장 위치

다운로드한 이미지를 다음 경로에 저장하세요:

```
d:\CascadeProjects\assets\crm_splash_tablet.jpg   (Image 1 - 태블릿용)
d:\CascadeProjects\assets\crm_splash_mobile.jpg   (Image 2 - 핸드폰용)
```

**중요:**
- 파일명을 정확히 `crm_splash_tablet.jpg`, `crm_splash_mobile.jpg`로 저장
- 파일 형식은 `.jpg` 또는 `.webp` 권장 (용량 최적화)
- `assets` 폴더가 없으면 생성

### Step 3: 이미지 최적화 (선택사항)

더 빠른 로딩을 위해 이미지를 WebP로 변환하는 것을 권장합니다:

**PowerShell에서 실행:**
```powershell
# WebP 변환 (ImageMagick 필요)
magick convert d:\CascadeProjects\assets\crm_splash_tablet.jpg -quality 85 d:\CascadeProjects\assets\crm_splash_tablet.webp
magick convert d:\CascadeProjects\assets\crm_splash_mobile.jpg -quality 85 d:\CascadeProjects\assets\crm_splash_mobile.webp
```

WebP로 변환한 경우, `crm_app_impl.py` line 208~209 수정:
```python
_mobile_src = _crm_load_splash_b64("crm_splash_mobile.webp")
_tablet_src = _crm_load_splash_b64("crm_splash_tablet.webp")
```

---

## 🧪 로컬 테스트

### Step 1: 로컬 서버 실행

```powershell
cd d:\CascadeProjects
streamlit run crm_app.py --server.port 8502
```

### Step 2: 브라우저 테스트

1. **PC 브라우저**: http://localhost:8502
2. **모바일 시뮬레이션**: Chrome DevTools (F12) → 모바일 모드

### Step 3: 확인 사항

- [ ] 앱 접속 시 즉시 랜딩페이지 노출 (백화현상 없음)
- [ ] 핸드폰 세로 모드: `crm_splash_mobile.jpg` 이미지 표시
- [ ] 태블릿 가로 모드: `crm_splash_tablet.jpg` 이미지 표시
- [ ] 2.5초 후 자동으로 로그인 화면 전환
- [ ] "🚀 시작하기" 버튼 클릭 시 즉시 전환
- [ ] 로그인 후 다시 접속 시 랜딩페이지 건너뜀 (세션 유지)

---

## 🚀 배포

### Step 1: Git 커밋

```powershell
cd d:\CascadeProjects
git add crm_app_impl.py
git add assets/crm_splash_*.jpg
git commit -m "feat: CRM 랜딩페이지 추가 - 기기별 이미지 분기"
```

### Step 2: CRM 배포 스크립트 실행

```powershell
powershell -ExecutionPolicy Bypass -File "d:\CascadeProjects\deploy_crm.ps1"
```

### Step 3: 배포 확인

1. Cloud Run 빌드 완료 대기 (약 3~5분)
2. 프로덕션 URL 접속: https://goldkey-crm-vje5ef5qka-du.a.run.app/
3. 모바일 기기에서 직접 테스트

---

## 🎯 기대 효과

### Before (현재)
- 백화현상 지속 시간: **6~8초**
- 사용자 경험: ⭐⭐ (불안정, 전문성 부족)

### After (랜딩페이지 적용)
- 백화현상 지속 시간: **0초** (즉시 이미지 노출)
- 체감 로딩 시간: **2.5초** (자동 전환)
- 사용자 경험: ⭐⭐⭐⭐⭐ (전문적, 안정적)

---

## 🔧 기술 세부사항

### 기기 감지 로직

```css
/* 기본 (모바일 세로) */
background: url("crm_splash_mobile.jpg") center/cover no-repeat;

/* 태블릿/가로 모드 (600px 이상 + 가로세로 비율 3:4 이상) */
@media (min-aspect-ratio:3/4) and (min-width:600px) {
  background: url("crm_splash_tablet.jpg") center/cover no-repeat;
}
```

### 자동 전환 메커니즘

1. **JavaScript 타이머**: 2.5초 후 `?_lp_auto=1` 파라미터 추가
2. **Python 감지**: `st.query_params.get("_lp_auto")` 체크
3. **세션 플래그**: `_crm_lp_landing = True` 설정
4. **Rerun**: `st.rerun()` 호출로 로그인 화면 전환

### 세션 관리

```python
# 랜딩 완료 플래그
st.session_state["_crm_lp_landing"] = True

# 다음 접속 시 랜딩 건너뜀
_landing_done = st.session_state.get("_crm_lp_landing", False)
if not _is_logged_in and not _landing_done:
    _crm_render_landing_page()
    st.stop()
```

---

## ⚠️ 주의사항

### 1. 이미지 파일명 정확히 일치

```
✅ 올바른 파일명:
- crm_splash_tablet.jpg
- crm_splash_mobile.jpg

❌ 잘못된 파일명:
- CRM_Splash_Tablet.jpg (대소문자 불일치)
- crm-splash-tablet.jpg (하이픈 대신 언더스코어)
- tablet_splash.jpg (순서 다름)
```

### 2. 이미지 용량 최적화

- **권장 용량**: 각 이미지 500KB 이하
- **최대 용량**: 1MB 이하
- **해상도**: 
  - 모바일: 1080x1920 (Full HD 세로)
  - 태블릿: 1920x1080 (Full HD 가로)

### 3. 폴백 배경

이미지 로드 실패 시 자동으로 그라디언트 배경 표시:
```css
background: linear-gradient(160deg, #050d1a 0%, #0a1e35 55%, #0d2747 100%);
```

---

## 🐛 문제 해결

### 문제 1: 이미지가 표시되지 않음

**원인**: 파일 경로 또는 파일명 불일치

**해결책**:
1. 파일명 확인: `crm_splash_tablet.jpg`, `crm_splash_mobile.jpg`
2. 파일 위치 확인: `d:\CascadeProjects\assets\`
3. 파일 존재 확인: PowerShell에서 `ls d:\CascadeProjects\assets\crm_splash_*.jpg`

### 문제 2: 랜딩페이지가 계속 반복됨

**원인**: `_crm_lp_landing` 플래그가 설정되지 않음

**해결책**:
1. 브라우저 콘솔 확인 (F12)
2. `st.query_params` 처리 로직 확인 (line 276~281)
3. 세션 초기화: 브라우저 쿠키 삭제 후 재접속

### 문제 3: 스크롤이 잠김

**원인**: CSS `overflow:hidden` 충돌

**해결책**:
랜딩페이지 CSS에 이미 `overscroll-behavior` 설정되어 있음 (line 260~263)
- 추가 조치 불필요
- 만약 문제 발생 시 `touchmove` 이벤트 리스너 사용 금지

---

## 📋 체크리스트

### 배포 전 필수 확인

- [ ] 이미지 파일 2개 저장 완료 (`crm_splash_tablet.jpg`, `crm_splash_mobile.jpg`)
- [ ] 로컬 테스트 완료 (http://localhost:8502)
- [ ] 모바일 시뮬레이션 테스트 완료 (Chrome DevTools)
- [ ] 자동 전환 2.5초 타이밍 확인
- [ ] 수동 버튼 클릭 정상 작동 확인
- [ ] 로그인 후 재접속 시 랜딩 건너뜀 확인
- [ ] Git 커밋 완료
- [ ] `deploy_crm.ps1` 실행 준비

### 배포 후 확인

- [ ] Cloud Run 빌드 성공 확인
- [ ] 프로덕션 URL 접속 테스트
- [ ] 실제 모바일 기기 테스트 (핸드폰 + 태블릿)
- [ ] 백화현상 제거 확인
- [ ] 로딩 시간 2.5초 이내 확인

---

## 📞 지원

문제 발생 시 다음 정보를 포함하여 보고:
1. 에러 메시지 (브라우저 콘솔 F12)
2. 이미지 파일 경로 및 용량
3. 테스트 환경 (로컬/프로덕션, PC/모바일)
4. 재현 단계

---

**작성자**: Cascade AI Assistant  
**최종 수정**: 2026-03-31
