"""
[Phase 4] 3-Way 보험 분석 PDF 리포트 생성기

ReportLab을 사용하여 최종 승인된 3-Way 비교 결과를 PDF로 렌더링
"""
from __future__ import annotations
from typing import Dict, List, Any
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("[WARNING] reportlab not installed. Install with: pip install reportlab")


class ThreeWayPDFGenerator:
    """3-Way 보험 분석 PDF 리포트 생성기"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_korean_font()
        self._setup_custom_styles()
    
    def _setup_korean_font(self):
        """한글 폰트 설정 (시스템 폰트 사용)"""
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))
            self.korean_font = 'NanumGothic'
        except:
            self.korean_font = 'Helvetica'
    
    def _setup_custom_styles(self):
        """커스텀 스타일 정의"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.korean_font,
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontName=self.korean_font,
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['BodyText'],
            fontName=self.korean_font,
            fontSize=10,
            leading=14
        )
    
    def generate_pdf(
        self,
        customer_name: str,
        agent_name: str,
        analysis_date: str,
        family_data: List[Dict[str, Any]],
        output_path: str = None
    ) -> BytesIO:
        """
        PDF 리포트 생성
        
        Args:
            customer_name: 고객명
            agent_name: 설계사명
            analysis_date: 분석 일자
            family_data: 가족 구성원별 3-Way 비교 데이터
            output_path: 파일 저장 경로 (None이면 BytesIO 반환)
        
        Returns:
            BytesIO: PDF 바이트 스트림
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer if not output_path else output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # 1. 표지
        story.extend(self._create_cover_page(customer_name, agent_name, analysis_date))
        story.append(PageBreak())
        
        # 2. 가족 구성원별 3-Way 대조표
        for member_data in family_data:
            story.extend(self._create_member_analysis(member_data))
            story.append(Spacer(1, 0.3*inch))
        
        # 3. 긴급 항목 요약
        story.extend(self._create_urgent_summary(family_data))
        story.append(PageBreak())
        
        # 4. 면책 조항
        story.extend(self._create_disclaimer())
        
        doc.build(story)
        
        if output_path:
            return None
        else:
            buffer.seek(0)
            return buffer
    
    def _create_cover_page(self, customer_name: str, agent_name: str, analysis_date: str) -> List:
        """표지 페이지 생성"""
        elements = []
        
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("🛡️ 가족 보험 3-Way 분석 리포트", self.title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        info_data = [
            ["고객명", customer_name],
            ["담당 설계사", agent_name],
            ["분석 일자", analysis_date]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a237e')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5'))
        ]))
        
        elements.append(info_table)
        
        return elements
    
    def _create_member_analysis(self, member_data: Dict[str, Any]) -> List:
        """구성원별 분석 테이블 생성"""
        elements = []
        
        member_name = member_data.get('name', '구성원')
        elements.append(Paragraph(f"📋 {member_name}님 보장 분석", self.heading_style))
        
        # 테이블 헤더
        table_data = [
            ["보장항목", "현재가입", "트리니티권장", "KB기준", "부족금액", "부족률(%)", "우선순위"]
        ]
        
        # 데이터 행 추가
        for row in member_data.get('coverage_data', []):
            table_data.append([
                row.get('category', ''),
                f"{row.get('current', 0):,}원",
                f"{row.get('trinity', 0):,}원",
                f"{row.get('kb_standard', 0):,}원",
                f"{row.get('shortage', 0):,}원",
                f"{row.get('shortage_rate', 0):.1f}%",
                row.get('priority', '보통')
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_urgent_summary(self, family_data: List[Dict[str, Any]]) -> List:
        """긴급 항목 요약 브리핑"""
        elements = []
        
        elements.append(Paragraph("🚨 우선 보완 필요 항목 (긴급)", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        urgent_items = []
        for member in family_data:
            for row in member.get('coverage_data', []):
                if row.get('priority') == '긴급':
                    urgent_items.append({
                        'member': member.get('name'),
                        'category': row.get('category'),
                        'shortage': row.get('shortage', 0)
                    })
        
        if urgent_items:
            urgent_data = [["구성원", "보장항목", "부족금액"]]
            for item in urgent_items[:5]:  # 상위 5개만
                urgent_data.append([
                    item['member'],
                    item['category'],
                    f"{item['shortage']:,}원"
                ])
            
            urgent_table = Table(urgent_data, colWidths=[2*inch, 3*inch, 2*inch])
            urgent_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c62828')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(urgent_table)
        else:
            elements.append(Paragraph("✅ 긴급 보완 항목이 없습니다.", self.body_style))
        
        return elements
    
    def _create_disclaimer(self) -> List:
        """면책 조항"""
        elements = []
        
        elements.append(Paragraph("⚠️ 면책 조항", self.heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        disclaimer_text = """
        본 분석 결과는 AI가 스캔된 증권을 바탕으로 산출한 참고용 자료이며, 
        실제 보상 및 법적 효력과 다를 수 있습니다. 
        정확한 보장 내용은 반드시 증권 원본 및 약관을 확인하시기 바랍니다.
        
        본 리포트는 goldkey_Ai_masters2026 시스템에 의해 자동 생성되었습니다.
        """
        
        elements.append(Paragraph(disclaimer_text, self.body_style))
        
        return elements


if __name__ == "__main__":
    # 테스트 코드
    generator = ThreeWayPDFGenerator()
    
    test_data = [
        {
            'name': '홍길동',
            'coverage_data': [
                {
                    'category': '질병수술비_1_5종',
                    'current': 0,
                    'trinity': 8000000,
                    'kb_standard': 10000000,
                    'shortage': 10000000,
                    'shortage_rate': 100.0,
                    'priority': '긴급'
                },
                {
                    'category': '상해사망후유장해',
                    'current': 30000000,
                    'trinity': 80000000,
                    'kb_standard': 100000000,
                    'shortage': 70000000,
                    'shortage_rate': 70.0,
                    'priority': '긴급'
                }
            ]
        }
    ]
    
    pdf_buffer = generator.generate_pdf(
        customer_name="홍길동",
        agent_name="김설계",
        analysis_date="2026-03-30",
        family_data=test_data
    )
    
    print("✅ PDF 생성 테스트 완료")
