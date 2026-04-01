-- ══════════════════════════════════════════════════════════════════════════════
-- [GP-PHASE-3] 25개 섹터 카테고리 등록 및 RAG 지식 베이스 확장
-- ══════════════════════════════════════════════════════════════════════════════
-- 작성일: 2026-04-01
-- 목적: gk_knowledge_base 테이블에 4대 프로토콜 기반 25개 섹터 카테고리 등록
-- ══════════════════════════════════════════════════════════════════════════════

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- [PSP] 인적 보안 프로토콜 (Personal Security Protocol) - 10개 섹터
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- PSP-01: 암보험
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-01_암보험_기초지식.pdf',
    'PSP-01-암보험',
    0,
    '암보험은 암 진단 시 진단금을 지급하는 보험입니다. 2021년 국가암등록통계(2023년 발표) 기준, 대한민국 국민이 기대수명까지 생존 시 암 발생 확률은 38.1%입니다. 남성은 약 39.1%(약 2.5명 중 1명), 여성은 36.0%(3명 중 1명)가 평생 한 번 암을 진단받습니다. 암 치료비 평균은 3,800만 원이며, 항암치료·방사선치료·수술비가 포함됩니다.',
    220,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['암보험', '진단금', '항암치료', '치료비', '보장', '국가암등록통계', '암발생확률']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-01-1: 2023 암 치료비 비급여 실태 보고서
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-01_2023_암치료비_비급여실태보고서.pdf',
    'PSP-01-암보험',
    0,
    '암 환자 1인당 연간 평균 비급여 치료비는 2,800만원~5,500만원입니다. 1세대 독성항암제는 수백만원, 2세대 표적항암제는 연간 3,000만원~8,000만원, 3세대 면역항암제는 연간 1억원 이상 소요됩니다. 의학의 발전으로 암은 죽는 병이 아니라 돈으로 고치는 병이 되었지만, 건강보험이 따라가지 못하는 비급여 표적항암제와 면역항암 요법의 비용은 가족의 경제적 파산을 초래할 수 있습니다.',
    280,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['비급여', '표적항암', '면역항암', '치료비폭증', '경제적파산', '1세대', '2세대', '3세대']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-01-2: NGS 검사 건강보험 가이드
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-01_NGS검사_건강보험가이드.pdf',
    'PSP-01-암보험',
    0,
    'NGS(차세대 염기서열 분석) 검사는 암 진단 시 정밀 분석을 위한 필수 검사입니다. 본인부담금은 70만원~150만원이며, 비급여 시 최대 400만원이 발생합니다. NGS 검사 결과에 따라 표적항암제 선택이 결정되므로, 암 치료의 첫 단계에서 경제적 부담이 시작됩니다. 진단비 5천만원은 최신 면역항암제 연간 치료비 1억원의 6개월치에 불과하므로, 표준 진단비 + 표적항암 치료비 최소 7천만원 이상의 보장이 권장됩니다.',
    260,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['NGS검사', '차세대염기서열', '본인부담금', '비급여', '정밀분석', '표적항암제선택', '7천만원권장']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;


-- PSP-02: 뇌혈관질환
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_뇌혈관질환_보장가이드.pdf',
    'PSP-02-뇌혈관',
    0,
    '뇌혈관질환은 뇌졸중, 뇌출혈, 뇌경색을 포함합니다. 발병 시 평균 치료비는 2,500만 원이며, 재활치료 기간은 평균 6개월입니다. 골든타임 3시간 내 치료가 중요합니다.',
    120,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['뇌혈관질환', '뇌졸중', '뇌출혈', '뇌경색', '재활치료']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-03: 심장질환
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-03_심장질환_보장가이드.pdf',
    'PSP-03-심장질환',
    0,
    '심장질환은 급성심근경색, 협심증, 부정맥을 포함합니다. 발병 시 평균 치료비는 2,000만 원이며, 스텐트 시술비는 500만 원입니다. 골든타임 2시간 내 치료가 생명을 좌우합니다.',
    110,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['심장질환', '급성심근경색', '협심증', '스텐트', '시술']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-04: 실손의료비
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-04_실손의료비_4세대_약관.pdf',
    'PSP-04-실손의료비',
    0,
    '4세대 실손의료보험은 비급여 본인부담 30%, 급여 본인부담 20% 적용됩니다. 입원 5,000만원, 통원 30만원 한도입니다. 도수치료, 주사치료, 체외충격파는 비급여 제외 대상입니다.',
    130,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['실손의료비', '4세대', '비급여', '본인부담', '통원']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-05: 수술/입원
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-05_수술입원_보장분석.pdf',
    'PSP-05-수술입원',
    0,
    '수술비는 수술 종류에 따라 10만원~1,000만원까지 차등 지급됩니다. 입원일당은 1일 5만원~10만원입니다. 상급병실료 차액은 별도 특약 가입 시 보장됩니다.',
    100,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['수술비', '입원일당', '상급병실료', '특약', '보장']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- [APP] 자산 보호 프로토콜 (Asset Protection Protocol) - 6개 섹터
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- APP-01: 자동차보험
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-01_자동차보험_약관요약.pdf',
    'APP-01-자동차',
    0,
    '자동차보험은 대인배상Ⅰ(무한), 대인배상Ⅱ(최소 3천만원), 대물배상(최소 1천만원), 자기신체사고(최소 1천500만원)로 구성됩니다. 1년 보험료 평균 70만원, 사고 1건 수리비 평균 180만원입니다.',
    140,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['자동차보험', '대인배상', '대물배상', '자기신체사고', '보험료']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-02: 운전자보험
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-02_운전자보험_민식이법_대응.pdf',
    'APP-02-운전자',
    0,
    '운전자보험은 형사합의금, 벌금, 변호사선임비용을 보장합니다. 민식이법 이후 어린이 보호구역 사고 시 형사합의금이 5,000만원을 넘습니다. 자동차보험과 별도 가입 필수입니다.',
    120,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['운전자보험', '형사합의금', '민식이법', '벌금', '변호사비용']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-03: 주택화재
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-03_주택화재_보장분석.pdf',
    'APP-03-주택화재',
    0,
    '주택화재보험은 건물, 가재도구, 임시거주비를 보장합니다. 아파트 화재 평균 복구비는 3,000만원입니다. 누수, 도난, 파손도 특약 가입 시 보장됩니다.',
    100,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['주택화재', '건물', '가재도구', '임시거주비', '누수']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-04: 개인공장화재 (핵심 섹터)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-04_개인공장화재_실무가이드.pdf',
    'APP-04-개인공장화재',
    0,
    '개인공장 화재보험은 건물, 기계설비, 재고자산, 영업손실을 보장합니다. 공장 화재 평균 복구비는 2억원이며, 영업중단 손실은 월 3,000만원입니다. 소방시설 완비 시 보험료 20% 할인됩니다.',
    150,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['개인공장', '화재보험', '기계설비', '재고자산', '영업손실', '소방시설']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-04_개인공장화재_실무가이드.pdf',
    'APP-04-개인공장화재',
    1,
    '공장 화재 발생 시 복구 비용은 보험료의 1,000배가 넘습니다. 화재 발생 후 평균 복구 기간은 6개월이며, 이 기간 동안 영업중단으로 인한 손실은 연 매출의 50%에 달합니다. 보험료는 비용이 아니라 자산 방어 프로토콜입니다.',
    160,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['복구비용', '영업중단', '자산방어', '화재예방', '손실보전']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-05: 법인공장화재 (핵심 섹터)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-05_법인공장화재_종합보험.pdf',
    'APP-05-법인공장화재',
    0,
    '법인공장 종합보험은 건물, 기계설비, 원재료, 제품, 영업이익손실을 보장합니다. 대형 공장 화재 시 평균 복구비는 10억원이며, 영업중단 손실은 월 1억원입니다. 스프링클러 설치 시 보험료 30% 할인됩니다.',
    160,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['법인공장', '종합보험', '영업이익손실', '스프링클러', '복구비']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-05_법인공장화재_종합보험.pdf',
    'APP-05-법인공장화재',
    1,
    '법인공장 화재는 단순 재산 손실을 넘어 기업 존속의 문제입니다. 화재 발생 후 6개월 내 폐업하는 기업이 40%에 달합니다. 종합보험은 화재뿐 아니라 폭발, 붕괴, 침수, 도난까지 보장하여 기업의 연속성을 보장합니다.',
    150,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['기업연속성', '폐업방지', '종합보장', '재산손실', '리스크관리']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-06: 상가화재 (핵심 섹터)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-06_상가화재_임차인보험.pdf',
    'APP-06-상가화재',
    0,
    '상가화재보험은 건물주용과 임차인용으로 구분됩니다. 임차인은 시설물, 집기비품, 재고상품, 영업손실을 보장받습니다. 상가 화재 평균 복구비는 5,000만원이며, 영업중단 손실은 월 500만원입니다.',
    150,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['상가화재', '임차인보험', '집기비품', '재고상품', '영업손실']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-06_상가화재_임차인보험.pdf',
    'APP-06-상가화재',
    1,
    '상가 화재는 인근 점포로 확산되어 배상책임이 발생할 수 있습니다. 배상책임 특약 미가입 시 개인 재산으로 배상해야 하며, 평균 배상액은 3,000만원입니다. 보험료는 월 3만원이지만, 화재 발생 시 손실은 수천만원입니다.',
    140,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['배상책임', '화재확산', '인근점포', '손실보전', '특약']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- [BRP] 비즈니스 리스크 프로토콜 (Business Risk Protocol) - 5개 섹터
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- BRP-01: PL보험 (제조물책임)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'BRP-01_PL보험_제조물책임법.pdf',
    'BRP-01-PL보험',
    0,
    'PL보험(제조물책임보험)은 제품 결함으로 인한 신체·재산 피해를 보장합니다. 제조물책임법에 따라 제조업자는 무과실책임을 집니다. 평균 배상액은 5,000만원이며, 소송비용은 별도입니다.',
    130,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['PL보험', '제조물책임', '무과실책임', '배상액', '소송비용']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- BRP-02: 전문직배상책임
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'BRP-02_전문직배상책임_의사변호사.pdf',
    'BRP-02-전문직배상책임',
    0,
    '전문직배상책임보험은 의사, 변호사, 회계사, 건축사의 업무상 과실로 인한 배상책임을 보장합니다. 의료사고 평균 배상액은 1억원이며, 소송 기간은 평균 3년입니다.',
    120,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['전문직배상책임', '의료사고', '업무과실', '배상액', '소송']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- BRP-03: 단체보험
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'BRP-03_단체보험_복리후생.pdf',
    'BRP-03-단체보험',
    0,
    '단체보험은 임직원 복리후생 목적으로 가입합니다. 사망, 상해, 암, 입원을 보장하며, 개인보험 대비 보험료가 30% 저렴합니다. 10인 이상 사업장 가입 가능합니다.',
    110,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['단체보험', '복리후생', '임직원', '사망', '상해']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- BRP-04: 근로자재해
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'BRP-04_근로자재해_산재보험.pdf',
    'BRP-04-근로자재해',
    0,
    '근로자재해보험은 산재보험을 보완합니다. 산재보험은 평균 임금의 70%만 보장하므로, 나머지 30%를 근로자재해보험으로 보장합니다. 건설업, 제조업 필수 가입 권장입니다.',
    120,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['근로자재해', '산재보험', '보완', '건설업', '제조업']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- BRP-05: 법인전환리스크
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'BRP-05_법인전환_세무리스크.pdf',
    'BRP-05-법인전환리스크',
    0,
    '개인사업자에서 법인 전환 시 세무리스크가 발생합니다. 양도소득세, 증여세, 법인세 문제를 사전에 점검해야 합니다. 법인전환 컨설팅 비용은 평균 500만원입니다.',
    110,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['법인전환', '세무리스크', '양도소득세', '증여세', '컨설팅']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- [WOP] 부의 이전 및 최적화 프로토콜 (Wealth Optimization Protocol) - 4개 섹터
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- WOP-01: CEO플랜
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'WOP-01_CEO플랜_법인보험.pdf',
    'WOP-01-CEO플랜',
    0,
    'CEO플랜은 법인이 보험료를 납부하고, CEO 사망 시 법인이 보험금을 수령하는 구조입니다. 보험료는 손금 처리되어 법인세 절감 효과가 있습니다. 비상장주식 평가액 감소 효과도 있습니다.',
    130,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['CEO플랜', '법인보험', '손금처리', '법인세절감', '비상장주식']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- WOP-02: 상속세/증여세
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'WOP-02_상속세증여세_절세전략.pdf',
    'WOP-02-상속세증여세',
    0,
    '상속세는 10억원 초과 시 최고세율 50%가 적용됩니다. 배우자 공제 5억원, 자녀 공제 5,000만원이 있습니다. 생명보험 활용 시 상속세 납부 재원 마련이 가능합니다.',
    120,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['상속세', '증여세', '절세', '배우자공제', '생명보험']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- WOP-03: 가업승계
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'WOP-03_가업승계_세제혜택.pdf',
    'WOP-03-가업승계',
    0,
    '가업승계 시 상속세 최대 500억원까지 100% 공제됩니다. 10년 이상 계속 경영, 정규직 근로자 유지 등 요건을 충족해야 합니다. 사전 증여 활용 시 세 부담을 최소화할 수 있습니다.',
    130,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['가업승계', '상속세공제', '사전증여', '경영유지', '세제혜택']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- WOP-04: 비상장주식평가
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'WOP-04_비상장주식평가_보충적평가.pdf',
    'WOP-04-비상장주식평가',
    0,
    '비상장주식은 순손익가치와 순자산가치를 3:2로 가중평균하여 평가합니다. 평가액이 높을수록 상속세·증여세 부담이 커집니다. 보험 활용 시 평가액을 낮출 수 있습니다.',
    120,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['비상장주식', '보충적평가', '순손익가치', '순자산가치', '평가액']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- ══════════════════════════════════════════════════════════════════════════════
-- 카테고리별 통계 조회
-- ══════════════════════════════════════════════════════════════════════════════

SELECT * FROM gk_knowledge_stats ORDER BY document_category;

-- ══════════════════════════════════════════════════════════════════════════════
-- END OF SCRIPT
-- ══════════════════════════════════════════════════════════════════════════════
