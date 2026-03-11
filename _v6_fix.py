# -*- coding: utf-8 -*-
"""_PHARMA_ALERT_INFO desc 필드 멀티라인 문자열 오류 수정"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')
print(f"총 줄: {len(lines)}")

# 오류 구간 확인 (10710~10750)
for i in range(10709, 10750):
    if i < len(lines):
        print(f"{i+1}: {repr(lines[i][:80])}")
