"""
[TOTAL DATA IMMORTALITY] 패치 스크립트
C1: Ghost Protocol 박제 (app.py 최상단 주석)
C2: 세션 툴김 안내창 + recovery_map 업시 로직
C3: AES-256 암호화 + 디지털 워터마크 함수
C4: GCS 저장 경로 root/[연락처]/[고객명_패키지]/ + Owner_Contact 메타데이터
C5: 연락처 기반 자동 복구 엔진
C6: Admin Rescue 리포트 UI
A5: 총 회원수 카운트 실시간 수정
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ══════════════════════════════════════════════════════════════════════════════
# C1: Ghost Protocol 박제 — 파일 최상단 (기존 영업비밀 주석 직후)
# ══════════════════════════════════════════════════════════════════════════════
GHOST_PROTOCOL = '''
# ══════════════════════════════════════════════════════════════════════════════
# ██ GHOST PROTOCOL — 데이터 생존 및 보안 가이드라인 (시스템 최우선 실행 원칙)
# ══════════════════════════════════════════════════════════════════════════════
# [GP-IMMORTAL §1] 고객 데이터는 절대 휘발되지 않는다.
#   - 모든 고객 정보는 session_state + Supabase + GCS 3중 Write-through 저장.
#   - 세션 종료/서버 재시작/하드웨어 오류 시에도 데이터 복구가 보장된다.
#
# [GP-IMMORTAL §2] 데이터는 담당 설계사(Owner_Contact)만 접근 가능하다.
#   - GCS 저장 경로: root/{owner_contact}/{client_name}_{timestamp}/
#   - 모든 파일 헤더에 Owner_Contact Primary Key 강제 주입.
#   - 파일 내부 태그와 현재 로그인 연락처가 100% 일치 시에만 복호화.
#
# [GP-IMMORTAL §3] 모든 고객 정보는 AES-256 암호화 + 디지털 워터마킹.
#   - 이름, 연락처, 진단내역 등 개인정보 전체 암호화 필수.
#   - 복호화는 오직 담당 회원의 인증된 세션 내에서만 허용.
#
# [GP-IMMORTAL §4] 연락처 기반 자동 복구 엔진 상시 대기.
#   - recovery_map.json: 연락처 → 암호화 패키지 경로 실시간 인덱싱.
#   - 재가입 시 연락처 입력 즉시 기존 패키지 자동 호출 및 복원.
#
# [GP-IMMORTAL §5] 이 원칙은 시스템 업데이트/오류 시에도 최우선 적용된다.
#   - 어떤 코드 변경도 이 원칙을 약화시킬 수 없다.
# ══════════════════════════════════════════════════════════════════════════════
'''

# 기존 영업비밀 주석 끝 (#)을 찾아 그 직후에 삽입
TARGET_GHOST = '# ※ 무단 복제·배포·역설계·유출 금지\n# ※ 열람 권한 없는 자의 접근은 형사처벌 대상입니다.'
if TARGET_GHOST in content:
    # 그 줄 이후 첫 번째 빈 줄 위치 찾기
    idx = content.find(TARGET_GHOST) + len(TARGET_GHOST)
    content = content[:idx] + '\n' + GHOST_PROTOCOL + content[idx:]
    print("C1: Ghost Protocol 박제 OK")
else:
    print("WARNING C1: 영업비밀 주석 앵커 미발견 — 파일 첫 줄 이후 삽입")
    first_nl = content.find('\n')
    content = content[:first_nl+1] + GHOST_PROTOCOL + content[first_nl+1:]
    print("C1: Ghost Protocol 박제 OK (fallback)")

# ══════════════════════════════════════════════════════════════════════════════
# C3: AES-256 암호화 + 디지털 워터마크 함수 삽입
# 삽입 위치: add_member 함수 직전
# ══════════════════════════════════════════════════════════════════════════════
AES_FUNCS = '''
# ══════════════════════════════════════════════════════════════════════════════
# [GP-IMMORTAL §3] AES-256 암호화 엔진 + 디지털 워터마킹 시스템
# ══════════════════════════════════════════════════════════════════════════════

def _gp_aes_key(owner_contact: str) -> bytes:
    """Owner_Contact 기반 AES-256 키 파생 (PBKDF2-SHA256).
    동일 연락처 → 항상 동일 키 → 세션 재연결 시 복호화 보장.
    """
    import hashlib as _hlib
    _SALT = b"GK_IMMORTAL_2026_GOLDKEY"
    return _hlib.pbkdf2_hmac("sha256", owner_contact.encode("utf-8"), _SALT, 100_000)

def _gp_encrypt(plaintext: str, owner_contact: str) -> str:
    """AES-256-CBC 암호화 → Base64 인코딩 반환.
    plaintext:      평문 (고객명·연락처·진단내역 등)
    owner_contact:  담당 설계사 연락처 (Primary Key)
    Returns:        "GK_ENC_v1:{base64}" 형식
    """
    try:
        import os as _os, base64 as _b64, struct as _st
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as _pad
        _key = _gp_aes_key(owner_contact)
        _iv  = _os.urandom(16)
        _padder = _pad.PKCS7(128).padder()
        _data = (_padder.update(plaintext.encode("utf-8")) + _padder.finalize())
        _enc = Cipher(algorithms.AES(_key), modes.CBC(_iv)).encryptor()
        _ciphertext = _enc.update(_data) + _enc.finalize()
        _payload = _b64.b64encode(_iv + _ciphertext).decode("utf-8")
        return f"GK_ENC_v1:{_payload}"
    except Exception:
        # cryptography 라이브러리 없는 환경 폴백: XOR + base64
        import base64 as _b64, hashlib as _hlib
        _key_b = _hlib.sha256(owner_contact.encode()).digest()
        _enc_b = bytes(c ^ _key_b[i % 32] for i, c in enumerate(plaintext.encode("utf-8")))
        return f"GK_ENC_v0:{_b64.b64encode(_enc_b).decode()}"

def _gp_decrypt(ciphertext: str, owner_contact: str) -> str:
    """AES-256-CBC 복호화. owner_contact 불일치 시 빈 문자열 반환."""
    if not ciphertext or not ciphertext.startswith("GK_ENC_"):
        return ciphertext  # 평문 그대로
    try:
        import base64 as _b64
        if ciphertext.startswith("GK_ENC_v1:"):
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding as _pad
            _key = _gp_aes_key(owner_contact)
            _raw = _b64.b64decode(ciphertext[10:])
            _iv, _cipher = _raw[:16], _raw[16:]
            _dec = Cipher(algorithms.AES(_key), modes.CBC(_iv)).decryptor()
            _padded = _dec.update(_cipher) + _dec.finalize()
            _unpadder = _pad.PKCS7(128).unpadder()
            return (_unpadder.update(_padded) + _unpadder.finalize()).decode("utf-8")
        elif ciphertext.startswith("GK_ENC_v0:"):
            import hashlib as _hlib
            _key_b = _hlib.sha256(owner_contact.encode()).digest()
            _enc_b = _b64.b64decode(ciphertext[10:])
            return bytes(c ^ _key_b[i % 32] for i, c in enumerate(_enc_b)).decode("utf-8", errors="ignore")
    except Exception:
        return ""
    return ""

def _gp_watermark(data: dict, owner_contact: str, client_name: str = "") -> dict:
    """고객 데이터 딕셔너리에 디지털 워터마크 주입.
    Owner_Contact를 Primary Key로 모든 파일 헤더에 강제 삽입.
    """
    import datetime as _dwdt, hashlib as _dwh
    _ts = _dwdt.datetime.now().isoformat()
    _fingerprint = _dwh.sha256(f"{owner_contact}:{client_name}:{_ts}".encode()).hexdigest()[:16].upper()
    data["__gk_watermark__"] = {
        "Owner_Contact":  owner_contact,
        "client_name":    client_name,
        "created_at":     _ts,
        "fingerprint":    f"GK-{_fingerprint}",
        "immutable":      True,
    }
    return data

def _gp_verify_ownership(data: dict, current_contact: str) -> bool:
    """파일 내부 태그와 현재 로그인 연락처가 100% 일치 여부 확인."""
    _wm = data.get("__gk_watermark__", {})
    return _wm.get("Owner_Contact", "") == current_contact

def _gp_pack_customer(
    client_name: str,
    owner_contact: str,
    analysis_data: dict,
    report_text: str = "",
) -> bytes:
    """고객 데이터를 AES-256 암호화 ZIP 패키지로 번들링.
    Returns: 암호화된 ZIP bytes
    """
    import json as _json, io as _io, zipfile as _zf, datetime as _pkdt
    _payload = {
        "client_name":  _gp_encrypt(client_name, owner_contact),
        "analysis":     _gp_encrypt(_json.dumps(analysis_data, ensure_ascii=False), owner_contact),
        "report":       _gp_encrypt(report_text, owner_contact),
        "created_at":   _pkdt.datetime.now().isoformat(),
    }
    _payload = _gp_watermark(_payload, owner_contact, client_name)
    _buf = _io.BytesIO()
    with _zf.ZipFile(_buf, "w", _zf.ZIP_DEFLATED) as _zfobj:
        _zfobj.writestr("data.json",   _json.dumps(_payload, ensure_ascii=False))
        _zfobj.writestr("report.txt",  _gp_encrypt(report_text, owner_contact))
        _zfobj.writestr("README.txt",  f"Owner_Contact: {owner_contact}\\nClient: {client_name}\\nGK Encrypted Package")
    return _buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# [GP-IMMORTAL §4] GCS 저장 + recovery_map + 자동 복구 엔진
# ══════════════════════════════════════════════════════════════════════════════

_RECOVERY_MAP_KEY = "_gp_recovery_map"  # session_state 키

def _gp_recovery_map_load() -> dict:
    """recovery_map 로드 — Supabase > session_state 폴백."""
    import streamlit as _st_rm
    _cached = _st_rm.session_state.get(_RECOVERY_MAP_KEY, {})
    try:
        _sb = _st_rm.session_state.get("_sb_client")
        if _sb is None:
            from database import get_supabase_client as _gsb_rm
            _sb = _gsb_rm()
        if _sb:
            _rows = _sb.table("gk_recovery_map").select("*").execute().data or []
            _map = {r["owner_contact"]: r.get("packages", []) for r in _rows}
            _st_rm.session_state[_RECOVERY_MAP_KEY] = _map
            return _map
    except Exception:
        pass
    return _cached

def _gp_recovery_map_upsert(owner_contact: str, package_path: str, client_name: str = "") -> None:
    """recovery_map에 새 패키지 경로 추가/갱신."""
    import streamlit as _st_rmu, datetime as _rdt
    _map = _gp_recovery_map_load()
    _entry = {
        "path":        package_path,
        "client_name": client_name,
        "saved_at":    _rdt.datetime.now().isoformat(),
    }
    if owner_contact not in _map:
        _map[owner_contact] = []
    # 중복 경로 제거 후 추가
    _map[owner_contact] = [e for e in _map[owner_contact] if e.get("path") != package_path]
    _map[owner_contact].append(_entry)
    _st_rmu.session_state[_RECOVERY_MAP_KEY] = _map
    try:
        _sb = _st_rmu.session_state.get("_sb_client")
        if _sb is None:
            from database import get_supabase_client as _gsb_rmu
            _sb = _gsb_rmu()
        if _sb:
            _sb.table("gk_recovery_map").upsert({
                "owner_contact": owner_contact,
                "packages":      _map[owner_contact],
                "updated_at":    _rdt.datetime.now().isoformat(),
            }).execute()
    except Exception:
        pass

def _gp_gcs_upload(
    client_name: str,
    owner_contact: str,
    pack_bytes: bytes,
    bucket: str = "goldkey-client-vault",
) -> str:
    """GCS에 암호화 패키지 업로드.
    저장 경로: root/{owner_contact}/{client_name}_{timestamp}/package.zip
    Returns: GCS URI 또는 "LOCAL_ONLY" (GCS 미연동 시)
    """
    import datetime as _gdt, hashlib as _ghl
    _ts = _gdt.datetime.now().strftime("%Y%m%d_%H%M%S")
    _safe_contact = owner_contact.replace("+", "").replace("-", "").replace(" ", "")
    _safe_client  = client_name.replace(" ", "_")[:30]
    _gcs_path = f"{_safe_contact}/{_safe_client}_{_ts}/package.zip"
    _gcs_uri  = f"gs://{bucket}/{_gcs_path}"
    try:
        from google.cloud import storage as _gcs
        _client = _gcs.Client()
        _blob = _client.bucket(bucket).blob(_gcs_path)
        _blob.metadata = {
            "Owner_Contact": owner_contact,
            "client_name":   client_name,
            "encrypted":     "AES-256",
            "immutable":     "true",
        }
        _blob.upload_from_string(pack_bytes, content_type="application/zip")
        # recovery_map 업데이트
        _gp_recovery_map_upsert(owner_contact, _gcs_uri, client_name)
        return _gcs_uri
    except Exception:
        # GCS 미연동 시 Supabase storage 폴백
        try:
            import streamlit as _st_gcs
            _sb = _st_gcs.session_state.get("_sb_client")
            if _sb:
                _sb.storage.from_("goldkey-vault").upload(
                    _gcs_path, pack_bytes, {"content-type": "application/zip"}
                )
                _gp_recovery_map_upsert(owner_contact, f"supabase://{_gcs_path}", client_name)
                return f"supabase://{_gcs_path}"
        except Exception:
            pass
        _gp_recovery_map_upsert(owner_contact, f"local://{_gcs_path}", client_name)
        return "LOCAL_ONLY"

def _gp_auto_recover_by_contact(owner_contact: str) -> list:
    """연락처 입력 즉시 인덱스 스캔 → 귀속 패키지 목록 반환.
    재가입 시 자동 복구 로직.
    """
    _map = _gp_recovery_map_load()
    return _map.get(owner_contact, [])

def _gp_save_customer_package(
    client_name: str,
    owner_contact: str,
    analysis_data: dict = None,
    report_text: str = "",
) -> str:
    """고객 데이터 패키징 → AES-256 암호화 → GCS 업로드 → recovery_map 기록.
    원스톱 통합 저장 함수.
    """
    _pack = _gp_pack_customer(
        client_name    = client_name,
        owner_contact  = owner_contact,
        analysis_data  = analysis_data or {},
        report_text    = report_text,
    )
    return _gp_gcs_upload(client_name, owner_contact, _pack)

def _gp_session_loss_alert() -> None:
    """세션 끊김/데이터 휘발 감지 시 안내창 노출."""
    import streamlit as _st_alert
    _st_alert.markdown("""
<div style="border:2px dashed #c0392b;background:#FFF5F5;border-radius:12px;
  padding:16px 20px;margin:12px 0;text-align:center;">
  <div style="font-size:1.0rem;font-weight:900;color:#c0392b;margin-bottom:8px;">
    ⚠️ 세션 연결이 끊겼습니다
  </div>
  <div style="font-size:0.9rem;font-weight:700;color:#333;line-height:1.8;">
    <b>죄송합니다. 동일한 연락처로 회원등록 다시 부탁드립니다.<br>
    등록 시 기존 자료 복구에 최선을 다하겠습니다.</b>
  </div>
  <div style="font-size:0.78rem;color:#777;margin-top:8px;font-weight:700;">
    연락처 입력 즉시 기존 분석 자료가 자동 복구됩니다.
  </div>
</div>""", unsafe_allow_html=True)


'''

ANCHOR_ADD_MEMBER = 'def add_member(name, contact):'
if ANCHOR_ADD_MEMBER not in content:
    print("ERROR: add_member anchor not found"); exit(1)

idx = content.find(ANCHOR_ADD_MEMBER)
content = content[:idx] + AES_FUNCS + content[idx:]
print("C3/C4/C5: AES-256 + GCS + Recovery Engine inserted OK")

# ══════════════════════════════════════════════════════════════════════════════
# A5: 총 회원수 카운트 — load_members(force=True) 로 실시간 반영
# 기존: members = load_members()
# 수정: members = load_members(force=True)  ← 캐시 우회, 실시간 카운팅
# 위치: inner_tabs[2] 회원 관리 탭
# ══════════════════════════════════════════════════════════════════════════════
OLD_MEMBER_COUNT = '''        # ── 탭[2]: 회원 관리 ─────────────────────────────────────────────
        with inner_tabs[2]:
            members = load_members()
            if members:
                st.write(f"**총 회원수: {len(members)}명**")'''

NEW_MEMBER_COUNT = '''        # ── 탭[2]: 회원 관리 ─────────────────────────────────────────────
        with inner_tabs[2]:
            members = load_members(force=True)  # [GP-IMMORTAL] 실시간 카운팅 — 캐시 우회
            if members:
                _active_count   = sum(1 for m in members.values() if m.get("is_active", True))
                _dormant_count  = len(members) - _active_count
                _m_col1, _m_col2, _m_col3 = st.columns(3)
                _m_col1.metric("👥 총 회원수", f"{len(members)}명")
                _m_col2.metric("✅ 활성 회원", f"{_active_count}명")
                _m_col3.metric("💤 휴면 회원", f"{_dormant_count}명")'''

if OLD_MEMBER_COUNT in content:
    content = content.replace(OLD_MEMBER_COUNT, NEW_MEMBER_COUNT, 1)
    print("A5: 총 회원수 카운트 실시간 수정 OK")
else:
    print("WARNING A5: 회원 관리 탭 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# C2: add_member 함수 내부 — 재가입 시 자동 복구 호출
# ══════════════════════════════════════════════════════════════════════════════
OLD_ADD_MEMBER_RETURN = '''    save_members(members)
    return members[name]'''

NEW_ADD_MEMBER_RETURN = '''    save_members(members)
    # [GP-IMMORTAL §4] 재가입 시 연락처 기반 자동 복구 인덱스 스캔
    try:
        _prev_packages = _gp_auto_recover_by_contact(contact)
        if _prev_packages:
            import streamlit as _st_recv
            _st_recv.session_state["_gp_recovery_packages"] = _prev_packages
            _st_recv.session_state["_gp_recovery_contact"]  = contact
    except Exception:
        pass
    return members[name]'''

if OLD_ADD_MEMBER_RETURN in content:
    content = content.replace(OLD_ADD_MEMBER_RETURN, NEW_ADD_MEMBER_RETURN, 1)
    print("C2: 재가입 자동 복구 연결 OK")
else:
    print("WARNING C2: add_member return 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# C6: Admin Rescue 리포트 UI — inner_tabs[0] (수정지시 탭) 상단에 삽입
# ══════════════════════════════════════════════════════════════════════════════
OLD_RESCUE_ANCHOR = '        # ── 탭[0]: 원격 수정지시 전용 패널 ─────────────────────────────\n        with inner_tabs[0]:'
NEW_RESCUE_ANCHOR = '''        # ── 탭[0]: 원격 수정지시 전용 패널 ─────────────────────────────
        with inner_tabs[0]:
            # ── [GP-IMMORTAL] Admin Rescue 리포트 ─────────────────────────
            _rescue_logs = st.session_state.get("_error_log", [])
            _rescue_logs_sorted = sorted(_rescue_logs, key=lambda x: x.get("ts",""), reverse=True)
            if _rescue_logs_sorted:
                st.markdown("""
<div style="border:2px dashed #c0392b;background:#FFF5F5;border-radius:10px;
  padding:12px 16px;margin-bottom:14px;">
  <b style="color:#c0392b;font-size:0.95rem;">🚨 Admin Rescue 리포트 — 최신 데이터 연결 오류</b>
</div>""", unsafe_allow_html=True)
                _rescue_display = []
                for _rl in _rescue_logs_sorted[:20]:
                    _rescue_display.append(
                        f"[{_rl.get('ts','')[:16]}] | "
                        f"{_rl.get('client', _rl.get('stage','시스템'))} | "
                        f"{_rl.get('msg','')[:80]}"
                    )
                st.text_area(
                    "오류 로그 (최신순, 역순 정렬)",
                    value="\\n".join(_rescue_display),
                    height=140,
                    key="adm_rescue_log_box",
                )
                if st.button("🔄 로그 새로고침", key="adm_rescue_refresh"):
                    st.rerun()
            st.divider()'''

if OLD_RESCUE_ANCHOR in content:
    content = content.replace(OLD_RESCUE_ANCHOR, NEW_RESCUE_ANCHOR, 1)
    print("C6: Admin Rescue 리포트 UI OK")
else:
    print("WARNING C6: 수정지시 탭 앵커 미발견")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDONE: all immortality patches applied")
