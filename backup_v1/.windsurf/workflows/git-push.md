---
description: 깃허브로 전송 (백업 자동 생성 → 최신 2개 유지 → add → commit → push)
---

## ⚠️ 절대 명령 — 배포 의무 규칙 (AI Cascade 필수 준수)

**다음 상황에서 Cascade(AI)는 사용자 요청 없이도 반드시 이 워크플로우를 자동 실행해야 한다:**

1. `app.py` 파일에 대한 코드 수정(edit/multi_edit)이 1건 이상 완료된 경우
2. 구문 검사(SYNTAX OK) 통과 후 해당 작업 세션이 종료되는 경우
3. 사용자가 "완료", "확인", "다음" 등의 작업 마무리 발언을 한 경우

**배포 누락은 가이딩 프로토콜 위반이다. 예외 없이 배포한다.**

---

## 배포 순서 (절대 순서 — 변경 금지)

```
[1단계] 코드 수정 완료 확인
      ↓
[2단계] Python 구문 검사 실행
      & "C:\Users\insus\AppData\Local\Programs\Python\Python312\python.exe" -c
        "import ast; src=open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read();
         ast.parse(src); print('SYNTAX OK')"
      → SYNTAX OK 확인 필수. 오류 시 수정 후 재검사.
      ↓
[3단계] 백업 + GitHub + HuggingFace Space 일괄 push
      (아래 // turbo 자동 실행)
```

## 깃허브 전송 워크플로우

변경된 파일을 GitHub 및 HuggingFace Space에 자동으로 push하고, 백업을 최신 2개만 유지합니다.
사용 방법: "깃허브로 전송해줘" 또는 "/git-push" 라고 입력하면 실행됩니다.

1. 백업 생성 + 최신 2개 유지 + git push 한번에 실행
// turbo
Run: powershell -ExecutionPolicy Bypass -File "D:\CascadeProjects\backup_and_push.ps1"
