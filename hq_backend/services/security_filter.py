# -*- coding: utf-8 -*-
"""
보안 필터 엔진 (Security Filter Engine)
개인정보 보호를 위한 PII 마스킹 파이프라인

작성일: 2026-03-31
목적: PDF 텍스트 내 개인정보(이름, 전화번호, 주민등록번호, 이메일) 자동 마스킹
원칙: 인물 식별 무결성 원칙 준수 - 민원 대응 정당성 유지
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PIIDetectionResult:
    """PII 감지 결과"""
    original_text: str
    masked_text: str
    detections: List[Dict[str, str]]
    detection_count: int


class SecurityFilter:
    """
    보안 필터 엔진
    
    핵심 기능:
    1. 한국인 이름 패턴 감지 및 마스킹
    2. 전화번호 (휴대폰, 일반전화) 마스킹
    3. 주민등록번호 마스킹
    4. 이메일 주소 마스킹
    5. 계좌번호 마스킹
    6. 카드번호 마스킹
    
    원칙:
    - 개인정보 보호법 준수
    - 금융감독원 보안 규정 준수
    - 민원 대응 정당성 유지
    """
    
    # 마스킹 문자
    MASK_CHAR = "***"
    
    # 한국인 성씨 목록 (상위 100개)
    KOREAN_SURNAMES = [
        "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
        "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
        "홍", "고", "문", "양", "손", "배", "백", "허", "남", "심",
        "노", "하", "곽", "성", "차", "주", "우", "구", "신", "라",
        "전", "민", "유", "진", "지", "엄", "채", "원", "천", "방",
        "공", "현", "함", "변", "염", "여", "추", "도", "소", "석",
        "선", "설", "마", "길", "연", "위", "표", "명", "기", "반",
        "왕", "금", "옥", "육", "인", "맹", "제", "모", "장", "남궁",
        "탁", "국", "어", "경", "은", "편", "용", "예", "봉", "사",
        "부", "가", "복", "태", "목", "형", "피", "두", "감", "음"
    ]
    
    def __init__(self, mask_char: str = MASK_CHAR):
        """
        Args:
            mask_char: 마스킹 문자 (기본값: ***)
        """
        self.mask_char = mask_char
        
        # 정규식 패턴 컴파일
        self._compile_patterns()
    
    def _compile_patterns(self):
        """정규식 패턴 컴파일"""
        
        # 1. 전화번호 패턴
        # 휴대폰: 010-1234-5678, 010.1234.5678, 01012345678
        # 일반전화: 02-123-4567, 031-123-4567
        self.phone_pattern = re.compile(
            r'(?:(?:010|011|016|017|018|019)[-.\s]?\d{3,4}[-.\s]?\d{4})|'
            r'(?:0(?:2|3[1-3]|4[1-4]|5[1-5]|6[1-4])[-.\s]?\d{3,4}[-.\s]?\d{4})'
        )
        
        # 2. 주민등록번호 패턴
        # 123456-1234567, 123456-*******
        self.rrn_pattern = re.compile(
            r'\d{6}[-\s]?[1-4]\d{6}|'
            r'\d{6}[-\s]?\*{7}'
        )
        
        # 3. 이메일 패턴
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )
        
        # 4. 계좌번호 패턴
        # 123-456-789012, 123456789012 (10~14자리)
        self.account_pattern = re.compile(
            r'\d{2,6}[-\s]?\d{2,6}[-\s]?\d{2,14}'
        )
        
        # 5. 카드번호 패턴
        # 1234-5678-9012-3456, 1234567890123456 (13~16자리)
        self.card_pattern = re.compile(
            r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}|'
            r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{3}'
        )
        
        # 6. 한국인 이름 패턴
        # 성씨 + 2~3글자 이름
        surnames_pattern = '|'.join(self.KOREAN_SURNAMES)
        self.name_pattern = re.compile(
            f'({surnames_pattern})[가-힣]{{1,3}}(?=\\s|님|씨|대표|설계사|고객|보험|계약|가입)'
        )
    
    def mask_phone_numbers(self, text: str) -> Tuple[str, List[str]]:
        """
        전화번호 마스킹
        
        Args:
            text: 원본 텍스트
        
        Returns:
            Tuple[str, List[str]]: (마스킹된 텍스트, 감지된 전화번호 리스트)
        """
        detected = []
        
        def replace_phone(match):
            phone = match.group(0)
            detected.append(phone)
            # 전화번호 중간 부분만 마스킹
            # 010-1234-5678 → 010-***-5678
            parts = re.split(r'[-.\s]', phone)
            if len(parts) >= 3:
                parts[1] = self.mask_char
                return '-'.join(parts)
            return self.mask_char
        
        masked_text = self.phone_pattern.sub(replace_phone, text)
        return masked_text, detected
    
    def mask_rrn(self, text: str) -> Tuple[str, List[str]]:
        """
        주민등록번호 마스킹
        
        Args:
            text: 원본 텍스트
        
        Returns:
            Tuple[str, List[str]]: (마스킹된 텍스트, 감지된 주민번호 리스트)
        """
        detected = []
        
        def replace_rrn(match):
            rrn = match.group(0)
            detected.append(rrn)
            # 주민번호 뒷자리 전체 마스킹
            # 123456-1234567 → 123456-*******
            parts = re.split(r'[-\s]', rrn)
            if len(parts) == 2:
                return f"{parts[0]}-{self.mask_char}"
            return self.mask_char
        
        masked_text = self.rrn_pattern.sub(replace_rrn, text)
        return masked_text, detected
    
    def mask_emails(self, text: str) -> Tuple[str, List[str]]:
        """
        이메일 주소 마스킹
        
        Args:
            text: 원본 텍스트
        
        Returns:
            Tuple[str, List[str]]: (마스킹된 텍스트, 감지된 이메일 리스트)
        """
        detected = []
        
        def replace_email(match):
            email = match.group(0)
            detected.append(email)
            # 이메일 @ 앞부분 일부 마스킹
            # user@example.com → u***@example.com
            parts = email.split('@')
            if len(parts) == 2:
                username = parts[0]
                if len(username) > 2:
                    masked_username = username[0] + self.mask_char
                else:
                    masked_username = self.mask_char
                return f"{masked_username}@{parts[1]}"
            return self.mask_char
        
        masked_text = self.email_pattern.sub(replace_email, text)
        return masked_text, detected
    
    def mask_account_numbers(self, text: str) -> Tuple[str, List[str]]:
        """
        계좌번호 마스킹
        
        Args:
            text: 원본 텍스트
        
        Returns:
            Tuple[str, List[str]]: (마스킹된 텍스트, 감지된 계좌번호 리스트)
        """
        detected = []
        
        def replace_account(match):
            account = match.group(0)
            # 숫자만 추출
            digits = re.sub(r'[^\d]', '', account)
            
            # 10~14자리 숫자만 계좌번호로 간주
            if 10 <= len(digits) <= 14:
                detected.append(account)
                # 계좌번호 중간 부분 마스킹
                return self.mask_char
            return account
        
        masked_text = self.account_pattern.sub(replace_account, text)
        return masked_text, detected
    
    def mask_card_numbers(self, text: str) -> Tuple[str, List[str]]:
        """
        카드번호 마스킹
        
        Args:
            text: 원본 텍스트
        
        Returns:
            Tuple[str, List[str]]: (마스킹된 텍스트, 감지된 카드번호 리스트)
        """
        detected = []
        
        def replace_card(match):
            card = match.group(0)
            # 숫자만 추출
            digits = re.sub(r'[^\d]', '', card)
            
            # 13~16자리 숫자만 카드번호로 간주
            if 13 <= len(digits) <= 16:
                detected.append(card)
                # 카드번호 중간 부분 마스킹
                # 1234-5678-9012-3456 → 1234-***-***-3456
                return f"{digits[:4]}-{self.mask_char}-{self.mask_char}-{digits[-4:]}"
            return card
        
        masked_text = self.card_pattern.sub(replace_card, text)
        return masked_text, detected
    
    def mask_names(self, text: str) -> Tuple[str, List[str]]:
        """
        한국인 이름 마스킹
        
        Args:
            text: 원본 텍스트
        
        Returns:
            Tuple[str, List[str]]: (마스킹된 텍스트, 감지된 이름 리스트)
        """
        detected = []
        
        def replace_name(match):
            name = match.group(0)
            detected.append(name)
            # 이름 중간 글자 마스킹
            # 홍길동 → 홍*동
            if len(name) == 2:
                return name[0] + "*"
            elif len(name) == 3:
                return name[0] + "*" + name[2]
            elif len(name) >= 4:
                return name[0] + "*" * (len(name) - 2) + name[-1]
            return self.mask_char
        
        masked_text = self.name_pattern.sub(replace_name, text)
        return masked_text, detected
    
    def apply_all_filters(self, text: str) -> PIIDetectionResult:
        """
        모든 보안 필터 적용
        
        Args:
            text: 원본 텍스트
        
        Returns:
            PIIDetectionResult: PII 감지 및 마스킹 결과
        """
        original_text = text
        detections = []
        
        # 1. 주민등록번호 마스킹 (최우선)
        text, rrn_detected = self.mask_rrn(text)
        if rrn_detected:
            detections.extend([{"type": "주민등록번호", "value": v} for v in rrn_detected])
        
        # 2. 전화번호 마스킹
        text, phone_detected = self.mask_phone_numbers(text)
        if phone_detected:
            detections.extend([{"type": "전화번호", "value": v} for v in phone_detected])
        
        # 3. 이메일 마스킹
        text, email_detected = self.mask_emails(text)
        if email_detected:
            detections.extend([{"type": "이메일", "value": v} for v in email_detected])
        
        # 4. 계좌번호 마스킹
        text, account_detected = self.mask_account_numbers(text)
        if account_detected:
            detections.extend([{"type": "계좌번호", "value": v} for v in account_detected])
        
        # 5. 카드번호 마스킹
        text, card_detected = self.mask_card_numbers(text)
        if card_detected:
            detections.extend([{"type": "카드번호", "value": v} for v in card_detected])
        
        # 6. 이름 마스킹 (마지막)
        text, name_detected = self.mask_names(text)
        if name_detected:
            detections.extend([{"type": "이름", "value": v} for v in name_detected])
        
        return PIIDetectionResult(
            original_text=original_text,
            masked_text=text,
            detections=detections,
            detection_count=len(detections)
        )
    
    def get_statistics(self, result: PIIDetectionResult) -> Dict:
        """
        PII 감지 통계 정보
        
        Args:
            result: PII 감지 결과
        
        Returns:
            Dict: 통계 정보
        """
        stats = {
            "total_detections": result.detection_count,
            "by_type": {}
        }
        
        for detection in result.detections:
            pii_type = detection["type"]
            stats["by_type"][pii_type] = stats["by_type"].get(pii_type, 0) + 1
        
        return stats


def main():
    """
    테스트 및 예제 실행
    """
    print("=" * 70)
    print("🔒 보안 필터 엔진 (Security Filter Engine)")
    print("=" * 70)
    
    # 보안 필터 초기화
    security_filter = SecurityFilter()
    
    # 테스트 텍스트
    test_text = """
    삼성생명 보험 상품 안내
    
    담당 설계사: 홍길동 (010-1234-5678)
    고객명: 김철수님 (010-9876-5432)
    주민등록번호: 850101-1234567
    이메일: customer@example.com
    계좌번호: 123-456-789012
    카드번호: 1234-5678-9012-3456
    
    보험료: 월 50,000원
    보장 내용: 암 진단 시 3,000만원
    """
    
    print("\n📄 원본 텍스트:")
    print("-" * 70)
    print(test_text)
    
    # 보안 필터 적용
    result = security_filter.apply_all_filters(test_text)
    
    print("\n🔒 마스킹된 텍스트:")
    print("-" * 70)
    print(result.masked_text)
    
    # 통계 정보
    stats = security_filter.get_statistics(result)
    
    print("\n📊 PII 감지 통계:")
    print("-" * 70)
    print(f"총 감지 건수: {stats['total_detections']}개")
    for pii_type, count in stats['by_type'].items():
        print(f"  - {pii_type}: {count}개")
    
    print("\n🔍 감지된 PII 상세:")
    print("-" * 70)
    for idx, detection in enumerate(result.detections, 1):
        print(f"{idx}. {detection['type']}: {detection['value']}")
    
    print("\n" + "=" * 70)
    print("✅ 보안 필터 테스트 완료")
    print("=" * 70)
    
    print("\n💡 사용 예시:")
    print("""
    from hq_backend.services.security_filter import SecurityFilter
    
    # 보안 필터 초기화
    security_filter = SecurityFilter()
    
    # 텍스트 마스킹
    result = security_filter.apply_all_filters(text)
    
    # 마스킹된 텍스트 사용
    masked_text = result.masked_text
    
    # 통계 확인
    stats = security_filter.get_statistics(result)
    print(f"PII 감지: {stats['total_detections']}개")
    """)


if __name__ == "__main__":
    main()
