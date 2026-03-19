"""최소 테스트 앱 — HF Space 환경 진단용"""
import streamlit as st
import sys, os, time

st.set_page_config(page_title="진단", page_icon="🔧")
st.title("🔧 HF Space 환경 진단")

st.write(f"Python: `{sys.version}`")
st.write(f"SPACE_ID: `{os.environ.get('SPACE_ID', 'N/A')}`")

pkgs = [
    ("streamlit", "import streamlit as _st; _st.__version__"),
    ("supabase", "from supabase import create_client"),
    ("google.genai", "from google import genai"),
    ("pdfplumber", "import pdfplumber"),
    ("pymupdf", "import pymupdf"),
    ("cryptography", "from cryptography.fernet import Fernet"),
    ("pandas", "import pandas"),
    ("numpy", "import numpy"),
    ("cv2", "import cv2"),
    ("playwright", "from playwright.sync_api import sync_playwright"),
    ("PIL", "from PIL import Image"),
    ("reportlab", "from reportlab.pdfgen import canvas"),
    ("ftfy", "import ftfy"),
    ("rapidfuzz", "import rapidfuzz"),
]

results = []
for name, stmt in pkgs:
    t = time.time()
    try:
        exec(stmt)
        elapsed = time.time() - t
        results.append(("✅", name, f"{elapsed:.2f}s", ""))
    except Exception as e:
        elapsed = time.time() - t
        results.append(("❌", name, f"{elapsed:.2f}s", str(e)[:80]))

for icon, name, elapsed, err in results:
    if err:
        st.error(f"{icon} `{name}` ({elapsed}) — {err}")
    else:
        st.success(f"{icon} `{name}` ({elapsed})")
