with open('app.py', encoding='utf-8') as f:
    content = f.read()

OLD = '                        # [GP-56] 로그인 전환 스켈레톤 — 화이트아웃 0ms 목표'

NEW = '''                        # ── [GP-SSO §1] 로그인 완료 후 CRM 딥링크 SSO 처리 ──────────────
                        try:
                            _sso_return_to = st.query_params.get("return_to", "")
                            if _sso_return_to and _sso_return_to.startswith("goldkeycrmapp://"):
                                import urllib.parse as _up_sso
                                _sso_uid   = m.get("user_id", "")
                                _sso_name  = ln
                                _sso_token = st.session_state.get("_auto_login_token", "")
                                _sso_params = _up_sso.urlencode({
                                    "token":   _sso_token,
                                    "user_id": _sso_uid,
                                    "name":    _sso_name,
                                    "role":    "agent" if _adm else "customer",
                                })
                                _sso_deeplink = _sso_return_to + "?" + _sso_params
                                st.markdown(
                                    "<script>(function(){try{window.location.href='"
                                    + _sso_deeplink.replace("'", "\\'")
                                    + "';}catch(e){}})()</script>",
                                    unsafe_allow_html=True
                                )
                                st.query_params.clear()
                        except Exception:
                            pass
                        # [GP-56] 로그인 전환 스켈레톤 — 화이트아웃 0ms 목표'''

assert OLD in content, "OLD 문자열을 찾을 수 없습니다"
content = content.replace(OLD, NEW, 1)
print("모 앱 SSO 삽입 완료")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("SAVED OK")
