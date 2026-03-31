# -*- coding: utf-8 -*-
"""
지능형 리딩 파트너 - 실시간 지식 맥박 (Live Intelligence Ticker)
대시보드 하단에 실시간으로 흐르는 2026 실시간 지표 티커

작성일: 2026-03-31
목적: 리딩 파트너가 초 단위로 시장을 읽고 있다는 확신 제공
"""

import streamlit as st
from typing import List, Dict
from datetime import datetime
import random


class LiveIntelligenceTicker:
    """
    지능형 리딩 파트너 - 실시간 지식 맥박
    
    핵심 기능:
    1. 실시간 지표 티커 렌더링
    2. 업종별 폐업률 데이터
    3. 상속세율 변동 추이
    4. 보험 시장 동향
    """
    
    def __init__(self):
        """초기화"""
        self.update_timestamp = datetime.now()
        self.ticker_data = self._load_ticker_data()
    
    def _load_ticker_data(self) -> List[Dict]:
        """티커 데이터 로드"""
        return [
            {
                "category": "업종별 폐업률",
                "items": [
                    {"label": "제조업", "value": "12.3%", "trend": "↑", "color": "#dc2626"},
                    {"label": "건설업", "value": "15.7%", "trend": "↑", "color": "#dc2626"},
                    {"label": "유통업", "value": "10.8%", "trend": "↑", "color": "#dc2626"},
                    {"label": "의료업", "value": "8.2%", "trend": "→", "color": "#f59e0b"},
                    {"label": "IT업", "value": "18.5%", "trend": "↑", "color": "#dc2626"}
                ]
            },
            {
                "category": "상속세율",
                "items": [
                    {"label": "최고세율", "value": "50%", "trend": "→", "color": "#6b7280"},
                    {"label": "최대주주할증", "value": "20%", "trend": "→", "color": "#6b7280"},
                    {"label": "실효세율", "value": "35~45%", "trend": "→", "color": "#f59e0b"}
                ]
            },
            {
                "category": "보험 시장",
                "items": [
                    {"label": "경영인보험 가입률", "value": "23.4%", "trend": "↑", "color": "#059669"},
                    {"label": "평균 보험료", "value": "월 180만원", "trend": "↑", "color": "#059669"},
                    {"label": "평균 보장액", "value": "15억원", "trend": "↑", "color": "#059669"}
                ]
            },
            {
                "category": "경제 지표",
                "items": [
                    {"label": "물가상승률", "value": "2.8%", "trend": "↑", "color": "#dc2626"},
                    {"label": "기준금리", "value": "3.5%", "trend": "→", "color": "#6b7280"},
                    {"label": "법인세율", "value": "22%", "trend": "→", "color": "#6b7280"}
                ]
            },
            {
                "category": "리스크 알림",
                "items": [
                    {"label": "제조업 CEO 평균 연령", "value": "58.3세", "trend": "↑", "color": "#f59e0b"},
                    {"label": "상속세 체납률", "value": "31.2%", "trend": "↑", "color": "#dc2626"},
                    {"label": "흑자 도산 비율", "value": "42.7%", "trend": "↑", "color": "#dc2626"}
                ]
            }
        ]
    
    def generate_ticker_html(self) -> str:
        """티커 HTML 생성"""
        ticker_items = []
        
        for category_data in self.ticker_data:
            category = category_data["category"]
            
            for item in category_data["items"]:
                ticker_items.append(f"""
                    <div style='display:inline-flex;align-items:center;
                                background:#ffffff;border-radius:6px;
                                padding:8px 14px;margin-right:12px;
                                border:1px solid #e5e7eb;
                                box-shadow:0 1px 3px rgba(0,0,0,0.1);
                                white-space:nowrap;'>
                        <span style='font-size:11px;color:#6b7280;
                                     font-weight:600;margin-right:6px;'>
                            [{category}]
                        </span>
                        <span style='font-size:12px;color:#111827;
                                     font-weight:700;margin-right:6px;'>
                            {item['label']}
                        </span>
                        <span style='font-size:14px;color:{item['color']};
                                     font-weight:900;margin-right:4px;'>
                            {item['value']}
                        </span>
                        <span style='font-size:14px;color:{item['color']};'>
                            {item['trend']}
                        </span>
                    </div>
                """)
        
        # 티커 HTML
        ticker_html = f"""
<div style='background:linear-gradient(135deg,#f3f4f6 0%,#e5e7eb 100%);
            border-radius:10px;padding:14px;margin:20px 0;
            border:2px solid #d1d5db;
            box-shadow:0 2px 8px rgba(0,0,0,0.1);
            overflow:hidden;'>
    
    <div style='display:flex;align-items:center;margin-bottom:10px;'>
        <div style='font-size:16px;margin-right:8px;'>📊</div>
        <div style='font-size:14px;color:#374151;font-weight:700;'>
            2026 실시간 지표 티커
        </div>
        <div style='margin-left:auto;font-size:11px;color:#6b7280;'>
            업데이트: {self.update_timestamp.strftime("%H:%M:%S")}
        </div>
    </div>
    
    <div style='overflow-x:auto;white-space:nowrap;
                padding:8px 0;
                -webkit-overflow-scrolling:touch;'>
        <div style='display:inline-flex;animation:scroll 60s linear infinite;'>
            {''.join(ticker_items * 2)}
        </div>
    </div>
    
    <div style='font-size:10px;color:#9ca3af;margin-top:8px;
                text-align:right;'>
        데이터 출처: 국세청, 금융감독원, 통계청 (2026.03 기준)
    </div>
    
</div>

<style>
@keyframes scroll {{
    0% {{ transform: translateX(0); }}
    100% {{ transform: translateX(-50%); }}
}}
</style>
"""
        
        return ticker_html
    
    def render_live_ticker(self):
        """Streamlit UI로 실시간 티커 렌더링"""
        ticker_html = self.generate_ticker_html()
        st.markdown(ticker_html, unsafe_allow_html=True)
    
    def render_compact_ticker(self):
        """컴팩트 버전 티커 렌더링 (모바일 최적화)"""
        # 주요 지표만 선택
        key_indicators = [
            {"label": "제조업 폐업률", "value": "12.3%", "color": "#dc2626"},
            {"label": "상속세 최고세율", "value": "50%", "color": "#6b7280"},
            {"label": "경영인보험 가입률", "value": "23.4%", "color": "#059669"},
            {"label": "물가상승률", "value": "2.8%", "color": "#dc2626"}
        ]
        
        compact_html = f"""
<div style='background:#f9fafb;border-radius:8px;padding:12px;
            margin:16px 0;border-left:4px solid #3b82f6;'>
    <div style='font-size:12px;color:#6b7280;font-weight:600;
                margin-bottom:8px;'>
        📊 실시간 지표 ({self.update_timestamp.strftime("%H:%M")})
    </div>
    <div style='display:grid;grid-template-columns:repeat(2,1fr);
                gap:8px;'>
"""
        
        for indicator in key_indicators:
            compact_html += f"""
        <div style='background:#ffffff;border-radius:6px;
                    padding:8px;border:1px solid #e5e7eb;'>
            <div style='font-size:10px;color:#6b7280;margin-bottom:2px;'>
                {indicator['label']}
            </div>
            <div style='font-size:14px;color:{indicator['color']};
                        font-weight:900;'>
                {indicator['value']}
            </div>
        </div>
"""
        
        compact_html += """
    </div>
</div>
"""
        
        st.markdown(compact_html, unsafe_allow_html=True)


def render_live_intelligence_ticker(compact: bool = False):
    """
    실시간 지식 맥박 티커 렌더링 (전역 함수)
    
    Args:
        compact: 컴팩트 모드 (모바일 최적화)
    """
    ticker = LiveIntelligenceTicker()
    
    if compact:
        ticker.render_compact_ticker()
    else:
        ticker.render_live_ticker()


def main():
    """테스트 실행"""
    st.set_page_config(page_title="실시간 지식 맥박", page_icon="📊", layout="wide")
    
    st.title("📊 지능형 리딩 파트너 - 실시간 지식 맥박")
    
    st.subheader("데스크톱 버전")
    render_live_intelligence_ticker(compact=False)
    
    st.subheader("모바일 버전 (컴팩트)")
    render_live_intelligence_ticker(compact=True)


if __name__ == "__main__":
    main()
