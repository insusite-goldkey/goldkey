# 배포 전 필수 체크리스트

## Streamlit Cloud Secrets 설정 (필수)

Streamlit Cloud 대시보드 → App Settings → Secrets 에 아래 항목을 반드시 입력하세요.

```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
ADMIN_CODE = "your-admin-password"
MASTER_CODE = "your-master-password"
ADMIN_KEY = "your-admin-key"
ENCRYPTION_KEY = "your-fernet-key-base64"
```

### ENCRYPTION_KEY 생성 방법
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## 배포 시 주의사항

1. `members.json`, `usage_log.json`, `insurance_data.db` 는 `.gitignore`에 포함되어 있어 Git에 올라가지 않습니다.
2. Streamlit Cloud 환경에서는 `/tmp/` 경로에 데이터가 저장됩니다 (앱 재시작 시 초기화됨).
3. 영구 데이터 저장이 필요하면 외부 DB(Supabase, Firebase 등) 연동을 권장합니다.

## 로컬 실행 방법
```bash
pip install -r requirements.txt
streamlit run app.py
```
