-- ============================================================
-- [GP-SEC §PIN] 골드키 회원 테이블 스키마 (6자리 PIN 인증 체계)
-- 설계 원칙: PIN 해시 기반 인증 / 연락처 암호화 저장
-- Supabase SQL Editor에서 실행하세요.
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- [gk_members] 설계사 회원 테이블
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gk_members (
    user_id         TEXT PRIMARY KEY,               -- UUID 또는 고유 ID
    name            TEXT NOT NULL,                  -- 회원 이름 (평문)
    name_encrypted  TEXT,                           -- 이름 암호화 (Fernet)
    contact         TEXT,                           -- 연락처 해시 (SHA-256) 또는 암호화
    pin_hash        TEXT NOT NULL,                  -- 6자리 PIN 해시 (SHA-256) ★ 필수
    job             TEXT,                           -- 직업/소속
    user_role       TEXT DEFAULT 'agent'            -- 'agent', 'admin', 'customer'
                    CHECK (user_role IN ('agent', 'admin', 'customer')),
    role            TEXT DEFAULT 'agent',           -- 호환성 유지
    quota_remaining INTEGER DEFAULT 10,             -- 남은 할당량
    is_active       BOOLEAN DEFAULT TRUE,           -- 활성 상태
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_gk_members_name      ON gk_members(name);
CREATE INDEX IF NOT EXISTS idx_gk_members_pin_hash  ON gk_members(pin_hash);
CREATE INDEX IF NOT EXISTS idx_gk_members_role      ON gk_members(user_role);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION public.gk_members_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_gk_members_updated_at ON gk_members;
CREATE TRIGGER trg_gk_members_updated_at
    BEFORE UPDATE ON gk_members
    FOR EACH ROW EXECUTE FUNCTION gk_members_set_updated_at();

-- ──────────────────────────────────────────────────────────
-- RLS(Row Level Security) 설정
-- ──────────────────────────────────────────────────────────
ALTER TABLE gk_members ENABLE ROW LEVEL SECURITY;

-- 서비스 롤은 모든 행 접근 허용 (앱 서버용)
DROP POLICY IF EXISTS "service_role_all_members" ON public.gk_members;
CREATE POLICY "service_role_all_members"
    ON public.gk_members FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- ──────────────────────────────────────────────────────────
-- 보안 정책 (GP-SEC §PIN)
-- ──────────────────────────────────────────────────────────
-- 1. pin_hash는 절대 평문으로 저장 금지 (SHA-256 해시만 허용)
-- 2. 6자리 숫자만 허용 (프론트엔드 검증)
-- 3. PIN 번호는 절대 로그에 기록 금지
-- 4. 기존 회원 데이터는 PIN 시스템 도입 시 전체 초기화

COMMENT ON TABLE gk_members IS '[GP-SEC §PIN] 설계사 회원 테이블 - 6자리 PIN 해시 기반 인증';
COMMENT ON COLUMN gk_members.pin_hash IS '6자리 PIN 번호의 SHA-256 해시값 (필수, 평문 저장 금지)';
COMMENT ON COLUMN gk_members.contact IS '연락처 해시 또는 암호화 (복구용, PIN 인증과 별개)';
