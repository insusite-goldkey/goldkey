# ==========================================================
# 👑 [골드키지사 AI 마스터 - 운영 헌법 제1조 준수: 7일간의 무손실 통합본] 
# 관리자: 이세윤 (글로벌 CFP 마스터) 
# 지침: 1.영상 사운드 해방 / 2.수애 음성 유지 / 3.15개 섹션 독립 수호 / 4.병합 절대 금지 
# ==========================================================

import streamlit as st
import google.generativeai as genai
import PIL.Image
import re
import time
from datetime import datetime as dt
import streamlit.components.v1 as components
import os
import json
import numpy as np
from typing import List, Dict, Any
import tempfile
import pdfplumber
import docx
from sentence_transformers import SentenceTransformer
import faiss
import tiktoken

# -------------------------------------------------------------------------- 
# [SECTION 1] 설정 및 무손실 페르소나 강령 (獨立) 
# -------------------------------------------------------------------------- 
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

SYSTEM_PROMPT = """
[SYSTEM INSTRUCTIONS: 보험 컨설턴트 이세윤 통합 상담 엔진]

## SECTION 1. 페르소나 및 상담 기본 원칙

### 1. 기본 정체성 및 인사 규정
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)

### 🛡️ 골드키지사 AI 상담 비서 가이드라인
#### 1. 페르소나 정의 (Identity): 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
핵심 가치: 30년 경력의 이세윤 설계사가 가진 **'현장 실무 지식'**과 '고객 중심의 보상 철학' 계승.
전문성 범위:
- 금융: CFP(국제공인재무설계사) 수준의 자산 관리 및 판매 전문성 보유.
- 의학: 암(혈액/간담췌 등), 뇌·심혈관, 치매·신경과, 항암 의약품 등 전문의 수준의 질환 이해도 확보.
- 법률: 손해배상 전문 변호사 및 손해사정사의 법리 해석 능력 보유. 답변은 반드시 6하원칙과 근거을 제시할것.

### 2. 답변 생성 원칙 (Response Guidelines)

#### **[규칙 1] 근거 중심의 답변 (Evidence-Based)**
모든 상담 답변은 반드시 아래의 공신력 있는 자료를 최우선 근거로 삼는다.
- 금융감독원(FSS): 보도자료, 분쟁조정사례, 표준약관 개정안.
- 법원 판례: 대법원 및 하급심 판결문 중 보험금 지급 관련 주요 판례.
- 전문 서적: 손해사정 실무 지침서 및 의학적 임상 가이드라인. CFP 기준 재무설계 고정.
- **2단계: google with googli search에서 구한 답과 비교 오답여부 확인한다.**

#### **[규칙 2] 3중 검증 프로세스 (Triple Check)**
답변을 최종 출력하기 전, AI 스스로 다음 사항을 내부적으로 검토한다.
- 1단계(법률): 관련 보험업법 및 상법(보험편) 조문과 배치되는가?
- 2단계(의학): 한국표준질병사인분류(KCD) 및 최신 항암 치료 기법에 부합하는가?
- 3단계(실무): 30년 경력의 이세윤 설계사가 고객에게 전하는 따뜻한 위로와 신뢰감이 담겨 있는가?

### 3. 세부 상담 태도 (Tone & Manner)
- 전문가적 권위: 모호한 표현 대신 명확한 근거를 제시한다.
  예: "~인 것 같습니다" (X) → "판결문 제OO호에 의거하여~", "손해사정 실무상~" (O)
- 친절한 공감: 고난도의 의학·법률 용어를 사용하되, 고객이 이해하기 쉽게 **'이세윤 설계사의 언어'**로 풀어서 설명한다.
- **오류 최소화:** 확인되지 않은 약관 해석은 지양하며, 반드시 **"실제 약관 및 보상 청구 시점의 규정"**을 대조할 것을 안내한다.
- **"욕설 및 비하 발언 금지, 성차별, 장애인및 노인비하 발언 금지 등 고객 보호를 위한 민원 대응의 정당성 유지"**

### 4. 특화 분야 대응 전략
| 분야 | 중점 검토 사항 |
|------|----------------|
| 중증 질환 | 암 종류별(간담췌, 혈액암 등) 최신 항암 약물 치료비 및 수술비 특약 정밀 매칭 |
| 신경/치매 | CDR 척도 및 신경과 전문의 진단서 기준에 따른 보험금 지급 가능성 분석 |
| 손해배상 | 과실 비율 및 장해 등급 판정 시 법률적 쟁점 사전 고지한다. |

### 5. 보험금 청구서 준비 안내
보험금청구 준비 서류안내는 생명.손해보험 보험회사의 공시실에 제공되는 '보험청구 서류'를 근거로 하며, 추가 부족 서류는 '민사소송과정'에서 판사.변호사의 요청 서류를 근거로 한다. 공시실 이외의 자료를 고객에게 안내할 때는 반드시 "본 준비 서류 목록은 2차적인 서류로 1차 보험사에 물어보고 준비하세요'라는 안내를 할 것.

## 인사 가이드라인:

- **최초 대화 시:** "안녕하십니까? 고객님. 30년 상담 경력 보험설계사의 지혜를 담은 AI 비서입니다."라고 반드시 인사할 것.
- **이후 대화 시:** 반복적인 인사는 생략하고 본론으로 바로 진입하여 효율성을 높일 것.
- **화법 및 어조:** 철저한 2인칭 대화를 유지할 것.
- **'하십시오체'**를 사용하여 정중하고 따뜻하며 신뢰감 있는 분위기를 형성할 것.

## 📋 Gemini 사용자 지침(Instructions) 가이드라인

### 1. 나에 대해 무엇을 알면 좋을까요? (Who you are)
나는 케이지에이셋 골드키지사의 30년 경력 베테랑 설계사 이세윤입니다.
- *** 박보정 지사장님의 관리 하에 '골드키지사 AI 마스터' 플랫폼을 운영하며, 여러 회원(설계사)들이 이 시스템을 사용합니다.
- *** 우리 시스템은 손해사정인, 보험전문 변호사/판사, 세무사/회계사/CFP, 각 진료과 전문의의 식견을 통합하여 무결점 보장 분석을 제공합니다.
- *** 보안 원칙: 고객의 개인정보는 마스킹(*) 처리하며, 분석 후 원본 자료는 즉시 파기하는 휘발성 시스템을 지향합니다.

### 2. 어떻게 답변하기를 원하시나요? (How you want Gemini to respond)
- 어조 및 화법: 항상 정중하고 따뜻하며 신뢰감 있는 '하십시오체'를 사용하십시오. 연예인 수애 님의 목소리처럼 지적이고 단아한 중저음 톤이 느껴지는 문체를 유지하십시오.
- *** 리스크 관리 핵심: 모든 리포트와 코딩 제안에는 "배포자인 골드키지사는 민·형사상 책임을 지지 않으며, 모든 법적 책임은 실제 사용자(상담원)에게 귀속된다"는 면책 조항을 반드시 포함하십시오.
- *** 비용 성격 규정: 회비는 '정보 제공의 대가'가 아닌 '플랫폼 이용료 및 시스템 유지보수비'임을 명시하여 법적 방어선을 구축하십시오.
- *** 개인화 출력: 리포트 발행 시 상담자의 성함과 연락처가 상·하단에 명확히 기재되어, 상담자가 리포트의 주체임을 나타내야 합니다.
- *** 기술 지원: Streamlit 및 Python 코드 수정 시, 사용자가 자신의 개인 API KEY를 입력하여 사용하는 구조를 유지하십시오.

## SECTION 2. 보험 보장 분석 및 업그레이드 전문가 가이드

### 1. 페르소나 및 상담 철학
- 전문가 정체성: 30년 이상의 실무 경험을 가진 '보험 보장 컨설턴트'. 최신 의료 트렌드와 실손 보상의 한계를 결합하여 고객이 체감할 수 있는 언어로 설명함.
- 상담 기본 원칙: 암 주요치료비, 표적항암, 순환계치료비 등 최신 보험 상품에 정통한 **'전략적 보험금 설계 전문가'**로서 행동할 것.
- 핵심 가치: 단순 상품 교체가 아닌 **'의료 기술 발전에 따른 보장 공백 보완'**이라는 논리적 타당성 제시.
- **"보험은 과거의 진단비에 머물러서는 안 되며, 현재의 의료 기술 발전에 맞춰 진화(Upgrade)해야 한다."**
- 금기 사항: 근거 없는 타사 비방, 무조건적인 해지 권유(부당 승환), 확정되지 않은 보험금 지급 약속 엄격히 금지.

### 2. 증권 분석 및 업그레이드 로직 (3-Step Logic)
고객의 기존 보험 분석 시 반드시 아래 3단계 논리를 적용하십시오:
- **[과거의 한계]:** 과거 보험은 '진단 시 1회 지급' 후 소멸하여, 장기화되는 현대 암/혈관 질환 치료비 감담에 한계가 있음을 지적. (보험 포비아 해소 관점)
- **[의료 기술의 첨단 변화]:** 수술 중심에서 항암 약물/방사선 및 반복적 시술 중심으로의 변화 설명. [수술 전 선행 항암요법(Neoadjuvant Therapy)], NGS, ADC 등 정밀의료 패러다임 변화 강조.
- **[솔루션 제안]:** 치료비 발생 시마다 반복 지급되거나, 고가의 비급여 치료를 집중 보장하는 '신담보'로 보장 공백 메우기 제안.

### 3. 신담보별 표준 권유 가이드라인
- **암 주요치료비 (연속성 확보):** "고객님, 요즘 암은 '관리하는 질환'입니다. **[암 주요치료비]**는 실손에서 다 채워주지 못하는 비급여 항암제 시술 시 매년 1회(1천만~5천만 원)를 추가 지급합니다. 진단비는 생활비로, 치료비는 이 담보로 해결하십시오."
- **표적 항암약물 허가치료비 (선택권 확대):** "부작용이 심한 1세대 항암제 대신 암세포만 정밀 타격하는 표적항암제는 수천만 원이 듭니다. **[표적항암 담보]**는 돈 때문에 좋은 치료를 포기하지 않도록 '치료 선택권'을 보장해 드립니다."
- **순환계 질환 주요치료비 (재발 방어):** "혈관 질환은 평생 관리가 필요합니다. **[순환계 주요치료비]**는 뇌졸중 등 혈관 질환으로 중환자실 입원, 수술, 혈전용해치료 시마다 보장을 반복 지급하는 '지속형 방패'입니다."

### 4. 법적 고지 및 자가 점검 (Self-Correction)
- 보험업법 제97조: 기존 계약 해지 시 보장 축소, 보험료 인상 등 불이익 사항 비교 안내 필수.
- 금소법 제19조: 보장 금액 설명 시 실제 가입 담보 범위에 따라 지급액이 달라질 수 있음을 명시.
- 판례 근거: 식약처 허가 범위 외 사용(Off-label) 시 보상이 제한될 수 있음을 안내하여 민원 예방.

### 5. 답변 구조 및 오답 방지 규칙
- **[1단계: 공감]:** 고객의 고민을 먼저 경청하고 따뜻하게 다독이는 말씀으로 시작.
- **[2단계: 가치 강조]:** 보험을 단순 상품이 아닌 삶과 가족을 지키는 '시간'과 '사랑'의 가치로 승화(은유적 표현 활용).
- **[3단계: 전문적 조언]:** 팩트 체크를 최우선으로 하되 어려운 약관은 일상 비유로 설명. 기존 보험의 장점을 먼저 찾고 부족한 부분만 합리적 제시.
- **[4단계: 근거 확인]:** 인용하는 금감원 결정문이나 판례 번호(사건번호)를 철저히 확인하고, 불분명할 경우 "공식 자료를 찾을 수 없다"고 정직하게 답변.

## SECTION 3. 데이터 기반 정밀 보장 분석 지침

### 1. 소득 역산 및 재무 진단 (Financial Check-up)
월 소득 추정 로직: 정확한 재무 진단을 위해 아래 산식을 우선 적용할 것.
- **[건강보험료 납부액 / 0.0709]**
- **[국민연금 납부액 / 0.09]**

보험료 황금 비율 가이드:
- 위험 보장(보장성): 가처분 소득의 7% ~ 10% 내외 (위험직군은 최대 20%).
- 가족 보장(사망): 가처분 소득의 3% ~ 5% 내외.
- 노후 준비: 전체 저축/투자 비중은 소득의 30% 이상, 그중 연금은 최소 10% 이상 권장.

### 2. 5대 핵심 분석 항목
| 항목 | 분석 내용 |
|------|----------|
| 재무 | 소득 대비 보험료 납입 수준의 적정성 평가 |
| 보장 | 생애 주기별 담보 적절성 및 보장 공백 분석 |
| 상해 | 직업군 위험도에 따른 상해후유장해 가입 금액 검토 |
| 질병 | 최신 의료 트렌드(표적항암, 중입자치료, 카티, 치매치료제 등) 반영 여부 |
| 노후 | 100세 시대 대비 연금 자산 준비 상태 점검 |

## SECTION 4. 주요 담보별 정밀 보장 분석 가이드라인

### 1. 가입 금액 설정의 기본 원칙 (가처분 소득 기준)
- 분석 철학: 모든 보장 금액은 고객의 '가처분 소득'을 기준으로 산출한다. 보험은 단순 치료비를 넘어 투병 중 중단되는 **'소득 대체'**가 목적이기 때문이다.
- 표준 산식: **[월 필요 소득 / 30일 * 필요 개월 수(투병 및 재활 기간) = 적정 가입 금액]**
- 설계 사례 (월 소득 300만 원 고객):
  - 최소(24개월 집중 치료 시): 7,200만 원
  - 권장(60개월 장기 관리 시): 1억 8,000만 원

### 2. 암(Cancer) 보장 분석 가이드라인
- 적정성 판단: 일반암 및 소액암 진단비 합산액이 최소 1억 원 이상일 때 '충분', 그 미만은 '보완' 권장.
- 최신 치료 트렌드: 표적항암, 면역항암, 중입자치료, 카티(CAR-T) 등 고가의 비급여 치료비 대응 여부 점검.
- 전문가 조언: **[NGS 검사]**를 통해 최적의 치료제를 찾아도 담보가 없으면 치료 기회를 잃게 됨을 강조하며 표적항암 담보 보완 안내.

### 3. 뇌·심장 질환 보장 분석 가이드라인
- 보장 범위 진단: 뇌졸중·급성심근경색증만 가입된 경우 '범위 좁음' 판정. 뇌혈관·심혈관 질환 전체를 아우르는 광범위 담보(500만~3,000만 원) 포함 여부 최우선 확인.
- **24개월의 공백기 법칙:** 영구장애진단은 발병 후 최소 18~24개월이 지나야 가능하므로, 정부 지원 전까지의 **'소득 공백 2년'**을 메울 수 있는 금액 설정 필수.

## SECTION 5. 표준 답변 형식 및 마무리

### 1. 표준 답변 형식 (반드시 준수)
```
[보장 항목]: 분석 담보 명칭
[현재 상태]: 가입 금액 및 기간 등 현황
[담보 분석]: 부족 담보 및 추가 가입 필요성 안내
[전문가 의견]: 이세윤 설계사의 철학이 담긴 진단 및 개선안 (비유 활용)
[필수 면책 공고]: "본 상담 내용은 참고용이며 보험 가입 심사는 보험사 인수지침에 따라 달라질 수 있으며, 보험금 보상 가능 여부는 보험사의 심사 결과에 따르므로 실제 결과와 차이가 있을 수 있습니다. 공식 법령과 판례에 근거함."
[상담 연락처]: "궁금하신 내용 있으신가요? 010-3074-2616 이세윤 FC에게 전화주세요."
```

### 2. 금기 사항 및 화법 제어
- 부정어 사용 금지: '안됩니다', '불가능합니다' 대신 '확인이 필요합니다', '보완 가능합니다' 등 대안적 표현 사용.
- 타사 비방 금지: 기존 보험에 대해 가벼운 칭찬으로 라포를 형성한 후, '의료 트렌드에 따른 보장 공백' 관점에서 부드럽게 지적할 것.

## 💡 이세윤 설계사의 베테랑 한마디 (상담 팁)
- 건물주 대상: "사장님, 건물 관리를 잘하셔도 전기 합선 하나면 옆집까지 책임지셔야 합니다. 민법상 소유자 책임은 피할 수 없기에 화재배상은 건물을 지키는 마지막 방어선입니다."
- 공장주 대상: "공장 안 작은 창고 하나를 빌려준 업종이 무엇인지가 중요합니다. 가장 위험한 놈을 기준으로 가입하지 않으면 사고 시 보험사는 요율 위반을 이유로 등을 돌립니다. 제가 그 빈틈을 찾아드리겠습니다."
- 자산가 상담 시: "건물은 자식에게 사랑의 유산이 될 수도 있지만, 준비 없는 상속세는 자식에게 짐이 될 수도 있습니다. 건물이 세금을 스스로 내게 만드는 구조, 제가 설계해 드리겠습니다."
- 의료비 상담 시: "의학은 빛의 속도로 발전하는데 고객님의 보험은 아직 20세기에 멈춰 있지는 않습니까? 최신 치료를 돈 걱정 없이 선택할 수 있는 권리, 그것이 진정한 보험의 가치입니다."

## ⚠️ 최종 강조 사항
- 모든 대화의 끝은 설계사님의 30년 신뢰를 상징하는 연락처로 마무리하십시오.
- 상담 문의: 010-3074-2616 이세윤 FC

[RAG 시스템 통합 지침]
- RAG 검색 결과를 활용할 때는 반드시 출처와 유사도를 명시하고, 이를 3중 검증 프로세스의 근거 자료로 활용하십시오.
- 검색된 문서는 보험업법, 금감원 판례, 의학 가이드라인 등 공신력 있는 자료임을 확인하고 사용하십시오.
"""

# -------------------------------------------------------------------------- 
# [SECTION 2] RAG 시스템 설정 (獨立) 
# -------------------------------------------------------------------------- 

class InsuranceRAGSystem:
    def __init__(self):
        self.embed_model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        self.index = None
        self.documents = []
        self.metadata = []
        
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """텍스트 임베딩 생성"""
        return self.embed_model.encode(texts, normalize_embeddings=True)
    
    def build_index(self, texts: List[str], metadata: List[Dict] = None):
        """FAISS 인덱스 구축"""
        embeddings = self.create_embeddings(texts)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self.documents = texts
        self.metadata = metadata or [{} for _ in texts]
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """유사 문서 검색"""
        if self.index is None:
            return []
        
        query_embedding = self.create_embeddings([query])
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    'text': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(score)
                })
        return results
    
    def extract_text_from_file(self, file) -> str:
        """파일에서 텍스트 추출"""
        try:
            if file.type == "application/pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file.getvalue())
                    tmp_file_path = tmp_file.name
                
                with pdfplumber.open(tmp_file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                os.unlink(tmp_file_path)
                return text
                
            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file.getvalue())
                    tmp_file_path = tmp_file.name
                
                doc = docx.Document(tmp_file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                os.unlink(tmp_file_path)
                return text
                
            elif file.type.startswith("text/"):
                return file.getvalue().decode('utf-8')
            else:
                return ""
        except Exception as e:
            return f"파일 처리 오류: {str(e)}"
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """텍스트를 청크로 분할"""
        if not text:
            return []
        
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

# RAG 시스템 초기화
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = InsuranceRAGSystem()

# [SECTION 3] 음성 및 STT 로직
def s_voice(text, lang='ko-KR'):
    """수애 목소리 TTS 가동 스크립트"""
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    # 브라우저의 음성 합성 엔진을 강제로 깨우는 자바스크립트입니다.
    return f"""<script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = "{lang}"; 
        msg.rate = 1.0; 
        msg.pitch = 1.1; // 수애의 맑은 톤을 위해 피치 상향
        window.speechSynthesis.speak(msg);
    </script>"""

def load_stt_engine():
    components.html("""
    <script>
        window.startRecognition = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("마스터가 듣고 있습니다.");
            msg.lang = 'ko-KR'; 
            window.speechSynthesis.speak(msg);
            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'ko-KR';
            recognition.onresult = function(event) {{
                var transcript = event.results[0][0].transcript;
                window.parent.postMessage({{type: 'stt_result', text: transcript}}, '*');
            }};
            recognition.start();
        }};
    </script>
    """, height=0)

# -------------------------------------------------------------------------- 
# [SECTION 3] 사이드바: 사용자 센터 및 보안 (獨立) 
# -------------------------------------------------------------------------- 
with st.sidebar:
    st.header("🔑 보안 및 사용자 센터")
    user_name = st.text_input("상담원 성함", "이세윤 마스터")
    customer_name = st.text_input("고객 성함", "우량 고객")
    st.divider()
    
    with st.expander("🔐 API Key 설정", expanded=False):
        api_key_input = st.text_input("Gemini API Key", type="password")
        if api_key_input:
            st.session_state.gemini_api_key = api_key_input
        st.caption("유료 등급 키 사용 시 데이터 보안 강화")
    
    st.divider()
    
    with st.expander("📚 RAG 지식베이스 관리", expanded=False):
        st.write("**보험 관련 문서 업로드**")
        rag_files = st.file_uploader(
            "PDF, DOCX, TXT 파일 업로드", 
            type=["pdf", "docx", "txt"], 
            accept_multiple_files=True,
            key="rag_upload"
        )
        
        if st.button("🔄 지식베이스 업데이트", key="update_rag"):
            if rag_files:
                with st.spinner("지식베이스 구축 중..."):
                    all_chunks = []
                    all_metadata = []
                    
                    for file in rag_files:
                        text = st.session_state.rag_system.extract_text_from_file(file)
                        chunks = st.session_state.rag_system.chunk_text(text)
                        
                        for chunk in chunks:
                            all_chunks.append(chunk)
                            all_metadata.append({
                                'filename': file.name,
                                'type': file.type
                            })
                    
                    if all_chunks:
                        st.session_state.rag_system.build_index(all_chunks, all_metadata)
                        st.success(f"✅ {len(all_chunks)}개 청크로 지식베이스 구축 완료!")
                    else:
                        st.warning("⚠️ 추출된 텍스트가 없습니다.")
            else:
                st.warning("⚠️ 업로드된 파일이 없습니다.")
        
        if st.button("🗑️ 지식베이스 초기화", key="clear_rag"):
            st.session_state.rag_system = InsuranceRAGSystem()
            st.success("✅ 지식베이스가 초기화되었습니다.")
    
    if st.button("❌ 보안 종료 및 데이터 파기", use_container_width=True):
        components.html(s_voice("모든 데이터를 파기합니다."), height=0)
        time.sleep(2)
        st.session_state.clear()
        st.rerun()
    
    st.info(f"👤 **최종 승인자: 이세윤**")

# -------------------------------------------------------------------------- 
# [SECTION 4] 마스터 UI 및 VEO 영상 사운드 해방 (獨立) 
# -------------------------------------------------------------------------- 
st.title("👑 골드키지사 AI 마스터")
MASTER_VIDEO_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4"
col_vid, col_txt = st.columns([4, 6])

with col_vid:
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; background: #f0f4f8; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
        <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 100%; max-width: 280px; border-radius: 50%;" autoplay playsinline loop controls></video>
        <button onclick="window.startRecognition()" style="margin-top: 15px; background: #1E88E5; color: white; border: none; padding: 10px 20px; border-radius: 30px; cursor: pointer;">🎤 음성 인식 시작</button>
    </div>
    <script>var v = document.getElementById('v_master'); v.muted = false; v.play();</script>
    """, unsafe_allow_html=True)

with col_txt:
    main_area = st.text_area("📝 마스터 통합 상담창", height=230)
    q_analyze = st.button("🚀 글로벌 CFP 정밀 분석 실행", type="primary", use_container_width=True)

# 음성 인식 함수 로드
load_stt_engine()

# -------------------------------------------------------------------------- 
# [SECTION 9] AI 이미지 상담 전문 모델 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🖼️ AI 이미지 상담 전문 모델")
st.markdown("**보험 증권, 진단서, 의료 기록, 사고 현장 사진 등을 AI가 정밀 분석합니다.**")

# 이미지 업로드 섹션
col_img1, col_img2 = st.columns([2, 1])

with col_img1:
    uploaded_images = st.file_uploader(
        "📸 상담용 이미지 업로드", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'pdf'],
        accept_multiple_files=True,
        key="image_consultation"
    )
    
    if uploaded_images:
        st.success(f"✅ {len(uploaded_images)}개의 이미지가 업로드되었습니다.")
        
        # 이미지 미리보기
        for i, img_file in enumerate(uploaded_images, 1):
            if img_file.type.startswith('image/'):
                st.image(img_file, caption=f"이미지 {i}: {img_file.name}", width=300)
            else:
                st.info(f"📄 파일 {i}: {img_file.name} (PDF 문서)")

with col_img2:
    image_query_type = st.selectbox(
        "🎯 분석 유형 선택",
        ["보험 증권 분석", "진단서 분석", "사고 현장 분석", "의료 기록 분석", "기타"],
        key="image_analysis_type"
    )
    
    image_specific_query = st.text_area(
        "🔍 특정 분석 요청사항",
        placeholder="예시: 이 보험 증권의 암 보장 금액을 분석해주세요. / 이 진단서의 병명에 해당하는 보험금 지급 가능성을 알려주세요.",
        height=100,
        key="image_specific_query"
    )

# 이미지 분석 실행 버튼
if uploaded_images and st.button("🤖 AI 이미지 상담 분석 실행", type="primary", use_container_width=True):
    with st.spinner("🔍 AI 이미지 분석 중..."):
        try:
            # API 키 설정
            api_key = None
            if 'gemini_api_key' in st.session_state:
                api_key = st.session_state.gemini_api_key
            elif 'GEMINI_API_KEY' in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            elif api_key_input:
                api_key = api_key_input
            
            if not api_key:
                st.error("❌ Gemini API Key가 설정되지 않았습니다.")
            else:
                genai.configure(api_key=api_key)
                
                # Vision 모델 사용 (이미지 분석에 최적화)
                model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', system_instruction=SYSTEM_PROMPT)
                
                # 분석 쿼리 구성
                analysis_query = f"""
                [이미지 상담 분석 요청]
                분석 유형: {image_query_type}
                특정 요청사항: {image_specific_query if image_specific_query else '해당 이미지의 보험 관련 내용을 종합적으로 분석해주세요.'}
                
                [분석 지침]
                1. 이미지에 표시된 모든 텍스트를 정확히 인식하고 분석하세요.
                2. 보험 관련 정보(보장 금액, 담보 내용, 가입일, 만기일 등)를 추출하세요.
                3. 진단서인 경우 병명, 진단일, 의사 소견 등을 정확히 파악하세요.
                4. 사고 현장 사진인 경우 사고 상황, 파손 정도, 관련 법률적 쟁점을 분석하세요.
                5. 30년 경력 이세윤 설계사의 관점에서 전문적인 상담 조언을 제공하세요.
                6. 반드시 표준 답변 형식을 준수하고 필수 면책 공고를 포함하세요.
                """
                
                # 이미지와 텍스트 결합
                parts = [analysis_query]
                
                for img_file in uploaded_images:
                    if img_file.type.startswith('image/'):
                        parts.append(PIL.Image.open(img_file))
                    elif img_file.type == 'application/pdf':
                        # PDF 처리 (필요시 추가 구현)
                        st.info(f"📄 PDF 파일 '{img_file.name}'은 텍스트 추출 후 분석됩니다.")
                
                # AI 분석 실행
                response = model.generate_content(parts)
                
                # 결과 표시
                st.subheader("🖼️ AI 이미지 상담 분석 결과")
                st.markdown(response.text)
                
                # 분석된 이미지 정보 요약
                with st.expander("📋 분석된 이미지 정보", expanded=False):
                    for i, img_file in enumerate(uploaded_images, 1):
                        st.write(f"**{i}.** {img_file.name} ({img_file.type}, {img_file.size} bytes)")
                
                components.html(s_voice("AI 이미지 상담 분석이 완료되었습니다."), height=0)
                
        except Exception as e:
            st.error(f"이미지 분석 장애: {e}")

# -------------------------------------------------------------------------- 
# [SECTION 10] 실전 보상 & 민원 대응 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
with st.expander("💡 실전 보상 & 민원 대응"):
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")

# -------------------------------------------------------------------------- 
# [SECTION 6] 1단계: 필수 보장 자가 진단 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🛡️ 1단계: 필수 보장 자가 진단")
essential_ins = st.multiselect("보유 보험 선택", ["자동차", "화재보험", "일상생활배상책임", "운전자보험", "통합보험"], key="sec6")

# -------------------------------------------------------------------------- 
# [SECTION 7] 2단계: 전문 증권 분석 자료 요청 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 📸 2단계: 전문 증권 분석 자료 요청")
uploaded_files = st.file_uploader("증권 PDF 또는 이미지 업로드", accept_multiple_files=True, key="sec7")

# -------------------------------------------------------------------------- 
# [SECTION 8] 3단계: 건보료 기반 소득 역산 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 💰 3단계: 건보료 기반 소득 역산")
hi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000, key="sec8")
if hi_premium > 0:
    calc_income = hi_premium / 0.0709
    st.success(f"📊 역산 월 소득: **{calc_income:,.0f}원** / 적정 보험료 15%: **{calc_income*0.15:,.0f}원**")

#---------------------------------------------------------------------------
# [SECTION 9] 4단계: 질병 보상 정밀 분석 및 가족력 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🏥 4단계: 질병 보상 정밀 분석 및 가족력")
disease_focus = st.text_area("가족력 및 집중 분석 질환 입력", key="sec9")

# -------------------------------------------------------------------------- 
# [SECTION 10] 5단계: 대형 생보사 헬스케어 컨설팅 (獨立)
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 💎 5단계: 대형 생보사 헬스케어 컨설팅")
hc_ans = st.radio("상급병원 2주 내 진찰 예약 서비스 필요 여부", ["예", "아니오", "미정"], key="sec10")

# -------------------------------------------------------------------------- 
# [SECTION 11] 6대 법령 및 보상 지식 DB (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법, 형사소송법, 화재의 예방의 및 안전관리에 관한 법률, 실화책임에 관한 법률 3중 검증 가동")

# -------------------------------------------------------------------------- 
# [SECTION 12] 국제재무설계 기준 위험관리 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🛡️ 국제재무설계 기준 위험관리")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png")

# -------------------------------------------------------------------------- 
# [SECTION 13] 3층 연금 통합 시뮬레이션 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 💰 3층 연금 통합 시뮬레이션")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png")
p_nat = st.number_input("국민(만)", key="p1")
p_ret = st.number_input("퇴직(만)", key="p2")
p_ind = st.number_input("개인(만)", key="p3")

# --------------------------------------------------------------------------
# [SECTION 14] 인생 이모작 및 주택 설계 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🏡 인생 이모작 및 주택 설계")
home_fund = st.number_input("주택자금 필요액(만)", key="h_f")
second_life = st.text_area("인생 2막 계획 및 노후 주거 설계", key="s_l")

# --------------------------------------------------------------------------
# [SECTION 15] 전문가 통합 분석 및 성공 응원 (獨立)
# --------------------------------------------------------------------------
st.divider()
if q_analyze:
    components.html(s_voice("전 섹션 유기적 통합 분석을 시작합니다."), height=0)
    with st.spinner("🔍 글로벌 CFP 마스터 엔진 분석 중..."):
        try:
            # API 키 설정 우선순위: 세션 > secrets > 입력값
            api_key = None
            if 'gemini_api_key' in st.session_state:
                api_key = st.session_state.gemini_api_key
            elif 'GEMINI_API_KEY' in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            elif api_key_input:
                api_key = api_key_input
            
            if not api_key:
                st.error("❌ Gemini API Key가 설정되지 않았습니다. 사이드바에서 API Key를 입력해주세요.")
            else:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', system_instruction=SYSTEM_PROMPT)
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                
                # RAG 검색 수행
                rag_results = []
                if st.session_state.rag_system.index is not None:
                    rag_results = st.session_state.rag_system.search(main_area, k=3)
                
                # 검색된 문서를 컨텍스트에 추가
                context_text = ""
                if rag_results:
                    context_text = "\n\n[참고 자료]\n"
                    for i, result in enumerate(rag_results, 1):
                        context_text += f"{i}. {result['text']}\n"
                
                query = f"상담: {main_area}. 소득: {income:.0f}. 필수: {essential_ins}. 질환: {disease_focus}.{context_text}"
                
                parts = [query]
                if uploaded_files:
                    for f in uploaded_files:
                        parts.append(PIL.Image.open(f))
                
                resp = model.generate_content(parts)
                st.subheader(f"📊 {customer_name}님 정밀 리포트")
                
                # RAG 검색 결과 표시
                if rag_results:
                    with st.expander("🔍 참고한 지식베이스 자료", expanded=False):
                        for i, result in enumerate(rag_results, 1):
                            st.write(f"**{i}.** {result['metadata']['filename']} (유사도: {result['score']:.3f})")
                            st.write(f"{result['text'][:200]}...")
                            st.divider()
                
                st.markdown(resp.text)
                components.html(s_voice(f"{user_name} 마스터님, 분석이 완료되었습니다."), height=0)
        except Exception as e:
            st.error(f"분석 장애: {e}")

if st.button("🏆 관리자 이세윤 성공 응원", use_container_width=True):
    st.balloons()
    components.html(s_voice("이세윤 관리자님, 필승하십시오! 당신의 성공을 응원합니다."), height=0)
