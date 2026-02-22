---
description: 깃허브로 전송 (add → commit → push)
---

## 깃허브 전송 워크플로우

변경된 파일을 GitHub에 자동으로 push합니다.
사용 방법: "깃허브로 전송해줘" 또는 "/git-push" 라고 입력하면 실행됩니다.

1. 현재 변경 사항 확인
// turbo
Run: git -C "c:\Users\insus\CascadeProjects" status

2. 모든 변경 파일 스테이징
// turbo
Run: git -C "c:\Users\insus\CascadeProjects" add -A

3. 날짜+시간 포함 커밋 (PowerShell 방식)
// turbo
Run: git -C "c:\Users\insus\CascadeProjects" commit -m "update: $(Get-Date -Format 'yyyy-MM-dd HH:mm') 자동 커밋"

4. GitHub으로 push
// turbo
Run: git -C "c:\Users\insus\CascadeProjects" push origin main
