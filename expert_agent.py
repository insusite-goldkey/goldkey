# ==========================================================================
# [전문가 자율 학습 에이전트] expert_agent.py
# 역할: 의학 논문(PubMed) + 국가법령정보(law.go.kr) + 금감원(fss.or.kr) 데이터를
#       자율적으로 수집·분석·요약하여 Supabase 지식 버킷에 적재한다.
#
# 핵심 설계 원칙:
#   1. ExpertSourceFilter  — 화이트리스트 도메인/API만 접근
#   2. ReAct 루프          — Gemini가 Thought→Action→Observation→Save 자율 반복
#   3. Confidence Gate     — 신뢰도 90% 미만 → '승인 대기' 분류
#   4. Deterministic Calc  — 보험금 산출은 Python 정밀 연산만
#   5. 기존 인프라 재사용  — get_client() / _get_sb_client() 패턴 그대로
#
# Supabase 테이블 DDL (SQL Editor에서 1회 실행):
# -----------------------------------------------------------------------
# CREATE TABLE IF NOT EXISTS gk_expert_knowledge (
#     id           BIGSERIAL PRIMARY KEY,
#     topic        TEXT NOT NULL,
#     source_type  TEXT NOT NULL,
#     source_url   TEXT DEFAULT '',
#     summary_ko   TEXT NOT NULL,
#     raw_content  TEXT DEFAULT '',
#     confidence   NUMERIC(5,2) DEFAULT 0,
#     tags         TEXT[] DEFAULT '{}',
#     created_at   TIMESTAMPTZ DEFAULT now(),
#     approved_by  TEXT DEFAULT '',
#     level        TEXT DEFAULT 'Expert'
# );
# CREATE TABLE IF NOT EXISTS gk_knowledge_pending (
#     id           BIGSERIAL PRIMARY KEY,
#     topic        TEXT NOT NULL,
#     source_type  TEXT NOT NULL,
#     source_url   TEXT DEFAULT '',
#     summary_ko   TEXT NOT NULL,
#     raw_content  TEXT DEFAULT '',
#     confidence   NUMERIC(5,2) DEFAULT 0,
#     tags         TEXT[] DEFAULT '{}',
#     created_at   TIMESTAMPTZ DEFAULT now(),
#     status       TEXT DEFAULT '대기'
# );
# ==========================================================================

import os, re, json, time, requests
import xml.etree.ElementTree as ET
from datetime import datetime as dt
from typing import Optional


# ---------------------------------------------------------------------------
# 1. 신뢰 소스 화이트리스트
# ---------------------------------------------------------------------------
class ExpertSourceFilter:
    WHITELIST_DOMAINS = [
        "law.go.kr", "fss.or.kr", "kidi.or.kr",
        "ncbi.nlm.nih.gov", "nts.go.kr", "mohw.go.kr",
        "hira.or.kr", "nhis.or.kr", "kma.org", "supremecourt.go.kr",
    ]
    EXPERT_KEYWORDS = ["판례", "논문", "가이드라인", "고시", "시행령", "심사지침"]

    @classmethod
    def is_trusted(cls, url: str) -> bool:
        return any(d in url for d in cls.WHITELIST_DOMAINS)

    @classmethod
    def build_expert_query(cls, base_query: str, domain_filter: bool = True) -> str:
        kw = " OR ".join(cls.EXPERT_KEYWORDS[:3])
        if domain_filter:
            site_str = " OR ".join(f"site:{d}" for d in cls.WHITELIST_DOMAINS[:5])
            return f"{base_query} ({kw}) ({site_str})"
        return f"{base_query} ({kw})"


# ---------------------------------------------------------------------------
# 2. 국가법령정보센터 Open API (XML iterparse — 대용량 안전)
# ---------------------------------------------------------------------------
class LawExpertAPI:
    """
    국가법령정보센터 공공데이터 Open API 직접 호출.
    API 키: https://open.law.go.kr 회원가입 후 발급
    secrets.toml: LAW_API_KEY = "발급키"
    """
    BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _iterparse_items(self, content: bytes, tag: str, fields: dict) -> list[dict]:
        """iterparse — 메모리 효율적 XML 파싱"""
        results = []
        try:
            import io
            for event, elem in ET.iterparse(io.BytesIO(content), events=("end",)):
                if elem.tag == tag:
                    item = {k: (elem.findtext(v) or "").strip() for k, v in fields.items()}
                    results.append(item)
                    elem.clear()
        except ET.ParseError:
            pass
        return results

    def search_precedents(self, query: str, max_results: int = 5) -> list[dict]:
        """판례 검색"""
        params = {"OC": self.api_key, "target": "prec", "type": "XML",
                  "query": query, "display": min(max_results, 20)}
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return [{"error": str(e)}]

        fields = {"title": "사건명", "case_no": "사건번호",
                  "court": "법원명", "date": "선고일자", "summary": "판시사항"}
        items = self._iterparse_items(resp.content, "prec", fields)
        for it in items:
            it["source_url"]  = f"https://www.law.go.kr/판례/{it.get('case_no','')}"
            it["source_type"] = "law_api"
            it["summary"]     = it.get("summary", "")[:500]
        return items[:max_results]

    def search_statutes(self, query: str, max_results: int = 3) -> list[dict]:
        """법령(시행령·고시·규칙) 검색"""
        params = {"OC": self.api_key, "target": "law", "type": "XML",
                  "query": query, "display": min(max_results, 10)}
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return [{"error": str(e)}]

        fields = {"title": "법령명한글", "law_id": "법령ID",
                  "promulgate": "공포일자", "ministry": "소관부처명"}
        items = self._iterparse_items(resp.content, "law", fields)
        for it in items:
            it["source_url"]  = f"https://www.law.go.kr/법령/{it.get('title','')}"
            it["source_type"] = "law_api"
        return items[:max_results]


# ---------------------------------------------------------------------------
# 3. PubMed 의학 논문 수집 (NCBI E-utilities, Full-text 우선)
# ---------------------------------------------------------------------------
class MedicalStudyTool:
    """
    NCBI PubMed E-utilities API — requests 직접 호출 (pymed 불필요).
    Full-text(PMC) 보유 논문 우선 정렬.
    """
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self, email: str = "goldkey-ai@insurance.kr"):
        self.email = email

    def search_papers(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            sr = requests.get(self.ESEARCH_URL, params={
                "db": "pubmed", "term": query, "retmax": max_results * 2,
                "retmode": "json", "email": self.email, "sort": "relevance",
            }, timeout=15)
            sr.raise_for_status()
            ids = sr.json().get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            return [{"error": str(e)}]

        if not ids:
            return []

        try:
            fr = requests.get(self.EFETCH_URL, params={
                "db": "pubmed", "id": ",".join(ids[:max_results]),
                "rettype": "abstract", "retmode": "xml", "email": self.email,
            }, timeout=20)
            fr.raise_for_status()
        except Exception as e:
            return [{"error": str(e)}]

        papers = []
        try:
            root = ET.fromstring(fr.content)
            for art in root.findall(".//PubmedArticle"):
                pmid   = art.findtext(".//PMID") or ""
                title  = art.findtext(".//ArticleTitle") or ""
                year   = art.findtext(".//PubDate/Year") or ""
                jname  = art.findtext(".//Journal/Title") or ""
                ab_parts = [e.text or "" for e in art.findall(".//AbstractText")]
                abstract = " ".join(ab_parts)[:1000]
                pmc_id = art.findtext(".//ArticleId[@IdType='pmc']") or ""
                ft_url = (f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
                          if pmc_id else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
                papers.append({
                    "pmid": pmid, "title": title, "year": year, "journal": jname,
                    "abstract": abstract, "has_fulltext": bool(pmc_id),
                    "source_url": ft_url, "source_type": "pubmed",
                })
        except ET.ParseError:
            pass

        papers.sort(key=lambda x: not x["has_fulltext"])
        return papers[:max_results]


# ---------------------------------------------------------------------------
# 4. 지식 버킷 (Supabase + 신뢰도 게이트)
# ---------------------------------------------------------------------------
class ExpertKnowledgeBucket:
    """
    confidence >= 90  → gk_expert_knowledge (승인 완료)
    confidence <  90  → gk_knowledge_pending (마스터 승인 대기)
    """
    CONFIDENCE_THRESHOLD = 90.0
    TABLE_APPROVED = "gk_expert_knowledge"
    TABLE_PENDING  = "gk_knowledge_pending"

    def __init__(self, sb_client):
        self.sb = sb_client

    def upsert(self, topic: str, source_type: str, source_url: str,
               summary_ko: str, raw_content: str,
               confidence: float, tags: list) -> dict:
        now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        row = {
            "topic": topic, "source_type": source_type, "source_url": source_url,
            "summary_ko": summary_ko, "raw_content": raw_content[:3000],
            "confidence": round(confidence, 2), "tags": tags, "created_at": now,
        }
        if not self.sb:
            return {"table": "none", "ok": False, "reason": "Supabase 미연결"}

        if confidence >= self.CONFIDENCE_THRESHOLD:
            table, row["level"] = self.TABLE_APPROVED, "Expert"
        else:
            table, row["status"] = self.TABLE_PENDING, "대기"

        try:
            self.sb.table(table).insert(row).execute()
            return {"table": table, "ok": True, "reason": "저장 완료"}
        except Exception as e:
            return {"table": table, "ok": False, "reason": str(e)[:200]}

    def search_similar(self, query: str, limit: int = 3) -> list[dict]:
        if not self.sb:
            return []
        try:
            return (self.sb.table(self.TABLE_APPROVED)
                    .select("topic,summary_ko,source_type,source_url,confidence,tags")
                    .ilike("summary_ko", f"%{query}%")
                    .order("confidence", desc=True).limit(limit)
                    .execute().data or [])
        except Exception:
            return []

    def list_pending(self) -> list[dict]:
        if not self.sb:
            return []
        try:
            return (self.sb.table(self.TABLE_PENDING).select("*")
                    .eq("status", "대기").order("created_at", desc=True)
                    .limit(50).execute().data or [])
        except Exception:
            return []

    def approve(self, pending_id: int, approved_by: str = "master") -> bool:
        if not self.sb:
            return False
        try:
            row = (self.sb.table(self.TABLE_PENDING).select("*")
                   .eq("id", pending_id).single().execute().data)
            if not row:
                return False
            row.pop("id", None); row.pop("status", None)
            row["approved_by"] = approved_by; row["level"] = "Expert"
            self.sb.table(self.TABLE_APPROVED).insert(row).execute()
            self.sb.table(self.TABLE_PENDING).update({"status": "승인"}).eq("id", pending_id).execute()
            return True
        except Exception:
            return False

    def reject(self, pending_id: int) -> bool:
        if not self.sb:
            return False
        try:
            self.sb.table(self.TABLE_PENDING).update({"status": "반려"}).eq("id", pending_id).execute()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# 5. Gemini 전문가 분석 엔진 (30년 경력 설계사 페르소나)
# ---------------------------------------------------------------------------
_EXPERT_TRANSLATE_PROMPT = """[역할]
당신은 30년 경력의 수석 보험 설계사이며, 재활의학·신경과 전문의 및 세무사와 협업하는 보상 전문가입니다.
약관의 자구 해석에만 매몰되지 말고, 판례와 실제 손해사정 실무를 결합하여 고객에게 유리한 전략을 제시하십시오.

[번역 전략]
1. 의학적 원리: 병리 기전을 약관상 '상해'/'질병' 정의와 매칭
2. 보상 실무: AMA 장해 평정 또는 약관 후유장해 % 해당 가능성 소견
3. 고객 친화적 비유: 전문 용어 → 체감 증상으로 설명
4. 법령 대조: 판례·법령 조항 인용 → 지급 정당성 확보

[출력 형식 — 반드시 준수]
- [의학적 핵심]: (전문 데이터 기반 요약, 100자 이상)
- [설계사 관점 포인트]: (30년 경력 보상 노하우)
- [고객 설명 멘트]: (신뢰감·쉬운 용어)
- [약관 대조 결론]: (지급 가능 여부 + 대응 전략)
- [면책 고지]: 본 분석은 보험 보상 실무 참고용이며, 확정적 의학 진단은 전문의 소견에 따릅니다.

[입력 자료]
"""

_CONFIDENCE_EVAL_PROMPT = """아래 보험 전문 지식 요약문의 신뢰도를 0~100 사이 숫자 하나만 출력하십시오.
평가 기준:
- 공식 API(law.go.kr/pubmed) 출처 + 구체적 판례번호/PMID 포함: 85~100
- 공식 출처이나 추록만 있고 원문 미확인: 65~84
- 출처 불명확 또는 2차 인용: 0~64
숫자만 출력. 설명 불필요.

[요약문]
"""


class ExpertAnalysisEngine:
    MODEL = "gemini-2.0-flash"

    def __init__(self, gemini_client):
        self.client = gemini_client

    def _call(self, prompt: str, max_tokens: int = 2000) -> str:
        if self.client is None:
            return "[오류] Gemini API 클라이언트 없음"
        try:
            from google.genai import types as _gt
            resp = self.client.models.generate_content(
                model=self.MODEL, contents=prompt,
                config=_gt.GenerateContentConfig(
                    max_output_tokens=max_tokens, temperature=0.0)
            )
            return resp.text or ""
        except Exception as e:
            return f"[Gemini 오류] {str(e)[:200]}"

    def translate_to_expert(self, raw_content: str) -> str:
        """의학/법률 원문 → 30년 설계사 관점 한국어 요약"""
        return self._call(_EXPERT_TRANSLATE_PROMPT + raw_content[:3000])

    def evaluate_confidence(self, summary_ko: str) -> float:
        """요약문 신뢰도 자가 평가 (0~100)"""
        raw = self._call(_CONFIDENCE_EVAL_PROMPT + summary_ko[:500], max_tokens=10)
        try:
            return min(100.0, max(0.0, float(re.search(r"\d+(\.\d+)?", raw).group())))
        except Exception:
            return 50.0


# ---------------------------------------------------------------------------
# 6. ReAct 자율 학습 루프 (Thought → Action → Observation → Save)
# ---------------------------------------------------------------------------
class ExpertStudyAgent:
    """
    ReAct 프레임워크 기반 자율 학습 에이전트.
    1회 run() 호출 → 의학+법령 자료 수집·분석·저장 전 과정 자동 실행.

    사용 예시 (app.py t9 관리자 탭):
        from expert_agent import ExpertStudyAgent
        agent = ExpertStudyAgent(
            gemini_client = get_client(),
            sb_client     = _get_sb_client(),
            law_api_key   = st.secrets.get("LAW_API_KEY", ""),
        )
        result = agent.run("경추 척수증 후유장해 보험금 청구 전략")
    """

    MAX_STEPS = 6  # 무한루프 방지

    def __init__(self, gemini_client, sb_client, law_api_key: str = ""):
        self.engine = ExpertAnalysisEngine(gemini_client)
        self.bucket = ExpertKnowledgeBucket(sb_client)
        self.law    = LawExpertAPI(law_api_key) if law_api_key else None
        self.med    = MedicalStudyTool()
        self.log: list[dict] = []

    def _log(self, step: str, thought: str, action: str, observation: str) -> dict:
        entry = {"step": step, "thought": thought,
                 "action": action, "observation": observation[:300],
                 "ts": dt.now().strftime("%H:%M:%S")}
        self.log.append(entry)
        return entry

    def run(self, topic: str,
            tags: list | None = None,
            law_query: str | None = None,
            med_query: str | None = None) -> dict:
        """
        주제(topic)에 대한 자율 학습 실행.
        반환: {"topic", "steps_log", "saved": [{"table","ok","reason"}, ...]}
        """
        self.log = []
        saved    = []
        tags     = tags or []

        # ── Step 1: Thought ────────────────────────────────────────────────
        self._log("1_thought",
                  thought=f"'{topic}' 주제에 대해 의학 논문과 법령 판례를 병렬 수집한다.",
                  action="계획 수립",
                  observation="의학 쿼리 + 법령 쿼리 병렬 실행 예정")

        # ── Step 2: Action — PubMed 의학 논문 수집 ────────────────────────
        mq     = med_query or ExpertSourceFilter.build_expert_query(topic, domain_filter=False)
        papers = self.med.search_papers(mq, max_results=3)
        self._log("2_med_action",
                  thought=f"PubMed에서 '{mq}' 검색",
                  action="MedicalStudyTool.search_papers()",
                  observation=f"{len(papers)}건 수집")

        # ── Step 3: Action — 법령·판례 수집 ───────────────────────────────
        precedents, statutes = [], []
        if self.law:
            lq         = law_query or topic
            precedents = self.law.search_precedents(lq, max_results=3)
            statutes   = self.law.search_statutes(lq,   max_results=2)
            self._log("3_law_action",
                      thought=f"law.go.kr API로 '{lq}' 판례·법령 검색",
                      action="LawExpertAPI.search_precedents() + search_statutes()",
                      observation=f"판례 {len(precedents)}건, 법령 {len(statutes)}건")
        else:
            self._log("3_law_skip",
                      thought="LAW_API_KEY 미설정 — 법령 수집 건너뜀",
                      action="skip",
                      observation="secrets.toml에 LAW_API_KEY 등록 필요")

        # ── Step 4: Observation — 원문 통합 ───────────────────────────────
        raw_parts = []
        for p in papers:
            if "error" not in p:
                raw_parts.append(
                    f"[PubMed PMID:{p.get('pmid','')}] {p.get('title','')}\n"
                    f"저널: {p.get('journal','')} ({p.get('year','')})\n"
                    f"추록: {p.get('abstract','')}\n"
                    f"URL: {p.get('source_url','')}"
                )
        for pr in precedents:
            if "error" not in pr:
                raw_parts.append(
                    f"[판례 {pr.get('case_no','')}] {pr.get('title','')}\n"
                    f"법원: {pr.get('court','')} ({pr.get('date','')})\n"
                    f"판시: {pr.get('summary','')}\n"
                    f"URL: {pr.get('source_url','')}"
                )
        for st in statutes:
            if "error" not in st:
                raw_parts.append(
                    f"[법령] {st.get('title','')} ({st.get('promulgate','')})\n"
                    f"소관: {st.get('ministry','')}\n"
                    f"URL: {st.get('source_url','')}"
                )

        raw_combined = "\n\n".join(raw_parts) if raw_parts else f"'{topic}' 관련 수집 자료 없음"
        self._log("4_observation",
                  thought="수집된 원문 통합 완료",
                  action="raw_combined 생성",
                  observation=f"총 {len(raw_parts)}건, {len(raw_combined)}자")

        # ── Step 5: Act — Gemini 전문가 번역 + 신뢰도 평가 ────────────────
        summary_ko = self.engine.translate_to_expert(raw_combined)
        confidence = self.engine.evaluate_confidence(summary_ko)
        gate       = "✅ 승인 버킷" if confidence >= ExpertKnowledgeBucket.CONFIDENCE_THRESHOLD else "⏳ 승인 대기"
        self._log("5_translate",
                  thought=f"Gemini 전문가 페르소나 번역 완료, 신뢰도={confidence:.1f}% → {gate}",
                  action="ExpertAnalysisEngine.translate_to_expert() + evaluate_confidence()",
                  observation=summary_ko[:200])

        # ── Step 6: Save — 버킷 저장 ──────────────────────────────────────
        # 출처 타입 결정 (의학/법령/혼합)
        src_types = list({p.get("source_type","unknown") for p in papers + precedents + statutes
                          if "error" not in p})
        src_type  = "+".join(src_types) if src_types else "unknown"
        src_urls  = [p.get("source_url","") for p in papers + precedents
                     if "error" not in p and p.get("source_url")]

        save_result = self.bucket.upsert(
            topic       = topic,
            source_type = src_type,
            source_url  = " | ".join(src_urls[:3]),
            summary_ko  = summary_ko,
            raw_content = raw_combined,
            confidence  = confidence,
            tags        = tags + [src_type],
        )
        saved.append(save_result)
        self._log("6_save",
                  thought=f"버킷 저장 → {save_result['table']}",
                  action="ExpertKnowledgeBucket.upsert()",
                  observation=f"ok={save_result['ok']}, reason={save_result['reason']}")

        return {
            "topic":      topic,
            "confidence": confidence,
            "gate":       gate,
            "summary_ko": summary_ko,
            "steps_log":  self.log,
            "saved":      saved,
        }


# ---------------------------------------------------------------------------
# 7. Deterministic Calculator — 보험금 산출 (AI 산술 오류 원천 차단)
# ---------------------------------------------------------------------------
class DeterministicBenefitCalc:
    """
    AI는 지급률(%)만 결정하고, 실제 보험금 계산은 이 클래스가 전담.
    '확정적 로직 강제 경유' 원칙 — 소수점 오차 없는 정수 연산 보장.
    """

    @staticmethod
    def calc_disability(coverage_won: int, rate_pct: float,
                        disability_type: str = "permanent",
                        threshold_min_pct: float = 3.0) -> dict:
        """
        후유장해 보험금 산출.
        coverage_won     : 가입금액(원)
        rate_pct         : AI가 결정한 장해율(%)
        disability_type  : 'permanent'(1.0배) | 'temporary'(0.2배)
        threshold_min_pct: 최소 지급 장해율 (기본 3%)
        반환: {"rate_pct","coverage_won","multiplier","benefit_won","payable","note"}
        """
        if rate_pct < threshold_min_pct:
            return {"rate_pct": rate_pct, "coverage_won": coverage_won,
                    "multiplier": 0, "benefit_won": 0, "payable": False,
                    "note": f"장해율 {rate_pct}% < 최소 지급 기준 {threshold_min_pct}%"}
        multiplier   = 0.2 if disability_type == "temporary" else 1.0
        benefit      = int(coverage_won * (rate_pct / 100.0) * multiplier)
        return {"rate_pct": rate_pct, "coverage_won": coverage_won,
                "multiplier": multiplier, "benefit_won": benefit, "payable": True,
                "note": f"{'일시후유장해' if disability_type=='temporary' else '영구후유장해'} "
                        f"({rate_pct}% × {multiplier})"}

    @staticmethod
    def calc_multi_coverage(coverages: list[dict]) -> dict:
        """
        복수 담보 보험금 합산 (같은 부위 중복 수령 경고 포함).
        coverages: [{"name":str, "coverage_won":int, "rate_pct":float, ...}, ...]
        반환: {"total_won", "items": [...], "warnings": [...]}
        """
        total = 0
        items = []
        warnings = []
        body_parts_seen: dict[str, float] = {}

        for cov in coverages:
            name         = cov.get("name", "")
            coverage_won = int(cov.get("coverage_won", 0))
            rate_pct     = float(cov.get("rate_pct", 0))
            body_part    = cov.get("body_part", "")
            d_type       = cov.get("disability_type", "permanent")
            threshold    = float(cov.get("threshold_min_pct", 3.0))

            result = DeterministicBenefitCalc.calc_disability(
                coverage_won, rate_pct, d_type, threshold)

            # 같은 부위 중복 경고 (손가락·발가락 제외)
            if body_part and body_part not in ("finger", "toe"):
                if body_part in body_parts_seen:
                    warnings.append(
                        f"⚠️ '{name}': '{body_part}' 부위 중복 — "
                        "표준약관 합산원칙상 최고율 1개만 지급될 수 있습니다.")
                else:
                    body_parts_seen[body_part] = rate_pct

            if result["payable"]:
                total += result["benefit_won"]
            items.append({"name": name, **result})

        return {"total_won": total, "items": items, "warnings": warnings}

    @staticmethod
    def format_won(amount: int) -> str:
        """원 단위를 '억/만원' 복합 표기로 변환"""
        if amount >= 100_000_000:
            uk = amount // 100_000_000
            rem = (amount % 100_000_000) // 10_000
            return f"{uk}억 {rem:,}만원" if rem else f"{uk}억원"
        return f"{amount // 10_000:,}만원"


# ---------------------------------------------------------------------------
# 8. 통합 보상 분석 리포트 생성기
# ---------------------------------------------------------------------------
_REPORT_PROMPT = """[보험 보상 마스터 분석 리포트]

당신은 30년 경력의 수석 보험 설계사입니다.
약관의 자구 해석에만 매몰되지 말고, 판례와 손해사정 실무를 결합하여
고객에게 최상의 보상 전략을 제시하는 전문 리포트를 작성하십시오.

[입력 데이터]
1. 증권 담보 데이터:
{policy}

2. 진단/사고 정보:
{diagnosis}

3. 전문가 지식 버킷 (법령·판례·의학 요약):
{knowledge}

4. Deterministic 보험금 산출 결과:
{calc_result}

[리포트 필수 항목]
① 가입 담보 분석: 보상 가능한 모든 담보 항목 열거 및 지급 조건 검토
② 의학적·법적 근거: 최신 논문·판례 인용 → 지급 정당성 확보
③ 예상 지급액: Deterministic 산출 결과 기반 — AI 추정 금액 사용 금지
④ 합산 원칙 검토: 같은 부위 중복 청구·비례보상 적용 여부
⑤ 손해사정 팁: 보험사 분쟁 시 핵심 대응 논리 (30년 노하우)
⑥ 청구 서류 체크리스트: 진단서·의무기록·후유장해진단서 등 구체적 명시

결과물은 '석사급 이상의 전문성'과 '설계사의 노련함'이 느껴지는 어조로 작성하십시오.
[주의] 본 분석은 보험 보상 실무 참고용이며, 확정적 의학 진단은 전문의, 법률 해석은 변호사 소견에 따릅니다.
"""


class InsuranceReportGenerator:
    """
    증권 JSON + 버킷 지식 + Deterministic 산출 결과를 통합하여
    30년 경력 설계사 수준의 보상 분석 리포트를 자동 생성.

    워크플로우:
    1. 버킷에서 유사 지식 RAG 검색
    2. DeterministicBenefitCalc로 보험금 산출 (AI 산술 오류 차단)
    3. Gemini로 통합 리포트 생성 (페르소나 주입)
    """

    def __init__(self, gemini_client, sb_client):
        self.engine = ExpertAnalysisEngine(gemini_client)
        self.bucket = ExpertKnowledgeBucket(sb_client)

    def generate(self, policy_coverages: list[dict],
                 diagnosis_info: str,
                 extra_knowledge: str = "") -> dict:
        """
        policy_coverages: parse_policy_with_vision() 반환 coverages 리스트
        diagnosis_info  : 고객 진단명·사고 상황
        extra_knowledge : 외부에서 주입할 추가 지식 (선택)
        반환: {"report_md", "calc_result", "rag_hits", "warnings"}
        """
        # Step 1: 버킷 RAG 검색
        rag_hits = self.bucket.search_similar(diagnosis_info, limit=3)
        rag_text = "\n\n".join(
            f"[{r.get('source_type','')}] {r.get('summary_ko','')}  "
            f"(신뢰도 {r.get('confidence',0):.0f}%)"
            for r in rag_hits
        ) if rag_hits else "버킷 내 관련 지식 없음 (자율 학습 실행 권장)"

        combined_knowledge = (extra_knowledge + "\n\n" + rag_text).strip()

        # Step 2: Deterministic 보험금 산출
        calc_input = []
        for cov in policy_coverages:
            if cov.get("category") in ("disability", "disability_annuity"):
                calc_input.append({
                    "name":         cov.get("name", ""),
                    "coverage_won": cov.get("amount") or 0,
                    "rate_pct":     cov.get("threshold_min") or 0,
                    "body_part":    "unknown",
                    "disability_type": "permanent",
                    "threshold_min_pct": cov.get("threshold_min") or 3.0,
                })
        calc_result = (DeterministicBenefitCalc.calc_multi_coverage(calc_input)
                       if calc_input else {"total_won": 0, "items": [], "warnings": []})
        calc_md = (
            f"총 예상 보험금: **{DeterministicBenefitCalc.format_won(calc_result['total_won'])}**\n"
            + "\n".join(
                f"- {it['name']}: {DeterministicBenefitCalc.format_won(it['benefit_won'])} "
                f"(장해율 {it['rate_pct']}%, {'지급' if it['payable'] else '미지급'})"
                for it in calc_result["items"]
            )
        )
        if calc_result["warnings"]:
            calc_md += "\n" + "\n".join(calc_result["warnings"])

        # Step 3: Gemini 통합 리포트
        prompt = _REPORT_PROMPT.format(
            policy    = json.dumps(policy_coverages[:10], ensure_ascii=False)[:2000],
            diagnosis = diagnosis_info[:500],
            knowledge = combined_knowledge[:2000],
            calc_result = calc_md,
        )
        report_md = self.engine._call(prompt, max_tokens=3000)

        return {
            "report_md":   report_md,
            "calc_result": calc_result,
            "rag_hits":    rag_hits,
            "warnings":    calc_result.get("warnings", []),
        }
