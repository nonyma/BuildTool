from flask import Flask, request, jsonify
import subprocess
import os
import json
from datetime import datetime
import shutil

app = Flask(__name__)

def archive_file(filepath, archive_dir="codex_archive"):
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    basename = os.path.basename(filepath)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(filepath, os.path.join(archive_dir, f"{ts}_{basename}"))

def to_wsl_path(win_path):
    r"""윈도우 경로 -> WSL2 경로 변환 (예: C:\WorkSpace\UAIAgent -> /mnt/c/WorkSpace/UAIAgent)"""
    drive, path = os.path.splitdrive(win_path)
    drive_letter = drive.rstrip(":").lower()
    wsl_path = f"/mnt/{drive_letter}{path.replace(os.sep, '/')}"
    return wsl_path

def read_build_request(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def write_build_request(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/ue_build", methods=["POST"])
def build():
    data = request.json
    project_path = data.get("project_path")
    project_name = data.get("project_name")
    branch_name = data.get("branch_name")

    build_request_path = os.path.join(project_path, "build_request.txt")
    log_path = os.path.join(project_path, "build.log")
    codex_prompt_path = os.path.join(project_path, "codex_prompt.txt")
    codex_context_path = os.path.join(project_path, "codex_context.log")

    state = read_build_request(build_request_path)
    should_build = str(state.get("should_build", "")).lower()
    # should_build 값이 true 또는 1이 아니면 바로 종료
    if should_build not in ("true", "1"):
        return jsonify({"status": "idle", "reason": "should_build is not true/1"}), 200

    # compile_error가 없으면 빌드부터 시도
    if not state.get("compile_error"):
        # 빌드 실행
        subprocess.run(f'git -C "{project_path}" fetch origin {branch_name}', shell=True)
        subprocess.run(f'git -C "{project_path}" checkout {branch_name}', shell=True)
        subprocess.run(f'git -C "{project_path}" pull origin {branch_name}', shell=True)

        build_cmd = f'ue_build.bat "{project_path}" "{project_name}" "{branch_name}"'
        result = subprocess.run(build_cmd, shell=True)
        if result.returncode == 0:
            # 빌드 성공: 에러 필드 모두 제거
            state.pop("compile_error", None)
            state.pop("codex_error", None)
            state["should_build"] = False
            write_build_request(build_request_path, state)
            archive_file(build_request_path)
            # 커밋 & 푸시
            subprocess.run(["git", "add", "."], cwd=project_path)
            subprocess.run(["git", "commit", "-m", "[auto] build succeeded"], cwd=project_path)
            subprocess.run(["git", "push"], cwd=project_path)
            return jsonify({"status": "build succeeded"}), 200
        else:
            # 빌드 실패: 컴파일 에러 로그 저장
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                build_log = f.read()
            state["compile_error"] = build_log
            state["should_build"] = False
            write_build_request(build_request_path, state)
            archive_file(build_request_path)
            # 커밋 & 푸시
            subprocess.run(["git", "add", "."], cwd=project_path)
            subprocess.run(["git", "commit", "-m", "[auto] build failed"], cwd=project_path)
            subprocess.run(["git", "push"], cwd=project_path)
            return jsonify({"status": "build failed", "compile_error": True}), 200

    # compile_error가 있으면 codex 단계
    else:
        # Codex(ToolAgent) 실행
        result = subprocess.run(
            [
                "python",
                "toolagent.py",
                "--project_path", to_wsl_path(project_path),
                "--prompt_path", codex_prompt_path
            ],
            capture_output=True, text=True
        )
        stdout = result.stdout
        stderr = result.stderr
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 작업 로그 누적
        with open(codex_context_path, "a", encoding="utf-8") as f:
            f.write(f"\n---\n[{now}] Codex CLI 자동화 작업 요약\n")
            f.write(stdout or "")
            if stderr:
                f.write("\n[stderr]\n")
                f.write(stderr)

        if result.returncode == 0:
            # Codex 성공: 에러 필드 모두 제거
            state.pop("compile_error", None)
            state.pop("codex_error", None)
            state["should_build"] = False
            write_build_request(build_request_path, state)
            archive_file(build_request_path)
            # 커밋 & 푸시
            subprocess.run(["git", "add", "."], cwd=project_path)
            subprocess.run(["git", "commit", "-m", "[auto] codex fix"], cwd=project_path)
            subprocess.run(["git", "push"], cwd=project_path)
            return jsonify({
                "status": "codex automation committed",
                "message": "Codex CLI로 코드 수정 및 커밋/푸시 완료",
                "toolagent_stdout": stdout,
                "toolagent_stderr": stderr
            }), 200
        else:
            # Codex 실패: codex_error 필드로 저장
            state["codex_error"] = stderr or "Codex CLI 실행 실패"
            state["should_build"] = False
            write_build_request(build_request_path, state)
            archive_file(build_request_path)
            # 커밋 & 푸시
            subprocess.run(["git", "add", "."], cwd=project_path)
            subprocess.run(["git", "commit", "-m", "[auto] codex failed"], cwd=project_path)
            subprocess.run(["git", "push"], cwd=project_path)
            return jsonify({
                "status": "codex automation failed",
                "message": "Codex CLI 실행 실패. codex_error 필드 생성됨.",
                "toolagent_stdout": stdout,
                "toolagent_stderr": stderr
            }), 200

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=9000)
    except Exception as e:
        print("서버 실행 중 에러:", e)
        input("엔터를 누르세요")
