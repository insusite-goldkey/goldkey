# 골드키 RAG 전송기 — Chrome Extension 설치 가이드

## 파일 구조

```
chrome_extension/
├── manifest.json     # Manifest V3 선언
├── background.js     # Service Worker — 우클릭 메뉴, PDF fetch, API 전송
├── popup.html        # 설정 팝업 UI
├── popup.js          # 설정 저장/로드 로직
└── icons/
    ├── icon16.png    # ← 직접 준비 필요 (16x16 PNG)
    ├── icon48.png    # ← 직접 준비 필요 (48x48 PNG)
    └── icon128.png   # ← 직접 준비 필요 (128x128 PNG)
```

> 아이콘이 없으면 Chrome이 기본 아이콘을 표시합니다. 임시로 1x1 투명 PNG를 넣어도 동작합니다.

---

## 설치 방법 (개발자 모드)

1. Chrome 주소창에 `chrome://extensions` 입력
2. 우측 상단 **"개발자 모드"** 토글 ON
3. **"압축 해제된 확장 프로그램을 로드합니다"** 클릭
4. `chrome_extension/` 폴더 선택
5. 확장 프로그램 목록에 **"골드키 약관 RAG 전송기"** 표시 확인

---

## 초기 설정

1. Chrome 툴바에서 확장 프로그램 아이콘 클릭 → 팝업 열기
2. **API 서버 주소** 입력:
   - 로컬 개발: `http://localhost:8000/api/upload-policy`
   - 배포 서버: `https://your-api-server.com/api/upload-policy`
3. **API 키** 입력 (FastAPI 서버의 `API_KEY` 환경변수 값)
4. **보험사명** 입력 (선택, 예: 삼성화재)
5. **💾 설정 저장** 클릭

---

## 사용 방법

1. 보험사 공시실 접속 (예: 삼성화재, DB손보, KB손보 등)
2. 약관 PDF 링크 위에서 **우클릭**
3. 컨텍스트 메뉴에서 **"📤 RAG 버킷으로 전송 (골드키)"** 클릭
4. Chrome 알림으로 진행 상황 확인:
   - "다운로드 중..." → PDF를 브라우저 세션으로 가져오는 중
   - "✅ 전송 완료" → GCS 업로드 성공
   - "❌ 전송 실패" → 오류 메시지 확인 후 재시도

---

## 주요 보험사 공시실 URL

| 보험사 | 공시실 URL |
|--------|-----------|
| 삼성화재 | https://www.samsungfire.com/disclosure |
| DB손보 | https://www.idbins.com |
| KB손보 | https://www.kbinsure.co.kr |
| 현대해상 | https://www.hi.co.kr |
| 메리츠화재 | https://www.meritzfire.com |
| 교보생명 | https://www.kyobo.co.kr |
| 삼성생명 | https://www.samsunglife.com |

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| "전송 실패 — HTTP 401" | API 키 불일치 | 팝업에서 API 키 재확인 |
| "전송 실패 — fetch failed" | API 서버 미실행 | `uvicorn main:app` 실행 확인 |
| "PDF 다운로드 실패" | 보험사 세션 만료 | 공시실 로그인 후 재시도 |
| 컨텍스트 메뉴 미표시 | 확장 프로그램 비활성 | `chrome://extensions` 에서 활성화 확인 |
