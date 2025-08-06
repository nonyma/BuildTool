
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
project_path: D:\Projects\MyUnrealProject
project_name: MyUnrealProject
branch_name: feature/login-api
should_build: true
# (필요 시 추가 정보: commit, options 등)
```

- `should_build`를 `true`(또는 `1`)로 설정하면 빌드가 실행되며, 빌드 후에는 자동으로 `false`로 되돌아갑니다.
- 서버는 빌드 실행 시 현재 파일을 `<project_path>/build_request_archive/` 폴더에 타임스탬프 이름으로 복사해 보관합니다.
- 각 값은 향후 다른 도구가 파일을 수정하여 빌드를 유발할 수 있도록 단순한 `key:value` 형식으로 유지합니다.
- 분기명을 변경하거나 추후 `commit` 등의 추가 파라미터를 넣어 빌드 조건을 제어할 수 있습니다.

---

## API 요청 예시

`build_request.txt` 내용을 수정한 뒤 빌드를 시작하려면 아래와 같이 POST 요청만 보내면 됩니다. 요청 본문은 비워도 됩니다.

```
POST http://<빌드서버주소>:9000/ue_build
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
