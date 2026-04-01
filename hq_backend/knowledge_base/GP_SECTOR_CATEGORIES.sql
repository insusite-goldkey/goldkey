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

-- PSP-01-3: 2026 지역 거점 병원 vs 수도권 Big 5 진료 전략
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-01_2026_지역거점병원_vs_수도권Big5_진료전략.pdf',
    'PSP-01-암보험',
    0,
    '암 치료는 병기(Stage)에 따라 전략이 달라야 합니다. 1~3기 초기 암의 경우, 수도권 대기로 인한 치료 지연(평균 2~4주)보다 지방 거점 병원(화순전남대병원, 부산대병원 등)에서의 신속한 수술이 예후에 15% 이상 유리합니다. 지방 거점 병원들은 CAR-T 센터를 운영하며 NCCN 가이드라인을 준수하여 생존율이 수도권과 평준화되었습니다. 반면 4기 또는 재발 환자의 경우, 수도권 Big 5(서울대병원, 삼성서울병원, 아산병원, 세브란스병원, 서울성모병원)의 신약 임상시험(Clinical Trials) 접근성이 핵심입니다. 임상시험 참여 시 수억 원대 신약을 무상으로 투여받을 수 있어, 지방에서 동일 약제를 비급여로 투여받을 때 월 1,000만 원 이상 발생하는 비용을 절감할 수 있습니다. 이것이 암 치료의 경제적 역설(Economic Paradox)입니다. 수도권 원정 진료비(교통비, 숙박비 월 200~300만 원)보다 무서운 것은 지방에서의 임상 기회 상실입니다.',
    520,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['지역거점병원', '수도권Big5', '병기별전략', '화순전남대병원', 'CAR-T센터', 'NCCN가이드라인', '임상시험', '경제적역설', '신약무상투여', '치료지연', '예후15%유리']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-01-4: 임상시험 경제성 분석 (Clinical Trials Economic Analysis)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-01_임상시험_경제성_분석.pdf',
    'PSP-01-암보험',
    0,
    '암 4기 또는 재발 환자의 경우, 수도권 Big 5 병원의 임상시험 참여는 경제적으로 매우 유리합니다. 예를 들어, 키트루다(펨브롤리주맙) 임상시험 참여 시 연간 약제비 1억 2천만 원을 무상으로 투여받을 수 있으며, 옵디보(니볼루맙) 임상시험은 연간 8천만 원 상당의 약제를 무료로 제공합니다. 반면 지방 병원에서 동일 약제를 비급여로 투여받을 경우 월 800만~1,200만 원의 본인부담금이 발생합니다. 임상시험 참여 조건은 까다롭지만(ECOG 성능 상태 0~1, 주요 장기 기능 정상), 일단 선정되면 약제비뿐만 아니라 검사비, 영상 촬영비까지 무상으로 제공됩니다. 수도권 원정 진료 시 발생하는 교통비(월 50만 원), 숙박비(월 150~250만 원), 간병비(월 200만 원)를 모두 합쳐도 월 400~500만 원 수준이므로, 비급여 약제비 월 1,000만 원과 비교하면 경제적으로 합리적입니다. 따라서 암보험 가입 시 수도권 원정 진료비(교통비, 숙박비, 간병비) 보장 특약을 반드시 포함해야 하며, 최소 월 500만 원 × 12개월 = 6,000만 원 이상의 부대비용 보장이 권장됩니다.',
    580,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['임상시험', '키트루다', '옵디보', '신약무상투여', '비급여약제비', '수도권원정진료', '교통비보장', '숙박비보장', '간병비보장', '부대비용6천만원', 'ECOG성능상태']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-01-3-1: 지방 거점 병원 CAR-T 센터 운영 성적
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-01_지방거점병원_CAR-T센터_운영성적.pdf',
    'PSP-01-암보험',
    0,
    '"지방은 불안하다"는 고객의 우려는 데이터로 반박됩니다. 화순전남대병원은 2023년 기준 CAR-T 세포치료 센터를 운영하며, 혈액암 치료 성적이 수도권 대형병원과 동등합니다. 부산대병원은 위암 5년 생존율 78.3%로 전국 평균 77.5%를 상회하며, NCCN(National Comprehensive Cancer Network) 가이드라인을 엄격히 준수합니다. 지방 거점 병원들은 상급종합병원으로 지정되어 있으며, 수술 대기 시간이 수도권의 1/3 수준으로 짧아 골든타임 내 치료가 가능합니다. 특히 1~3기 초기 암의 경우, 수술 대기 시간 2주 단축이 5년 생존율을 15% 이상 향상시키는 연구 결과가 있습니다. 따라서 "서울로 가야 할까요?"라는 질문에 대한 답변은 병기에 따라 달라집니다. 2기 환자라면 "서울 대기보다 화순전남대에서의 신속한 수술이 생존율을 높이는 최적의 프로토콜"입니다.',
    580,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['화순전남대병원', '부산대병원', 'CAR-T센터', 'NCCN가이드라인', '상급종합병원', '수술대기시간단축', '5년생존율', '골든타임', '지방불안반박', '병기별맞춤답변']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;



-- PSP-02: 뇌혈관질환 (KCD 정밀 매핑 및 부지급 방어 엔진)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_뇌혈관질환_KCD코드_위계매핑.pdf',
    'PSP-02-뇌혈관',
    0,
    '뇌혈관질환 KCD 코드 위계 및 담보 매핑: 1) 뇌출혈(I60~I62): 지주막하출혈(I60), 뇌내출혈(I61), 기타 비외상성 두개내출혈(I62). 2) 뇌졸중(I60~I63, I65, I66): 뇌출혈 + 뇌경색(I63) + 경동맥 협착(I65) + 대뇌동맥 폐색(I66). 3) 뇌혈관질환 전체(I60~I69): 뇌졸중 + 뇌혈관 후유증(I69) + 기타 뇌혈관질환(I67, I68). 보험사 면책 논리 차단 포인트: I64(출혈 또는 경색으로 명시되지 않은 뇌졸중)는 일반 뇌졸중 담보에서 면책되나, 뇌혈관질환 전체 담보로 전환 시 보장 가능. I65(경동맥 협착)는 생명보험(뇌출혈/뇌경색)에서 제외되나 손해보험(뇌졸중)에서는 포함되는 보장 격차 존재. 특수 질환: 모야모야병(I67.5)은 뇌혈관 전체 담보 필수, 열공성 뇌경색(I63.8/9)은 크기 1.5cm 이하 시 부지급 사유 발생 가능.',
    520,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['뇌혈관질환', 'KCD코드', 'I60', 'I61', 'I62', 'I63', 'I64', 'I65', 'I66', 'I67', 'I68', 'I69', '뇌출혈', '뇌경색', '뇌졸중', '면책지뢰', '경동맥협착', '모야모야병', '열공성뇌경색', '부지급방어']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-1: I64 면책 지뢰 방어 로직
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_I64_면책지뢰_방어전략.pdf',
    'PSP-02-뇌혈관',
    1,
    'I64(출혈 또는 경색으로 명시되지 않은 뇌졸중)는 보험사의 대표적인 면책 지뢰입니다. 응급실에서 뇌졸중 의심으로 입원했으나 CT/MRI 검사 결과 출혈과 경색이 명확히 구분되지 않을 경우, 의사는 I64 코드를 부여합니다. 이 경우 일반 뇌졸중 담보(I60~I63)에서는 I64가 제외되어 보험금 부지급 사유가 됩니다. 방어 전략: 1) 뇌혈관질환 전체 담보(I60~I69) 가입 필수. 2) 진단서 발급 시 의사에게 "I64 대신 I63.9(상세불명의 뇌경색) 또는 I61.9(상세불명의 뇌내출혈) 코드 부여 요청" 가능 여부 확인. 3) 재검사를 통해 출혈 또는 경색 확정 시 코드 변경 요청. 통계: 전체 뇌졸중 환자 중 약 8~12%가 I64 코드를 받으며, 이 중 70%는 추가 검사로 I63 또는 I61로 변경 가능합니다.',
    480,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['I64', '면책지뢰', '출혈경색미명시', '부지급사유', '뇌혈관전체담보', 'I63.9', 'I61.9', '진단서코드변경', '재검사', '방어전략']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-2: I65 경동맥 협착 보장 격차
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_I65_경동맥협착_보장격차.pdf',
    'PSP-02-뇌혈관',
    2,
    'I65(경동맥 및 뇌동맥의 폐색 및 협착, 뇌경색을 유발하지 않은 것)는 생명보험과 손해보험 간 보장 격차가 존재하는 대표적인 질환입니다. 생명보험의 뇌출혈/뇌경색 담보는 I60~I63만 보장하므로 I65는 제외됩니다. 반면 손해보험의 뇌졸중 담보는 I60~I66을 보장하므로 I65가 포함됩니다. 경동맥 협착은 뇌경색의 전조 증상으로, 협착률 70% 이상 시 스텐트 시술(비용 500만~800만원) 또는 경동맥 내막절제술(비용 1,000만~1,500만원)이 필요합니다. 치료하지 않을 경우 5년 내 뇌경색 발생률 30% 이상. 보장 전략: 1) 손해보험 뇌졸중 담보(I60~I66) 필수 가입. 2) 생명보험 가입자는 뇌혈관질환 전체 담보(I60~I69) 추가 가입 권장. 3) 경동맥 초음파 검사 결과 협착률 50% 이상 시 즉시 보험 보강.',
    480,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['I65', '경동맥협착', '보장격차', '생명보험', '손해보험', '뇌졸중담보', '스텐트시술', '경동맥내막절제술', '뇌경색전조', '협착률70%', '보장전략']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-3: 모야모야병 및 열공성 뇌경색 부지급 방어
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_특수질환_부지급방어.pdf',
    'PSP-02-뇌혈관',
    3,
    '특수 뇌혈관질환 부지급 방어 전략: 1) 모야모야병(I67.5, Moyamoya disease): 뇌혈관이 좁아져 연기처럼 보이는 희귀질환. 주로 소아 및 40대 여성에서 발생. 뇌출혈 또는 뇌경색으로 진행 가능하나, I67.5 코드는 뇌출혈/뇌경색 담보에서 제외될 수 있음. 반드시 뇌혈관질환 전체 담보(I60~I69) 가입 필수. 수술비(혈관우회술) 2,000만~3,000만원. 2) 열공성 뇌경색(Lacunar infarction, I63.8/I63.9): 뇌 심부의 작은 혈관이 막혀 발생하는 작은 크기(직경 1.5cm 이하)의 뇌경색. 보험사는 "크기가 작아 일상생활에 지장이 없다"는 이유로 부지급 주장 가능. 방어: MRI 영상 및 신경학적 검사 결과(NIHSS 점수, 장애 정도) 제출하여 실제 후유장해 입증. 열공성 뇌경색도 재발률 30% 이상이며, 다발성 열공성 뇌경색은 혈관성 치매로 진행 가능.',
    520,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['모야모야병', 'I67.5', '열공성뇌경색', 'I63.8', 'I63.9', '부지급방어', '크기1.5cm이하', '혈관우회술', 'NIHSS점수', '후유장해입증', '다발성열공성', '혈관성치매', '재발률30%']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-4: ADLs 25% 판정의 벽과 CI 보험금 지급 기준
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_ADLs_25%_CI보험금지급기준.pdf',
    'PSP-02-뇌혈관',
    4,
    'ADLs(Activities of Daily Living, 일상생활 수행능력) 25% 판정의 벽: CI(Critical Illness) 보험은 5대 ADLs 항목(이동/식사/배변/탈의/목욕) 중 장해율 25% 이상일 때만 보험금을 지급합니다. 회복의 역설(Recovery Paradox): 재활 치료로 조금씩 좋아지는 순간, 보험금은 0원이 됩니다. 예시: 지팡이 없이 걷는 순간 → 이동 능력 점수 15점 감소 → 장해율 24% → 12.8% 하락 → CI 보험금 5,000만 원 → 0원. 하지만 현실은 재활 치료비 월 300만 원 × 6개월 = 1,800만 원, 간병비 월 400만 원 × 6개월 = 2,400만 원, 생활비 월 250만 원 × 6개월 = 1,500만 원으로 총 5,700만 원이 필요합니다. 장해 판정 타임라인: 보험사 CI 판정(6개월) vs 국가 장애 판정(18개월) 시간차로 인해 12개월 무소득 기간 발생. 월 250만 원 × 12개월 = 3,000만 원 소득 손실. 방어 전략: CI 보험은 중환자가 되어야 주지만, 종신보험 선지급은 환자만 되어도 가족의 생활비까지 책임집니다.',
    520,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['ADLs', '25%판정', 'CI보험', '회복의역설', '5대항목', '이동능력', '식사능력', '배변능력', '탈의능력', '목욕능력', '장해율', '보험사판정6개월', '국가장애판정18개월', '무소득기간', '재활치료비']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-5: 트리니티 가처분 소득 결손과 간병비 블랙홀
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_트리니티_가처분소득결손_간병비블랙홀.pdf',
    'PSP-02-뇌혈관',
    5,
    '트리니티 가처분 소득 결손 공식: Total Gap = (Monthly Caregiving + Monthly Living Cost) × 24 - Diagnosis Benefit. 간병비 블랙홀 시뮬레이션: 진단비 5,000만 원은 전문 간병비(월 400만 원)로 인해 12개월 만에 증발합니다. 진단비로 간병비를 내고 나면 가족 생활비(월 250만 원)는 24개월 동안 마이너스 6,000만 원이 됩니다. 필요 금액 분석: 간병비 400만 원 × 24개월 = 9,600만 원, 생활비 250만 원 × 24개월 = 6,000만 원, 총 1억 5,600만 원 필요. 현재 보장: 진단비 5,000만 원. 부족액: 1억 600만 원. 돈의 용도 분리 원칙: 진단비 5,000만 원 → 간병비 전용, 종신보험 선지급 6,000만~8,000만 원 → 생활비 전용. 전문가 클로징: 사장님, 5천만 원 진단비는 간병인 앞에서는 1년도 못 버팁니다. 진단비로 간병비를 내고 나면, 사모님과 아이들 생활비는 누가 줍니까?',
    540,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['트리니티', '가처분소득', '소득결손', '간병비블랙홀', '월400만원', '진단비증발', '12개월소진', '생활비마이너스', '용도분리', '간병비전용', '생활비전용', '부족액1억', '무소득기간24개월']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-6: 종신보험 생존 자산 전환(Acceleration) 프로토콜
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_종신보험_생존자산전환_Acceleration.pdf',
    'PSP-02-뇌혈관',
    6,
    '종신보험 생존 자산 전환(Acceleration): 사망 보험금은 죽어서 주는 위로금이 아니라, 가족의 가처분 소득을 지켜내는 생존 엔진입니다. 질병장해 50% 선지급: 종신보험 사망 보험금 1억 원 × 50% = 5,000만 원 생존 중 선지급. 뇌졸중 진단 확정 시 사망하지 않아도 5,000만 원 수령. 생활비 250만 원 × 20개월 = 5,000만 원 확보. 질병장해 80% 선지급: 종신보험 사망 보험금 1억 원 × 80% = 8,000만 원 생존 중 선지급. 생활비 250만 원 × 32개월 = 8,000만 원 확보. 용도 분리 전략: 진단비 5,000만 원(간병비 전용) + 선지급 5,000만~8,000만 원(생활비 전용) = 총 1억~1억 3,000만 원 확보. 가처분 소득 방어 시뮬레이션: 선지급 없이 진단비만 사용 시 12개월 만에 소진 → 부족액 1억 600만 원. 선지급 포함 시 24개월 이상 방어 → 부족액 0원 또는 최소화. 전문가 클로징: 사장님, 종신보험 사망 보험금 1억 원을 죽어서 받으시겠습니까? 아니면 살아서 받으시겠습니까? 보험은 죽어서 받는 것이 아닙니다. 살아서 가족을 지키는 것입니다.',
    580,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['종신보험', '생존자산전환', 'Acceleration', '선지급', '50%선지급', '80%선지급', '사망보험금재배치', '생존엔진', '가처분소득방어', '용도분리', '생활비전용', '뇌졸중진단확정', '살아서받는보험']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-5: 뇌수종 션트 수술 및 치매 신약 비용
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_뇌수종_치매신약_비용분석.pdf',
    'PSP-02-뇌혈관',
    5,
    '뇌수종(Hydrocephalus, 수두증) 및 치매 치료 비용 분석: 1) 정상압 수두증(Normal Pressure Hydrocephalus, NPH): 뇌척수액이 과도하게 축적되어 보행장애, 인지장애, 요실금 3대 증상 발생. 알츠하이머 치매와 오진되기 쉬우나, 션트(Shunt) 수술로 완치 가능. 션트 수술: 뇌실에서 복강으로 뇌척수액을 배출하는 관 삽입. 수술비 800만~1,200만원(비급여 포함). 수술 후 80% 이상 증상 호전. 2) 알츠하이머 치매 신약 레카네맙(Lecanemab): 2023년 FDA 승인, 초기 알츠하이머 환자 대상 아밀로이드 베타 제거 항체 치료제. 연간 치료비 약 3,000만~5,000만원(비급여). 건강보험 미적용 시 평생 치료비 1억 5,000만원 이상. 보험 전략: 1) 뇌혈관질환 후유증(I69) 보장 확인. 2) 치매 진단비 최소 3,000만원 이상 가입. 3) 장기간병 특약 추가(월 100만원 × 10년 = 1억 2,000만원).',
    540,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['뇌수종', '수두증', 'NPH', '정상압수두증', '션트수술', '보행장애', '인지장애', '요실금', '알츠하이머', '레카네맙', 'Lecanemab', '아밀로이드베타', '치매신약', '연간3천만원', '장기간병특약']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-6: 경동맥 협착(I65) 보험금 지급 분쟁 방어 프로토콜
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_I65_경동맥협착_분쟁방어_전문가프로토콜.pdf',
    'PSP-02-뇌혈관',
    6,
    '경동맥 협착(I65) 보험금 지급 분쟁의 본질: 보험사는 고객의 진단이 경동맥의 폐쇄 및 협착(I65)임에도 불구하고 이를 죽상경화증(I70)으로 격하시키려 합니다. 보험사 논리: "협착이 경미(Mild)하므로 질병이 아니라 노화에 따른 단순 동맥경화(I70)다." 에이젠틱 방어: "약관은 KCD 분류를 따르며, 영상판독지상 실질적 협착이 확인된다면 수치와 관계없이 I65 진단은 의학적·법률적으로 정당하다." 협착 정도별 손해사정 실무 판단 기준: 1) Mild(경도, 50% 미만): 최대 분쟁 구역. 보험사의 I70 변경 유도 집중. 작성자 불이익 원칙과 임상적 유의성으로 정면 돌파 필요. 2) Moderate(중등도, 50~69%): 지급 가능성 높음. NASCET 등 측정 방식에 따른 수치 검증 필요. 3) Severe(중증, 70~99%): 통상적 보상 대상. 스텐트 삽입술 등 수술 여부와 관계없이 지급 근거 명확. 4) Occlusion(폐쇄, 100%): 혈관 완전 폐쇄. 의학적 이견이 없는 확정적 지급 대상.',
    580,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['I65', '경동맥협착', '보험금분쟁', 'I70', '죽상경화증', 'Mild협착', 'NASCET', 'ECST', '작성자불이익원칙', '협착률', '손해사정', '부지급방어', '영상판독지', 'KCD분류']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-7: I65 분쟁 4대 필수 객관적 지표 및 증거 확보 전략
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_I65_4대필수증거_확보전략.pdf',
    'PSP-02-뇌혈관',
    7,
    '경동맥 협착(I65) 보험금 수령을 위한 4대 필수 객관적 지표: 1) 영상 의학 자료(Golden Evidence): 뇌혈관 MRA/CTA(혈관의 좁아진 정도를 수치화하는 표준 검사), 뇌혈관 조영술(TFCA, 분쟁 시 가장 강력한 최종 확정 증거), 경동맥 초음파(PSV 최대 수축기 혈류속도 값이 유의미하게 높은지 확인). 2) 측정 방식의 유리함 검토: NASCET 방식 vs ECST 방식은 분모 설정에 따라 협착률(%)이 달라짐. 고객에게 더 유리한 수치가 도출된 방식을 채택해야 함. 3) 영상판독지(Radiology Report) 정밀 분석: 단순히 Mild라는 표현에 매몰되지 말고, 판독지 내 기재된 구체적 수치(%)를 추출하여 기록. 4) 전문의 진단 소견서 3요소 필수 포함: ① 영상 검사 결과 확인된 구체적 협착 부위와 수치(%) 명시. ② 해당 수치가 한국표준질병사인분류(KCD)상 I65에 부합한다는 확정적 소견. ③ 환자가 호소하는 신경학적 증상(어지럼증, 마비감 등)과의 상관관계 기술.',
    560,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['MRA', 'CTA', 'TFCA', '뇌혈관조영술', '경동맥초음파', 'PSV', 'NASCET방식', 'ECST방식', '영상판독지', '전문의소견서', '신경학적증상', '협착수치', '진단근거']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-8: I65 보험사 대응 전략 및 법률 근거
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_I65_보험사대응전략_법률근거.pdf',
    'PSP-02-뇌혈관',
    8,
    '경동맥 협착(I65) 보험사 대응 프로세스(Strategic Action): 1) 의료자문 동의권 행사 주의: 보험사 측 자문은 Mild를 근거로 I70(부지급)으로 격하시키는 수단. 자문 동의 전, 주치의에게 "KCD 지침상 영상 결과가 있다면 I65 진단이 적정하다"는 재확인을 받는 것이 우선. 2) 작성자 불이익의 원칙(상법 제661조 연계): 보험약관에서 "협착률 50% 이상만 지급한다"는 구체적인 제한 규정을 두지 않았다면, 의학적 판단에 따른 I65 진단은 약관상 지급 대상임을 강력히 주장. 3) 대법원 판례 및 분쟁조정례 활용: 대법원 2017다201XXX 판례 - 약관의 뜻이 명백하지 않을 때는 고객에게 유리하게 해석해야 함. 금감원 결정 - 협착 정도가 낮더라도 임상적으로 유의미한 증상이 있다면 뇌혈관질환으로 인정함이 타당함. 관련 법조문: 상법 제661조(사고발생의 통지), 약관의 규제에 관한 법률 제5조(해석의 원칙), 보험업법 제185조(손해사정). 전문가 조언: 경동맥 협착은 보험금 액수가 크기 때문에 보험사의 현장 심사가 반드시 나옴. 청구 전 반드시 영상판독지와 진단서를 전문가에게 검토받아 논리적 허점이 없는지 확인하는 것이 보험금을 온전히 수령하는 지름길.',
    620,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['의료자문', '작성자불이익원칙', '상법제661조', '약관규제법', '보험업법제185조', '대법원판례', '금감원결정', '손해사정', '현장심사', '전문가검토', 'I70격하방어', '임상적유의성']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-9: CI(중대한) 뇌졸중 및 ADLs 25% 판정 프로토콜 (The Wall of 25%)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_CI뇌졸중_ADLs25%판정_프로토콜.pdf',
    'PSP-02-뇌혈관',
    9,
    'CI(중대한) 뇌졸중 보험의 숨겨진 함정: The Wall of 25%. CI 보험은 뇌졸중 진단 후 ADLs(일상생활 동작) 5대 항목의 장해율이 25% 이상이어야 보험금을 지급합니다. ADLs 5대 항목: 1) 이동하기(10~40%): 휠체어 사용 및 타인 부축 여부. 지팡이 보행 가능 시 10%, 타인 부축 필요 시 25%, 휠체어 전적 의존 시 40%. 2) 음식물 섭취(5~20%): 튜브 영양 및 수저 사용 불가 여부. 3) 배변/배뇨(5~20%): 기저귀 착용 및 화장실 이용 타인 도움 여부. 4) 옷 입고 벗기(5~10%): 스스로 탈의 가능 여부. 5) 목욕하기(5~10%): 전신 목욕 타인 도움 여부. 회복의 역설(The Recovery Paradox): 뇌졸중 진단 후 재활 치료로 지팡이 없이 걷게 되는 순간, CI 보험금은 0원이 됩니다. 일반 뇌졸중 보험은 진단 즉시 95% 지급 확률로 평균 3,000만원을 지급하지만, CI 뇌졸중 보험은 장해율 25% 이상이어야 하므로 35% 지급 확률로 평균 5,000만원을 지급합니다. 뇌졸중 환자 100명 중 65명은 CI 보험금을 받지 못합니다. 전문가 권고: 일반 뇌졸중 진단비 3,000만원 이상 필수 가입 + CI 보험은 보험료 절감용 보조 수단으로만 활용.',
    600,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['CI보험', '중대한뇌졸중', 'ADLs', '일상생활동작', '25%장해율', '회복의역설', '지팡이보행', '휠체어', '타인부축', '이동하기', '음식물섭취', '배변배뇨', '옷입고벗기', '목욕하기']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-10: 트리니티 가처분 소득 결손 및 자산 전환 프로토콜 (The Trinity Gap)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_트리니티결손_종신보험선지급_프로토콜.pdf',
    'PSP-02-뇌혈관',
    10,
    '트리니티 결손(Trinity Gap): 진단비가 간병비로 증발할 때 사라지는 가족의 생활비. 트리니티 결손 = (월 간병비 + 월 가처분 소득) × 24개월 - 진단비. 예시: 월 간병비 400만원 + 월 가처분 소득 250만원 = 월 650만원. 24개월 총 필요 금액 1억 5,600만원 - 진단비 5,000만원 = 트리니티 결손 1억 600만원. 간병비 블랙홀: 진단비 5,000만원은 월 간병비 400만원으로 12개월 내 소진됩니다. 이후 모든 비용은 가족의 자비 부담으로 전환되며, 이때 가족의 가처분 소득이 전액 결손됩니다. 종신보험 생존 자산 전환(Acceleration): 사망 담보 1~2억원 가입 시, 질병장해 50% 또는 80% 선지급을 통해 확보되는 5,000만원~1억 6,000만원의 현금 흐름이 간병비 블랙홀을 메우고 남은 가족의 가처분 소득을 지켜내는 최후의 보루입니다. 두부 외상성 장해(S코드): S06.5 외상성 경막하출혈(장해율 65%) 등 두부 외상 시 종신보험 80% 선지급 가능. 최적 사망 보험금: 트리니티 결손 1억 600만원 ÷ 0.8 = 1억 3,250만원 이상 권장.',
    560,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['트리니티결손', '가처분소득', '간병비블랙홀', '종신보험선지급', 'Acceleration', '50%장해', '80%장해', 'S코드', '두부외상', '경막하출혈', '최후의보루', '가족생활비']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- PSP-02-11: 간병 공백 및 노후 자산 전용 프로토콜 (Caregiver & Pension Synergy)
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'PSP-02_간병공백_연금LTC전환_프로토콜.pdf',
    'PSP-02-뇌혈관',
    11,
    '간병인 보험 365일+180일 리스크: 간병인 보험은 1년(365일) 보장 후 180일(6개월) 면책 기간이 발생합니다. 이 공백 기간 동안 월 간병비 400만원 × 6개월 = 2,400만원을 자비 부담해야 합니다. 공백 기간 대비 전략: 추가 진단비 2,400만원 이상 확보 또는 연금 LTC 전환으로 자급자족 프로토콜 구축. 개인연금 LTC(장기요양) 전환: 연금 보험의 요양병원비 및 요양비 전용 기능을 활용하여, 뇌졸중 발생 시 증액 연금(2배)이 간병비를 스스로 해결하는 자급자족 프로토콜입니다. 예시: 월 연금 200만원 → LTC 전환 시 월 400만원 × 10년 = 4억 8,000만원 확보. 치매 및 파킨슨 융합 설계: 치매 보험 설계 시 운동 능력 상실(파킨슨병, G20) 특약의 필수 가입 여부를 체크해야 합니다. 인지 능력은 있으나 거동이 불가한 경우의 보장 공백 방지. 3대 치매 경로의 수렴점: 알츠하이머(F00), 혈관성 치매(F01), 외상성 치매(F02)는 모두 최종적으로 중증 치매로 수렴하며, 이때 필요한 것은 마르지 않는 재원입니다. 연금 LTC 전환이 최후의 보루입니다.',
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
    ARRAY['주택화재', '화재보험', '임차인배상', '가재도구', '보장']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-04: 법인공장 화재보험
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-04_법인공장_화재보험_실무가이드.pdf',
    'APP-04-법인공장',
    0,
    '법인공장 화재보험의 가장 큰 리스크는 재조달가액 산정 미비로 인한 비례보상입니다. 재조달가액은 현재 시점에서 동일한 건물을 새로 지을 때 드는 비용을 의미하며, 보험가액이 재조달가액보다 낮을 경우 비례보상 원칙이 적용됩니다. 예를 들어, 재조달가액 10억 원인 공장에 5억 원만 가입하면 화재 시 1억 원 피해가 발생해도 50%인 5천만 원만 보상받습니다. 업종별 평균 화재 사고 피해액은 제조업 3억 5천만 원, 창고업 2억 8천만 원, 식품공장 4억 2천만 원입니다. 영업중단 손실(BI) 특약 가입 시 화재 복구 기간 동안 고정비(임차료, 인건비 등) 및 영업이익 손실을 보상받을 수 있습니다.',
    420,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['법인공장', '화재보험', '재조달가액', '비례보상', '영업중단손실', 'BI특약', '제조업', '창고업', '식품공장']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-05: 개인공장 화재보험
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-05_개인공장_화재보험_실무가이드.pdf',
    'APP-05-개인공장',
    0,
    '개인공장 화재보험은 법인공장과 동일하게 재조달가액 산정 미비로 인한 비례보상 리스크가 존재합니다. 특히 개인사업자는 세금 문제로 인해 공장 건물 가치를 낮게 평가하는 경향이 있어 보험가액 부족 문제가 빈발합니다. 소규모 공장(연면적 500㎡ 이하)의 평균 화재 피해액은 1억 5천만 원이며, 중규모 공장(500~1,500㎡)은 3억 2천만 원입니다. 공장 내 재고자산(원자재, 제품 등)은 별도 평가하여 보험가액에 포함해야 하며, 기계장비는 감가상각 후 현재 가치로 산정해야 합니다.',
    360,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['개인공장', '화재보험', '재조달가액', '비례보상', '소규모공장', '중규모공장', '재고자산', '기계장비']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- APP-06: 상가화재 및 영업중단 손실 보상
INSERT INTO gk_knowledge_base (
    document_name, document_category, chunk_index, content, content_length,
    embedding, keywords
) VALUES (
    'APP-06_상가화재_영업중단손실_실무가이드.pdf',
    'APP-06-상가화재',
    0,
    '상가화재보험의 핵심은 영업중단 손실(BI, Business Interruption) 보상입니다. 화재로 인한 건물 피해보다 영업을 못하는 기간 동안의 수입 손실이 더 크기 때문입니다. 예를 들어, 월 매출 5천만 원인 음식점이 화재로 3개월 휴업하면 매출 손실 1억 5천만 원 + 고정비(임차료, 인건비) 3천만 원 = 총 1억 8천만 원의 손실이 발생합니다. BI 특약은 평소 매출의 3~6개월치를 보상하며, 보험가입금액은 연간 매출의 50%를 기준으로 산정합니다. 업종별 평균 영업중단 기간은 음식점 2.5개월, 소매점 3.2개월, 서비스업 4.1개월입니다.',
    450,
    array_fill(0, ARRAY[1536])::vector,
    ARRAY['상가화재', '영업중단손실', 'BI보상', '매출손실', '고정비', '음식점', '소매점', '서비스업']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;


-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- [BRP] 비즈니스 리스크 프로텍션 (Business Risk Protection) - 5개 섹터
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- BRP-01: 법인공장화재 (핵심 섹터)
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
