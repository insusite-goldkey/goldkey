# ==========================================================================
# service_manager.py — 골드키 중앙집중 서비스 관리자 (SSOT Control Tower)
#
# [설계 원칙]
#   1. 모든 핵심 기능(스캔·STT·크롤링·RAG)을 단일 클래스로 관리
#   2. st.session_state의 SSOT 키를 이 클래스에서만 읽고 씀
#   3. app.py의 모든 탭은 이 클래스의 메서드만 호출 — 직접 session_state 접근 금지
#   4. 기능 변경 시 이 파일 1곳만 수정하면 전체 탭에 즉시 반영
#
# [관리 서비스]
#   A. ScanService       — 문서 스캔(OCR/Vision), 증권 파싱, SSOT 저장
#   B. STTService        — 음성인식 설정 중앙 관리, 부스트 용어 관리
#   C. CrawlerService    — 약관 크롤링, JIT 인덱싱, 배치 처리
#   D. RAGService        — Semantic Search, 임베딩, 약관 QA 조회
#   E. GoldKeyServiceManager — 위 4개를 통합하는 최상위 컨트롤러
# ==========================================================================

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime as _dt
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# SSOT 세션 키 상수 (app.py와 공유 — 이 값만 참조)
# ---------------------------------------------------------------------------
class _SSOT:
    """session_state SSOT 키 네임스페이스. 오타 방지용."""
    # ── 스캔 허브 ──────────────────────────────────────────────────────────
    SCAN_DATA      = "ssot_scan_data"       # list[dict] — 스캔된 파일 텍스트 목록
    SCAN_TYPE      = "ssot_scan_type"       # str        — 'policy'|'medical'|'other'
    SCAN_FILES     = "ssot_scan_files"      # list[str]  — 파일명 목록
    SCAN_TS        = "ssot_scan_ts"         # str        — 마지막 스캔 시각
    SCAN_TABLES    = "ssot_tables"          # list       — 표 추출 결과
    FULL_TEXT      = "ssot_full_text"       # str        — 전체 결합 텍스트
    # ── 보험증권 파싱 ──────────────────────────────────────────────────────
    POLICY_INFO    = "ssot_policy_info"     # dict       — AI 추출 증권 기본정보
    COVERAGES      = "ssot_coverages"       # list[dict] — 담보 목록
    CLIENT_NAME    = "ssot_client_name"     # str        — 피보험자명
    PARSED_COVS    = "dis_parsed_coverages" # list[dict] — 장해 탭용 담보
    PARSED_ERRS    = "dis_parsed_errors"    # list[str]  — 파싱 오류
    PARSED_RAW     = "dis_parsed_raw_debug" # str        — AI raw JSON (디버그)
    # ── 약관 크롤링 ────────────────────────────────────────────────────────
    CRAWL_RESULT   = "sh_batch_crawl_result"# list[dict] — 배치 크롤링 결과
    # ── RAG ────────────────────────────────────────────────────────────────
    RAG_SYNCED     = "_rag_sync_done"       # bool       — RAG 초기화 완료 여부
    # ── STT ────────────────────────────────────────────────────────────────
    STT_ACTIVE     = "_stt_active"          # bool       — STT 현재 활성 여부


# ---------------------------------------------------------------------------
# A. ScanService — 문서 스캔 & 증권 파싱 중앙 관리
# ---------------------------------------------------------------------------
class ScanService:
    """
    모든 문서 스캔(OCR/Vision) 및 보험증권 파싱을 중앙에서 관리.

    사용법:
        svc = GoldKeyServiceManager.get()
        result = svc.scan.parse_policy(files)
        svc.scan.save_to_ssot(result, st.session_state)
    """

    def parse_policy(self, files: list, parse_fn: Callable) -> dict:
        """
        증권 파일 리스트를 parse_policy_with_vision으로 파싱.
        parse_fn: app.py의 parse_policy_with_vision 함수를 주입받아 사용.
        반환: {policy_info, coverages, errors, _raw_ai_response}
        """
        if not files:
            return {"policy_info": {}, "coverages": [], "errors": [], "_raw_ai_response": ""}
        return parse_fn(files)

    def save_to_ssot(self, parse_result: dict, ss: Any,
                     client_name: str = "", scan_texts: list = None,
                     type_key: str = "policy") -> None:
        """
        parse_policy 결과를 session_state SSOT에 저장.
        scan_hub, policy_scan, disability 탭 모두 이 메서드 사용.
        """
        covs    = parse_result.get("coverages", [])
        pi      = parse_result.get("policy_info") or {}
        raw     = parse_result.get("_raw_ai_response", "")
        ts_now  = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

        # 담보
        if covs:
            ss[_SSOT.COVERAGES]   = covs
            ss[_SSOT.PARSED_COVS] = covs
        # 증권 기본정보
        if pi:
            ss[_SSOT.POLICY_INFO] = pi
            _name = pi.get("insured_name") or client_name
            if _name:
                ss[_SSOT.CLIENT_NAME] = _name
        # raw 디버그
        ss[_SSOT.PARSED_RAW]  = raw
        ss[_SSOT.PARSED_ERRS] = parse_result.get("errors", [])
        # scan_data 병합
        if scan_texts:
            prev = ss.get(_SSOT.SCAN_DATA, [])
            prev.extend(scan_texts)
            ss[_SSOT.SCAN_DATA] = prev
            ss[_SSOT.SCAN_TYPE] = type_key
            ss[_SSOT.SCAN_TS]   = ts_now
            full = "\n\n".join(f"[{d['file']}]\n{d['text']}" for d in prev)
            ss[_SSOT.FULL_TEXT] = full

    def get_ssot_summary(self, ss: Any) -> dict:
        """현재 SSOT 상태 요약 반환 — UI 상태 표시용."""
        return {
            "scan_count":    len(ss.get(_SSOT.SCAN_DATA, [])),
            "coverage_count": len(ss.get(_SSOT.COVERAGES, [])),
            "client_name":   ss.get(_SSOT.CLIENT_NAME, ""),
            "policy_info":   ss.get(_SSOT.POLICY_INFO, {}),
            "last_scan_ts":  ss.get(_SSOT.SCAN_TS, ""),
            "full_text_len": len(ss.get(_SSOT.FULL_TEXT, "")),
        }

    def clear_ssot(self, ss: Any) -> None:
        """전체 SSOT 스캔 데이터 초기화."""
        for key in [
            _SSOT.SCAN_DATA, _SSOT.SCAN_TYPE, _SSOT.SCAN_FILES,
            _SSOT.SCAN_TS, _SSOT.COVERAGES, _SSOT.FULL_TEXT,
            _SSOT.PARSED_COVS, _SSOT.SCAN_TABLES,
            _SSOT.POLICY_INFO, _SSOT.CLIENT_NAME, _SSOT.PARSED_RAW, _SSOT.PARSED_ERRS,
        ]:
            ss.pop(key, None)


# ---------------------------------------------------------------------------
# B. STTService — 음성인식 설정 중앙 관리
# ---------------------------------------------------------------------------
class STTService:
    """
    Web Speech API STT 설정을 중앙에서 관리.
    app.py 상단의 STT_* 상수들을 이 클래스로 위임.
    """

    # ── 기본값 (app.py STT_* 상수와 동기화) ──────────────────────────────
    LANG              = "ko-KR"
    INTERIM           = True
    CONTINUOUS        = True
    MAX_ALT           = 3
    NO_SPEECH_MS      = 3500
    SILENCE_TIMEOUT   = 2000
    MIN_UTTERANCE_MS  = 300
    POST_ROLL_MS      = 800
    RESTART_MS        = 1000
    PREFIX_PAD_MS     = 600
    LEV_THRESHOLD     = 0.88
    LEV_QUEUE         = 10
    DUP_TIME_MS       = 4000

    # ── 보험 전문용어 부스트 목록 ─────────────────────────────────────────
    BOOST_TERMS: List[str] = [
        "치매보험", "경도인지장애", "납입면제", "해지환급금", "CDR척도",
        "장기요양등급", "노인성질환", "알츠하이머", "혈관성치매",
        "실손보험", "암진단비", "뇌혈관질환", "심근경색", "후유장해",
        "보험료", "보장기간", "갱신형", "비갱신형", "특약", "주계약",
        "설명의무", "청약철회", "보험금청구", "표준약관",
        "상해후유장해", "교통상해", "질병입원일당", "질병수술비",
        "골절진단비", "화상진단비", "뇌졸중", "급성심근경색",
    ]

    def add_boost_term(self, term: str) -> None:
        """보험 전문용어를 부스트 목록에 추가. 중복 방지."""
        if term and term not in self.BOOST_TERMS:
            self.BOOST_TERMS.append(term)

    def remove_boost_term(self, term: str) -> None:
        """부스트 목록에서 용어 제거."""
        if term in self.BOOST_TERMS:
            self.BOOST_TERMS.remove(term)

    def get_config(self) -> dict:
        """현재 STT 설정 dict 반환 — UI 설정 화면용."""
        return {
            "lang":             self.LANG,
            "interim":          self.INTERIM,
            "continuous":       self.CONTINUOUS,
            "no_speech_ms":     self.NO_SPEECH_MS,
            "silence_timeout":  self.SILENCE_TIMEOUT,
            "min_utterance_ms": self.MIN_UTTERANCE_MS,
            "post_roll_ms":     self.POST_ROLL_MS,
            "restart_ms":       self.RESTART_MS,
            "lev_threshold":    self.LEV_THRESHOLD,
            "dup_time_ms":      self.DUP_TIME_MS,
            "boost_terms":      self.BOOST_TERMS[:],
        }

    def build_js_config(self) -> str:
        """STT JS 초기화용 설정 JSON 문자열 반환."""
        cfg = self.get_config()
        return json.dumps({
            "lang":           cfg["lang"],
            "interimResults": cfg["interim"],
            "continuous":     cfg["continuous"],
            "maxAlternatives": self.MAX_ALT,
            "noSpeechMs":     cfg["no_speech_ms"],
            "silenceTimeout": cfg["silence_timeout"],
            "minUtteranceMs": cfg["min_utterance_ms"],
            "postRollMs":     cfg["post_roll_ms"],
            "restartMs":      cfg["restart_ms"],
            "levThreshold":   cfg["lev_threshold"],
            "dupTimeMs":      cfg["dup_time_ms"],
        }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# C. CrawlerService — 약관 크롤링 & JIT 인덱싱 중앙 관리
# ---------------------------------------------------------------------------
class CrawlerService:
    """
    disclosure_crawler의 run_jit_policy_lookup / run_batch_jit_from_scan을
    중앙에서 호출. sb_client 관리, 진행 로그 집계.
    """

    def __init__(self, sb_client=None):
        self._sb = sb_client

    def set_sb_client(self, sb_client) -> None:
        """Supabase 클라이언트 주입 (앱 시작 시 1회 설정)."""
        self._sb = sb_client

    def lookup_single(self, company: str, product: str, join_date: str,
                      progress_cb: Optional[Callable] = None) -> dict:
        """
        단건 약관 JIT 조회.
        반환: {cached, pdf_url, period, confidence, reason, chunks_indexed, error}
        """
        try:
            from disclosure_crawler import run_jit_policy_lookup
            return run_jit_policy_lookup(
                company_name=company,
                product_name=product,
                join_date=join_date,
                sb_client=self._sb,
                progress_cb=progress_cb,
            )
        except ImportError:
            return {"error": "disclosure_crawler 모듈 없음", "cached": False,
                    "pdf_url": "", "period": "", "confidence": 0,
                    "reason": "", "chunks_indexed": 0}
        except Exception as e:
            return {"error": str(e), "cached": False, "pdf_url": "",
                    "period": "", "confidence": 0, "reason": "", "chunks_indexed": 0}

    def lookup_batch(self, policies: List[Dict],
                     progress_cb: Optional[Callable] = None) -> List[Dict]:
        """
        복수 증권 배치 JIT 조회.
        policies: [{company, product, join_date, confidence, source_file}, ...]
        반환: [{status, company, product, join_date, chunks_indexed, error}, ...]
        """
        try:
            from disclosure_crawler import run_batch_jit_from_scan
            return run_batch_jit_from_scan(
                scan_policies=policies,
                sb_client=self._sb,
                progress_cb=progress_cb,
            )
        except ImportError:
            return [{"status": "failed", "error": "disclosure_crawler 모듈 없음",
                     "company": p.get("company",""), "product": p.get("product",""),
                     "join_date": p.get("join_date",""), "chunks_indexed": 0}
                    for p in policies]
        except Exception as e:
            return [{"status": "failed", "error": str(e),
                     "company": p.get("company",""), "product": p.get("product",""),
                     "join_date": p.get("join_date",""), "chunks_indexed": 0}
                    for p in policies]

    def build_target_list(self, ss: Any, mode: str = "high_confidence") -> List[Dict]:
        """
        SSOT에서 약관 추적 대상 리스트 구성.
        mode: 'high_confidence'(70%↑) | 'all' | 'ssot_only'
        """
        pi = ss.get(_SSOT.POLICY_INFO, {})
        targets = []
        if pi and (pi.get("company") or pi.get("product_name")):
            targets.append({
                "source_file": "증권 AI 자동추출",
                "company":     pi.get("company", ""),
                "product":     pi.get("product_name", ""),
                "join_date":   pi.get("join_date", ""),
                "confidence":  100,
            })
        if mode == "high_confidence":
            targets = [t for t in targets if t["confidence"] >= 70]
        return targets

    def is_cached(self, company: str, product: str, join_date: str) -> bool:
        """Supabase DB 캐시 여부 확인."""
        try:
            from disclosure_crawler import JITPipelineRunner
            return JITPipelineRunner(self._sb).is_cached(company, product, join_date)
        except Exception:
            return False


# ---------------------------------------------------------------------------
# D. RAGService — Semantic Search & 약관 QA 중앙 관리
# ---------------------------------------------------------------------------
class RAGService:
    """
    RAG 시스템(임베딩 검색, 약관 QA)을 중앙에서 관리.
    app.py의 rag_system 세션 객체와 연동.
    """

    def __init__(self, sb_client=None):
        self._sb    = sb_client
        self._index = None  # FAISS 또는 Supabase pgvector

    def set_sb_client(self, sb_client) -> None:
        self._sb = sb_client

    def search(self, query: str, ss: Any, k: int = 3,
               product_hint: str = "") -> list[dict]:
        """
        RAG 시스템으로 유사 문서 검색.
        ss에 rag_system이 있으면 그것을 사용, 없으면 Supabase 직접 검색 시도.
        """
        rag = ss.get("rag_system")
        if rag and getattr(rag, "index", None) is not None:
            try:
                return rag.search(query, k=k, product_hint=product_hint)
            except Exception:
                pass
        # Supabase fallback
        return self._search_supabase(query, k)

    def _search_supabase(self, query: str, k: int = 3) -> list[dict]:
        """Supabase gk_policy_terms_qa 테이블에서 텍스트 검색 (keyword fallback)."""
        if not self._sb:
            return []
        try:
            resp = (
                self._sb.table("gk_policy_terms_qa")
                .select("chunk_text, company, product, section_type")
                .ilike("chunk_text", f"%{query[:30]}%")
                .limit(k)
                .execute()
            )
            return [{"text": r["chunk_text"],
                     "source": f"{r['company']} {r['product']}"}
                    for r in (resp.data or [])]
        except Exception:
            return []

    def search_policy_terms(self, company: str, product: str,
                            join_date: str, query: str,
                            k: int = 5) -> list[dict]:
        """
        특정 상품의 약관 청크에서 Semantic Search.
        반환: [{chunk_text, section_type, chunk_idx}, ...]
        """
        if not self._sb:
            return []
        try:
            resp = (
                self._sb.table("gk_policy_terms_qa")
                .select("chunk_text, section_type, chunk_idx")
                .eq("company", company)
                .eq("product", product)
                .ilike("chunk_text", f"%{query[:40]}%")
                .limit(k)
                .execute()
            )
            return resp.data or []
        except Exception:
            return []

    def get_indexed_products(self) -> list[dict]:
        """Supabase에 인덱싱된 상품 목록 반환 — 관리 화면용."""
        if not self._sb:
            return []
        try:
            resp = (
                self._sb.table("gk_policy_terms_qa")
                .select("company, product, join_date")
                .eq("section_type", "original")
                .execute()
            )
            seen = {}
            for r in (resp.data or []):
                key = f"{r['company']}|{r['product']}|{r['join_date']}"
                if key not in seen:
                    seen[key] = r
            return list(seen.values())
        except Exception:
            return []

    def delete_product(self, company: str, product: str, join_date: str) -> bool:
        """인덱싱된 상품 삭제 — 관리 화면용."""
        if not self._sb:
            return False
        try:
            self._sb.table("gk_policy_terms_qa") \
                .delete() \
                .eq("company", company) \
                .eq("product", product) \
                .eq("join_date", join_date) \
                .execute()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# E. GoldKeyServiceManager — 최상위 컨트롤러 (싱글톤)
# ---------------------------------------------------------------------------
class GoldKeyServiceManager:
    """
    스캔·STT·크롤링·RAG 4개 서비스를 통합 관리하는 싱글톤 컨트롤러.

    사용법 (app.py 어디서나):
        from service_manager import GoldKeyServiceManager
        gsm = GoldKeyServiceManager.get()

        # 증권 파싱 + SSOT 저장
        result = gsm.scan.parse_policy(files, parse_policy_with_vision)
        gsm.scan.save_to_ssot(result, st.session_state)

        # 약관 크롤링
        gsm.crawler.lookup_single("삼성화재", "무배당암보험", "2019-01-01")

        # RAG 검색
        hits = gsm.rag.search("암 진단 시 보험금 지급 조건", st.session_state)

        # STT 설정
        cfg = gsm.stt.get_config()
    """

    _instance: Optional["GoldKeyServiceManager"] = None

    def __init__(self):
        self.scan    = ScanService()
        self.stt     = STTService()
        self.crawler = CrawlerService()
        self.rag     = RAGService()
        self._initialized = False

    @classmethod
    def get(cls) -> "GoldKeyServiceManager":
        """싱글톤 인스턴스 반환."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, sb_client=None) -> None:
        """
        앱 시작 시 1회 호출. Supabase 클라이언트를 모든 서비스에 주입.
        app.py: GoldKeyServiceManager.get().initialize(_get_sb_client())
        """
        if self._initialized:
            return
        if sb_client:
            self.crawler.set_sb_client(sb_client)
            self.rag.set_sb_client(sb_client)
        self._initialized = True

    def get_status(self, ss: Any) -> dict:
        """
        전체 서비스 상태 요약 반환 — 관리 대시보드용.
        """
        scan_summary = self.scan.get_ssot_summary(ss)
        indexed      = self.rag.get_indexed_products()
        return {
            "scan": scan_summary,
            "rag": {
                "indexed_count": len(indexed),
                "products":      indexed[:5],  # 최대 5개 미리보기
            },
            "stt": {
                "lang":        self.stt.LANG,
                "boost_count": len(self.stt.BOOST_TERMS),
            },
            "crawler": {
                "sb_connected": self.crawler._sb is not None,
            },
        }

    def reset_all(self, ss: Any) -> None:
        """
        전체 SSOT 초기화 (세션 종료 / 고객 전환 시 사용).
        """
        self.scan.clear_ssot(ss)
        ss.pop(_SSOT.CRAWL_RESULT, None)
        ss.pop(_SSOT.RAG_SYNCED, None)


# ---------------------------------------------------------------------------
# SSOT 키 외부 노출 (app.py에서 import하여 사용)
# ---------------------------------------------------------------------------
SSOT = _SSOT
