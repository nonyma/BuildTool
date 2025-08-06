
# Codex 빌드 자동화 워크플로우

이 저장소는 Codex CLI, 빌드 서버, GitHub Actions를 연동하여  
언리얼 프로젝트 자동 빌드 및 코드 수정을 실험하는 프로젝트입니다.

---

## 설치 및 필수 구성요소

### 1. Python 및 pip
- [Python 공식 다운로드](https://www.python.org/downloads/)
- pip는 Python 설치 시 기본 포함

### 2. 패키지 설치
```bash
pip install openai flask
```
- [openai-python 공식 문서](https://github.com/openai/openai-python)
- [Flask 공식 문서](https://flask.palletsprojects.com/)

### 3. Codex CLI  
- [OpenAI Codex CLI 공식 문서](https://github.com/openai/openai-codex-cli)
- (CLI 도구 직접 활용 시만 필요. 단순 python+api 사용시 생략 가능)

---

## 필수 환경 변수

- `OPENAI_API_KEY_BUILDSERVER`  
  - Build_server.py가 OpenAI Codex API 호출 시 사용  
  - [OpenAI 플랫폼에서 키 발급](https://platform.openai.com/api-keys)
- (`FLASK_RUN_PORT`: Flask를 커스텀 포트로 실행할 때만 사용. 일반적으로 9000 포트로 고정)

#### 환경 변수 등록 예시
**Windows CMD**
```
set OPENAI_API_KEY_BUILDSERVER=sk-xxxxxxxxxxxxxxxxxxxxxx
```
**PowerShell**
```
$env:OPENAI_API_KEY_BUILDSERVER="sk-xxxxxxxxxxxxxxxxxxxxxx"
```
**bash(Linux/macOS)**
```
export OPENAI_API_KEY_BUILDSERVER=sk-xxxxxxxxxxxxxxxxxxxxxx
```

---

## build_request.txt 양식

빌드 서버에 전달하는 `build_request.txt` 파일은 다음과 같이 작성합니다.

```txt
project_path: C:\WorkSpace\UAIAgent
project_name: MyUnrealProject
branch_name: feature/login-api
# (필요 시 추가 정보: commit, options 등)
```

- 각 값은 POST /ue_build API 호출 시 json 파라미터와 동일하게 사용됨
- (예시: GitHub Action 등에서 자동으로 생성해 전송)

---

## API 요청 예시

빌드 서버에 빌드를 요청할 때  
아래와 같이 POST로 요청합니다.

```
POST http://<빌드서버주소>:9000/ue_build
Content-Type: application/json

{
  "project_path": "D:\Projects\MyUnrealProject",
  "project_name": "MyUnrealProject",
  "branch_name": "feature/login-api"
}
```

**응답 예시**
- 빌드 성공:  
  ```json
  { "status": "build succeeded" }
  ```
- 빌드 실패(Codex fix 제안 포함):  
  ```json
  { "status": "build failed", "fix_suggestion": "D:\Projects\MyUnrealProject\codex_fix.txt" }
  ```

---

## 기본 워크플로우 요약

1. **빌드 요청(POST 또는 build_request.txt)**  
2. **서버에서 ue_build.bat 실행 & 로그 기록**  
3. **빌드 실패 시 Codex를 통해 자동 코드 수정안 생성**  
4. **성공/실패 결과를 응답 및 깃헙 연동 처리**

---

## 참고

- [OpenAI API Key 관리](https://platform.openai.com/api-keys)
- [openai-python 공식 문서](https://github.com/openai/openai-python)
- [Flask 공식](https://flask.palletsprojects.com/)
- [Codex CLI](https://github.com/openai/openai-codex-cli)
- [GitHub Actions](https://docs.github.com/actions)

---
