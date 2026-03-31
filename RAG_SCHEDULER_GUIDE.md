# RAG 자동 임베딩 작업 스케줄러 가이드

**작성일**: 2026-03-30  
**목적**: 매일 밤 12시에 source_docs 폴더의 새 PDF를 자동으로 RAG 임베딩 처리

---

## ✅ 생성된 파일

1. **`RAG_Auto_Ingestion_Task.xml`** — Windows 작업 스케줄러 작업 정의 파일
2. **`register_rag_scheduler.ps1`** — 작업 스케줄러 등록 PowerShell 스크립트
3. **`RAG_SCHEDULER_GUIDE.md`** — 사용 가이드 (현재 파일)

---

## 🔧 주요 설정

### 작업 이름
```
GoldKey_RAG_Auto_Ingestion
```

### 실행 시간
```
매일 밤 12시 (00:00)
```

### 실행 명령
```
python run_intelligent_rag.py
```

### 작업 경로
```
d:\CascadeProjects
```

### 핵심 옵션

#### 1. ✅ 사용자 로그온 여부와 관계없이 실행
```xml
<Principal id="Author">
  <UserId>S-1-5-18</UserId>  <!-- SYSTEM 계정 -->
  <RunLevel>HighestAvailable</RunLevel>
</Principal>
```

#### 2. ✅ 절전 모드 해제하여 실행
```xml
<WakeToRun>true</WakeToRun>
```
- 컴퓨터가 절전 모드(Sleep)에 있어도 작업 실행 시간에 자동으로 깨어남
- 작업 완료 후 다시 절전 모드로 전환 가능

#### 3. ✅ 배터리 사용 중에도 실행
```xml
<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
```

#### 4. ✅ 네트워크 연결 시에만 실행
```xml
<RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
```
- OpenAI API 및 Supabase 연결 필요

#### 5. ✅ 최대 실행 시간: 2시간
```xml
<ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
```

---

## 🚀 작업 스케줄러 등록 방법

### 방법 1: PowerShell 스크립트 실행 (권장)

1. **PowerShell을 관리자 권한으로 실행**:
   - Windows 검색 → "PowerShell" 입력
   - 우클릭 → "관리자 권한으로 실행"

2. **프로젝트 폴더로 이동**:
   ```powershell
   cd d:\CascadeProjects
   ```

3. **등록 스크립트 실행**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File "register_rag_scheduler.ps1"
   ```

4. **기존 작업이 있으면 삭제 여부 확인**:
   ```
   기존 작업을 삭제하고 다시 등록하시겠습니까? (Y/N): Y
   ```

5. **등록 완료 확인**:
   ```
   ✅ 작업 스케줄러 등록 완료!
   작업 이름: GoldKey_RAG_Auto_Ingestion
   실행 시간: 매일 밤 12시 (00:00)
   ```

### 방법 2: 작업 스케줄러 GUI 사용

1. **작업 스케줄러 열기**:
   ```
   Win + R → taskschd.msc → Enter
   ```

2. **작업 가져오기**:
   - 우측 패널 → "작업 가져오기..."
   - `d:\CascadeProjects\RAG_Auto_Ingestion_Task.xml` 선택

3. **작업 설정 확인**:
   - 트리거: 매일 밤 12시
   - 동작: python run_intelligent_rag.py
   - 조건: 절전 모드 해제 체크됨

4. **확인 클릭**

---

## 📊 작업 관리 명령어

### 1. 작업 수동 실행 (테스트)
```powershell
Start-ScheduledTask -TaskName "GoldKey_RAG_Auto_Ingestion"
```

### 2. 작업 상태 확인
```powershell
Get-ScheduledTask -TaskName "GoldKey_RAG_Auto_Ingestion" | Format-List *
```

### 3. 작업 실행 이력 확인
```powershell
Get-ScheduledTaskInfo -TaskName "GoldKey_RAG_Auto_Ingestion"
```

**출력 예시**:
```
LastRunTime        : 2026-03-30 오후 11:00:00
LastTaskResult     : 0 (성공)
NextRunTime        : 2026-03-31 오전 12:00:00
NumberOfMissedRuns : 0
```

### 4. 작업 비활성화
```powershell
Disable-ScheduledTask -TaskName "GoldKey_RAG_Auto_Ingestion"
```

### 5. 작업 활성화
```powershell
Enable-ScheduledTask -TaskName "GoldKey_RAG_Auto_Ingestion"
```

### 6. 작업 삭제
```powershell
Unregister-ScheduledTask -TaskName "GoldKey_RAG_Auto_Ingestion" -Confirm:$false
```

---

## 🧪 테스트 방법

### 1. 수동 실행 테스트

```powershell
# 작업 수동 실행
Start-ScheduledTask -TaskName "GoldKey_RAG_Auto_Ingestion"

# 실행 상태 확인 (5초 대기 후)
Start-Sleep -Seconds 5
Get-ScheduledTaskInfo -TaskName "GoldKey_RAG_Auto_Ingestion"
```

### 2. 로그 확인

**작업 스케줄러 GUI에서 확인**:
1. `taskschd.msc` 실행
2. 작업 스케줄러 라이브러리 → `GoldKey_RAG_Auto_Ingestion`
3. 하단 "이력" 탭 클릭
4. 최근 실행 로그 확인

**이벤트 뷰어에서 확인**:
1. `eventvwr.msc` 실행
2. Windows 로그 → 응용 프로그램
3. "작업 스케줄러" 원본 필터링

### 3. 실행 결과 확인

**RAG 임베딩 보고서**:
```
d:\CascadeProjects\RAG_INGESTION_REPORT_YYYYMMDD_HHMMSS.json
```

**보고서 내용**:
```json
{
  "success": true,
  "total_files": 10,
  "processed": 3,
  "skipped": 7,
  "failed": 0,
  "summary": {
    "기존 파일 유지": 7,
    "새 파일 추가 완료": 3,
    "중복 제외": 7,
    "실패": 0
  }
}
```

---

## 🔍 트러블슈팅

### 문제 1: "작업이 실행되지 않음"

**원인**: 절전 모드 해제 설정이 적용되지 않음

**해결**:
1. 작업 스케줄러 열기 (`taskschd.msc`)
2. `GoldKey_RAG_Auto_Ingestion` 우클릭 → 속성
3. "조건" 탭 → "작업을 실행하기 위해 컴퓨터를 절전 모드에서 해제" 체크
4. "설정" 탭 → "작업이 실행되지 않으면 가능한 빨리 실행" 체크
5. 확인 클릭

### 문제 2: "Python을 찾을 수 없음"

**원인**: Python이 시스템 PATH에 없음

**해결**:
1. XML 파일 수정:
   ```xml
   <Command>C:\Python311\python.exe</Command>
   ```
   (Python 설치 경로로 변경)

2. 작업 재등록:
   ```powershell
   powershell -ExecutionPolicy Bypass -File "register_rag_scheduler.ps1"
   ```

### 문제 3: "환경변수 미설정 오류"

**원인**: .env 파일이 없거나 환경변수가 설정되지 않음

**해결**:
1. `.env` 파일 확인:
   ```
   d:\CascadeProjects\.env
   ```

2. 필수 환경변수 확인:
   - SUPABASE_URL
   - SUPABASE_SERVICE_KEY
   - OPENAI_API_KEY

3. 환경변수가 없으면 추가

### 문제 4: "네트워크 연결 없음"

**원인**: 작업 실행 시 네트워크 연결이 없음

**해결**:
1. 작업 스케줄러 속성 → "조건" 탭
2. "다음 네트워크 연결을 사용할 수 있는 경우에만 시작" 체크 해제
3. 또는 네트워크 연결 확인 후 재실행

### 문제 5: "작업이 2시간 후 강제 종료됨"

**원인**: 실행 시간 제한 초과

**해결**:
1. XML 파일 수정:
   ```xml
   <ExecutionTimeLimit>PT4H</ExecutionTimeLimit>
   ```
   (4시간으로 변경)

2. 작업 재등록

---

## 📋 체크리스트

### 등록 전
- [ ] Python 설치 확인 (`python --version`)
- [ ] `.env` 파일 확인 (환경변수 설정)
- [ ] `run_intelligent_rag.py` 파일 확인
- [ ] source_docs 폴더 확인

### 등록 후
- [ ] 작업 스케줄러에서 작업 확인
- [ ] 작업 수동 실행 테스트
- [ ] 실행 이력 확인
- [ ] RAG 임베딩 보고서 확인

### 운영 중
- [ ] 매일 아침 실행 이력 확인
- [ ] RAG 임베딩 보고서 확인
- [ ] 새 파일이 정상적으로 처리되었는지 확인
- [ ] Supabase에서 데이터 확인

---

## 🎯 사용 시나리오

### 시나리오 1: 매일 밤 자동 처리
1. **오후 11시**: source_docs 폴더에 새 PDF 파일 추가
2. **밤 12시**: 작업 스케줄러가 자동으로 실행
3. **새벽 12시 10분**: RAG 임베딩 완료 (보고서 생성)
4. **아침 9시**: 보고서 확인 및 CRM 앱에서 RAG 기능 테스트

### 시나리오 2: 절전 모드에서 자동 실행
1. **오후 11시**: 컴퓨터를 절전 모드로 전환
2. **밤 12시**: 작업 스케줄러가 컴퓨터를 깨움
3. **밤 12시 ~ 12시 10분**: RAG 임베딩 처리
4. **새벽 12시 10분**: 작업 완료 후 다시 절전 모드로 전환

### 시나리오 3: 수동 실행 (긴급)
1. **오후 3시**: 중요한 새 문서 추가
2. **오후 3시 1분**: 작업 수동 실행
   ```powershell
   Start-ScheduledTask -TaskName "GoldKey_RAG_Auto_Ingestion"
   ```
3. **오후 3시 10분**: 처리 완료 확인
4. **오후 3시 15분**: CRM 앱에서 새 문서 검색 테스트

---

## 🎉 결론

**매일 밤 12시 자동 RAG 임베딩 작업 스케줄러가 설정되었습니다!**

### 핵심 기능
- ✅ **매일 밤 12시 자동 실행**
- ✅ **절전 모드 해제하여 실행** (WakeToRun)
- ✅ **사용자 로그온 여부와 관계없이 실행** (SYSTEM 계정)
- ✅ **배터리 사용 중에도 실행**
- ✅ **네트워크 연결 시에만 실행**
- ✅ **최대 실행 시간: 2시간**

### 다음 단계
1. **관리자 권한으로 등록 스크립트 실행**
2. **작업 수동 실행으로 테스트**
3. **실행 이력 및 보고서 확인**
4. **매일 아침 자동 처리 결과 확인**

---

**작성일**: 2026-03-30  
**작성자**: Windsurf Cascade AI  
**Phase**: Phase 5 고도화 - 자동화 완성
