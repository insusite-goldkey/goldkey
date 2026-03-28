# 🔧 CRM 로그인 로직 치명적 버그 수정 완료

## 🐛 발견된 문제

### 1. HQ로 리다이렉트되는 문제
- **증상**: 관리자 로그인 시 "✅ 인증 완료 — HQ 전문 분석 시스템으로 이동합니다..." 메시지 표시
- **원인**: `shared_components.py` line 1666-1686에서 `resolve_hq_app_url()` 호출 후 HQ로 강제 리다이렉트
- **위치**: `render_member_emergency_btn()` 함수 내 관리자 로그인 처리 로직

### 2. 두 번 클릭해야 로그인되는 문제
- **증상**: 첫 번째 클릭 시 세션 저장만 되고, 두 번째 클릭해야 대시보드 진입
- **원인**: 세션 저장 후 `st.rerun()` 호출 없이 `st.stop()` 또는 리다이렉트 시도
- **결과**: 사용자가 버튼을 다시 클릭해야 세션 상태가 반영됨

## ✅ 수정 내용

### 1. shared_components.py (Line 1665-1667)

**수정 전**:
```python
if _adm_auth_ok:
    _hq_dest = resolve_hq_app_url()
    _st3.success("✅ 인증 완료 — HQ 전문 분석 시스템으로 이동합니다...")
    try:
        import streamlit.components.v1 as _sc_adm
        _sc_adm.html(
            f'<script>window.top.location.href="{_hq_dest}";</script>',
            height=0,
        )
    except Exception:
        pass
    _st3.markdown(
        f"<div style='text-align:center;margin:14px 0;'>"
        f"<a href='{_hq_dest}' target='_self' "
        f"style='display:inline-block;background:linear-gradient(135deg,#1e3a8a,#2563eb);"
        f"color:#fff;padding:13px 30px;border-radius:12px;font-weight:900;"
        f"font-size:clamp(0.9rem,3vw,1.05rem);text-decoration:none;"
        f"box-shadow:0 3px 10px rgba(30,58,138,0.3);'>"
        f"🏗️ HQ 전문 상담 파트로 이동 →</a></div>",
        unsafe_allow_html=True,
    )
    _st3.stop()
```

**수정 후**:
```python
if _adm_auth_ok:
    _st3.success("✅ 관리자 인증 완료 — CRM 대시보드로 이동합니다...")
    _st3.rerun()
```

### 2. 세션 상태 즉시 저장 및 리런

**핵심 변경**:
- ✅ HQ 리다이렉트 로직 완전 제거
- ✅ `st.stop()` 제거 → `st.rerun()` 사용
- ✅ 세션 저장 후 즉시 앱 재실행으로 대시보드 진입
- ✅ 메시지 변경: "HQ 전문 분석 시스템" → "CRM 대시보드"

## 🔍 추가 검색 필요 항목

### HQ 리다이렉트 관련 코드 (전체 검색 결과)

1. **shared_components.py**:
   - Line 343: `def resolve_hq_app_url()` - 함수 정의 (유지 필요 - 다른 곳에서 사용)
   - Line 357: `HQ_APP_URL = resolve_hq_app_url()` - 전역 변수 (유지 필요)
   - Line 2176: "🚀 [HQ]앱 이동 — 심화상담" - 딥링크 버튼 (정상 기능)

2. **crm_app_impl.py**:
   - Line 1348: "# ── [GP-FOOTER] 피드백·오류신고 + [HQ] 이동" - 주석 (정상)
   - Line 3280: "# ── [GP-FOOTER] 고객 업무 화면 — 피드백·오류신고 + [HQ] 이동" - 주석 (정상)

**결론**: 로그인 로직 외 HQ 이동 기능은 정상적인 딥링크/브릿지 기능이므로 유지

## 📊 테스트 시나리오

### 관리자 로그인
1. CRM 앱 접속: https://goldkey-crm-vje5ef5qka-du.a.run.app
2. 하단 "🔐 관리자 로그인" 클릭
3. ID: admin, 코드: (ADMIN_CODE 또는 MASTER_CODE) 입력
4. "🔐 관리자 로그인" 버튼 **1회 클릭**
5. **예상 결과**: "✅ 관리자 인증 완료 — CRM 대시보드로 이동합니다..." 메시지 후 즉시 대시보드 진입

### 일반 회원 로그인
1. CRM 앱 접속
2. 이름 + 연락처 입력
3. "🔐 로그인" 버튼 **1회 클릭**
4. **예상 결과**: 즉시 CRM 대시보드 진입 (HQ로 이동하지 않음)

## 🚀 다음 단계

1. ✅ shared_components.py 수정 완료
2. ⏳ CRM 배포 (deploy_crm.ps1)
3. ⏳ 라이브 테스트
4. ⏳ 일반 회원 로그인 동작 확인

---

**수정 완료 시각**: 2026-03-27 22:58 KST
