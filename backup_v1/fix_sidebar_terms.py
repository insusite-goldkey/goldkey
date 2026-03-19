"""
사이드바 수정 스크립트
(3) 이용약관 if False: 해제 → 약관 전문 활성화 + 껍데기 텍스트 제거 + (6)내보험다보여 통합
(1) 로그인 후 사이드바 강제 열기 JS 복구 (if False 제거)
(2) 미구현 항목 추가: (7)앱공지, (8)관리자등록 → 로그인 후 사이드바 하단에 삽입
"""

with open("D:/CascadeProjects/app.py", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ──────────────────────────────────────────────────────────────────────────────
# STEP (3-a): 이용약관 expander 껍데기 텍스트 제거 + if False: 해제
# ──────────────────────────────────────────────────────────────────────────────
OLD_3A = (
    '            with st.expander("이용약관 · 서비스 안내", expanded=False):\n'
    '                st.markdown("""\n'
    '    <div style="line-height:1.5;">\n'
    '      <div style="font-size:0.95rem;font-weight:800;color:#1a2d5a;letter-spacing:0.02em;">\n'
    '    📜 이용약관 · 서비스 안내\n'
    '      </div>\n'
    '      <div style="font-size:0.82rem;font-weight:700;color:#c0392b;margin-top:2px;">\n'
    '    (로그인 후 이용 가능)\n'
    '      </div>\n'
    '    </div>\n'
    '    """, unsafe_allow_html=True)\n'
    '                st.caption("로그인 후 사이드바 하단에서 전체 약관을 확인하실 수 있습니다.")\n'
    '\n'
    '            if False:  # 약관 전문 — 로딩 지연 방지용 비활성화 블록\n'
    '                st.markdown("""'
)
NEW_3A = (
    '            with st.expander("📜 이용약관 전문 (로그인 전·후 열람 가능)", expanded=False):\n'
    '                st.markdown("""\n'
    '    <div style="font-size:0.78rem;font-weight:800;color:#1a2d5a;margin-bottom:4px;">\n'
    '    📜 Goldkey AI Masters 2026 이용약관\n'
    '    </div>\n'
    '    <div style="font-size:0.70rem;color:#888;margin-bottom:8px;">\n'
    '    동의 후 서비스 이용 · 로그인 전·후 모두 열람 가능\n'
    '    </div>\n'
    '    """, unsafe_allow_html=True)\n'
    '                st.markdown("""'
)
if OLD_3A in content:
    content = content.replace(OLD_3A, NEW_3A, 1)
    changes += 1
    print("✅ STEP(3-a): 이용약관 껍데기 제거 + if False 해제")
else:
    print("❌ STEP(3-a): 미발견")

# ──────────────────────────────────────────────────────────────────────────────
# STEP (3-b): 제13조 (내보험다보여) 이용약관 끝에 추가
# ──────────────────────────────────────────────────────────────────────────────
OLD_3B = '    *최종 개정일: 2026년 2월*\n            """)'
NEW_3B = (
    '    *최종 개정일: 2026년 2월*\n\n'
    '    ---\n\n'
    '    **제13조 (내보험다보여 서비스 연계 이용)**\n\n'
    '    본 서비스는 금융감독원 **내보험다보여(www.insure.or.kr)** 조회 결과를 상담 보조 자료로 활용할 수 있습니다.\n\n'
    '    - **서비스 목적:** 고객이 직접 조회한 내보험다보여 결과를 AI 분석 참고 자료로 입력 가능\n'
    '    - **데이터 처리:** 조회 데이터는 해당 세션 내 분석 목적으로만 사용되며 서버에 저장되지 않음\n'
    '    - **독립성:** 본 앱은 금융감독원과 제휴·위탁 관계가 없는 독립 보조 도구임\n'
    '    - **이용 방법:** 내보험다보여(www.insure.or.kr) → 본인인증 → 보험계약 조회 → 결과를 앱 내 해당 탭에 입력\n\n'
    '    *최종 개정일: 2026년 3월*\n'
    '            """)'
)
if OLD_3B in content:
    content = content.replace(OLD_3B, NEW_3B, 1)
    changes += 1
    print("✅ STEP(3-b): 내보험다보여 제13조 추가")
else:
    print("❌ STEP(3-b): 약관 끝 미발견")

# ──────────────────────────────────────────────────────────────────────────────
# STEP (1): 로그인 후 사이드바 강제 열기 JS 복구
# ──────────────────────────────────────────────────────────────────────────────
OLD_1 = '    if False and st.session_state.get("_open_sidebar", False):'
NEW_1 = '    if st.session_state.get("_open_sidebar", False):'
if OLD_1 in content:
    content = content.replace(OLD_1, NEW_1, 1)
    changes += 1
    print("✅ STEP(1): 사이드바 강제 열기 JS 복구")
else:
    print("❌ STEP(1): if False and 문자열 미발견")

# ──────────────────────────────────────────────────────────────────────────────
# STEP (2): (7)앱공지 + (8)관리자등록 → 로그인 후 사이드바 하단 삽입
# 삽입 위치: "# ── [GP200 §4] 끝 ──" 바로 다음, st.stop() 직전
# ──────────────────────────────────────────────────────────────────────────────
OLD_2 = (
    '                # ── [GP200 §4] 끝 ─────────────────────────────────────────────\n'
    '\n'
    '        st.stop()'
)
NEW_2 = (
    '                # ── [GP200 §4] 끝 ─────────────────────────────────────────────\n'
    '\n'
    '                st.markdown("---")\n'
    '\n'
    '                # ── (7) 앱 공지 ──────────────────────────────────────────────\n'
    '                with st.expander("📢 앱 공지 · 업데이트 안내", expanded=False):\n'
    '                    st.markdown("""\n'
    '    <div style=\'font-size:0.78rem;font-weight:900;color:#1a2d5a;margin-bottom:6px;\'>\n'
    '    📢 Goldkey AI Masters 2026 — 공지사항\n'
    '    </div>\n'
    '    """, unsafe_allow_html=True)\n'
    '                    st.markdown("""\n'
    '**[2026.03 업데이트]**\n'
    '- GP88 통합 상담 허브 v2 배포 (OCR 고도화, 화법 탭 추가)\n'
    '- 자가복구 엔진 SECTION 9 전역 스코프 복구 완료\n'
    '- 이용약관 전문 사이드바 상시 노출 전환\n\n'
    '**[이용 안내]**\n'
    '- 서비스 문의: insusite@gmail.com\n'
    '- 긴급 문의: 010-3074-2616\n'
    '- 베타 서비스 운영 기간: ~2026.08.31.\n'
    '    """)\n'
    '\n'
    '                # ── (8) 관리자 등록 안내 ─────────────────────────────────────\n'
    '                _sb_is_admin = st.session_state.get("is_admin", False)\n'
    '                with st.expander("⚙️ 관리자 · 계정 관리", expanded=False):\n'
    '                    if _sb_is_admin:\n'
    '                        st.success("✅ 관리자 권한으로 로그인됨")\n'
    '                        st.markdown("""\n'
    '**관리자 전용 메뉴**\n'
    '- 메인 화면 → 관리자 탭에서 회원/지시/헬스체크 관리 가능\n'
    '- 관리자 진단 엔진: 메인 하단 AS요청 박스 활용\n'
    '                        """)\n'
    '                    else:\n'
    '                        st.info("👤 일반 회원으로 로그인됨")\n'
    '                        st.markdown("""\n'
    '**계정 관련 문의**\n'
    '- 이름/연락처 변경: 메인 화면 → 내 정보 탭\n'
    '- 관리자 권한 신청: 010-3074-2616 문의\n'
    '- 탈퇴 및 정보 삭제: insusite@gmail.com\n'
    '                        """)\n'
    '\n'
    '        st.stop()'
)
if OLD_2 in content:
    content = content.replace(OLD_2, NEW_2, 1)
    changes += 1
    print("✅ STEP(2): (7)앱공지 + (8)관리자등록 삽입")
else:
    print("❌ STEP(2): 삽입 위치 미발견")

# ──────────────────────────────────────────────────────────────────────────────
print(f"\n총 {changes}/4 단계 적용 완료")

with open("D:/CascadeProjects/app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("파일 저장 완료")

