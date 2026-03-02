/**
 * analyzeMedicalDocument — 전역 AI 의료문서 분석 파이프라인
 *
 * 제2장: 전역 AI 스캐너 & 철통 보안
 *
 * ┌ 파이프라인 흐름 ──────────────────────────────────────────────┐
 * │  rawText (OCR)                                                │
 * │    └─▶ [1] PII 클라이언트 사전 마스킹 (정규식)                │
 * │    └─▶ [2] Gemini API 호출 (System Prompt: 강제 마스킹 지시)  │
 * │    └─▶ [3] 응답 파싱 → 문서 분류 + 구조화                    │
 * │    └─▶ [4] useCustomerStore.completeScanResult() SSOT 업데이트│
 * │    └─▶ [5] Firestore upsert stub                             │
 * └───────────────────────────────────────────────────────────────┘
 *
 * 사용법:
 *   import { analyzeMedicalDocument } from '../utils/analyzeMedicalDocument';
 *   const result = await analyzeMedicalDocument({ scanId, customerId, agentId, rawText, geminiApiKey });
 */

import { useCustomerStore } from '../store/customerStore';

// ── 문서 유형 분류 키워드 맵 ──────────────────────────────────────────────────
const DOC_TYPE_MAP = [
  { type: 'disability',          keywords: ['장해진단서', '장해율', '장해등급', 'ABI', '맥브라이드'] },
  { type: 'surgery',             keywords: ['수술확인서', '수술명', '수술일', '집도의', '마취'] },
  { type: 'diagnosis',           keywords: ['진단서', '상병명', 'KCD', 'ICD', '질병분류'] },
  { type: 'medical_certificate', keywords: ['진료확인서', '진료기간', '외래', '입원', '치료'] },
];

// ── [1] 클라이언트 사전 PII 마스킹 ───────────────────────────────────────────
const PRE_MASK_RULES = [
  // 주민등록번호 뒷자리
  { pattern: /(\d{6})[-\s]?([1-4]\d{6})/g,          replace: '$1-*******' },
  // 전화번호
  { pattern: /(\d{2,3})[-\s]?(\d{3,4})[-\s]?\d{4}/g, replace: '$1-$2-****' },
  // 상세 주소 (시/도 이하 상세)
  { pattern: /(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n,]{1,30}(로|길|동|읍|면)\s?\d+[-\d]*/g,
    replace: '***지역 ***번지' },
  // 이메일
  { pattern: /[\w.-]+@[\w.-]+\.\w{2,}/g,             replace: '***@***.***' },
];

export function preMaskPII(text) {
  let masked = text;
  for (const { pattern, replace } of PRE_MASK_RULES) {
    masked = masked.replace(pattern, replace);
  }
  return masked;
}

// ── [2] Gemini System Prompt ──────────────────────────────────────────────────
const SYSTEM_PROMPT = `
당신은 대한민국 보험 설계사를 위한 의료문서 분석 전문 AI입니다.

[🛡️ 철통 보안 지시 - 반드시 준수]
1. 주민등록번호 뒷자리(7자리)는 절대 출력하지 마십시오. 앞 6자리만 허용, 뒷자리는 반드시 '*******'로 마스킹.
2. 상세 주소(동/번지/호수)는 출력 금지. 시/도·구 수준까지만 허용.
3. 전화번호 끝 4자리는 반드시 '****'로 마스킹.
4. 이메일 주소는 전체 마스킹.
5. 위 규칙을 어길 경우 의료 개인정보 보호법 위반이 발생합니다.

[분석 지시]
다음 의료문서 텍스트를 분석하여 아래 JSON 형식으로만 응답하십시오.
JSON 이외의 텍스트는 절대 출력하지 마십시오.

{
  "docType": "diagnosis|surgery|disability|medical_certificate|other",
  "summary": "설계사용 정밀 요약 (KCD코드, 장해율, 수술명 포함, 3~5문장)",
  "clientSummary": "고객용 안심 요약 (전문용어 배제, 2~3문장, 친절하고 이해하기 쉽게)",
  "kcdCodes": [{"code": "KCD코드", "name": "질병명", "note": "보험 관련 특이사항"}],
  "disabilityRate": null또는숫자(퍼센트),
  "surgeries": ["수술명1", "수술명2"],
  "expectedPayout": 예상수령보험금추정액만원단위_숫자또는0,
  "upsellPoints": ["AI 업셀링 추천 포인트1", "포인트2"],
  "kakaoScript": "카카오톡 상담 멘트 초안 (2~4문장, 친근하고 전문적)"
}
`.trim();

// ── [3] Gemini API 호출 ───────────────────────────────────────────────────────
async function callGemini(maskedText, apiKey) {
  const endpoint =
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

  const body = {
    system_instruction: { parts: [{ text: SYSTEM_PROMPT }] },
    contents: [{
      role: 'user',
      parts: [{ text: `[의료문서 텍스트]\n${maskedText}` }],
    }],
    generationConfig: {
      temperature: 0.1,
      maxOutputTokens: 1024,
      responseMimeType: 'application/json',
    },
  };

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Gemini API 오류 ${res.status}: ${err}`);
  }

  const data = await res.json();
  const raw  = data?.candidates?.[0]?.content?.parts?.[0]?.text ?? '{}';

  try {
    return JSON.parse(raw);
  } catch {
    throw new Error(`Gemini 응답 파싱 실패: ${raw.slice(0, 200)}`);
  }
}

// ── [4] 문서 유형 클라이언트 분류 (API 실패 시 fallback) ─────────────────────
function classifyDocType(text) {
  for (const { type, keywords } of DOC_TYPE_MAP) {
    if (keywords.some((kw) => text.includes(kw))) return type;
  }
  return 'other';
}

// ── [5] 메인 파이프라인 함수 ──────────────────────────────────────────────────
/**
 * @param {object} params
 * @param {string} params.scanId          — SSOT 스캔 레코드 ID
 * @param {string} params.customerId      — 고객 ID
 * @param {string} params.agentId         — 설계사 ID
 * @param {string} params.rawText         — OCR 원본 텍스트
 * @param {string} params.geminiApiKey    — Gemini API 키
 * @returns {Promise<object>}             — 완성된 analysis 객체
 */
export async function analyzeMedicalDocument({
  scanId,
  customerId,
  agentId,
  rawText,
  geminiApiKey,
}) {
  const store = useCustomerStore.getState();

  // scanId가 없으면 신규 레코드 생성
  const resolvedScanId = scanId || store.upsertScanResult(customerId, agentId, {
    rawText, status: 'pending',
  });

  try {
    // 1. 클라이언트 사전 마스킹
    const maskedText = preMaskPII(rawText);

    // 2. Gemini 호출
    let analysis;
    if (geminiApiKey) {
      analysis = await callGemini(maskedText, geminiApiKey);
    } else {
      // API 키 없을 때 목업 fallback (개발/테스트용)
      analysis = _mockAnalysis(maskedText);
    }

    // 3. docType 보정 (AI가 'other'를 반환하면 클라이언트 분류로 보완)
    if (!analysis.docType || analysis.docType === 'other') {
      analysis.docType = classifyDocType(rawText);
    }
    const docType = analysis.docType;

    // 4. SSOT 업데이트 — id 하나만 patch → 전체 동기화
    store.completeScanResult(resolvedScanId, analysis, docType);

    // 5. Firestore upsert stub
    // await firebaseUpsertScan(customerId, agentId, { id: resolvedScanId, analysis, docType, masked: true });

    // 6. audit_log 기록
    console.info('[audit_log]', JSON.stringify({
      action: 'SCAN_COMPLETE', scanId: resolvedScanId,
      customerId, agentId, docType, at: new Date().toISOString(),
    }));

    return { scanId: resolvedScanId, analysis, docType };

  } catch (error) {
    // 에러 시 status → 'error' patch
    store.upsertScanResult(customerId, agentId, {
      id: resolvedScanId, status: 'error',
    });
    console.error('[analyzeMedicalDocument]', error);
    throw error;
  }
}

// ── 목업 분석 결과 (개발/오프라인용) ─────────────────────────────────────────
function _mockAnalysis(text) {
  const hasDisability = /장해|장애/.test(text);
  const hasSurgery    = /수술|절제|성형/.test(text);
  return {
    docType:         hasSurgery ? 'surgery' : hasDisability ? 'disability' : 'diagnosis',
    summary:         '【설계사용】 C34.1 폐악성신생물(우상엽) 진단. 2024-11-10 수술 시행. 장해율 35% 판정. 4세대 실손 비급여 한도 초과 가능성 높음.',
    clientSummary:   '안녕하세요 고객님. 이번 진단서를 분석한 결과, 현재 가입하신 보험에서 치료비 지원을 받으실 수 있는 항목이 확인되었습니다. 구체적인 보험금 청구 절차를 함께 안내해 드리겠습니다.',
    kcdCodes:        [{ code: 'C34.1', name: '기관지 및 폐의 악성신생물', note: '3대 질병 특약 해당, 수술비 청구 가능' }],
    disabilityRate:  hasDisability ? 35 : null,
    surgeries:       hasSurgery ? ['폐우상엽절제술'] : [],
    expectedPayout:  3200,
    upsellPoints:    [
      '4세대 실손 비급여 한도 도달 시 추가 보완 상품 추천 필요',
      '가족력 확인 후 CI보험 추가 설계 검토',
      '수술비 특약 미가입 확인 시 신규 계약 제안 가능',
    ],
    kakaoScript:     '안녕하세요 고객님 😊 진단서 검토 완료되었습니다! 현재 보험으로 수술비+입원비 합산 약 3,200만원 수령 예상되며, 추가로 챙길 수 있는 보장 포인트도 발견했습니다. 편하신 시간에 자세히 말씀드릴게요 🙏',
  };
}
