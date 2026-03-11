# -*- coding: utf-8 -*-
lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
targets = ['def _render_report_send_ui', 'def gp200_brand_footer', 'def _auth_gate', 'def _rag_annotate_report']
for i, ln in enumerate(lines):
    for t in targets:
        if t in ln:
            print(f'L{i+1}: {repr(ln[:100])}')
