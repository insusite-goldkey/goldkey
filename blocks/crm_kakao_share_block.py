# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_kakao_share_block.py
# STEP 10: 카카오톡 공유 브릿지 — Supabase 키 연동 + Kakao Link API
# 2026-03-29 신규 생성 - GP 전술 명령 3
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional


def render_kakao_share_button(
    customer_name: str = "고객",
    shortage_summary: str = "",
    emotional_message: str = "",
    coverage_data: Optional[list[dict]] = None,
) -> None:
    """
    [STEP 10] 카카오톡으로 분석 결과 보내기 버튼 렌더링.
    
    Args:
        customer_name: 고객 이름
        shortage_summary: 부족 금액 요약 (예: "총 24,000만원 부족")
        emotional_message: 감성 멘트 (STEP 8에서 생성된 메시지)
        coverage_data: 보장 분석 데이터 (선택)
    """
    # ── 카카오 API 키 안전 로드 ────────────────────────────────────────────
    try:
        from shared_components import get_env_secret
        kakao_js_key = get_env_secret("KAKAO_JS_KEY", "").strip()
        if not kakao_js_key:
            # 폴백: KAKAO_API_KEY 시도
            kakao_js_key = get_env_secret("KAKAO_API_KEY", "").strip()
    except Exception:
        kakao_js_key = ""
    
    # ── 헤더 ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:linear-gradient(135deg, #10b981 0%, #059669 100%);"
        "border-radius:12px;padding:16px;margin:20px 0 16px 0;'>"
        "<div style='font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:6px;'>"
        "💬 STEP 10. 카카오톡으로 분석 결과 보내기</div>"
        "<div style='font-size:0.78rem;color:#d1fae5;line-height:1.6;'>"
        "고객님께 AI 맞춤형 보험 진단 리포트를 카카오톡으로 즉시 공유하세요.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    
    # ── 카카오 키 미설정 시 안내 ───────────────────────────────────────────
    if not kakao_js_key:
        st.warning(
            "⚠️ 카카오톡 공유 기능을 사용하려면 `KAKAO_JS_KEY` 또는 `KAKAO_API_KEY`를 "
            "환경변수 또는 `.streamlit/secrets.toml`에 설정해야 합니다."
        )
        
        # 텍스트 복사 폴백
        fallback_text = f"""
🏆 {customer_name}님의 AI 맞춤형 보험 진단 리포트

{shortage_summary}

{emotional_message}

📊 자세한 분석 결과는 담당 설계사에게 문의하세요.

🔑 GoldKey AI Masters 2026
"""
        st.text_area(
            "📋 카카오톡에 복사하여 전송 (텍스트 모드)",
            value=fallback_text.strip(),
            height=200,
            key="kakao_share_fallback",
        )
        st.caption("💡 카카오 JavaScript SDK 키를 설정하면 원클릭 공유 버튼이 활성화됩니다.")
        return
    
    # ── 메시지 템플릿 준비 ────────────────────────────────────────────────
    # 부족 금액 자동 계산
    total_shortage = 0
    if coverage_data:
        total_shortage = sum(item.get("shortage_amount", 0) for item in coverage_data)
    
    if not shortage_summary and total_shortage > 0:
        shortage_summary = f"현재 총 {total_shortage:,}만원의 보장이 부족한 상황입니다."
    
    if not emotional_message:
        emotional_message = (
            "이 부분의 위험이 진심으로 걱정됩니다. "
            "만약의 상황에서 경제적 어려움이 가중될 수 있어 마음이 무겁습니다."
        )
    
    # 카카오톡 메시지 본문
    kakao_title = f"{customer_name}님의 AI 맞춤형 보험 진단 리포트"
    kakao_description = f"{shortage_summary}\n\n{emotional_message}"
    
    # HQ 앱 URL (딥링크)
    try:
        from shared_components import resolve_hq_app_url
        app_url = resolve_hq_app_url()
    except Exception:
        app_url = "https://goldkey-ai-vje5ef5qka-du.a.run.app"
    
    # ── Kakao Link API 브릿지 HTML/JS ──────────────────────────────────────
    import json
    
    safe_title = json.dumps(kakao_title)
    safe_desc = json.dumps(kakao_description)
    safe_url = json.dumps(app_url)
    safe_key = json.dumps(kakao_js_key)
    
    kakao_html = f"""
<script src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js"
    integrity="sha384-TiCUE00h649CAMonG018J2ujOgDKW/kVWlChEuu4jK2vxfAAD0eZxzCKakxg55G4"
    crossorigin="anonymous"></script>

<style>
.kakao-share-btn {{
    background: linear-gradient(135deg, #FEE500 0%, #FFD700 100%);
    color: #3C1E1E;
    border: none;
    border-radius: 12px;
    padding: 16px 32px;
    font-size: 1.05rem;
    font-weight: 900;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(254, 229, 0, 0.4);
    transition: all 0.3s ease;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}}

.kakao-share-btn:hover {{
    background: linear-gradient(135deg, #FFD700 0%, #FEE500 100%);
    box-shadow: 0 6px 16px rgba(254, 229, 0, 0.6);
    transform: translateY(-2px);
}}

.kakao-share-btn:active {{
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(254, 229, 0, 0.3);
}}

.kakao-status {{
    margin-top: 12px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.85rem;
    text-align: center;
}}

.kakao-status.success {{
    background: #d1fae5;
    color: #065f46;
    border: 1px solid #10b981;
}}

.kakao-status.error {{
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #ef4444;
}}
</style>

<button class="kakao-share-btn" onclick="shareKakao()">
    <span style="font-size:1.4rem;">💬</span>
    <span>카카오톡으로 분석 결과 보내기</span>
</button>

<div id="kakao-status" class="kakao-status" style="display:none;"></div>

<script>
(function() {{
    try {{
        if (!window.Kakao.isInitialized()) {{
            window.Kakao.init({safe_key});
        }}
    }} catch(e) {{
        document.getElementById('kakao-status').innerText = '⚠️ Kakao SDK 초기화 실패: ' + e.message;
        document.getElementById('kakao-status').className = 'kakao-status error';
        document.getElementById('kakao-status').style.display = 'block';
    }}
}})();

function shareKakao() {{
    try {{
        window.Kakao.Share.sendDefault({{
            objectType: 'feed',
            content: {{
                title: {safe_title},
                description: {safe_desc},
                imageUrl: 'https://storage.googleapis.com/goldkey-assets/goldkey_logo.png',
                link: {{
                    mobileWebUrl: {safe_url},
                    webUrl: {safe_url},
                }},
            }},
            buttons: [
                {{
                    title: '자세히 보기',
                    link: {{
                        mobileWebUrl: {safe_url},
                        webUrl: {safe_url},
                    }},
                }},
            ],
        }});
        
        document.getElementById('kakao-status').innerText = '✅ 카카오톡 공유창이 열렸습니다!';
        document.getElementById('kakao-status').className = 'kakao-status success';
        document.getElementById('kakao-status').style.display = 'block';
        
        setTimeout(function() {{
            document.getElementById('kakao-status').style.display = 'none';
        }}, 3000);
        
    }} catch(e) {{
        document.getElementById('kakao-status').innerText = '❌ 공유 실패: ' + e.message;
        document.getElementById('kakao-status').className = 'kakao-status error';
        document.getElementById('kakao-status').style.display = 'block';
    }}
}}
</script>
"""
    
    # ── HTML 컴포넌트 렌더링 ───────────────────────────────────────────────
    components.html(kakao_html, height=120)
    
    # ── 안내 메시지 ───────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#f0fdf4;border-left:4px solid #10b981;"
        "border-radius:8px;padding:12px 16px;margin-top:16px;'>"
        "<div style='font-size:0.82rem;color:#065f46;line-height:1.7;'>"
        "💡 <b>버튼을 클릭하면</b> 카카오톡 공유창이 즉시 열립니다.<br>"
        "📱 모바일에서는 카카오톡 앱이 자동으로 실행됩니다.<br>"
        "💻 PC에서는 QR 코드 또는 친구 선택 화면이 표시됩니다."
        "</div></div>",
        unsafe_allow_html=True,
    )


def render_kakao_share_with_coverage_data(
    customer_name: str,
    coverage_data: list[dict],
) -> None:
    """
    [STEP 10] 보장 분석 데이터와 함께 카카오톡 공유 버튼 렌더링.
    
    Args:
        customer_name: 고객 이름
        coverage_data: 보장 분석 결과 리스트 (STEP 8에서 생성)
    """
    # 부족 금액 자동 계산
    total_shortage = sum(item.get("shortage_amount", 0) for item in coverage_data)
    
    # 요약 메시지 생성
    shortage_summary = f"현재 총 {total_shortage:,}만원의 보장이 부족한 상황입니다."
    
    # 감성 메시지 생성
    emotional_message = (
        f"{customer_name}님, 이 부분의 위험이 진심으로 걱정됩니다. "
        "만약의 상황에서 경제적 어려움이 가중될 수 있어 마음이 무겁습니다. "
        "아래 AI 제안금액을 참고하시어 보장을 보강해 주시길 간곡히 부탁드립니다."
    )
    
    # 카카오톡 공유 버튼 렌더링
    render_kakao_share_button(
        customer_name=customer_name,
        shortage_summary=shortage_summary,
        emotional_message=emotional_message,
        coverage_data=coverage_data,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 테스트용 샘플 함수
# ══════════════════════════════════════════════════════════════════════════════
def test_kakao_share_button():
    """테스트용 카카오톡 공유 버튼 렌더링."""
    st.title("🧪 카카오톡 공유 버튼 테스트")
    
    # 샘플 데이터
    sample_coverage = [
        {"category": "암 진단비", "current_amount": 3000, "shortage_amount": 2000, "recommended_amount": 5000, "insurance_type": "장기"},
        {"category": "뇌혈관 진단비", "current_amount": 2000, "shortage_amount": 3000, "recommended_amount": 5000, "insurance_type": "장기"},
        {"category": "심장 진단비", "current_amount": 1000, "shortage_amount": 4000, "recommended_amount": 5000, "insurance_type": "장기"},
    ]
    
    render_kakao_share_with_coverage_data(
        customer_name="홍길동",
        coverage_data=sample_coverage,
    )


if __name__ == "__main__":
    test_kakao_share_button()
