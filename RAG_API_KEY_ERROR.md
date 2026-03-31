# RAG 임베딩 실행 오류 보고서

**실행일시**: 2026-03-30 19:35  
**상태**: ❌ OpenAI API 키 오류

---

## ❌ 발생한 오류

### OpenAI API 키 인증 실패

**오류 메시지**:
```
Error code: 401 - Incorrect API key provided
You can find your API key at https://platform.openai.com/account/api-keys
```

**원인**:
- `.env` 파일의 `OPENAI_API_KEY`가 잘못되었거나 만료됨
- 현재 키: `CFgMHnNB...dg4A` (마스킹됨)
- OpenAI 대시보드에서 새 API 키 발급 필요

---

## ✅ 정상 작동 확인

1. **PDF 로드**: ✅ 3개 파일 모두 성공
2. **청크 분할**: ✅ 332개 청크 생성 완료
3. **환경변수 로드**: ✅ .env 파일 정상 로드

---

## 🔧 해결 방법

### 1. OpenAI API 키 확인

**접속**: https://platform.openai.com/api-keys

**확인 사항**:
- ✅ API 키가 활성화되어 있는지 확인
- ✅ 결제 정보가 등록되어 있는지 확인 (크레딧 $10 충전 완료 확인)
- ✅ 사용 한도가 남아있는지 확인

### 2. 새 API 키 발급 (필요 시)

1. OpenAI 대시보드 → API keys 메뉴
2. **"Create new secret key"** 버튼 클릭
3. 키 이름 입력 (예: "RAG Embedding Key")
4. 생성된 키 복사 (한 번만 표시됨!)

### 3. .env 파일 업데이트

**파일**: `d:\CascadeProjects\.env`  
**비밀번호**: 6803

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=새로운_supabase_key
SUPABASE_SERVICE_KEY=새로운_service_role_key
OPENAI_API_KEY=sk-proj-새로운_openai_키  # 이 부분 교체!
```

⚠️ **중요**: 
- OpenAI API 키는 반드시 `sk-proj-` 또는 `sk-`로 시작해야 함
- 키 전체를 복사하여 붙여넣기 (공백 없이)

---

## 🧪 API 키 테스트 방법

### 간단한 테스트 스크립트

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 테스트 임베딩 생성
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="테스트"
)
print("✅ OpenAI API 키 정상 작동!")
print(f"임베딩 차원: {len(response.data[0].embedding)}")
```

---

## 💰 OpenAI 크레딧 확인

**대시보드**: https://platform.openai.com/usage

**확인 사항**:
- ✅ $10 충전이 정상 반영되었는지 확인
- ✅ 사용 가능한 크레딧 잔액 확인
- ✅ 월간 사용 한도 설정 확인

**예상 비용**:
- 332개 청크 임베딩: 약 $0.01~0.02
- 충분한 크레딧 보유 확인 필요

---

## 🚀 다음 단계

### API 키 업데이트 후 재실행

```powershell
python d:\CascadeProjects\hq_backend\run_rag_ingestion.py
```

**예상 소요 시간**: 3~5분  
**예상 결과**: 332개 청크 → Supabase 저장 완료

---

## 📊 현재 상태

| 단계 | 상태 | 비고 |
|------|------|------|
| PDF 로드 | ✅ 완료 | 3개 파일, 151페이지 |
| 청크 분할 | ✅ 완료 | 332개 청크 생성 |
| OpenAI 임베딩 | ❌ 실패 | API 키 오류 |
| Supabase 저장 | ⏳ 대기 | 임베딩 완료 후 진행 |

---

**작성일**: 2026-03-30  
**상태**: OpenAI API 키 업데이트 대기 중
