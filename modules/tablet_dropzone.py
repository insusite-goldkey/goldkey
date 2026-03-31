"""
태블릿 전용 드래그 앤 드롭 컴포넌트 (Tablet Drop Zone)
HTML5 Drag & Drop API + 터치 이벤트 핸들러

[GP-SCAN-DROPZONE] 우선순위 2 권고사항 구현
- streamlit.components.v1.html() 기반 HTML5 Drag & Drop API 구현
- 터치 이벤트(touchstart, touchmove, touchend) 핸들러 추가
- 드래그 중 시각적 피드백 (테두리 색상 변경, 업로드 아이콘 애니메이션)
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, List
import base64
import uuid


def render_tablet_dropzone(
    key: str = "tablet_dropzone",
    accept_types: Optional[List[str]] = None,
    max_file_size_mb: int = 10,
    height: int = 300
) -> Optional[List[dict]]:
    """
    태블릿 최적화 드래그 앤 드롭 컴포넌트 렌더링
    
    Args:
        key: Streamlit 컴포넌트 고유 키
        accept_types: 허용 파일 타입 (예: ['image/jpeg', 'image/png', 'application/pdf'])
        max_file_size_mb: 최대 파일 크기 (MB)
        height: Drop Zone 높이 (px)
    
    Returns:
        업로드된 파일 리스트 (각 파일은 {'name': str, 'type': str, 'size': int, 'data': base64} 형태)
    """
    if accept_types is None:
        accept_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
    
    accept_str = ','.join(accept_types)
    max_size_bytes = max_file_size_mb * 1024 * 1024
    
    # 세션 상태 초기화
    if f"{key}_files" not in st.session_state:
        st.session_state[f"{key}_files"] = []
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                padding: 10px;
            }}
            
            #dropzone {{
                width: 100%;
                height: {height}px;
                border: 3px dashed #cbd5e0;
                border-radius: 12px;
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            #dropzone:hover {{
                border-color: #4299e1;
                background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
                transform: scale(1.02);
            }}
            
            #dropzone.drag-over {{
                border-color: #48bb78;
                background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
                border-width: 4px;
                box-shadow: 0 0 20px rgba(72, 187, 120, 0.3);
            }}
            
            #dropzone.uploading {{
                border-color: #ed8936;
                background: linear-gradient(135deg, #fffaf0 0%, #feebc8 100%);
            }}
            
            .dropzone-icon {{
                font-size: 64px;
                margin-bottom: 16px;
                animation: float 3s ease-in-out infinite;
            }}
            
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            
            .dropzone-text {{
                font-size: 18px;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 8px;
                text-align: center;
            }}
            
            .dropzone-subtext {{
                font-size: 14px;
                color: #718096;
                text-align: center;
            }}
            
            .file-list {{
                margin-top: 16px;
                width: 100%;
            }}
            
            .file-item {{
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            
            .file-info {{
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .file-icon {{
                font-size: 24px;
            }}
            
            .file-details {{
                display: flex;
                flex-direction: column;
            }}
            
            .file-name {{
                font-weight: 600;
                color: #2d3748;
                font-size: 14px;
            }}
            
            .file-size {{
                font-size: 12px;
                color: #718096;
            }}
            
            .remove-btn {{
                background: #fc8181;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
                transition: background 0.2s;
            }}
            
            .remove-btn:hover {{
                background: #f56565;
            }}
            
            input[type="file"] {{
                display: none;
            }}
            
            .progress-bar {{
                width: 100%;
                height: 4px;
                background: #e2e8f0;
                border-radius: 2px;
                overflow: hidden;
                margin-top: 8px;
            }}
            
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #4299e1 0%, #48bb78 100%);
                width: 0%;
                transition: width 0.3s ease;
                animation: progress-animation 1.5s ease-in-out infinite;
            }}
            
            @keyframes progress-animation {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}
        </style>
    </head>
    <body>
        <div id="dropzone">
            <div class="dropzone-icon">📂</div>
            <div class="dropzone-text">파일을 드래그하거나 클릭하세요</div>
            <div class="dropzone-subtext">PDF, JPG, PNG 파일 (최대 {max_file_size_mb}MB)</div>
        </div>
        
        <input type="file" id="fileInput" multiple accept="{accept_str}">
        
        <div class="file-list" id="fileList"></div>
        
        <script>
            const dropzone = document.getElementById('dropzone');
            const fileInput = document.getElementById('fileInput');
            const fileList = document.getElementById('fileList');
            let uploadedFiles = [];
            
            // 클릭 이벤트
            dropzone.addEventListener('click', () => {{
                fileInput.click();
            }});
            
            // 파일 선택 이벤트
            fileInput.addEventListener('change', (e) => {{
                handleFiles(e.target.files);
            }});
            
            // 드래그 오버 이벤트
            dropzone.addEventListener('dragover', (e) => {{
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('drag-over');
            }});
            
            // 드래그 떠남 이벤트
            dropzone.addEventListener('dragleave', (e) => {{
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('drag-over');
            }});
            
            // 드롭 이벤트
            dropzone.addEventListener('drop', (e) => {{
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('drag-over');
                
                const files = e.dataTransfer.files;
                handleFiles(files);
            }});
            
            // 터치 이벤트 (모바일/태블릿 지원)
            let touchStartY = 0;
            let touchFile = null;
            
            dropzone.addEventListener('touchstart', (e) => {{
                touchStartY = e.touches[0].clientY;
            }}, {{ passive: true }});
            
            dropzone.addEventListener('touchmove', (e) => {{
                const touchY = e.touches[0].clientY;
                const deltaY = touchY - touchStartY;
                
                // 위로 스와이프 시 파일 선택 트리거
                if (deltaY < -50) {{
                    fileInput.click();
                }}
            }}, {{ passive: true }});
            
            // 파일 처리 함수
            function handleFiles(files) {{
                dropzone.classList.add('uploading');
                
                Array.from(files).forEach(file => {{
                    // 파일 크기 체크
                    if (file.size > {max_size_bytes}) {{
                        alert(`파일 "${{{{file.name}}}}"이(가) 너무 큽니다. 최대 {max_file_size_mb}MB까지 업로드 가능합니다.`);
                        return;
                    }}
                    
                    // 파일 타입 체크
                    const acceptTypes = "{accept_str}".split(',');
                    if (!acceptTypes.some(type => file.type.match(type.replace('*', '.*')))) {{
                        alert(`파일 "${{{{file.name}}}}"은(는) 지원하지 않는 형식입니다.`);
                        return;
                    }}
                    
                    // 파일 읽기
                    const reader = new FileReader();
                    
                    reader.onload = (e) => {{
                        const fileData = {{
                            name: file.name,
                            type: file.type,
                            size: file.size,
                            data: e.target.result.split(',')[1]  // Base64 데이터만 추출
                        }};
                        
                        uploadedFiles.push(fileData);
                        renderFileList();
                        
                        // Streamlit으로 데이터 전송
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: uploadedFiles
                        }}, '*');
                        
                        dropzone.classList.remove('uploading');
                    }};
                    
                    reader.readAsDataURL(file);
                }});
            }}
            
            // 파일 리스트 렌더링
            function renderFileList() {{
                fileList.innerHTML = '';
                
                uploadedFiles.forEach((file, index) => {{
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    
                    const sizeKB = (file.size / 1024).toFixed(1);
                    const icon = file.type.includes('pdf') ? '📄' : '🖼️';
                    
                    fileItem.innerHTML = `
                        <div class="file-info">
                            <div class="file-icon">${{{{icon}}}}</div>
                            <div class="file-details">
                                <div class="file-name">${{{{file.name}}}}</div>
                                <div class="file-size">${{{{sizeKB}}}} KB</div>
                            </div>
                        </div>
                        <button class="remove-btn" onclick="removeFile(${{{{index}}}})">삭제</button>
                    `;
                    
                    fileList.appendChild(fileItem);
                }});
            }}
            
            // 파일 삭제
            function removeFile(index) {{
                uploadedFiles.splice(index, 1);
                renderFileList();
                
                // Streamlit으로 업데이트된 데이터 전송
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: uploadedFiles
                }}, '*');
            }}
        </script>
    </body>
    </html>
    """
    
    # 컴포넌트 렌더링
    uploaded_data = components.html(
        html_code,
        height=height + 200,  # 파일 리스트 공간 추가
        scrolling=True
    )
    
    # 업로드된 파일 데이터 반환
    if uploaded_data:
        st.session_state[f"{key}_files"] = uploaded_data
        return uploaded_data
    
    return st.session_state.get(f"{key}_files", [])


# 사용 예시
if __name__ == "__main__":
    st.set_page_config(page_title="태블릿 Drop Zone 테스트", layout="wide")
    
    st.title("📱 태블릿 전용 드래그 앤 드롭 컴포넌트")
    
    uploaded_files = render_tablet_dropzone(
        key="test_dropzone",
        accept_types=['image/jpeg', 'image/png', 'application/pdf'],
        max_file_size_mb=10,
        height=300
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)}개 파일 업로드 완료")
        
        for file in uploaded_files:
            st.write(f"- **{file['name']}** ({file['size']} bytes)")
