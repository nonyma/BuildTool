from flask import Flask, jsonify
import subprocess
import os
import threading
import shutil
from datetime import datetime
from openai import OpenAI

print("OPENAI_API_KEY_BUILDSERVER =", os.environ.get("OPENAI_API_KEY_BUILDSERVER"))
app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY_BUILDSERVER"))

# 동시에 하나의 빌드만 처리하도록 Lock 사용
build_lock = threading.Lock()


def parse_build_request(path):
    """build_request.txt 파일을 파싱하여 키-값 딕셔너리로 반환"""
    info = {}
    if not os.path.exists(path):
        return info
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return info


@app.route("/ue_build", methods=["POST"])
def build():
    # 다른 빌드가 진행 중이면 "busy" 응답
    if not build_lock.acquire(blocking=False):
        return jsonify({"status": "busy"}), 429

    try:
        request_path = os.path.join(os.path.dirname(__file__), "build_request.txt")
        info = parse_build_request(request_path)

        project_path = info.get("project_path")
        project_name = info.get("project_name")
        branch_name = info.get("branch_name")
        should_build = info.get("should_build", "false").lower() not in ("false", "0", "no")
        # codex_fix.txt 등의 존재 여부와 무관하게 should_build 플래그로 빌드를 제어

        if not should_build:
            return jsonify({"status": "no build requested"}), 200

        if not project_path or not project_name or not branch_name:
            return jsonify({"error": "Missing project_path, project_name, or branch_name"}), 400

        # Git 브랜치 전환
        subprocess.run(f'git -C "{project_path}" fetch origin {branch_name}', shell=True)
        subprocess.run(f'git -C "{project_path}" checkout {branch_name}', shell=True)
        subprocess.run(f'git -C "{project_path}" pull origin {branch_name}', shell=True)

        # 빌드 실행
        build_cmd = f'ue_build.bat "{project_path}" "{project_name}" "{branch_name}"'
        result = subprocess.run(build_cmd, shell=True)

        if result.returncode != 0:
            # 빌드 실패 시 Codex 호출
            log_path = os.path.join(project_path, "build.log")
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                build_log = f.read()

            prompt = f"""
Build failed for Unreal project {project_name}.
Build log:
{build_log}

Please fix the code so the build passes.
"""

            response = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are an expert Unreal Engine C++ developer."},
                    {"role": "user", "content": prompt}
                ]
            )

            fix_code = response.choices[0].message.content
            fix_file_path = os.path.join(project_path, "codex_fix.txt")
            with open(fix_file_path, "w", encoding="utf-8") as f:
                f.write(fix_code)

            resp = {
                "status": "build failed",
                "fix_suggestion": fix_file_path
            }
        else:
            resp = {"status": "build succeeded"}

        # 빌드 요청 파일을 아카이브 폴더에 복사
        archive_dir = os.path.join(project_path, "build_request_archive")
        os.makedirs(archive_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(request_path, os.path.join(archive_dir, f"build_request_{timestamp}.txt"))

        # 플래그 초기화 (should_build:false)
        info["should_build"] = "false"
        with open(request_path, "w", encoding="utf-8") as f:
            for k, v in info.items():
                f.write(f"{k}:{v}\n")

        return jsonify(resp), 200
    finally:
        build_lock.release()


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=9000)
    except Exception as e:
        print("서버 실행 중 에러:", e)
        input("엔터를 누르세요")

