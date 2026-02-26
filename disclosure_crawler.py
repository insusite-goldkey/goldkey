# ==========================================================================
# [보험 공시실 실시간 약관 크롤러] disclosure_crawler.py
#
# 역할: 보험사 상품공시실에서 특정 상품·가입일자에 맞는 약관 PDF를
#       실시간 탐색·다운로드·RAG 인덱싱하는 JIT(Just-in-Time) 파이프라인.
#
# 설치:
#   pip install playwright pdfplumber requests
#   playwright install chromium
# ==========================================================================

import io, re, time, hashlib, requests, logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger("disclosure_crawler")


# ---------------------------------------------------------------------------
# 0. AI 크롤링 에이전트 시스템 프롬프트
# ---------------------------------------------------------------------------
CRAWLER_SYSTEM_PROMPT = """[역할] 너는 보험 약관 전문 크롤링 및 인덱싱 에이전트야.

[임무]
1. 사용자가 입력한 [보험사명, 상품명, 가입일자]를 확인해.
2. 해당 보험사의 '상품공시실' URL 규칙을 바탕으로 검색 쿼리를 생성해.
3. 판매 기간(판매개시일 ~ 판매종료일)이 가입일자를 포함하는 PDF만 선택해.
4. 여러 버전: (a) 판매 기간 포함 우선 (b) 동일 조건이면 개정일 최신 선택.
5. 다운로드된 PDF를 JIT RAG 파이프라인으로 즉시 전달해.

[출력] 선택 PDF URL / 판매 기간 / 개정일 / 신뢰도(0~100%) / 선택 근거

[금지] 가입일 범위 외 약관 / 비공식 경로(블로그·2차사이트) / 약관 임의 수정"""


# ---------------------------------------------------------------------------
# 1. 보험사별 공시실 URL 레지스트리
# ---------------------------------------------------------------------------
class CompanyUrlRegistry:
    _REG: dict = {
        "삼성생명":    {"base": "https://www.samsunglife.com",    "url": "https://www.samsunglife.com/customer/publicInfo/productDisclosure.do",    "p": "searchKeyword"},
        "한화생명":    {"base": "https://www.hanwhalife.com",      "url": "https://www.hanwhalife.com/cust/disclosure/productlist.do",               "p": "searchWord"},
        "교보생명":    {"base": "https://www.kyobo.co.kr",         "url": "https://www.kyobo.co.kr/prd/disclosures/productDisclosure",              "p": "keyword"},
        "신한라이프":  {"base": "https://www.shinhanlife.co.kr",   "url": "https://www.shinhanlife.co.kr/hp/cdha0100.do",                           "p": "searchWord"},
        "NH농협생명":  {"base": "https://www.nhlife.co.kr",        "url": "https://www.nhlife.co.kr/disclosure/product",                            "p": "searchText"},
        "미래에셋생명":{"base": "https://life.miraeasset.com",     "url": "https://life.miraeasset.com/csc/disclosure/productTerms.do",             "p": "searchWord"},
        "DB생명":      {"base": "https://www.db-life.com",         "url": "https://www.db-life.com/customer/publicInfo/product.do",                 "p": "keyword"},
        "삼성화재":    {"base": "https://www.samsungfire.com",     "url": "https://www.samsungfire.com/cust/disclosure/productDisclosure.do",        "p": "searchKeyword"},
        "현대해상":    {"base": "https://www.hi.co.kr",            "url": "https://www.hi.co.kr/cms/disclosure/product/list.do",                    "p": "searchKeyword"},
        "DB손해보험":  {"base": "https://www.idb.co.kr",           "url": "https://www.idb.co.kr/cust/disclosure/product.do",                       "p": "keyword"},
        "KB손해보험":  {"base": "https://www.kbinsure.co.kr",      "url": "https://www.kbinsure.co.kr/cust/disclosure/product.do",                  "p": "searchWord"},
        "메리츠화재":  {"base": "https://www.meritzfire.com",      "url": "https://www.meritzfire.com/cust/disclosure/product.do",                  "p": "searchKeyword"},
        "롯데손해보험":{"base": "https://www.lotteins.co.kr",      "url": "https://www.lotteins.co.kr/cust/disclosure/product.do",                  "p": "keyword"},
        "한화손해보험":{"base": "https://www.hwgeneralins.com",    "url": "https://www.hwgeneralins.com/cust/disclosure/product.do",                "p": "keyword"},
        "흥국화재":    {"base": "https://www.heungkukfire.co.kr",  "url": "https://www.heungkukfire.co.kr/cust/disclosure/product.do",              "p": "keyword"},
        "생명보험협회":{"base": "https://klia.or.kr",              "url": "https://klia.or.kr/consumer/publicRelation/productDisclosure.do",        "p": "searchKeyword"},
        "손해보험협회":{"base": "https://www.knia.or.kr",          "url": "https://www.knia.or.kr/consumer/publicRelation/productDisclosure.do",    "p": "searchKeyword"},
    }
    _ALIAS: dict = {
        "삼성": "삼성화재", "삼성화재보험": "삼성화재",
        "현대": "현대해상", "현대해상화재": "현대해상",
        "DB": "DB손해보험", "동부화재": "DB손해보험", "동부생명": "DB생명",
        "KB": "KB손해보험", "한화": "한화생명",
        "농협": "NH농협생명", "미래에셋": "미래에셋생명", "메리츠": "메리츠화재",
    }

    @classmethod
    def normalize(cls, name: str) -> str:
        return cls._ALIAS.get(name.strip(), name.strip())

    @classmethod
    def get(cls, company_name: str) -> Optional[dict]:
        return cls._REG.get(cls.normalize(company_name))

    @classmethod
    def all_companies(cls) -> list:
        return list(cls._REG.keys())


# ---------------------------------------------------------------------------
# 2. 판매 기간 날짜 매처
# ---------------------------------------------------------------------------
class DateRangeMatcher:
    _DATE_PATS = [
        r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})",
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        r"(\d{8})",
    ]
    _OPEN_KW = {"현재", "판매중", "판매 중"}

    @classmethod
    def _parse(cls, s: str) -> Optional[date]:
        for pat in cls._DATE_PATS:
            m = re.search(pat, s.strip())
            if not m:
                continue
            g = m.groups()
            if len(g) == 1:
                r = g[0]
                y, mo, d = int(r[:4]), int(r[4:6]), int(r[6:8])
            else:
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
            try:
                return date(y, mo, d)
            except ValueError:
                continue
        return None

    @classmethod
    def is_date_in_period(cls, join_date_str: str, period_text: str) -> bool:
        jd = cls._parse(join_date_str)
        if not jd:
            return False
        sep = re.search(r"[~\-－–—]", period_text)
        if not sep:
            return False
        left, right = period_text[:sep.start()], period_text[sep.start() + 1:]
        start = cls._parse(left)
        if not start:
            return False
        end_raw = right.strip()
        end = (date.today() if any(kw in end_raw for kw in cls._OPEN_KW) or not end_raw
               else (cls._parse(end_raw) or date.today()))
        return start <= jd <= end

    @classmethod
    def best_match(cls, join_date_str: str, candidates: list) -> Optional[dict]:
        matched = [c for c in candidates if cls.is_date_in_period(join_date_str, c.get("period", ""))]
        if not matched:
            return None
        matched.sort(
            key=lambda c: cls._parse(c.get("revision_date", "")) or date(1900, 1, 1),
            reverse=True,
        )
        return matched[0]


# ---------------------------------------------------------------------------
# 3. Playwright 기반 공시실 크롤러
# ---------------------------------------------------------------------------
class PolicyDisclosureCrawler:
    """headless Playwright로 공시실을 탐색하여 약관 PDF URL 추출."""

    _TIMEOUT_MS = 20_000
    _NAV_WAIT   = 2.0

    # Stealth: 봇 탐지 우회용 추가 헤더/인자
    _STEALTH_ARGS = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]
    _STEALTH_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.co.kr/",
    }

    def __init__(self, headless: bool = True):
        self.headless = headless

    def _launch(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            self._pw      = sync_playwright().__enter__()
            self._browser = self._pw.chromium.launch(
                headless=self.headless,
                args=self._STEALTH_ARGS,
            )
            return True
        except ImportError:
            return False

    def _close(self):
        try:
            self._browser.close()
            self._pw.__exit__(None, None, None)
        except Exception:
            pass

    def _safe_goto(self, page, url: str) -> bool:
        try:
            page.goto(url, timeout=self._TIMEOUT_MS, wait_until="domcontentloaded")
            time.sleep(self._NAV_WAIT)
            return True
        except Exception:
            return False

    def _extract_candidates(self, page, product_name: str) -> list:
        candidates = []
        keywords   = [kw for kw in product_name.split() if len(kw) >= 2]

        # 전략 1: PDF 링크 직접 수집
        try:
            links = page.query_selector_all("a[href$='.pdf'], a[href*='pdf'], a[href*='PDF']")
            for link in links:
                href = link.get_attribute("href") or ""
                text = (link.inner_text() or "").strip()
                try:
                    row_text = str(link.evaluate(
                        "el => el.closest('tr')?.innerText || el.closest('li')?.innerText || ''"
                    ))
                except Exception:
                    row_text = text
                if not any(kw in row_text for kw in keywords):
                    continue
                period_m = re.search(
                    r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}\s*[~\-－–—]\s*"
                    r"(?:\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}|현재|판매중|판매 중)",
                    row_text,
                )
                rev_m = re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", text)
                if href:
                    candidates.append({
                        "url": href, "text": text,
                        "period": period_m.group(0) if period_m else "",
                        "revision_date": rev_m.group(0) if rev_m else "",
                    })
        except Exception:
            pass

        # 전략 2: 행 기반 탐색 (JS 렌더링 공시실 대응)
        if not candidates:
            try:
                rows = page.query_selector_all("tr, .list-item, .product-item")
                for row in rows:
                    row_text = row.inner_text() or ""
                    if not any(kw in row_text for kw in keywords):
                        continue
                    btn  = row.query_selector("a[href], button")
                    href = (btn.get_attribute("href") or "") if btn else ""
                    period_m = re.search(
                        r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}\s*[~\-－–—]\s*"
                        r"(?:\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}|현재|판매중)",
                        row_text,
                    )
                    candidates.append({
                        "url": href,
                        "text": (btn.inner_text()[:80] if btn else ""),
                        "period": period_m.group(0) if period_m else "",
                        "revision_date": "",
                    })
            except Exception:
                pass

        return candidates

    def _try_discontinued_tab(self, page, product_name: str) -> list:
        """판매중지 탭/버튼을 자동 탐색하여 후보 추출."""
        _DISC_KEYWORDS = [
            "판매중지", "판매 중지", "과거상품", "과거 상품",
            "discontinued", "판매종료", "판매 종료",
        ]
        try:
            for kw in _DISC_KEYWORDS:
                btns = page.query_selector_all(
                    f"a, button, li, span, div"
                )
                for btn in btns:
                    try:
                        txt = (btn.inner_text() or "").strip()
                        if kw in txt and len(txt) < 30:
                            btn.click()
                            time.sleep(self._NAV_WAIT)
                            cands = self._extract_candidates(page, product_name)
                            if cands:
                                logger.info(f"판매중지 탭 '{txt}' 클릭으로 {len(cands)}개 후보 발견")
                                return cands
                    except Exception:
                        continue
        except Exception:
            pass
        return []

    @staticmethod
    def _resolve_url(base: str, href: str) -> str:
        if href.startswith("http"):
            return href
        from urllib.parse import urljoin
        return urljoin(base, href)

    def fetch(self, company_name: str, product_name: str, join_date: str) -> dict:
        """공시실 탐색 실행. 반환: {pdf_url, period, revision_date, confidence, reason, candidates_count, error}"""
        info = CompanyUrlRegistry.get(company_name)
        if not info:
            return self._err(f"'{company_name}' 공시실 미등록")
        if not self._launch():
            return self._err("실시간 공시실 크롤링은 서버 환경에서 비활성화됩니다. DB 캐시 검색을 이용하세요.")

        res = dict(pdf_url="", period="", revision_date="",
                   confidence=0, reason="", candidates_count=0, error="")
        try:
            page = self._browser.new_page()
            page.set_extra_http_headers(self._STEALTH_HEADERS)
            # navigator.webdriver 속성 제거 (봇 탐지 우회)
            page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )

            search_url = f"{info['url']}?{info['p']}={requests.utils.quote(product_name)}"
            if not self._safe_goto(page, search_url):
                self._safe_goto(page, info["url"])
                try:
                    page.fill(f"input[name='{info['p']}']", product_name)
                    page.keyboard.press("Enter")
                    time.sleep(self._NAV_WAIT)
                except Exception:
                    pass

            candidates = self._extract_candidates(page, product_name)

            # (3) 판매중지 탭 자동 탐색: 결과 없으면 판매중지 탭 클릭 시도
            if not candidates:
                candidates = self._try_discontinued_tab(page, product_name)

            res["candidates_count"] = len(candidates)

            if not candidates:
                res["error"]  = "공시실에서 PDF 링크를 찾지 못했습니다."
                res["reason"] = "상품명 검색 결과 없음 또는 JS 렌더링 필요"
                return res

            best = DateRangeMatcher.best_match(join_date, candidates)
            if best:
                res.update(
                    pdf_url       = self._resolve_url(info["base"], best["url"]),
                    period        = best["period"],
                    revision_date = best["revision_date"],
                    confidence    = 92,
                    reason        = (
                        f"판매 기간 '{best['period']}'이 가입일자 {join_date}를 포함. "
                        f"개정일: {best['revision_date'] or '미확인'}. "
                        f"총 {len(candidates)}개 후보 중 최적 선택."
                    ),
                )
            else:
                fb = candidates[0]
                res.update(
                    pdf_url    = self._resolve_url(info["base"], fb["url"]),
                    period     = fb["period"],
                    confidence = 40,
                    reason     = (
                        f"가입일자 {join_date} 매칭 실패. "
                        f"첫 번째 결과({fb['text'][:60]}) 반환. 수동 확인 권장."
                    ),
                )
        except Exception as e:
            res["error"] = str(e)[:300]
        finally:
            self._close()
        return res

    @staticmethod
    def _err(msg: str) -> dict:
        return dict(pdf_url="", period="", revision_date="",
                    confidence=0, reason=msg, candidates_count=0, error=msg)


# ---------------------------------------------------------------------------
# 4. JIT 인덱싱 파이프라인
# ---------------------------------------------------------------------------
class JITPipelineRunner:
    """
    PDF URL → pdfplumber 청킹 → Supabase gk_policy_terms 테이블 적재.

    필요 DDL (Supabase SQL Editor에서 1회 실행):
        CREATE TABLE IF NOT EXISTS gk_policy_terms (
            id           BIGSERIAL PRIMARY KEY,
            company      TEXT NOT NULL,
            product      TEXT NOT NULL,
            join_date    TEXT,
            pdf_url      TEXT,
            chunk_idx    INT  DEFAULT 0,
            chunk_text   TEXT NOT NULL,
            char_count   INT  DEFAULT 0,
            content_hash TEXT,
            indexed_at   TIMESTAMPTZ DEFAULT now()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_gk_policy_terms_hash
            ON gk_policy_terms(content_hash);
    """

    TABLE         = "gk_policy_terms"
    CHUNK_SIZE    = 800
    CHUNK_OVERLAP = 100

    def __init__(self, sb_client):
        self.sb = sb_client

    def _download_pdf(self, url: str) -> Optional[bytes]:
        try:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
                "Accept": "application/pdf,*/*",
            }, timeout=30)
            resp.raise_for_status()
            return resp.content
        except Exception:
            return None

    def _pdf_to_chunks(self, pdf_bytes: bytes) -> list:
        full_text = ""
        # 1차: pdfplumber (텍스트 PDF)
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        except Exception:
            pass
        # 2차: pypdf fallback (암호화/구형 PDF 대응)
        if not full_text.strip():
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(pdf_bytes))
                full_text = "\n".join(
                    (page.extract_text() or "") for page in reader.pages
                )
            except Exception:
                pass
        # 3차: 텍스트 추출 완전 실패 시 경고 로그
        if not full_text.strip():
            logger.warning("PDF 텍스트 추출 실패 — 이미지 전용 PDF이거나 암호화됨")
            return []
        step = self.CHUNK_SIZE - self.CHUNK_OVERLAP
        return [
            full_text[i: i + self.CHUNK_SIZE].strip()
            for i in range(0, len(full_text), step)
            if len(full_text[i: i + self.CHUNK_SIZE].strip()) > 50
        ]

    def _upsert(self, company, product, join_date, pdf_url, idx, text,
                revision_date: str = "", period: str = "") -> bool:
        h = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        if not self.sb:
            return False
        try:
            self.sb.table(self.TABLE).upsert(
                {"company": company, "product": product, "join_date": join_date,
                 "pdf_url": pdf_url, "chunk_idx": idx,
                 "chunk_text": text[:4000], "char_count": len(text),
                 "content_hash": h,
                 "revision_date": revision_date,   # (4) 메타데이터 아카이브
                 "sale_period": period,
                 "indexed_at": datetime.utcnow().isoformat()},
                on_conflict="content_hash",
            ).execute()
            return True
        except Exception:
            return False

    def is_cached(self, company: str, product: str, join_date: str) -> bool:
        if not self.sb:
            return False
        try:
            r = (self.sb.table(self.TABLE)
                 .select("id", count="exact")
                 .eq("company", company).eq("product", product).eq("join_date", join_date)
                 .limit(1).execute())
            return (r.count or 0) > 0
        except Exception:
            return False

    def run(self, company: str, product: str, join_date: str,
            pdf_url: str, progress_cb=None) -> dict:
        def _log(msg):
            if progress_cb:
                progress_cb(msg)

        res = dict(ok=False, chunks_indexed=0, chunks_failed=0,
                   pdf_bytes_size=0, error="")

        _log(f"📥 PDF 다운로드 중: {pdf_url[:80]}...")
        pdf_bytes = self._download_pdf(pdf_url)
        if not pdf_bytes:
            res["error"] = "PDF 다운로드 실패. URL 접근 불가 또는 보안 차단."
            _log(f"❌ {res['error']}")
            return res

        res["pdf_bytes_size"] = len(pdf_bytes)
        _log(f"✅ 다운로드 완료 ({len(pdf_bytes)//1024}KB). 텍스트 추출 중...")

        chunks = self._pdf_to_chunks(pdf_bytes)
        if not chunks:
            res["error"] = "PDF 텍스트 추출 실패 (이미지 PDF 또는 암호화)."
            _log(f"❌ {res['error']}")
            return res

        _log(f"📄 {len(chunks)}개 청크 → Supabase 적재 중...")
        for idx, chunk in enumerate(chunks):
            if self._upsert(company, product, join_date, pdf_url, idx, chunk):
                res["chunks_indexed"] += 1
            else:
                res["chunks_failed"] += 1
            if progress_cb and idx % 10 == 0:
                progress_cb(f"  청크 {idx+1}/{len(chunks)} 적재...")

        res["ok"] = res["chunks_indexed"] > 0
        _log(f"✅ 인덱싱 완료: {res['chunks_indexed']}개 성공 / {res['chunks_failed']}개 실패")

        # (5) 오류 알림: 인덱싱 전체 실패 시 Supabase 오류 로그 기록
        if not res["ok"]:
            _write_crawl_error_log(self.sb, company, product, join_date,
                                   pdf_url, "인덱싱 전체 실패")
        return res

    def search_terms(self, company: str, product: str, keyword: str, limit: int = 5) -> list:
        """인덱싱된 약관에서 키워드 ILIKE 검색"""
        if not self.sb:
            return []
        try:
            r = (self.sb.table(self.TABLE)
                 .select("chunk_text, chunk_idx, join_date, pdf_url")
                 .eq("company", company).eq("product", product)
                 .ilike("chunk_text", f"%{keyword}%")
                 .order("chunk_idx").limit(limit).execute())
            return r.data or []
        except Exception:
            return []


# ---------------------------------------------------------------------------
# 4-b. 오류 알림 시스템 (5번 기능)
# ---------------------------------------------------------------------------
_ERROR_LOG_TABLE = "gk_crawl_error_log"
"""
DDL (Supabase SQL Editor에서 1회 실행):
    CREATE TABLE IF NOT EXISTS gk_crawl_error_log (
        id          BIGSERIAL PRIMARY KEY,
        company     TEXT,
        product     TEXT,
        join_date   TEXT,
        pdf_url     TEXT,
        error_msg   TEXT,
        logged_at   TIMESTAMPTZ DEFAULT now()
    );
"""

def _write_crawl_error_log(
    sb_client, company: str, product: str, join_date: str,
    pdf_url: str, error_msg: str
):
    """크롤링/인덱싱 실패 시 Supabase 오류 로그 테이블에 기록."""
    if not sb_client:
        logger.error(f"[CrawlError] {company}/{product}/{join_date}: {error_msg}")
        return
    try:
        sb_client.table(_ERROR_LOG_TABLE).insert({
            "company": company, "product": product,
            "join_date": join_date, "pdf_url": pdf_url,
            "error_msg": error_msg[:500],
            "logged_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"[CrawlError 로그 기록 실패] {e}")


def get_crawl_error_logs(sb_client, limit: int = 50) -> list:
    """관리자용: 최근 크롤링 오류 로그 조회."""
    if not sb_client:
        return []
    try:
        r = (sb_client.table(_ERROR_LOG_TABLE)
             .select("*")
             .order("logged_at", desc=True)
             .limit(limit)
             .execute())
        return r.data or []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 5. 통합 JIT 조회 진입점 (app.py에서 단일 호출)
# ---------------------------------------------------------------------------
def run_jit_policy_lookup(
    company_name: str,
    product_name: str,
    join_date: str,
    sb_client,
    progress_cb=None,
) -> dict:
    """
    JIT 약관 조회 전체 파이프라인 단일 진입점.

    흐름:
      1. Supabase DB 캐시 확인 (이미 인덱싱 → 즉시 반환)
      2. 없으면 공시실 크롤링 → PDF URL 획득
      3. JIT 인덱싱 → Supabase 적재

    반환:
      {
        "cached": bool,
        "pdf_url": str,
        "period": str,
        "confidence": int,       # 0~100
        "reason": str,
        "chunks_indexed": int,
        "error": str,
      }
    """

    def _log(msg: str):
        if progress_cb:
            progress_cb(msg)

    pipeline = JITPipelineRunner(sb_client)
    result   = dict(cached=False, pdf_url="", period="",
                    confidence=0, reason="", chunks_indexed=0, error="")

    # ── Step 1: 캐시 확인 ─────────────────────────────────────────────
    if pipeline.is_cached(company_name, product_name, join_date):
        result.update(cached=True, confidence=100,
                      reason="Supabase DB에 이미 인덱싱된 약관입니다. 즉시 검색 가능.")
        _log("✅ DB 캐시 히트 — 공시실 크롤링 생략")
        return result

    _log(f"🔍 DB 미등록 → 공시실 실시간 크롤링 시작 "
         f"({company_name} / {product_name} / 가입일 {join_date})")

    # ── Step 2: 공시실 크롤링 ─────────────────────────────────────────
    crawl = PolicyDisclosureCrawler().fetch(company_name, product_name, join_date)
    result.update(pdf_url=crawl["pdf_url"], period=crawl["period"],
                  confidence=crawl["confidence"], reason=crawl["reason"],
                  error=crawl["error"])

    if not crawl["pdf_url"]:
        _log(f"❌ 공시실 크롤링 실패: {crawl['error']}")
        # (5) 오류 알림: 크롤링 실패 로그 기록
        _write_crawl_error_log(
            sb_client, company_name, product_name, join_date,
            "", crawl["error"]
        )
        return result

    _log(f"✅ 약관 PDF 확보 (신뢰도 {crawl['confidence']}%) → 인덱싱 시작")

    # ── Step 3: JIT 인덱싱 ────────────────────────────────────────────
    pipe_res = pipeline.run(
        company_name, product_name, join_date, crawl["pdf_url"], progress_cb=_log
    )
    result["chunks_indexed"] = pipe_res["chunks_indexed"]
    if pipe_res["error"]:
        result["error"] = pipe_res["error"]

    return result


# ---------------------------------------------------------------------------
# 6. 합성 데이터 생성 (Synthetic QA Generator) — Gemini 기반
# ---------------------------------------------------------------------------

# 핵심 조항 섹션 키워드 (SDG 집중 대상)
_CORE_SECTION_KEYWORDS = [
    "보상하는 손해", "보상하지 않는 손해", "면책", "면책사항", "면책조항",
    "지급 사유", "지급사유", "보험금 지급", "지급 기준", "지급기준",
    "보장내용", "보장 내용", "담보", "특약", "주요 보장",
    "진단", "수술", "입원", "통원", "재활",
    "고지의무", "계약 전 알릴 의무", "알릴 의무",
    "보험료 납입", "납입면제", "실효", "해지", "환급",
]


class SyntheticQAGenerator:
    """
    보험 약관 텍스트 → Gemini Flash(저렴)로 핵심 조항 선별
    → Gemini Pro(고성능)로 합성 QA 20개 생성
    → Supabase gk_policy_terms_qa 테이블에 원문+QA 병렬 적재.

    DDL (Supabase SQL Editor에서 1회 실행):
        CREATE TABLE IF NOT EXISTS gk_policy_terms_qa (
            id            BIGSERIAL PRIMARY KEY,
            company       TEXT NOT NULL,
            product       TEXT NOT NULL,
            join_date     TEXT,
            section_type  TEXT,        -- 'original' | 'synthetic_q' | 'synthetic_qa'
            chunk_idx     INT  DEFAULT 0,
            chunk_text    TEXT NOT NULL,
            char_count    INT  DEFAULT 0,
            content_hash  TEXT,
            indexed_at    TIMESTAMPTZ DEFAULT now()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_gk_policy_terms_qa_hash
            ON gk_policy_terms_qa(content_hash);
    """

    TABLE_QA    = "gk_policy_terms_qa"
    CHUNK_SIZE  = 600
    MAX_CHUNKS_FOR_SDG = 30   # SDG 대상 청크 최대 수 (비용 제어)

    # 핵심 조항 섹션 감지 (CORE_SECTION_KEYWORDS)
    _CORE_KW = _CORE_SECTION_KEYWORDS

    # Gemini 모델 설정
    # - 질문 생성(고성능): gemini-2.0-flash  ← GPT-4o 대신 Gemini 계열 최고성능
    # - 저장/검색용 임베딩: 텍스트 그대로 저장 (sentence-transformers는 JITPipeline이 담당)
    MODEL_SDG   = "gemini-2.0-flash"       # 합성 질문 생성 (고품질)
    MODEL_CHEAP = "gemini-2.0-flash-lite"  # 핵심 조항 선별 (저비용)

    def __init__(self, sb_client, gemini_client=None):
        self.sb     = sb_client
        self._gc    = gemini_client   # google.genai client (없으면 생략)

    # ── 핵심 조항 감지 ────────────────────────────────────────────────
    def _is_core_section(self, text: str) -> bool:
        """텍스트에 핵심 조항 키워드가 포함되어 있으면 True"""
        return any(kw in text for kw in self._CORE_KW)

    # ── 합성 QA 생성 ──────────────────────────────────────────────────
    def _generate_qa(self, chunk_text: str, company: str, product: str) -> list:
        """
        Gemini로 약관 청크 → 예상 질문 20개 생성.
        반환: ["질문1", "질문2", ...]
        """
        if not self._gc:
            return []

        prompt = (
            f"너는 베테랑 보험 설계사야. 다음 보험 약관 내용을 보고, "
            f"고객들이 실제로 물어볼 법한 질문 20개를 만들어줘.\n\n"
            f"[보험사] {company}\n"
            f"[상품명] {product}\n\n"
            f"[약관 내용]\n{chunk_text[:1200]}\n\n"
            f"[요구사항]\n"
            f"- 질문은 \"암 진단 시 얼마를 받나요?\"와 같이 구어체로 작성할 것.\n"
            f"- 보험금 지급 조건, 면책 조항, 특약 사항에 집중할 것.\n"
            f"- 결과는 반드시 한 줄에 하나씩 질문만 나열할 것. 번호·기호 없이 질문 텍스트만.\n"
            f"- 한국어로만 작성할 것."
        )
        try:
            from google.genai import types as _gt
            resp = self._gc.models.generate_content(
                model=self.MODEL_SDG,
                contents=prompt,
                config=_gt.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
            )
            raw = (resp.text or "").strip()
            questions = [
                ln.strip().lstrip("0123456789.-) ").strip()
                for ln in raw.split("\n")
                if ln.strip() and len(ln.strip()) > 5
            ]
            return questions[:20]
        except Exception:
            return []

    # ── Supabase upsert ───────────────────────────────────────────────
    def _upsert_qa(self, company: str, product: str, join_date: str,
                   section_type: str, idx: int, text: str) -> bool:
        h = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        if not self.sb:
            return False
        try:
            self.sb.table(self.TABLE_QA).upsert(
                {"company": company, "product": product, "join_date": join_date,
                 "section_type": section_type, "chunk_idx": idx,
                 "chunk_text": text[:4000], "char_count": len(text),
                 "content_hash": h},
                on_conflict="content_hash",
            ).execute()
            return True
        except Exception:
            return False

    # ── 메인 실행 ─────────────────────────────────────────────────────
    def run(self, company: str, product: str, join_date: str,
            chunks: list, progress_cb=None) -> dict:
        """
        chunks: JITPipelineRunner._pdf_to_chunks() 결과 (str 리스트)
        흐름:
          1. 원문 청크 → gk_policy_terms_qa 저장 (section_type='original')
          2. 핵심 조항 선별 (CORE_SECTION_KEYWORDS 포함 청크만)
          3. 선별된 청크 → Gemini SDG → 합성 QA 생성
          4. "질문\n답변근거: 원문" 형태로 gk_policy_terms_qa 저장 (section_type='synthetic_qa')
        """
        def _log(msg: str):
            if progress_cb:
                progress_cb(msg)

        res = dict(original_saved=0, core_chunks=0,
                   qa_generated=0, qa_saved=0, error="")

        # Step 1: 원문 저장
        _log("📄 원문 청크 저장 중...")
        for idx, chunk in enumerate(chunks):
            if self._upsert_qa(company, product, join_date, "original", idx, chunk):
                res["original_saved"] += 1

        # Step 2: 핵심 조항 선별
        core_chunks = [c for c in chunks if self._is_core_section(c)]
        core_chunks  = core_chunks[:self.MAX_CHUNKS_FOR_SDG]
        res["core_chunks"] = len(core_chunks)
        _log(f"🎯 핵심 조항 {len(core_chunks)}개 청크 선별 완료 (SDG 대상)")

        if not core_chunks:
            _log("ℹ️ 핵심 조항 키워드 미포함 — SDG 생략. 원문만 저장됨.")
            return res

        if not self._gc:
            _log("⚠️ Gemini 클라이언트 미연결 — SDG 생략. 원문만 저장됨.")
            return res

        # Step 3 & 4: SDG 실행
        _log(f"🤖 Gemini({self.MODEL_SDG}) SDG 시작 — 핵심 {len(core_chunks)}개 청크 처리...")
        qa_idx = len(chunks)   # 원문 이후 idx 부터 시작
        for c_idx, chunk in enumerate(core_chunks):
            _log(f"  [{c_idx+1}/{len(core_chunks)}] 합성 질문 생성 중...")
            questions = self._generate_qa(chunk, company, product)
            res["qa_generated"] += len(questions)

            for q in questions:
                combined = f"질문: {q}\n답변근거: {chunk[:600]}"
                if self._upsert_qa(company, product, join_date,
                                   "synthetic_qa", qa_idx, combined):
                    res["qa_saved"] += 1
                    qa_idx += 1

        _log(
            f"✅ SDG 완료: 원문 {res['original_saved']}개 + "
            f"합성 QA {res['qa_saved']}개 저장"
        )
        return res

    def search_semantic(self, company: str, product: str,
                        keyword: str, limit: int = 5,
                        include_synthetic: bool = True) -> list:
        """
        gk_policy_terms_qa에서 ILIKE 검색.
        include_synthetic=True면 원문+합성QA 모두, False면 원문만.
        """
        if not self.sb:
            return []
        try:
            q = (self.sb.table(self.TABLE_QA)
                 .select("chunk_text, chunk_idx, section_type, join_date")
                 .eq("company", company).eq("product", product)
                 .ilike("chunk_text", f"%{keyword}%")
                 .order("section_type").order("chunk_idx")
                 .limit(limit))
            if not include_synthetic:
                q = q.eq("section_type", "original")
            return q.execute().data or []
        except Exception:
            return []
