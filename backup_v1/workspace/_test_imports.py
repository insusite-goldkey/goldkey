"""각 패키지 import 시간 측정 — hanging 패키지 탐지"""
import time, sys

pkgs = [
    ("streamlit", "import streamlit"),
    ("cryptography", "from cryptography.fernet import Fernet"),
    ("supabase", "from supabase import create_client"),
    ("google.genai", "from google import genai"),
    ("pdfplumber", "import pdfplumber"),
    ("pymupdf", "import pymupdf"),
    ("PIL", "from PIL import Image"),
    ("pandas", "import pandas"),
    ("numpy", "import numpy"),
    ("cv2", "import cv2"),
    ("playwright", "from playwright.sync_api import sync_playwright"),
    ("reportlab", "from reportlab.pdfgen import canvas"),
    ("openpyxl", "import openpyxl"),
    ("docx", "import docx"),
    ("pypdf", "import pypdf"),
    ("rapidfuzz", "import rapidfuzz"),
    ("ftfy", "import ftfy"),
]

for name, stmt in pkgs:
    t = time.time()
    try:
        exec(stmt)
        elapsed = time.time() - t
        flag = "SLOW" if elapsed > 2 else "OK"
        print(f"  [{flag}] {name}: {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - t
        print(f"  [ERR] {name}: {elapsed:.2f}s — {type(e).__name__}: {e}")
    sys.stdout.flush()
