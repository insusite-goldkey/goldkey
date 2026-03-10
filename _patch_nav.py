import re

with open('app.py', encoding='utf-8-sig') as f:
    content = f.read()

original = content

# ── NAV-01 래퍼 추가 ──────────────────────────────────────────────────────
old1 = (
    "        with _nav01_r:\n"
    "            if st.button(\"\u2705 \uc815\ubcf4 \uc800\uc7a5 \uc644\ub8cc! 'AI \ubcf4\uc7a5 \ubd84\uc11d' \uc2dc\uc791\ud558\uae30 \u2192\",\n"
    "                         key=\"nav01_next\", use_container_width=True):\n"
    "                st.session_state[\"current_tab\"] = \"t0\"\n"
    "                st.session_state[\"_scroll_top\"] = True\n"
    "                st.rerun()"
)
new1 = (
    "        with _nav01_r:\n"
    "            st.markdown('<div style=\"background:#E3F2FD !important;border-radius:8px;\">', unsafe_allow_html=True)\n"
    "            if st.button(\"\u2705 \uc815\ubcf4 \uc800\uc7a5 \uc644\ub8cc! 'AI \ubcf4\uc7a5 \ubd84\uc11d' \uc2dc\uc791\ud558\uae30 \u2192\",\n"
    "                         key=\"nav01_next\", use_container_width=True):\n"
    "                st.session_state[\"current_tab\"] = \"t0\"\n"
    "                st.session_state[\"_scroll_top\"] = True\n"
    "                st.rerun()\n"
    "            st.markdown('</div>', unsafe_allow_html=True)"
)
if old1 in content:
    content = content.replace(old1, new1, 1)
    print("NAV-01 OK")
else:
    print("NAV-01 NOT FOUND")

# ── NAV-02 래퍼 추가 ──────────────────────────────────────────────────────
old2 = (
    "        with _nav02_r:\n"
    "            if st.button(\"\U0001f50d \ubd84\uc11d \uc644\ub8cc! '\ubcf4\ud5d8\uae08 \uc0c1\ub2f4/\uac80\uc0c9' \uc774\ub3d9\ud558\uae30 \u2192\",\n"
    "                         key=\"nav02_next\", use_container_width=True):\n"
    "                st.session_state[\"current_tab\"] = \"t1\"\n"
    "                st.session_state[\"_scroll_top\"] = True\n"
    "                st.rerun()"
)
new2 = (
    "        with _nav02_r:\n"
    "            st.markdown('<div style=\"background:#E3F2FD !important;border-radius:8px;\">', unsafe_allow_html=True)\n"
    "            if st.button(\"\U0001f50d \ubd84\uc11d \uc644\ub8cc! '\ubcf4\ud5d8\uae08 \uc0c1\ub2f4/\uac80\uc0c9' \uc774\ub3d9\ud558\uae30 \u2192\",\n"
    "                         key=\"nav02_next\", use_container_width=True):\n"
    "                st.session_state[\"current_tab\"] = \"t1\"\n"
    "                st.session_state[\"_scroll_top\"] = True\n"
    "                st.rerun()\n"
    "            st.markdown('</div>', unsafe_allow_html=True)"
)
if old2 in content:
    content = content.replace(old2, new2, 1)
    print("NAV-02 OK")
else:
    print("NAV-02 NOT FOUND")

# ── NAV-07 래퍼 추가 ──────────────────────────────────────────────────────
old7 = (
    "        with _nav07_r:\n"
    "            if st.button(\"\U0001f504 \ucc98\uc74c\uc73c\ub85c \u2014 '\uace0\uac1d \ub9c8\uc2a4\ud130 \ub370\uc774\ud130' \uc7ac\uc785\ub825\ud558\uae30 \u2192\", key=\"nav07_next\", use_container_width=True):\n"
    "                st.session_state[\"_scroll_top\"] = True\n"
    "                st.session_state[\"_home_scroll_to_sec01\"] = True\n"
    "                st.rerun()"
)
new7 = (
    "        with _nav07_r:\n"
    "            st.markdown('<div style=\"background:#E3F2FD !important;border-radius:8px;\">', unsafe_allow_html=True)\n"
    "            if st.button(\"\U0001f504 \ucc98\uc74c\uc73c\ub85c \u2014 '\uace0\uac1d \ub9c8\uc2a4\ud130 \ub370\uc774\ud130' \uc7ac\uc785\ub825\ud558\uae30 \u2192\", key=\"nav07_next\", use_container_width=True):\n"
    "                st.session_state[\"_scroll_top\"] = True\n"
    "                st.session_state[\"_home_scroll_to_sec01\"] = True\n"
    "                st.rerun()\n"
    "            st.markdown('</div>', unsafe_allow_html=True)"
)
if old7 in content:
    content = content.replace(old7, new7, 1)
    print("NAV-07 OK")
else:
    print("NAV-07 NOT FOUND")

if content != original:
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SAVED")
else:
    print("NO CHANGES")
