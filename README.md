
# Codex 빌드 자동화 워크플로우

이 저장소는 Codex CLI와 빌드 서버, GitHub Actions를 연동하여  
코드 자동화 및 빌드/수정 작업을 실험하는 프로젝트입니다.

---

## 구성 요소

- **agent.md**  
  자동화 워크플로우와 빌드 요청 규칙, Codex 사용 지침 등 정의

- **빌드 서버 스크립트**  
  빌드 요청을 받고 Codex CLI를 호출하여 자동화 수행

- **Codex CLI**  
  자연어 프롬프트 기반 코드 생성 및 수정, 빌드 오류 자동 수정 루프 구현

- **GitHub Actions**  
  빌드 결과에 따라 PR 머지, 실패 알림 등 자동화 분기 처리

---

## 기본 사용 흐름

1. **빌드 요청/PR 생성**  
   - 사용자가 PR을 생성하거나, 직접 빌드 요청을 작성

2. **빌드 서버에서 Codex CLI 실행**  
   - `build_request.txt` 또는 에러 로그 기반으로 Codex 자동화 실행

3. **자동 수정/재시도 루프**  
   - 빌드 실패 시 Codex가 수정안 제안 및 자동 반영

4. **빌드 결과를 GitHub Actions로 전달**  
   - 성공/실패 결과에 따라 자동 머지 또는 알림 분기

---

## 시작하기

```bash
# Codex CLI 로그인(최초 1회)
codex login

# 빌드 자동화 요청 예시
python build_server.py
```

---

## 커스텀 규칙/자동화 설정

자동화 규칙 및 상세 워크플로우는  
`agent.md` 파일에서 관리합니다.

---

## 참고

- Codex CLI 공식 문서: https://github.com/openai/openai-codex-cli
- GitHub Actions: https://docs.github.com/actions

---
