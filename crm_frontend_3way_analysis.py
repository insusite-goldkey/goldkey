"""
CRM Phase 3 프론트엔드 — 가족 통합 보험증권 3-Way 분석
5:5 스플릿 스크린 + Human-in-the-Loop 검수 UI
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json
import time

# 백엔드 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "hq_backend"))

try:
    from hq_backend.core.pdf_generator import ThreeWayPDFGenerator
    from hq_backend.core.kakao_generator import KakaoMessageGenerator
except ImportError:
    print("[WARNING] 백엔드 모듈을 찾을 수 없습니다. 시뮬레이션 모드로 실행됩니다.")
    ThreeWayPDFGenerator = None
    KakaoMessageGenerator = None

def generate_final_outputs():
    """PDF 리포트 및 카카오톡 멘트 생성"""
    try:
        # 1. PDF 생성
        if ThreeWayPDFGenerator:
            pdf_generator = ThreeWayPDFGenerator()
            
            # 가족 데이터 변환
            family_data = []
            for member_name, data in st.session_state.editable_data.items():
                df = pd.DataFrame(data)
                coverage_data = []
                
                for _, row in df.iterrows():
                    coverage_data.append({
                        'category': row['보장항목'],
                        'current': row['현재가입'],
                        'trinity': row['트리니티권장'],
                        'kb_standard': row['KB기준'],
                        'shortage': row['부족금액'],
                        'shortage_rate': row['부족률(%)'],
                        'priority': row['우선순위']
                    })
                
                family_data.append({
                    'name': member_name,
                    'coverage_data': coverage_data
                })
            
            # PDF 생성
            pdf_buffer = pdf_generator.generate_pdf(
                customer_name=list(st.session_state.editable_data.keys())[0],
                agent_name="설계사",
                analysis_date=time.strftime("%Y-%m-%d"),
                family_data=family_data
            )
            
            st.session_state.pdf_buffer = pdf_buffer.getvalue()
        else:
            st.session_state.pdf_buffer = b"PDF Generator not available"
        
        # 2. 카카오톡 멘트 생성
        if KakaoMessageGenerator:
            kakao_gen = KakaoMessageGenerator()
            
            # 긴급 항목 수집
            urgent_items = []
            total_shortage = 0
            
            for member_name, data in st.session_state.editable_data.items():
                df = pd.DataFrame(data)
                total_shortage += df['부족금액'].sum()
                
                urgent_df = df[df['우선순위'] == '긴급'].nlargest(2, '부족금액')
                for _, row in urgent_df.iterrows():
                    urgent_items.append({
                        'category': row['보장항목'],
                        'shortage': row['부족금액']
                    })
            
            # 멘트 생성
            message = kakao_gen.generate_message(
                customer_name=list(st.session_state.editable_data.keys())[0],
                urgent_items=urgent_items[:2],
                total_shortage=total_shortage
            )
            
            st.session_state.kakao_message = message
        else:
            st.session_state.kakao_message = "카카오톡 멘트 생성기를 사용할 수 없습니다."
    
    except Exception as e:
        st.error(f"❌ 생성 중 오류 발생: {str(e)}")
        st.session_state.pdf_buffer = None
        st.session_state.kakao_message = None

def init_session_state():
    """세션 상태 초기화"""
    if 'analysis_stage' not in st.session_state:
        st.session_state.analysis_stage = 'input'  # input, processing, review, completed
    
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    if 'family_income_data' not in st.session_state:
        st.session_state.family_income_data = {}
    
    if 'ocr_results' not in st.session_state:
        st.session_state.ocr_results = []
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    if 'editable_data' not in st.session_state:
        st.session_state.editable_data = None
    
    if 'pdf_buffer' not in st.session_state:
        st.session_state.pdf_buffer = None
    
    if 'kakao_message' not in st.session_state:
        st.session_state.kakao_message = None

def render_header():
    """상단 헤더"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0; text-align: center;'>
            🏥 가족 통합 보험증권 분석 및 3-Way 비교
        </h1>
        <p style='color: #f0f0f0; margin: 10px 0 0 0; text-align: center;'>
            AI 증권 스캔 → 16대 보장 분류 → KB/트리니티 기준 비교
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_left_panel():
    """좌측 패널 — 입력 및 스마트 피더"""
    st.markdown("### 📝 가족 정보 입력")
    
    # 가족 구성원 수 입력
    num_members = st.number_input(
        "가족 구성원 수",
        min_value=1,
        max_value=10,
        value=2,
        help="증권 분석 대상 가족 구성원 수를 입력하세요"
    )
    
    # 구성원별 가처분소득 입력
    st.markdown("#### 💰 구성원별 월 가처분소득 (만원)")
    
    family_income = {}
    for i in range(num_members):
        col1, col2 = st.columns([2, 1])
        with col1:
            member_name = st.text_input(
                f"구성원 {i+1} 이름",
                value=f"가족{i+1}",
                key=f"member_name_{i}"
            )
        with col2:
            income = st.number_input(
                f"가처분소득",
                min_value=0,
                value=150,
                step=10,
                key=f"member_income_{i}",
                label_visibility="collapsed"
            )
        
        family_income[member_name] = income
    
    st.session_state.family_income_data = family_income
    
    st.markdown("---")
    
    # 파일 업로더
    st.markdown("### 📤 증권 이미지 업로드")
    
    uploaded_files = st.file_uploader(
        "증권 이미지를 드래그하거나 선택하세요 (PDF, JPG, PNG)",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="여러 장의 증권을 한 번에 업로드할 수 있습니다"
    )
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.success(f"✅ {len(uploaded_files)}개 파일 업로드 완료")
        
        # 업로드된 파일 목록
        with st.expander("📋 업로드된 파일 목록"):
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"{i}. {file.name} ({file.size / 1024:.1f} KB)")
    
    st.markdown("---")
    
    # 분석 실행 버튼
    can_analyze = len(st.session_state.uploaded_files) > 0 and len(family_income) > 0
    
    if st.button(
        "🚀 AI 3-Way 증권 분석 시작",
        type="primary",
        disabled=not can_analyze,
        use_container_width=True
    ):
        st.session_state.analysis_stage = 'processing'
        st.rerun()
    
    if not can_analyze:
        st.info("💡 증권 이미지를 업로드하고 가족 정보를 입력하면 분석을 시작할 수 있습니다.")

def simulate_ocr_analysis():
    """OCR 분석 시뮬레이션 (실제 환경에서는 master_router 호출)"""
    # 샘플 OCR 결과 (실제로는 master_router.process_family_policies() 호출)
    sample_results = [
        {
            "insured_name": list(st.session_state.family_income_data.keys())[0],
            "insurance_company": "삼성화재",
            "coverages": [
                {"name": "암진단비", "amount": 30000000},
                {"name": "뇌혈관진단비", "amount": 20000000},
                {"name": "허혈성심장진단비", "amount": 15000000},
                {"name": "일반사망", "amount": 50000000}
            ]
        },
        {
            "insured_name": list(st.session_state.family_income_data.keys())[0] if len(st.session_state.family_income_data) > 0 else "가족1",
            "insurance_company": "현대해상",
            "coverages": [
                {"name": "상해사망후유장해", "amount": 30000000},
                {"name": "입원일당", "amount": 30000},
                {"name": "배상책임", "amount": 50000000}
            ]
        }
    ]
    
    if len(st.session_state.family_income_data) > 1:
        sample_results.append({
            "insured_name": list(st.session_state.family_income_data.keys())[1],
            "insurance_company": "KB손해보험",
            "coverages": [
                {"name": "암진단비", "amount": 40000000},
                {"name": "뇌혈관진단비", "amount": 25000000},
                {"name": "배상책임", "amount": 100000000}
            ]
        })
    
    return sample_results

def calculate_3way_comparison_simple(ocr_results, family_income_data):
    """간단한 3-Way 비교 계산 (실제로는 coverage_calculator 사용)"""
    # KB 기준 (간단 버전)
    kb_standards = {
        "일반사망": 100000000,
        "상해사망후유장해": 100000000,
        "암진단비": 50000000,
        "뇌혈관진단비": 30000000,
        "허혈성심장진단비": 30000000,
        "질병수술비_1_5종": 10000000,
        "N대질병수술비": 10000000,
        "입원일당": 50000,
        "배상책임": 100000000,
        "운전자비용": 250000000,
        "표적항암_고액치료": 50000000,
        "치매간병비": 30000000,
        "연금_저축": 500000,
        "주택화재": 100000000,
        "실손의료비": 50000000,
        "기타": 0
    }
    
    # 가족별 현재 가입 현황 집계
    family_coverages = {}
    for result in ocr_results:
        member_name = result["insured_name"]
        if member_name not in family_coverages:
            family_coverages[member_name] = {}
        
        for coverage in result["coverages"]:
            cat = coverage["name"]
            amount = coverage["amount"]
            family_coverages[member_name][cat] = family_coverages[member_name].get(cat, 0) + amount
    
    # 3-Way 비교 결과 생성
    comparison_results = {}
    
    for member_name, coverages in family_coverages.items():
        disposable_income = family_income_data.get(member_name, 150)
        base_premium = disposable_income * 10000 * 0.12
        
        member_results = []
        
        for category, kb_amount in kb_standards.items():
            current = coverages.get(category, 0)
            
            # 트리니티 간단 계산 (실제로는 그룹별 배분)
            trinity = int(base_premium * 0.1)  # 간단 버전
            
            shortage_kb = max(0, kb_amount - current)
            shortage_rate = (shortage_kb / kb_amount * 100) if kb_amount > 0 else 0
            
            if shortage_rate >= 70:
                priority = "긴급"
            elif shortage_rate >= 40:
                priority = "중요"
            else:
                priority = "보통"
            
            member_results.append({
                "보장항목": category,
                "현재가입": current,
                "트리니티권장": trinity,
                "KB기준": kb_amount,
                "부족금액": shortage_kb,
                "부족률(%)": round(shortage_rate, 1),
                "우선순위": priority
            })
        
        # 부족률 높은 순 정렬
        member_results.sort(key=lambda x: x["부족률(%)"], reverse=True)
        
        comparison_results[member_name] = member_results
    
    return comparison_results

def render_right_panel():
    """우측 패널 — 진행 상태 및 HITL 검수 UI"""
    
    if st.session_state.analysis_stage == 'input':
        # 대기 상태
        st.markdown("### 📊 분석 결과")
        st.info("👈 좌측에서 증권을 업로드하고 분석을 시작하세요")
        
        # 안내 이미지 또는 설명
        st.markdown("""
        #### 분석 프로세스
        
        1. **OCR 추출**: Google Vision API로 증권 텍스트 추출
        2. **16대 분류**: AI가 담보를 16대 표준 항목으로 분류
        3. **3-Way 비교**: 현재 가입 vs 트리니티 권장 vs KB 기준
        4. **Human 검수**: 설계사가 최종 데이터 확인 및 수정
        5. **리포트 생성**: 승인된 데이터로 PDF 리포트 생성
        """)
    
    elif st.session_state.analysis_stage == 'processing':
        # 진행 중
        st.markdown("### ⚙️ 분석 진행 중...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 단계별 진행 시뮬레이션
        stages = [
            ("📄 OCR 텍스트 추출 중...", 0.2),
            ("🔍 16대 보장 항목 분류 중...", 0.5),
            ("📊 3-Way 비교 연산 중...", 0.8),
            ("✅ 분석 완료!", 1.0)
        ]
        
        for stage_text, progress in stages:
            status_text.markdown(f"**{stage_text}**")
            progress_bar.progress(progress)
            time.sleep(0.5)
        
        # OCR 분석 실행 (시뮬레이션)
        with st.spinner("데이터 처리 중..."):
            ocr_results = simulate_ocr_analysis()
            st.session_state.ocr_results = ocr_results
            
            # 3-Way 비교 계산
            comparison_results = calculate_3way_comparison_simple(
                ocr_results,
                st.session_state.family_income_data
            )
            st.session_state.analysis_results = comparison_results
            
            # 편집 가능한 데이터 준비
            st.session_state.editable_data = comparison_results
        
        st.success("✅ 분석 완료! 검수 단계로 이동합니다.")
        time.sleep(1)
        st.session_state.analysis_stage = 'review'
        st.rerun()
    
    elif st.session_state.analysis_stage == 'review':
        # 검수 단계
        st.markdown("### 🔍 Human-in-the-Loop 검수")
        
        st.info("💡 AI가 분석한 데이터를 확인하고, 필요시 수정하세요. 수정 후 하단의 승인 버튼을 클릭하세요.")
        
        # 구성원별 탭
        member_tabs = st.tabs(list(st.session_state.editable_data.keys()))
        
        for tab, (member_name, data) in zip(member_tabs, st.session_state.editable_data.items()):
            with tab:
                st.markdown(f"#### {member_name}님 보장 현황")
                
                # 데이터프레임 생성
                df = pd.DataFrame(data)
                
                # 요약 정보
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_shortage = df["부족금액"].sum()
                    st.metric("총 부족 금액", f"{total_shortage:,}원")
                with col2:
                    urgent_count = len(df[df["우선순위"] == "긴급"])
                    st.metric("긴급 항목", f"{urgent_count}개")
                with col3:
                    disposable_income = st.session_state.family_income_data.get(member_name, 0)
                    st.metric("가처분소득", f"{disposable_income:,}만원")
                
                st.markdown("---")
                
                # 데이터 에디터 (HITL 핵심)
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "보장항목": st.column_config.TextColumn("보장항목", width="medium", disabled=True),
                        "현재가입": st.column_config.NumberColumn("현재 가입", format="%d원", width="medium"),
                        "트리니티권장": st.column_config.NumberColumn("트리니티 권장", format="%d원", width="medium", disabled=True),
                        "KB기준": st.column_config.NumberColumn("KB 기준", format="%d원", width="medium", disabled=True),
                        "부족금액": st.column_config.NumberColumn("부족 금액", format="%d원", width="medium", disabled=True),
                        "부족률(%)": st.column_config.NumberColumn("부족률", format="%.1f%%", width="small", disabled=True),
                        "우선순위": st.column_config.SelectboxColumn(
                            "우선순위",
                            options=["긴급", "중요", "보통"],
                            width="small"
                        )
                    },
                    key=f"data_editor_{member_name}"
                )
                
                # 수정된 데이터 저장
                st.session_state.editable_data[member_name] = edited_df.to_dict('records')
                
                # 상위 5개 부족 항목 하이라이트
                st.markdown("##### 🎯 최우선 보완 항목 (상위 5개)")
                top_5 = edited_df.nlargest(5, "부족률(%)")
                
                for idx, row in top_5.iterrows():
                    priority_color = {
                        "긴급": "#FF6B6B",
                        "중요": "#FFD93D",
                        "보통": "#6BCF7F"
                    }.get(row["우선순위"], "#E0E0E0")
                    
                    st.markdown(f"""
                    <div style='background-color: {priority_color}; padding: 10px; border-radius: 5px; margin-bottom: 5px;'>
                        <strong>{row["보장항목"]}</strong>: {row["부족금액"]:,}원 부족 ({row["부족률(%)"]:.1f}%, {row["우선순위"]})
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 승인 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "✅ 최종 데이터 승인 및 리포트 생성",
                type="primary",
                use_container_width=True
            ):
                # PDF 및 카카오톡 멘트 생성
                with st.spinner("📄 PDF 리포트 및 카카오톡 멘트 생성 중..."):
                    generate_final_outputs()
                
                st.session_state.analysis_stage = 'completed'
                st.rerun()
        
        # 재분석 버튼
        if st.button("🔄 처음부터 다시 분석", use_container_width=True):
            # 세션 초기화
            st.session_state.analysis_stage = 'input'
            st.session_state.uploaded_files = []
            st.session_state.ocr_results = []
            st.session_state.analysis_results = None
            st.session_state.editable_data = None
            st.rerun()
    
    elif st.session_state.analysis_stage == 'completed':
        # 완료 단계
        st.markdown("### ✅ 분석 완료")
        
        st.success("🎉 데이터가 승인되었습니다! 리포트를 생성합니다.")
        
        # 최종 결과 요약
        st.markdown("#### 📋 최종 분석 요약")
        
        total_members = len(st.session_state.editable_data)
        total_shortage = 0
        total_urgent = 0
        
        for member_name, data in st.session_state.editable_data.items():
            df = pd.DataFrame(data)
            total_shortage += df["부족금액"].sum()
            total_urgent += len(df[df["우선순위"] == "긴급"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("가족 구성원", f"{total_members}명")
        with col2:
            st.metric("가족 전체 부족 금액", f"{total_shortage:,}원")
        with col3:
            st.metric("긴급 보완 항목", f"{total_urgent}개")
        
        st.markdown("---")
        
        # PDF 다운로드 버튼
        if 'pdf_buffer' in st.session_state and st.session_state.pdf_buffer:
            st.download_button(
                label="📄 PDF 리포트 다운로드",
                data=st.session_state.pdf_buffer,
                file_name=f"가족_보험_3Way_분석_리포트_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.warning("⚠️ PDF 생성 중 오류가 발생했습니다.")
        
        # 카카오톡 멘트 표시
        if 'kakao_message' in st.session_state and st.session_state.kakao_message:
            st.markdown("### 💬 카카오톡 전송용 멘트")
            st.info("아래 멘트를 복사하여 고객에게 전송하세요.")
            
            st.code(st.session_state.kakao_message, language=None)
            
            # 복사 버튼 (시각적 표시)
            if st.button("📋 클립보드에 복사", use_container_width=True):
                st.success("✅ 멘트가 클립보드에 복사되었습니다! (수동으로 복사해주세요)")
        else:
            st.warning("⚠️ 카카오톡 멘트 생성 중 오류가 발생했습니다.")
        
        # 새 분석 시작
        if st.button("🔄 새로운 분석 시작", use_container_width=True):
            st.session_state.analysis_stage = 'input'
            st.session_state.uploaded_files = []
            st.session_state.ocr_results = []
            st.session_state.analysis_results = None
            st.session_state.editable_data = None
            st.rerun()

def main():
    """메인 함수"""
    st.set_page_config(
        page_title="CRM 3-Way 증권 분석",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # [GP-DESIGN-V4] 반응형 디자인 시스템 주입
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from shared_components import inject_global_responsive_design
        inject_global_responsive_design()
    except Exception:
        pass
    
    # 세션 상태 초기화
    init_session_state()
    
    # 헤더
    render_header()
    
    # 5:5 스플릿 레이아웃
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        st.markdown("## 📥 입력 & 스마트 피더")
        render_left_panel()
    
    with right_col:
        st.markdown("## 📊 출력 & Human 검수")
        render_right_panel()

if __name__ == "__main__":
    main()
