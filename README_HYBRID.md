# ==========================================================
# 골드키지사 마스터 AI - 하이브리드 모듈화 구조
# ==========================================================

# 사용자 기능: 모바일 최적화 SPA
# 관리자 기능: PC 최적화 멀티페이지

## 📁 프로젝트 구조

```
project_root/
│
├── app.py                    # 사용자 메인 엔트리 (모바일 최적화 SPA)
├── pages/                     # 관리자 전용 (PC 최적화)
│   └── 🛠️_Admin_Console.py   # 관리자 콘솔
│
├── modules/                   # 핵심 기능 모듈 (중복 방지)
│   ├── __init__.py           # 패키지 초기화
│   ├── auth.py               # 로그인/보안
│   ├── ai_engine.py          # Gemini API 로직
│   ├── pdf_generator.py      # PDF 병합 로직
│   └── database.py           # SQLite/CRUD 로직
│
└── assets/                    # 이미지 및 CSS (향후 확장)

```

## 🚀 실행 방법

### 사용자 모드 (모바일 최적화)
```bash
streamlit run app.py
```

### 관리자 모드 (PC 최적화)
```bash
streamlit run pages/🛠️_Admin_Console.py
```

## 📱 사용자 기능 (app.py)

- **모바일 친화적 UI**: segmented_control 메뉴
- **SPA 방식**: 단일 페이지 내 기능 전환
- **기기별 최적화**: 반응형 CSS 적용
- **핵심 기능**: 상담, 분석, 문서 관리, 상속 설계

### 메뉴 구조
- 💬 상담: AI 채팅 인터페이스
- 📊 분석: 문서 업로드 및 분석
- 📄 내문서: 개인 문서 관리
- 🏛️ 상속: 상속/유언 플랜

## 🛠️ 관리자 기능 (pages/Admin_Console.py)

- **PC 최적화**: 사이드바 기반 네비게이션
- **멀티페이지**: Streamlit Pages 기능 활용
- **전체 관리**: 사용자, 문서, 시스템, 보안

### 관리자 메뉴
- 📊 대시보드: 시스템 통계 및 현황
- 👥 사용자 관리: 회원 정보 및 상태
- 📄 문서 관리: 전체 문서 모니터링
- ⚙️ 시스템 설정: AI 및 보안 설정
- 🔐 보안 로그: 접속 및 보안 기록

## 🔧 모듈화 장점

### 1. 코드 중복 방지
- `auth.py`: 인증 로직 중앙화
- `ai_engine.py`: AI 기능 모듈화
- `pdf_generator.py`: PDF 처리 분리
- `database.py`: 데이터베이스 CRUD 통합

### 2. 유지보수성 향상
- 기능별 모듈 분리로 수정 용이
- 테스트 및 디버깅 용이성
- 확장성 및 재사용성

### 3. 보안 강화
- 인증 로직 중앙 관리
- 권한별 기능 분리
- 보안 로그 통합

## 📱 모바일 최적화 특징

### 반응형 디자인
```css
@media (max-width: 768px) {
    .stApp { padding: 0.5rem !important; }
    .stButton>button { width: 100% !important; }
    .stSegmentedControl { flex-direction: column !important; }
}
```

### 터치 친화적 UI
- 큰 버튼 및 입력창
- 간소한 메뉴 구조
- 스와이프 제스처 지원

## 🖥️ PC 최적화 특징

### 관리자 콘솔
- 넓은 화면 활용
- 사이드바 네비게이션
- 상세한 데이터 표시
- 다중 작업 영역

## 🔐 보안 아키텍처

### 인증 체계
- 사용자: 간단 로그인 (이름+연락처)
- 관리자: 비밀번호 인증 (goldkey777)
- 세션 관리 및 타임아웃

### 데이터 보호
- AES-256 암호화
- 프롬프트 인젝션 방어
- 개인정보 마스킹
- 자동 데이터 파기

## 🚀 확장성

### 향후 추가 가능 기능
- 실시간 알림 시스템
- 고급 분석 리포트
- API 연동 확장
- 클라우드 배포 자동화

### 모듈 확장
- `notification.py`: 알림 시스템
- `analytics.py`: 고급 분석
- `api_client.py`: 외부 API 연동
- `deployment.py`: 배포 자동화

## 📋 요구사항

### 필수 라이브러리
```bash
pip install streamlit google-genai cryptography
```

### 선택 라이브러리 (PDF 기능)
```bash
pip install PyMuPDF pdfplumber python-docx
```

### Secrets 설정
```toml
GEMINI_API_KEY = "your-api-key"
ENCRYPTION_KEY = "your-encryption-key"
```

## 🎯 사용 시나리오

### 일반 사용자
1. `streamlit run app.py` 실행
2. 이름과 연락처로 로그인
3. 모바일 친화적 메뉴로 기능 이용
4. 상담, 문서 관리, 상속 설계 활용

### 관리자
1. `streamlit run pages/🛠️_Admin_Console.py` 실행
2. 관리자 비밀번호로 인증
3. PC 최적화 관리자 콘솔 이용
4. 시스템 전체 관리 및 모니터링
