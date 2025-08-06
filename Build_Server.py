from flask import Flask, request, jsonify
import subprocess
import os
from datetime import datetime
import shutil

app = Flask(__name__)

def archive_file(filepath, archive_dir="codex_archive"):
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    basename = os.path.basename(filepath)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(filepath, os.path.join(archive_dir, f"{ts}_{basename}"))

@app.route("/ue_build", methods=["POST"])
def build():
    data = request.json
    project_path = data.get("project_path")
    project_name = data.get("project_name")
    branch_name = data.get("branch_name")

    codex_fix_path = os.path.join(project_path, "codex_fix.txt")
    codex_fix_fail_path = os.path.join(project_path, "codex_fix_fail.txt")
    build_request_path = os.path.join(project_path, "build_request.txt")
    log_path = os.path.join(project_path, "build.log")
    codex_prompt_path = os.path.join(project_path, "codex_prompt.txt")
    codex_context_path = os.path.join(project_path, "codex_context.log")

    # 1. codex_fix_fail.txt가 있으면 종료
    if os.path.exists(codex_fix_fail_path):
        print("codex_fix_fail.txt 감지: 자동화 중단")
        return jsonify({"status": "codex automation stopped", "reason": "codex_fix_fail.txt exists"}), 200

    # 2. codex_fix.txt가 있으면: codex로 코드 수정
    if os.path.exists(codex_fix_path):
        codex_path = r"C:\Users\banbe\AppData\Roaming\npm\codex.cmd"
        # 프롬프트 파일 내용을 문자열로 읽어 전달
        with open(codex_prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        codex_cli_cmd = [
            codex_path, "run",
            "--prompt", prompt_text,  # --prompt: codex run --help에 명시된 옵션
            "--error-log", codex_fix_path,  # --error-log: codex run --help에 명시된 옵션
            "--project-doc", codex_context_path,  # --project-doc: codex run --help에 명시된 옵션
            "--approval-mode", "always",  # --approval-mode: 자동 승인 (codex run --help 참고)
            "-q"  # -q: 비상호작용(quiet) 모드, codex run --help에 명시
        ]
        print("[Codex CLI 실행]", " ".join(codex_cli_cmd))
        # NOTE: 현재 컨테이너에는 codex CLI가 설치되어 있지 않아 옵션 지원 여부를 실제로 확인하지 못함
        # Windows 환경에서 cp949 디코딩 오류가 발생할 수 있어, 바이너리로 캡처 후 UTF-8로 디코드
        cli_result = subprocess.run(codex_cli_cmd, capture_output=True, cwd=project_path)
        stdout = cli_result.stdout.decode("utf-8", errors="replace") if cli_result.stdout else ""
        stderr = cli_result.stderr.decode("utf-8", errors="replace") if cli_result.stderr else ""
        if stdout:
            print("CLI stdout:", stdout)
        if stderr:
            print("Codex CLI stderr:", stderr)

        # 작업 요약을 codex_context.log에 누적
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(codex_context_path, "a", encoding="utf-8") as f:
            f.write(f"\n---\n[{now}] Codex CLI 자동화 작업 요약\n")
            f.write(stdout)
            if stderr:
                f.write("\n[stderr]\n")
                f.write(stderr)

        # 코드 변경(커밋/푸시) 자동 처리
        git_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=project_path)
        if git_status.stdout.strip():
            subprocess.run(["git", "add", "."], cwd=project_path)
            subprocess.run(["git", "commit", "-m", "[auto] codex fix"], cwd=project_path)
            subprocess.run(["git", "push"], cwd=project_path)
            archive_file(codex_fix_path)
            return jsonify({
                "status": "codex automation committed",
                "message": "Codex CLI로 코드 수정 및 커밋/푸시 완료"
            }), 200
        else:
            # 변경 없음 → 실패 플래그 생성
            os.rename(codex_fix_path, codex_fix_fail_path)
            return jsonify({
                "status": "codex automation nochange",
                "message": "Codex CLI가 코드에 변화를 주지 않음(자동화 중단)",
                "fail_flag": codex_fix_fail_path
            }), 200

    # 3. codex_fix.txt가 없고 build_request.txt가 있으면: 빌드 수행
    if os.path.exists(build_request_path):
        # Git 브랜치 전환
        subprocess.run(f'git -C "{project_path}" fetch origin {branch_name}', shell=True)
        subprocess.run(f'git -C "{project_path}" checkout {branch_name}', shell=True)
        subprocess.run(f'git -C "{project_path}" pull origin {branch_name}', shell=True)

        build_cmd = f'ue_build.bat "{project_path}" "{project_name}" "{branch_name}"'
        result = subprocess.run(build_cmd, shell=True)

        if result.returncode != 0:
            # 빌드 실패 로그 저장
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                build_log = f.read()
            with open(codex_fix_path, "w", encoding="utf-8") as f:
                f.write(build_log)
            archive_file(build_request_path)
            return jsonify({"status": "build failed", "codex_fix": codex_fix_path}), 200
        else:
            archive_file(build_request_path)
            return jsonify({"status": "build succeeded"}), 200

    # 4. 처리할 게 없으면
    return jsonify({"status": "idle", "reason": "Nothing to process"}), 200

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=9000)
    except Exception as e:
        print("서버 실행 중 에러:", e)
        input("엔터를 누르세요")
