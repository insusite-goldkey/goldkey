# 🔧 마이그레이션 스크립트 긴급 수정 완료

## ✅ 수정 사항

### 1️⃣ 사용자 입력 제거
**문제**: `input("계속하려면 'YES'를 입력하세요: ")` 무한 반복으로 터미널 멈춤

**해결**:
- `--yes` 옵션 추가: 확인 메시지 없이 자동 실행
- `KeyboardInterrupt` 예외 처리: Ctrl+C로 안전하게 중단 가능
- `input()` 호출 시 `try-except`로 감싸서 오류 방지

```bash
# 기존 (무한 루프 발생 가능)
python scripts/migrate_hq_to_crm.py --execute

# 수정 후 (자동 실행)
python scripts/migrate_hq_to_crm.py --execute --yes
```

---

### 2️⃣ 진행률 표시 개선
**문제**: `y` 문자가 무한 반복되며 진행 상태 파악 불가

**해결**:
- 진행률 형식 변경: `[1/100] 홍길동 - 저장 완료`
- 이름 표시: 각 회원의 이름이 로그에 출력
- 상태 아이콘: ✅ 성공, ❌ 실패, ⚠️ 스킵

**출력 예시**:
```
[3/4] 데이터 변환 및 저장 중...
  총 100명 처리 예정

  [1/100] ✅ 홍길동 - 저장 완료
  [2/100] ✅ 김영희 - 저장 완료
  [3/100] ⚠️ 이철수 - 이미 존재 (스킵)
  [4/100] ❌ 박민수 - 저장 실패
  [5/100] ✅ 최지은 - 저장 완료
  ...
```

---

### 3️⃣ 무한 루프 방지 (try-except 강화)
**문제**: 한 명에게서 에러 발생 시 전체 프로세스 중단

**해결**:
- **3단계 예외 처리**:
  1. HQ 회원 조회 실패 → 전체 중단 (치명적 오류)
  2. 기존 CRM 회원 조회 실패 → 경고 후 계속 진행
  3. 개별 회원 처리 실패 → 실패 기록 후 다음 회원으로 이동

- **개별 회원 처리 루프**:
  ```python
  for idx, hq_member in enumerate(hq_members, 1):
      try:
          # 변환
          crm_member = transform_member_data(hq_member)
          if not crm_member:
              stats["failed"] += 1
              continue  # 다음 회원으로
          
          # 저장
          try:
              success = save_member_to_gcs(crm_member)
              if success:
                  stats["success"] += 1
              else:
                  stats["failed"] += 1
          except Exception as save_error:
              stats["failed"] += 1
              continue  # 다음 회원으로
      
      except Exception as e:
          stats["failed"] += 1
          continue  # 다음 회원으로 (무한 루프 방지)
  ```

- **Ctrl+C 중단 지원**:
  ```python
  try:
      stats = migrate_members(dry_run=not args.execute)
  except KeyboardInterrupt:
      print("\n\n❌ 사용자가 중단했습니다")
      return
  ```

---

## 🚀 Cloud Shell 재실행 가이드

### 1단계: Git Pull (최신 코드 받기)

```bash
cd ~/CascadeProjects
git pull origin main
```

### 2단계: 환경변수 설정

```bash
export ENCRYPTION_KEY="19IPhRrXEWJZqKPMmb-lJIGVPECKUqBCUJNDKmIpZQg="
```

### 3단계: 마이그레이션 실행 (자동 모드)

```bash
# 확인 메시지 없이 자동 실행
python scripts/migrate_hq_to_crm.py --execute --yes
```

**또는 확인 메시지 포함**:
```bash
# YES 입력 필요
python scripts/migrate_hq_to_crm.py --execute
```

### 4단계: 진행 상황 모니터링

실행 중 다음과 같은 로그가 출력됩니다:

```
================================================================================
[MIGRATION] HQ → CRM 회원 데이터 마이그레이션 시작
================================================================================
✅ EXECUTE 모드: 실제 GCS 저장을 진행합니다

[1/4] HQ 회원 데이터 조회 중...
✅ HQ에서 100명 회원 조회 완료

[2/4] 기존 CRM 회원 확인 중...
  기존 CRM 회원: 0명

[3/4] 데이터 변환 및 저장 중...
  총 100명 처리 예정

  [1/100] ✅ 홍길동 - 저장 완료
  [2/100] ✅ 김영희 - 저장 완료
  [3/100] ⚠️ 이철수 - 이미 존재 (스킵)
  [4/100] ❌ 박민수 - 저장 실패
  [5/100] ✅ 최지은 - 저장 완료
  ...
  [100/100] ✅ 마지막회원 - 저장 완료

[4/4] 마이그레이션 완료
================================================================================
총 회원 수: 100
성공: 95
실패: 2
스킵: 3
================================================================================
📝 로그 저장: migration_log_20260327_213000.json

================================================================================
📊 마이그레이션 결과 요약
================================================================================
✅ 성공: 95명
❌ 실패: 2명
⚠️ 스킵: 3명 (이미 존재)
```

---

## 🛑 중단 방법

실행 중 문제가 발생하면 **Ctrl+C**를 눌러 안전하게 중단할 수 있습니다:

```
^C
❌ 사용자가 중단했습니다
```

---

## 📊 로그 파일 확인

마이그레이션 완료 후 로그 파일이 자동 생성됩니다:

```bash
# 로그 파일 확인
cat migration_log_20260327_213000.json

# 예시 내용
{
  "total": 100,
  "success": 95,
  "failed": 2,
  "skipped": 3,
  "errors": [
    "저장 실패: user-id-123 (박민수)",
    "변환 실패: hq-456 (정수진)"
  ]
}
```

---

## 🔍 문제 해결

### 문제 1: "ModuleNotFoundError: No module named 'google.cloud'"

**해결**:
```bash
pip install google-cloud-storage cryptography supabase
```

### 문제 2: "RuntimeError: ENCRYPTION_KEY not found"

**해결**:
```bash
export ENCRYPTION_KEY="19IPhRrXEWJZqKPMmb-lJIGVPECKUqBCUJNDKmIpZQg="
```

### 문제 3: GCS 권한 오류

**해결**:
```bash
# 서비스 계정에 권한 부여
gsutil iam ch serviceAccount:817097913199-compute@developer.gserviceaccount.com:objectAdmin gs://goldkey-admin
```

### 문제 4: 특정 회원만 계속 실패

**원인**: 데이터 형식 문제 또는 필수 필드 누락

**해결**:
1. 로그 파일에서 실패한 회원 ID 확인
2. HQ Supabase에서 해당 회원 데이터 확인
3. 필요 시 수동으로 데이터 수정 후 재실행

---

## ✅ 최종 확인 사항

마이그레이션 완료 후:

1. **GCS 파일 확인**
   ```bash
   gsutil ls gs://goldkey-admin/members/ | wc -l
   ```

2. **샘플 파일 다운로드**
   ```bash
   gsutil cp gs://goldkey-admin/members/{user_id}.json ./sample.json
   cat sample.json | jq .
   ```

3. **CRM 앱에서 로그인 테스트**
   - URL: https://goldkey-crm-vje5ef5qka-du.a.run.app
   - 마이그레이션된 회원 계정으로 로그인 시도

---

**수정 완료 시각**: 2026-03-27 21:30 KST
