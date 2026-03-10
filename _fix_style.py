src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# </style> 다음 줄에 """ 닫힘이 없음 → 수정
old = '}\n</style>\n        st.markdown'
new = '}\n</style>""", unsafe_allow_html=True)\n\n        st.markdown'

if old in src:
    print('FOUND')
    src2 = src.replace(old, new, 1)
    open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src2)
    print('DONE')
else:
    print('NOT FOUND')
    # 문제 구간 확인
    idx = src.find('</style>\n        st.markdown')
    print(repr(src[idx-20:idx+80]))
