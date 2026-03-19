# ==========================================================
# 데이터베이스 및 CRUD 모듈
# ==========================================================

import streamlit as st
import sqlite3
import json
from datetime import datetime as dt, timedelta

def setup_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    
    # 사용자 문서 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            document_name TEXT,
            document_type TEXT,
            file_size INTEGER,
            status TEXT DEFAULT 'ACTIVE',
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 사용자 로그 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def log_user_action(action, details=""):
    """사용자 액션 로깅"""
    if 'user_id' in st.session_state:
        conn = sqlite3.connect('insurance_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_logs (user_id, action, details)
            VALUES (?, ?, ?)
        ''', (st.session_state.user_id, action, details))
        conn.commit()
        conn.close()

def get_user_documents():
    """사용자 문서 목록 조회"""
    if 'user_id' not in st.session_state:
        return []
    
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT document_name, document_type, file_size, created_at
        FROM user_documents 
        WHERE user_id = ? AND status = 'ACTIVE'
        ORDER BY created_at DESC
    ''', (st.session_state.user_id,))
    
    documents = cursor.fetchall()
    conn.close()
    
    return [
        {
            "name": doc[0],
            "type": doc[1], 
            "size": f"{doc[2]/1024:.1f}KB",
            "date": doc[3][:10]
        }
        for doc in documents
    ]

def save_document_info(document_name, document_type, file_size):
    """문서 정보 저장"""
    if 'user_id' not in st.session_state:
        return False
    
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_documents (user_id, document_name, document_type, file_size, expiry_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (st.session_state.user_id, document_name, document_type, file_size, 
           (dt.now() + timedelta(days=30)).strftime('%Y-%m-%d')))
    
    conn.commit()
    conn.close()
    log_user_action("문서 업로드", f"{document_name} ({document_type})")
    return True

def delete_document(document_name):
    """문서 삭제"""
    if 'user_id' not in st.session_state:
        return False
    
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_documents 
        SET status = 'DELETED' 
        WHERE user_id = ? AND document_name = ?
    ''', (st.session_state.user_id, document_name))
    
    conn.commit()
    conn.close()
    log_user_action("문서 삭제", document_name)
    return True

def purge_expired_data():
    """30일 경과한 만료 데이터 영구 삭제"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    
    # 만료 문서 삭제
    cursor.execute("DELETE FROM user_documents WHERE status = 'DELETED' AND expiry_date <= date('now', '-30 days')")
    
    # 오래된 로그 삭제 (90일 이상)
    cursor.execute("DELETE FROM user_logs WHERE created_at <= date('now', '-90 days')")
    
    conn.commit()
    conn.close()
    return True
