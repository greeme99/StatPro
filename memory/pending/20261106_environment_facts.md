target: project-memory
action: add
---
- 로컬 실행 환경: 백엔드는 127.0.0.1:8765, 프론트엔드는 127.0.0.1:5173에서 구동되며, 데이터 저장소 기본 경로는 D:\StatProData (부재 시 프로젝트 내 data 폴더 자동 생성).
- Windows 배치 스크립트 작성 규칙: Windows CMD(cmd.exe) 파서 호환을 위해 반드시 CRLF(\r\n) 개행 및 CP949 인코딩으로 저장해야 하며, 괄호 탈출 버그 방지를 위해 조건문은 if ... goto 선형 구조를 사용한다.
---
reason: start.bat, stop.bat, tools/run_backend.bat 구현 및 디버깅 과정에서 검증된 핵심 환경 사실.

