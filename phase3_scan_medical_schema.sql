-- ══════════════════════════════════════════════════════════════════════════════
-- Goldkey AI Masters 2026 — Phase 3: 스캔/의무기록 메타데이터 DB 스키마
-- 치명적 단절 지점 2번, 4번 복구: GCS 파일 명찰 부착 + 의무기록 OCR 활성화
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
-- [테이블 1] gk_scan_files: 스캔 파일 메타데이터 저장소
-- ──────────────────────────────────────────────────────────────────────────────
-- 목적: CRM/HQ에서 업로드된 모든 스캔 파일(증권, 의무기록, 영수증 등)의
--       GCS 경로, 파일 타입, 업로드 시각, 연결된 person_id/agent_id를 추적
-- 보안: gcs_path는 암호화 저장 (AES-256), person_id는 해시 처리
-- ──────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS gk_scan_files (
    -- 기본 식별자
    scan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 연결 정보 (암호화 필수)
    person_id TEXT NOT NULL,  -- SHA-256 해시된 고객 ID
    agent_id TEXT NOT NULL,   -- 설계사 ID
    
    -- 파일 메타데이터
    file_type TEXT NOT NULL,  -- 'policy', 'medical', 'receipt', 'claim', 'other'
    file_name TEXT,           -- 원본 파일명 (암호화 권장)
    gcs_path TEXT NOT NULL,   -- GCS 전체 경로 (암호화 필수: gs://bucket/path/to/file.pdf)
    gcs_bucket TEXT,          -- GCS 버킷명
    file_size_bytes BIGINT,   -- 파일 크기 (바이트)
    mime_type TEXT,           -- MIME 타입 (application/pdf, image/jpeg 등)
    
    -- OCR/처리 상태
    ocr_status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    ocr_engine TEXT,          -- 사용된 OCR 엔진 ('google_vision', 'tesseract', 'policy_ocr_engine')
    
    -- 추출된 텍스트 (평문 저장 - 검색 용도)
    extracted_text TEXT,      -- OCR로 추출된 전체 텍스트
    
    -- 구조화된 데이터 (JSON)
    extracted_fields JSONB,   -- 파싱된 필드 (보험사명, 증권번호, 진단명 등)
    
    -- 태그 및 분류
    tags TEXT[],              -- 검색용 태그 배열
    category TEXT,            -- 세부 카테고리 ('health_insurance', 'life_insurance', 'medical_record' 등)
    
    -- 암호화 메타데이터
    encryption_key_version TEXT,  -- 사용된 암호화 키 버전
    is_encrypted BOOLEAN DEFAULT true,  -- 암호화 여부
    
    -- 타임스탬프
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 소프트 삭제
    deleted_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    
    -- 인덱스 힌트
    CONSTRAINT valid_file_type CHECK (file_type IN ('policy', 'medical', 'receipt', 'claim', 'other')),
    CONSTRAINT valid_ocr_status CHECK (ocr_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- 인덱스 생성 (검색 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_scan_files_person_id ON gk_scan_files(person_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_scan_files_agent_id ON gk_scan_files(agent_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_scan_files_file_type ON gk_scan_files(file_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_scan_files_ocr_status ON gk_scan_files(ocr_status) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_scan_files_uploaded_at ON gk_scan_files(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_files_tags ON gk_scan_files USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_scan_files_extracted_fields ON gk_scan_files USING GIN(extracted_fields);

-- RLS (Row Level Security) 활성화
ALTER TABLE gk_scan_files ENABLE ROW LEVEL SECURITY;

-- RLS 정책: agent_id 기반 접근 제어 (멱등성 보장)
DROP POLICY IF EXISTS "Users can view their own scan files" ON gk_scan_files;
CREATE POLICY "Users can view their own scan files"
    ON gk_scan_files FOR SELECT
    USING (auth.uid()::text = agent_id OR is_active = true);

DROP POLICY IF EXISTS "Users can insert their own scan files" ON gk_scan_files;
CREATE POLICY "Users can insert their own scan files"
    ON gk_scan_files FOR INSERT
    WITH CHECK (auth.uid()::text = agent_id);

DROP POLICY IF EXISTS "Users can update their own scan files" ON gk_scan_files;
CREATE POLICY "Users can update their own scan files"
    ON gk_scan_files FOR UPDATE
    USING (auth.uid()::text = agent_id);


-- ──────────────────────────────────────────────────────────────────────────────
-- [테이블 2] gk_medical_records: 의무기록 OCR 분석 결과 저장소
-- ──────────────────────────────────────────────────────────────────────────────
-- 목적: policy_ocr_engine.py로 처리된 의무기록의 구조화된 데이터 저장
-- 보안: 민감한 의료 정보 암호화 필수 (진단명, 처방 내역 등)
-- ──────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS gk_medical_records (
    -- 기본 식별자
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 연결 정보
    scan_id UUID REFERENCES gk_scan_files(scan_id) ON DELETE CASCADE,  -- 원본 스캔 파일 참조
    person_id TEXT NOT NULL,  -- SHA-256 해시된 고객 ID
    agent_id TEXT NOT NULL,   -- 설계사 ID
    
    -- 의무기록 메타데이터
    record_type TEXT,         -- 'diagnosis', 'prescription', 'lab_result', 'surgery', 'consultation'
    hospital_name TEXT,       -- 병원명 (암호화 권장)
    doctor_name TEXT,         -- 의사명 (암호화 필수)
    visit_date DATE,          -- 진료 날짜
    
    -- 진단 정보 (암호화 필수)
    diagnosis_codes TEXT[],   -- ICD-10 코드 배열
    diagnosis_names TEXT[],   -- 진단명 배열 (암호화)
    
    -- 처방 정보 (암호화 필수)
    prescriptions JSONB,      -- 처방 내역 JSON (약물명, 용량, 기간 등)
    
    -- 검사 결과
    lab_results JSONB,        -- 검사 결과 JSON (항목, 수치, 정상 범위 등)
    
    -- OCR 원본 데이터
    ocr_raw_text TEXT,        -- OCR 추출 원문
    ocr_confidence FLOAT,     -- OCR 신뢰도 (0.0 ~ 1.0)
    
    -- 구조화된 필드 (JSON)
    structured_data JSONB,    -- 파싱된 전체 데이터 구조
    
    -- AI 분석 결과
    ai_summary TEXT,          -- AI 요약 (GPT-4 등)
    risk_flags TEXT[],        -- 위험 플래그 ('chronic_disease', 'surgery_history', 'high_risk' 등)
    insurance_relevance_score FLOAT,  -- 보험 관련성 점수 (0.0 ~ 1.0)
    
    -- 암호화 메타데이터
    encryption_key_version TEXT,
    is_encrypted BOOLEAN DEFAULT true,
    
    -- 타임스탬프
    record_date TIMESTAMPTZ,  -- 의무기록 작성 날짜
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 소프트 삭제
    deleted_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    
    -- 제약 조건
    CONSTRAINT valid_record_type CHECK (record_type IN ('diagnosis', 'prescription', 'lab_result', 'surgery', 'consultation', 'other'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_medical_records_scan_id ON gk_medical_records(scan_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_person_id ON gk_medical_records(person_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_medical_records_agent_id ON gk_medical_records(agent_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_medical_records_record_type ON gk_medical_records(record_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_medical_records_visit_date ON gk_medical_records(visit_date DESC);
CREATE INDEX IF NOT EXISTS idx_medical_records_diagnosis_codes ON gk_medical_records USING GIN(diagnosis_codes);
CREATE INDEX IF NOT EXISTS idx_medical_records_risk_flags ON gk_medical_records USING GIN(risk_flags);
CREATE INDEX IF NOT EXISTS idx_medical_records_structured_data ON gk_medical_records USING GIN(structured_data);

-- RLS 활성화
ALTER TABLE gk_medical_records ENABLE ROW LEVEL SECURITY;

-- RLS 정책 (멱등성 보장)
DROP POLICY IF EXISTS "Users can view their own medical records" ON gk_medical_records;
CREATE POLICY "Users can view their own medical records"
    ON gk_medical_records FOR SELECT
    USING (auth.uid()::text = agent_id OR is_active = true);

DROP POLICY IF EXISTS "Users can insert their own medical records" ON gk_medical_records;
CREATE POLICY "Users can insert their own medical records"
    ON gk_medical_records FOR INSERT
    WITH CHECK (auth.uid()::text = agent_id);

DROP POLICY IF EXISTS "Users can update their own medical records" ON gk_medical_records;
CREATE POLICY "Users can update their own medical records"
    ON gk_medical_records FOR UPDATE
    USING (auth.uid()::text = agent_id);


-- ──────────────────────────────────────────────────────────────────────────────
-- [뷰] 스캔 파일 + 의무기록 통합 조회 뷰
-- ──────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_scan_medical_integrated AS
SELECT 
    sf.scan_id,
    sf.person_id,
    sf.agent_id,
    sf.file_type,
    sf.file_name,
    sf.gcs_path,
    sf.ocr_status,
    sf.uploaded_at,
    mr.record_id,
    mr.record_type,
    mr.hospital_name,
    mr.visit_date,
    mr.diagnosis_names,
    mr.ai_summary,
    mr.risk_flags,
    mr.insurance_relevance_score
FROM gk_scan_files sf
LEFT JOIN gk_medical_records mr ON sf.scan_id = mr.scan_id
WHERE sf.is_active = true
ORDER BY sf.uploaded_at DESC;


-- ──────────────────────────────────────────────────────────────────────────────
-- [함수] 스캔 파일 메타데이터 자동 업데이트 트리거
-- ──────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_scan_file_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성 (멱등성 보장)
DROP TRIGGER IF EXISTS trg_update_scan_files_timestamp ON gk_scan_files;
CREATE TRIGGER trg_update_scan_files_timestamp
    BEFORE UPDATE ON gk_scan_files
    FOR EACH ROW
    EXECUTE FUNCTION update_scan_file_timestamp();

DROP TRIGGER IF EXISTS trg_update_medical_records_timestamp ON gk_medical_records;
CREATE TRIGGER trg_update_medical_records_timestamp
    BEFORE UPDATE ON gk_medical_records
    FOR EACH ROW
    EXECUTE FUNCTION update_scan_file_timestamp();


-- ══════════════════════════════════════════════════════════════════════════════
-- Phase 3 스키마 생성 완료
-- 다음 단계: Supabase SQL Editor에서 위 코드 전체 실행
-- ══════════════════════════════════════════════════════════════════════════════
