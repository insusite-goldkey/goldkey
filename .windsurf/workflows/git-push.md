---
description: 깃허브로 전송 (백업 자동 생성 → 최신 2개 유지 → add → commit → push)
---

## 깃허브 전송 워크플로우

변경된 파일을 GitHub에 자동으로 push하고, 백업을 최신 2개만 유지합니다.
사용 방법: "깃허브로 전송해줘" 또는 "/git-push" 라고 입력하면 실행됩니다.

1. 백업 생성 + 최신 2개 유지 + git push 한번에 실행
// turbo
Run: powershell -ExecutionPolicy Bypass -File "D:\CascadeProjects\backup_and_push.ps1"
