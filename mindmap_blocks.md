# Goldkey AI Masters 2026 — app.py 마인드맵 블록화 설계도
> 버전: v1.0 | 작성: 2026-03-15 | 총 라인: 59,712
> 규칙: 디멘드 > 대블록 > 중블록 > 소블록 > 섹터 > 파트

---

## ═══════════════════════════════════════════════
## DEMAND-0 : 앱 부팅 & 전역 설정
## ID: D0 | 위치: line 1~485 | 불변
## ═══════════════════════════════════════════════

### [D0-L1] 대블록: 앱 시동
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D0-L1-M1 | set_page_config + CSS | 1~65 | `st.set_page_config`, `get_base64_image` | #BOOT #CSS |
| D0-L1-M2 | 스플래시 | 67~103 | 5초 스플래시 로직 | #SPLASH #UI |
| D0-L1-M3 | TRADE SECRET + 섹션 목록 | 104~217 | 섹션 구조 선언 | #META |
| D0-L1-M4 | imports + 지연로드 | 218~485 | `get_env_secret`, `initialize_session`, `_lazy_*`, `_load_smart_scanner` | #IMPORT #LAZY |

---

## ═══════════════════════════════════════════════
## DEMAND-1 : 가이딩 프로토콜 & 전문가 자문 엔진
## ID: D1 | 위치: line 486~4878 | SECTION 0 + 제6편
## ═══════════════════════════════════════════════

### [D1-L1] 대블록: 앱 아이덴티티 & 기본 상수
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L1-M1 | SECTION 0 앱 아이덴티티 | 476~690 | `APP_NAME`, `APP_VERSION`, `_bid()` | #IDENTITY #CONST |
| D1-L1-M2 | 게스트 모드 제어 | 691~779 | `_is_guest()`, `_guest_block_modal()` | #AUTH #GUEST |

### [D1-L2] 대블록: ART34 요율 엔진 (중복 정의 주의)
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L2-M1 | ART34 요율 1차 | 780~897 | `_art34_load_rates()`, `_art34_update_rate()`, `_art34_rate_banner_html()`, `_art34_report_footer()` | #ART34 #RATE ⚠️중복 |
| D1-L2-M2 | GP200 브랜딩 | 898~1062 | `gp200_brand_footer()`, `gp200_search_companies()` | #GP200 #BRAND |

### [D1-L3] 대블록: 법인 자동완성 (CORP-AC)
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L3-M1 | CORP-AC 엔진 | 1063~1280 | `_corp_search()`, `_corp_search_rag()`, `render_corp_autocomplete()` | #CORP #AUTOCOMPLETE |

### [D1-L4] 대블록: HIRA-KCD + LAW-API + GP-JOB 엔진
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L4-M1 | HIRA-KCD 질병 검색 | 1281~1557 | `_hira_get_key()`, `_hira_disease_search()`, `_kcd_get_coverage()`, `render_kcd_autocomplete()` | #HIRA #KCD #DISEASE |
| D1-L4-M2 | LAW-API 법령 검색 | 1558~1918 | `_law_get_oc()`, `_law_search()`, `_law_get_linked()`, `render_law_search()` | #LAW #API |
| D1-L4-M3 | GP-JOB 직업 탐색 | 1919~2270 | `_job_search()`, `render_job_navigator()` | #JOB #NAVIGATOR |

### [D1-L5] 대블록: 계산 엔진 (ART32/35/62/63)
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L5-M1 | ART35 치매 계산 | 2271~2336 | `_art35_calc_report()` | #ART35 #DEMENTIA |
| D1-L5-M2 | ART32 보험료 계산 | 2337~2396 | `_art32_calc()`, `_art32_briefing()` | #ART32 #PREMIUM |
| D1-L5-M3 | ART62/63 취약성 계산 | 2397~2577 | `_art62_calc()`, `_art63_vulnerable()` | #ART62 #GAP |

### [D1-L6] 대블록: GP64 마스터 설정 + S39 세션 캐시
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L6-M1 | GP64 마스터 설정 | 2578~2685 | `_gp64_load()`, `_gp64_save()` | #GP64 #CONFIG |
| D1-L6-M2 | S39 세션 캐시 + 스켈레톤 | 2686~3014 | `_s39_save_session_cache()`, `_s39_sidebar_skeleton()`, `_s39_render_landing_page()` | #S39 #SESSION #CACHE |
| D1-L6-M3 | GP140 LocalStorage 토큰 | 3015~3285 | `_gp140_save_token_js()`, `_gp140_restore_from_ls()` | #GP140 #TOKEN #LS |

### [D1-L7] 대블록: ART44 OTA + S40 성능 모니터
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L7-M1 | GP-라벨 + GP-44 OTA 동기화 | 3286~3475 | `gp_label()`, `_art44_ota_sync()`, `_art44_apply_rules()`, `_art44_get_flag()` | #GP44 #OTA #RULES |
| D1-L7-M2 | ART43 보장 지수 | 3476~4087 | `_art43_calc_security_index()`, `_art43_build_report_html()`, `_art43_render_tab()` | #ART43 #SECURITY |
| D1-L7-M3 | S40 성능 모니터 + LS 캐시 | 4088~4239 | `_s40_record_blocking()`, `_s40_perf_watchdog_js()`, `_s40_night_report()` | #S40 #PERF #MONITOR |

### [D1-L8] 대블록: ART38 야간 워커 + AI 캐시
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D1-L8-M1 | ART38 AI 캐시 + 야간워커 | 4240~4737 | `_art38_extract_keywords()`, `_art38_cache_get()`, `_art38_cache_put()`, `_art38_night_worker()` | #ART38 #AI #CACHE #NIGHT |
| D1-L8-M2 | ART34 요율 엔진 2차 ⚠️중복 | 4738~4878 | `_art34_load_rates()`, `_art34_update_rate()` | #ART34 #RATE ⚠️중복 |

---

## ═══════════════════════════════════════════════
## DEMAND-2 : 인프라 엔진 (보안 + DB + 인증)
## ID: D2 | 위치: line 4879~8957 | SECTION 1~2
## ═══════════════════════════════════════════════

### [D2-L1] 대블록: SECTION 1 — 보안 & 암호화
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D2-L1-M1 | 암호화 엔진 | 4879~5016 | `get_encryption_key()`, `encrypt_val()`, `decrypt_val()`, `encrypt_contact()` | #ENCRYPT #SECURITY |
| D2-L1-M2 | CRM 초기화 + 보험 계산 | 5017~5279 | `_crm_init()`, `calculate_insurance_gap()`, `kcd_lookup()` | #CRM #CALC |
| D2-L1-M3 | CRM CRUD | 5280~5501 | `crm_set_profile()`, `crm_search()`, `crm_save_to_db()`, `crm_load_from_db()` | #CRM #DB |
| D2-L1-M4 | 관리자 키 + 프롬프트 정제 | 5486~5521 | `sanitize_prompt()`, `get_admin_key()`, `_check_admin_key()` | #ADMIN #SECURITY |

### [D2-L2] 대블록: SECTION 1.8 — 로그인 방어
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D2-L2-M1 | Brute-force 방어 | 5522~5579 | `_get_login_fail_store()`, `_LoginGuard` | #LOGIN #GUARD #BRUTEFORCE |

### [D2-L3] 대블록: SECTION 1.5/1.6 — 비상장주식 + CEO플랜
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D2-L3-M1 | 비상장주식 평가 엔진 | 5580~5637 | 상증법+법인세법 계산 상수 | #STOCK #TAX |
| D2-L3-M2 | CEO플랜 AI 프롬프트 | 5638~5674 | CEO플랜 프롬프트 상수 | #CEO #PROMPT |

### [D2-L4] 대블록: SECTION 2 — DB & 회원 관리
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D2-L4-M1 | SQLite DB + 회원 CRUD | 5675~5813 | `setup_database()`, `load_members()`, `save_members()` | #DB #MEMBER |
| D2-L4-M2 | GP75 기기 지문 관리 | 5814~6046 | `_gp75_save_device()`, `_gp75_check_device()` | #GP75 #DEVICE #FINGERPRINT |
| D2-L4-M3 | GP512 접속 제한 | 5941~6051 | `_gp512_check_and_record()` | #GP512 #RATELIMIT |
| D2-L4-M4 | GP84 전역 CSS + GP86 세션 종료 | 6052~6951 | `_gp84_inject_global_css()`, `_gp86_terminate_session()`, `_gp82_render_nav_bar()` | #GP84 #CSS #NAV |
| D2-L4-M5 | GP81 용어 해설 엔진 | 6952~7319 | `_gp81_annotate()`, `_gp81_detect_domain()`, `_gp81_build_answer()` | #GP81 #GLOSSARY |
| D2-L4-M6 | PIN 인증 + 마스터 회원 | 7316~7642 | `_pin_make_hash()`, `save_member_pin()`, `ensure_master_members()` | #PIN #AUTH |
| D2-L4-M7 | GP 암호화 패키지 + GCS 백업 | 7393~7701 | `_gp_aes_key()`, `_gp_encrypt()`, `_gp_pack_customer()`, `_gp_gcs_upload()` | #GP #AES #GCS #BACKUP |

### [D2-L5] 대블록: SECTION 2-B — 동시접속 + 구독 검증
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D2-L5-M1 | 동시접속 세션 관리 | 7702~7790 | `_session_checkin()`, `_session_checkout()`, `MAX_CONCURRENT` | #SESSION #CONCURRENT #GP49 |
| D2-L5-M2 | 에러 로그 | 7791~7843 | `log_error()`, `load_error_log()` | #ERROR #LOG |
| D2-L5-M3 | Hybrid API + Supabase + GCS 클라이언트 | 7844~8268 | `hybrid_login()`, `_get_sb_client()`, `_gcs_cache_get()` | #HYBRID #SB #GCS |
| D2-L5-M4 | 고객 문서 관리 | 8269~8393 | `customer_doc_save()`, `customer_doc_list()` | #DOC #CUSTOMER |
| D2-L5-M5 | GP51 설계사 프로필 | 8394~8504 | `save_agent_profile()`, `load_agent_profile()` | #GP51 #AGENT #PROFILE |
| D2-L5-M6 | 홈 노트/보험 저장 | 8505~8699 | `save_home_note()`, `save_home_ins()` | #HOME #NOTE |
| D2-L5-M7 | 지시사항 + 사용량 관리 | 8700~8957 | `load_directives()`, `check_usage_count()`, `check_membership_status()` | #USAGE #DIRECTIVE |

---

## ═══════════════════════════════════════════════
## DEMAND-3 : 중앙 사령부 (라우팅 + 비즈니스 로직)
## ID: D3 | 위치: line 8958~28647 | SECTION 3
## ═══════════════════════════════════════════════

### [D3-L1] 대블록: 라우팅 코어 (중앙 사령부)
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L1-M1 | AI 클라이언트 + SECTOR_CODES | 8958~9251 | `get_client()`, `SECTOR_CODES`, `SUB_CODES` | #ROUTING #SECTOR #AI_CLIENT |
| D3-L1-M2 | APP_REGISTRY + 은닉 라우팅 | 9252~9344 | `_build_app_registry()`, `_gk_route()`, `_gk_track()` | #APP_REGISTRY #ROUTE #SECURITY |
| D3-L1-M3 | EID 엔티티 ID + 행동 추적 v2 | 9345~9577 | `_eid_issue()`, `_gk_track_v2()`, `calculate_top_targets()` | #EID #TRACKING |

### [D3-L2] 대블록: GP92/101/102/103 — 심리/전략 엔진
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L2-M1 | GP92 피보험자 후킹 | 9578~9641 | `mask_name_gp92()` | #GP92 #HOOK |
| D3-L2-M2 | GP101 심리지능 + 전략 대화 | 9642~9874 | `get_gp101_persona()`, `generate_gp101_hook()`, `render_gp101_hook_card()` | #GP101 #PERSONA #HOOK |
| D3-L2-M3 | GP102 소득역산 안보공백 | 9875~10008 | `_gp102_calc()`, `render_gp102_gap_card()` | #GP102 #GAP #INCOME |
| D3-L2-M4 | GP103 GCS 지식 그라운딩 | 10009~10206 | `_gp103_detect_domain()`, `_gp103_grounding_query()`, `_gp103_build_script()` | #GP103 #GCS #RAG |

### [D3-L3] 대블록: 개인 보장 분석 (Life Gap)
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L3-M1 | RAG 섹터별 지능형 검색 | 10259~10429 | `_loss_ins_get_key()`, RAG 자가호출 | #RAG #SECTOR |
| D3-L3-M2 | Life Gap 보장 분석 | 10399~10634 | `_life_gap_assess()`, `render_life_gap_panel()` | #LIFEGAP #COVERAGE |
| D3-L3-M3 | FSS 금융상품 패널 | 10525~11138 | `_fss_search_products()`, `render_fss_product_panel()` | #FSS #PRODUCT |
| D3-L3-M4 | KOSIS 통계 대시보드 | 11139~11509 | `_kosis_fetch_cancer_rate()`, `render_kosis_dashboard()` | #KOSIS #STATS |
| D3-L3-M5 | 데이터 요새 + 혈관차트 | 11510~11930 | `fortress_auto_refresh()`, `render_vascular_chart()`, `render_life_stat_dashboard()` | #FORTRESS #STATS |
| D3-L3-M6 | 상담 리포트 + KB 스코어 | 11931~12383 | `render_consulting_report()`, `render_kb_score_donut()`, `render_kb_standard_dashboard()` | #REPORT #KB #SCORE |

### [D3-L4] 대블록: WAR ROOM (실전 상담 전략실)
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L4-M1 | 특수작전 5단계 전략 | 12384~12991 | `render_special_ops_sector()` | #SPECIAL_OPS #STRATEGY |
| D3-L4-M2 | 회원 프로필 설정 | 12992~13043 | `render_member_profile_settings()` | #PROFILE #MEMBER |
| D3-L4-M3 | WAR ROOM 허브 | 17039~17469 | `show_war_room()`, `render_gp92_report()` | #WAR_ROOM #HUB |

### [D3-L5] 대블록: 질환 상담 (암/뇌/심장)
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L5-M1 | 항암 정밀 엔진 | 13044~13336 | `render_oncology_chemo_panel()` | #ONCOLOGY #CANCER #CHEMO |
| D3-L5-M2 | 제약 패널 | 13337~13553 | `render_pharma_panel()` | #PHARMA |
| D3-L5-M3 | 손해보험 분석 | 13554~13863 | `_loss_gap_analysis()`, `render_loss_insurance_panel()` | #LOSS #INSURANCE |

### [D3-L6] 대블록: 보험 전문 섹터 렌더러
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L6-M1 | GK-RISK 위험도 분석 | 13864~14242 | `_render_gk_risk()` | #RISK #GK |
| D3-L6-M2 | GK-JOB 직업 진단 | 14243~14270 | `_render_gk_job()` | #JOB #GK |
| D3-L6-M3 | SEC10 내보험다보여 | 14271~15126 | `_render_gk_sec10()`, `_sec10_fetch_mydata()` | #SEC10 #MY_INS |
| D3-L6-M4 | SEC09 VVIP CEO | 15127~15807 | `_render_gk_sec09()` | #SEC09 #CEO #VVIP |
| D3-L6-M5 | SEC08 화재/특종보험 | 15808~16508 | `_render_gk_sec08()`, `_rag_sector_query()` | #SEC08 #FIRE |
| D3-L6-M6 | SEC07 자동차보험 | 16509~17038 | `_render_gk_sec07()` | #SEC07 #AUTO |

### [D3-L7] 대블록: 통신 & 음성 & AI 허브
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L7-M1 | 카카오톡 + 음성 내비 | 17470~17590 | `_generate_kakao_draft()`, `_voice_navigate()` | #KAKAO #VOICE |
| D3-L7-M2 | 에러 로그 + STT 엔진 | 17591~17909 | `log_error()`, `stt_correct()`, `stt_llm_correct()`, `s_voice()` | #ERROR #STT #VOICE |
| D3-L7-M3 | GP88 통합 상담 허브 **구버전** ⚠️dead code | 17910~18300 | `_gp88_hub() -> dict` (4탭, 토글버튼형) | #GP88 #HUB ⚠️중복/삭제대상 |

### [D3-L8] 대블록: GP94~GP97 암/첨단치료/리플렛
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L8-M1 | GP94 손해보험 암 화법 | 18301~18854 | `_gp94_panel()` | #GP94 #CANCER #SPEECH |
| D3-L8-M2 | GP95 첨단암치료 보장 | 18855~19201 | `_gp95_panel()`, `_gp95_compare_companies()` | #GP95 #CANCER #COVERAGE |
| D3-L8-M3 | GP96 리플렛 RAG/GCS | 19202~19803 | `_gp96_upload_leaflet()`, `_gp96_rag_search()`, `_gp96_panel()` | #GP96 #RAG #GCS #LEAFLET |
| D3-L8-M4 | GP97 미래 상품 자율학습 | 19584~19937 | `_gp97_analyze_diff()`, `_gp97_panel()` | #GP97 #AI #LEARNING |

### [D3-L9] 대블록: GP100/110/120 — 인생 방어 사령부
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L9-M1 | GP100 의무기록 분석 | 20081~20513 | `_gp100_scan_document()`, `_gp100_panel()` | #GP100 #MEDICAL_RECORD |
| D3-L9-M2 | GP110 판례 시뮬레이션 | 20514~20670 | `_gp110_search_cases()`, `_gp110_panel()` | #GP110 #CASE #PAYOUT |
| D3-L9-M3 | GP120 데이터 보안 파쇄 | 20671~20866 | `_gp120_encrypt_aes256()`, `_gp120_panel()` | #GP120 #AES #SECURITY |
| D3-L9-M4 | 인생 방어 사령부 허브 | 20867~21115 | `_life_defense_command_panel()` | #LIFE_DEF #HUB |
| D3-L9-M5 | GP131/132/135 치매/미래플랜 | 21042~21773 | `_gp131_calc_gap_fv()`, `_gp135_dementia_panel()` | #GP131 #DEMENTIA #PLAN |

### [D3-L10] 대블록: GP86/89/90/91/93 — 체험/동기화/생애주기
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L10-M1 | GP86 황금카드 + GP93 음성 육성 | 21443~22196 | `_gp86_golden_card()`, `_gp93_voice_recorder()` | #GP86 #GP93 #VOICE #GOLDEN |
| D3-L10-M2 | GP87 카카오 공유 | 22197~22364 | `_gp87_kakao_share()` | #GP87 #KAKAO #SHARE |
| D3-L10-M3 | GP89 유기체 파이프라인 | 22365~22708 | `_mch_init()`, `_gp89_set_customer()`, `_gp89_flow_banner()` | #GP89 #PIPELINE #FLOW |
| D3-L10-M4 | GP90/91 생애주기 동기화 | 22709~23530 | `_gp90_sync()`, `_gp91_trigger()`, `_gp91_report_panel()` | #GP90 #GP91 #LIFECYCLE |
| D3-L10-M5 | GP88 통합 허브 (2차 정의) | 23531~23992 | `_gp88_hub()`, `_gp88_master_scripts()`, `_gp88_kakao_send()` | #GP88 #HUB ⚠️중복 |

### [D3-L11] 대블록: AI 쿼리 엔진 + 증권 분석
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D3-L11-M1 | PDF/DOCX 파싱 + GP91 의무기록 | 23993~24948 | `extract_pdf_chunks()`, `parse_policy_with_vision()`, `parse_medical_record_with_vision()` | #PDF #OCR #MEDICAL |
| D3-L11-M2 | 보안 사이드바 + 섹션8 브랜드 | 24949~25193 | `display_security_sidebar()`, `get_goldkey_avatar()`, `render_goldkey_sidebar()` | #SIDEBAR #BRAND #AVATAR |

---

## ═══════════════════════════════════════════════
## DEMAND-4 : AI 프롬프트 & RAG 시스템
## ID: D4 | 위치: line 25194~28647 | SECTION 4~7
## ═══════════════════════════════════════════════

### [D4-L1] 대블록: SECTION 4 — AI 시스템 프롬프트
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D4-L1-M1 | 시스템 프롬프트 상수 | 25194~25782 | `GP_SYSTEM_PROMPT`, `_get_strict_config()` | #PROMPT #AI #SYSTEM |
| D4-L1-M2 | GP85 1인칭 화법 (라우팅 후 정의) | 34227~35128 | 1인칭 화법 원칙 | #GP85 #SPEECH |

### [D4-L2] 대블록: SECTION 4-B — 금감원 finlife API
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D4-L2-M1 | finlife API + 전문가 패널 | 25783~26126 | `finlife_get_deposit()`, `render_expert_panel()`, `_render_finlife_dashboard()` | #FSS #FINLIFE #API |

### [D4-L3] 대블록: SECTION 5 — RAG SQLite 시스템
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D4-L3-M1 | RAG DB CRUD | 26127~26844 | `_rag_db_init()`, `_rag_db_add_document()`, `_rag_self_diagnose()` | #RAG #SQLITE #DB |
| D4-L3-M2 | RAG 동기화 + 검색 엔진 | 26845~27024 | `_get_rag_store()`, `_rag_sync_from_db()` | #RAG #SYNC |

### [D4-L4] 대블록: SECTION 5.5 — 공장화재보험
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D4-L4-M1 | 공장화재 계산 + UI | 27025~27703 | `_calc_factory_fire()`, `_section_factory_fire_ui()` | #FIRE #FACTORY #CALC |
| D4-L4-M2 | AI 쿼리 블록 | 27704~28360 | `ai_query_block()` | #AI #QUERY #BLOCK |

### [D4-L5] 대블록: SECTION 6~7 — 상속/증여 + 주택연금
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D4-L5-M1 | 상속/증여 정밀 로직 | 28361~28616 | `_calc_inheritance_tax()`, `section_inheritance_will()` | #INHERITANCE #TAX |
| D4-L5-M2 | 주택연금 시뮬레이션 | 28617~28647 | `section_housing_pension()` | #PENSION #HOUSING |

---

## ═══════════════════════════════════════════════
## DEMAND-5 : 메인 UI & 탭 라우터 (main() 함수)
## ID: D5 | 위치: line 28648~59471 | SECTION 8
## ═══════════════════════════════════════════════

### [D5-L1] 대블록: 인증 & 사이드바 진입부
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D5-L1-M1 | SSO 토큰 수신 + 세션복원 | 28648~28697 | SSO 핸드오프, `_saved_user_id` 복원 | #SSO #AUTH #SESSION |
| D5-L1-M2 | ★미인증 차단 블록 | 28698~28903 | `if not _is_auth_now:` 메인 로그인폼 + `st.stop()` | #AUTH #STOP ⚠️핵심 |
| D5-L1-M3 | ★사이드바 렌더 (공통) | 28908~30713 | `with st.sidebar:` 아바타+로그인폼+GP200 | #SIDEBAR #LOGIN #RENDER |

### [D5-L2] 대블록: 전역 CSS/JS + 초기화
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D5-L2-M1 | 로딩 UI 한국어화 CSS | 30714~30817 | Running... 숨김 CSS | #CSS #UI |
| D5-L2-M2 | 반응형 CSS + 디바이스 감지 | 30818~31344 | `_gp_responsive_css`, 기기UUID, DB초기화 | #CSS #DEVICE #INIT |
| D5-L2-M3 | 세션 복원 + OTA + RAG sync | 31345~31759 | QP 토큰복원, OTA sync, RAG sync | #SESSION #OTA #RAG |
| D5-L2-M4 | 사이드바 CSS 주입 + JS 훅 | 31760~32080 | `_sidebar_css_injected`, 사이드바 토글 JS | #SIDEBAR #CSS #JS |
| D5-L2-M5 | 자동 닫기/인증실패 처리 | 32082~32184 | `_auto_close_sidebar`, `_s39_auth_failed` | #SIDEBAR #AUTH |

### [D5-L3] 대블록: 전역 디자인 시스템 + JS 엔진
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D5-L3-M1 | Glassmorphism CSS v2 | 32195~33472 | Global Design System | #CSS #DESIGN |
| D5-L3-M2 | UX JS 엔진 (Dynamic Theme 등) | 33475~33747 | Dynamic Theme, Lottie, Count-up, Haptic | #JS #UX #ANIMATION |
| D5-L3-M3 | 보험용어 툴팁 JS | 33753~33939 | 툴팁 전역 스타일 + 데이터 | #TOOLTIP #JS |

### [D5-L4] 대블록: ★인증 후 차단 + 관리자 + 동시접속
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D5-L4-M1 | ★2차 미인증 차단 | 33944~33945 | `if not _is_auth_now: st.stop()` | #AUTH #STOP ⚠️중복차단 |
| D5-L4-M2 | 관리자 지시목록 + 성능리포트 | 33946~34080 | `load_directives()`, 야간성능리포트 | #ADMIN #DIRECTIVE |
| D5-L4-M3 | 동시접속 체크인 | 34081~34092 | `_session_checkin()` | #SESSION #GP49 |

### [D5-L5] 대블록: 랜딩 + 탭 라우터 코어
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D5-L5-M1 | ★비로그인 스플래시 차단 | 34093~34188 | `if not _is_logged_in: st.stop()` | #AUTH #STOP ⚠️3번째 차단 |
| D5-L5-M2 | 탭 라우터 초기화 | 34189~34589 | `current_tab`, `_go_tab()`, `show_home_portal()`, `show_claim_scanner()` | #TAB #ROUTER #INIT |

### [D5-L6] 대블록: 탭 라우터 실행부
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D5-L6-M1 | 홈 포털 라우터 | 35129~36460 | `show_home_portal()` 내부 | #HOME #PORTAL |
| D5-L6-M2 | 탭별 라우터 분기 (home/scan/war) | 36461~39380 | `cur=="home"`, `cur=="war_room"`, `cur=="gk_sec0X"` | #TAB #ROUTE |
| D5-L6-M3 | 섹터 라우터 (암/뇌/화재/자동차/증권) | 39381~57710 | SECTOR-CANCER, SECTOR-STROKE, SECTOR-FIRE, SECTOR-AUTO, SECTOR-SECURITIES | #SECTOR #ANALYSIS |
| D5-L6-M4 | 관리자 탭 | 52779~58825 | RAG 인덱스 관리, 회원관리, GP-ADMIN | #ADMIN #RAG #MEMBER |

---

## ═══════════════════════════════════════════════
## DEMAND-6 : 자가복구 + 진입점
## ID: D6 | 위치: line 58826~59712 | SECTION 9
## ═══════════════════════════════════════════════

### [D6-L1] 대블록: SECTION 9-A — 에러 레지스트리 + 자가진단
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D6-L1-M1 | 에러 레지스트리 + 헬스체크 | 58826~59470 | `_run_self_diagnosis()`, `_hc_take_baseline()` | #ERROR #HEALTH #DIAG |

### [D6-L2] 대블록: SECTION 9 — 자가복구 + 진입점
| ID | 중블록 | 위치 | 함수/상수 | 태그 |
|----|--------|------|-----------|------|
| D6-L2-M1 | auto_recover + _run_safe | 59471~59710 | `auto_recover()`, `_run_safe()` | #RECOVER #ENTRY |
| D6-L2-M2 | ★앱 진입점 | 59710~59712 | `_run_safe()` 호출 | #ENTRY #BOOT |

---

## ★★★ 긴급 이슈 목록 (블록화 분석 결과) ★★★

| 우선순위 | ID | 이슈 | 위치 | 영향 |
|---------|-----|------|------|------|
| 🔴 P1 | D5-L4-M1 | `if not _is_auth_now: st.stop()` 2번째 중복 | line 33944 | 미인증 차단 중복 (무해) |
| 🔴 P1 | D5-L5-M1 | `if not _is_logged_in: st.stop()` 3번째 차단 | line 34093~34188 | **로그인 후에도 차단 가능** |
| 🟠 P2 | D1-L2-M1 / D1-L8-M2 | `_art34_load_rates()` / `_art34_update_rate()` 중복 정의 | 780~897 & 4738~4878 | 런타임 덮어쓰기 |
| 🟠 P2 | D3-L7-M3 / D3-L10-M5 | `_gp88_hub()` 중복 정의 | 17910 & 23533 | 런타임 덮어쓰기 |
| 🟡 P3 | D3-L11-M2 | `display_security_sidebar()` 위치 | 24972 | SECTION 3 안에 있어 SECTION 8 이전 정의됨 |
| 🟡 P3 | D4-L1-M2 | `GP85 1인칭 화법` main() 내부 정의 | 34227 | 함수 밖 상수가 main() 안에 있음 |

---

## ★★★ 메인 앱 미노출 원인 추적 경로 ★★★

```
D5-L1-M1: SSO/세션 복원 (28648~28697)
  ↓ 인증 확인
D5-L1-M2: if not _is_auth_now: → st.stop() (28698~28903)  ← 미인증 차단
  ↓ 인증 완료 시 건너뜀
D5-L1-M3: with st.sidebar: 렌더 (28908~30713)
  ↓
[중간 수천 줄 CSS/JS/초기화]
  ↓
D5-L4-M1: if not _is_auth_now: → st.stop() (33944) ← 2번째 중복 (무해)
  ↓
D5-L4-M3: _session_checkin() 실패 → st.stop() (34082~34085) ← ⚠️실패 시 차단
  ↓
D5-L5-M1: if not _is_logged_in: → st.stop() (34093~34188) ← ⚠️3번째 차단
           _is_logged_in = bool(st.session_state.get("user_id"))
           → user_id가 세션에 없으면 차단!
  ↓
D5-L5-M2: 탭 라우터 → 메인 앱 ← 여기까지 와야 함
```

**핵심 용의자**: `D5-L5-M1` — `_is_logged_in = bool(st.session_state.get("user_id"))` 로그인 후 `user_id`가 세션에 없으면 차단
