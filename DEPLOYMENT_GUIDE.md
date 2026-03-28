# 🚀 CRM 배포 완료 및 마이그레이션 가이드

## ✅ 1단계: CRM 배포 완료

**배포 정보**:
- **서비스**: goldkey-crm
- **Revision**: goldkey-crm-00294-bj8
- **URL**: https://goldkey-crm-vje5ef5qka-du.a.run.app
- **Image**: asia-northeast3-docker.pkg.dev/gen-lang-client-0777682955/goldkey/goldkey-crm:v20260327-2059
- **배포 시각**: 2026-03-27 20:59 KST

**적용된 변경사항**:
- ✅ 마스터키 정책 (ENCRYPTION_KEY 공유)
- ✅ 폴백 로직 제거 (키 없으면 에러)
- ✅ 회원가입/비밀번호 재설정 Modal
- ✅ GCS 마스터 명부 동기화
- ✅ 브라우저 핑거프린팅

---

## 🔄 2단계: HQ → CRM 마이그레이션 실행

### Cloud Shell에서 실행

로컬 환경에 `google-cloud-storage` 패키지가 없어 Cloud Shell에서 실행해야 합니다.

```bash
# 1. Cloud Shell 접속
gcloud cloud-shell ssh

# 2. 프로젝트 클론 (또는 기존 디렉토리 이동)
cd ~/CascadeProjects
git pull origin main

# 3. 환경변수 설정
export ENCRYPTION_KEY="19IPhRrXEWJZqKPMmb-lJIGVPECKUqBCUJNDKmIpZQg="

# 4. Python 패키지 설치
pip install google-cloud-storage cryptography supabase

# 5. Dry-run 테스트 (실제 저장 없이 확인)
python scripts/migrate_hq_to_crm.py

# 6. 실제 마이그레이션 실행
python scripts/migrate_hq_to_crm.py --execute
```

### 예상 출력

```
================================================================================
[MIGRATION] HQ → CRM 회원 데이터 마이그레이션 시작
================================================================================

[1/4] HQ 회원 데이터 조회 중...
✅ HQ에서 XX명 회원 조회 완료

[2/4] 기존 CRM 회원 확인 중...
  기존 CRM 회원: 0명

[3/4] 데이터 변환 및 저장 중...
  [1/XX] 처리 중...
    ✅ 저장 완료: user-id-1
  [2/XX] 처리 중...
    ✅ 저장 완료: user-id-2
  ...

[4/4] 마이그레이션 완료
================================================================================
총 회원 수: XX
성공: XX
실패: 0
스킵: 0
================================================================================
📝 로그 저장: migration_log_20260327_HHMMSS.json
```

---

## 🧪 3단계: 라이브 검증

### A. 회원가입 Modal 테스트

1. **CRM 앱 접속**
   ```
   https://goldkey-crm-vje5ef5qka-du.a.run.app
   ```

2. **로그인 화면에서 확인**
   - `[🔐 회원가입]` 버튼 클릭
   - Modal 팝업 정상 표시 확인
   - 입력 필드 확인:
     - 이름
     - 연락처 (로그인 ID)
     - 연락처 확인
     - 비밀번호
     - 비밀번호 확인

3. **테스트 가입**
   ```
   이름: 테스트사용자
   연락처: 010-0000-0000
   연락처 확인: 010-0000-0000
   비밀번호: test1234
   비밀번호 확인: test1234
   ```

4. **예상 결과**
   - ✅ 회원가입이 완료되었습니다!
   - 자동 로그인 또는 로그인 화면으로 이동

### B. 비밀번호 재설정 Modal 테스트

1. **로그인 화면에서 확인**
   - `[🔑 비밀번호 찾기]` 버튼 클릭
   - Modal 팝업 정상 표시 확인
   - 베타 경고 메시지 확인:
     ```
     ⚠️ 베타 테스트용 시뮬레이션 모드입니다
     ```

2. **본인인증 시뮬레이션**
   - `[🅿️ PASS 인증]` 또는 `[💬 카카오 인증]` 클릭
   - 이름 + 연락처 입력
   - `[✅ 인증 완료]` 클릭

3. **새 비밀번호 설정**
   - 새 비밀번호 입력
   - 새 비밀번호 확인 입력
   - `[✅ 비밀번호 변경]` 클릭

4. **예상 결과**
   - ✅ 비밀번호가 변경되었습니다!

### C. 관리자 탭 복호화 출력 확인

**⚠️ 중요**: 관리자 탭은 현재 CRM 앱에 구현되어 있지 않을 수 있습니다. HQ 앱에서 확인하거나, CRM 앱에 관리자 기능을 추가해야 합니다.

1. **HQ 앱 접속** (관리자 계정)
   ```
   https://goldkey-ai-vje5ef5qka-du.a.run.app
   ```

2. **회원 목록 확인**
   - 마이그레이션된 회원 이름이 복호화되어 표시되는지 확인
   - 예: "홍길동", "김영희" 등 (암호화된 문자열이 아님)

3. **예상 결과**
   - ✅ 이름이 평문으로 정상 표시
   - ✅ 연락처는 해시값으로 표시 (복호화 불가)

---

## 🗂️ 4단계: GCS 파일 생성 확인

### Google Cloud Console에서 확인

1. **GCS 버킷 접속**
   ```
   https://console.cloud.google.com/storage/browser/goldkey-admin
   ```

2. **members/ 폴더 확인**
   - `goldkey-admin/members/` 경로 이동
   - 암호화된 JSON 파일 목록 확인
   - 파일명 형식: `{user_id}.json` (UUID)

3. **파일 내용 확인** (샘플)
   ```json
   {
     "user_id": "abc123-def456-...",
     "name_encrypted": "gAAAAABpxm...",
     "contact_hash": "e60124f2fe...",
     "password_hash": "6e659deaa8...",
     "role": "member",
     "quota_remaining": 10,
     "device_fingerprint": "",
     "created_at": "2026-01-15T10:00:00",
     "updated_at": "2026-03-27T20:59:00",
     "_migrated_from_hq": true,
     "_hq_original_id": "hq-001"
   }
   ```

4. **예상 결과**
   - ✅ 마이그레이션된 회원 수만큼 JSON 파일 생성
   - ✅ 파일명에 PII 없음 (UUID만 사용)
   - ✅ 파일 내용 암호화 확인

### gcloud CLI로 확인

```bash
# 파일 목록 조회
gsutil ls gs://goldkey-admin/members/

# 파일 개수 확인
gsutil ls gs://goldkey-admin/members/ | wc -l

# 샘플 파일 다운로드 및 확인
gsutil cp gs://goldkey-admin/members/{user_id}.json ./sample.json
cat sample.json | jq .
```

---

## 🔐 5단계: 환경변수 최종 확인

### Cloud Run 환경변수 확인

```bash
# goldkey-crm 환경변수 확인
gcloud run services describe goldkey-crm \
  --region asia-northeast3 \
  --format="value(spec.template.spec.containers[0].env)"

# goldkey-ai 환경변수 확인
gcloud run services describe goldkey-ai \
  --region asia-northeast3 \
  --format="value(spec.template.spec.containers[0].env)"
```

**예상 출력**:
```
ENCRYPTION_KEY=19IPhRrXEWJZqKPMmb-lJIGVPECKUqBCUJNDKmIpZQg=
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
```

**확인 사항**:
- ✅ `ENCRYPTION_KEY`가 양쪽 앱에 동일하게 설정됨
- ✅ 키 값이 `19IPhR...`로 시작 (기존 마스터키)

---

## 📋 최종 체크리스트

### 배포 완료
- [x] CRM 앱 Cloud Run 배포 성공
- [x] Revision: goldkey-crm-00294-bj8
- [x] URL: https://goldkey-crm-vje5ef5qka-du.a.run.app

### 마이그레이션 (Cloud Shell에서 실행 필요)
- [ ] HQ 회원 데이터 조회
- [ ] CRM GCS로 데이터 이관
- [ ] 마이그레이션 로그 생성

### 라이브 검증
- [ ] 회원가입 Modal 정상 작동
- [ ] 비밀번호 재설정 Modal 정상 작동
- [ ] 관리자 탭 복호화 출력 확인
- [ ] GCS goldkey-admin/members/ 파일 생성 확인

### 환경변수
- [ ] ENCRYPTION_KEY 양쪽 앱 동일 설정 확인
- [ ] 마스터키 값 확인 (19IPhR...)

---

## 🚨 문제 해결

### 회원가입 실패 시

**증상**: "❌ 회원가입 중 오류가 발생했습니다"

**원인**:
1. ENCRYPTION_KEY 환경변수 미설정
2. GCS 버킷 권한 부족
3. Supabase 연결 오류

**해결**:
```bash
# 1. 환경변수 확인
gcloud run services describe goldkey-crm \
  --region asia-northeast3 \
  --format="value(spec.template.spec.containers[0].env)"

# 2. 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=goldkey-crm" \
  --limit 50 \
  --format json

# 3. 환경변수 재설정
gcloud run services update goldkey-crm \
  --set-env-vars ENCRYPTION_KEY=19IPhRrXEWJZqKPMmb-lJIGVPECKUqBCUJNDKmIpZQg= \
  --region asia-northeast3
```

### 마이그레이션 실패 시

**증상**: "❌ 저장 실패: user-id-xxx"

**원인**:
1. GCS 버킷 권한 부족
2. ENCRYPTION_KEY 불일치
3. Supabase 연결 오류

**해결**:
```bash
# 1. GCS 버킷 권한 확인
gsutil iam get gs://goldkey-admin

# 2. 서비스 계정에 권한 부여
gsutil iam ch serviceAccount:817097913199-compute@developer.gserviceaccount.com:objectAdmin gs://goldkey-admin

# 3. 마이그레이션 재실행 (실패한 회원만 재시도)
python scripts/migrate_hq_to_crm.py --execute
```

---

## 📞 지원

**운영자**: 이세윤  
**연락처**: 010-3074-2616  
**이메일**: insusite@gmail.com

**Cloud Run 서비스**:
- HQ: https://goldkey-ai-vje5ef5qka-du.a.run.app
- CRM: https://goldkey-crm-vje5ef5qka-du.a.run.app

**GCS 버킷**:
- goldkey-admin/members/

---

**최종 업데이트**: 2026-03-27 20:59 KST
