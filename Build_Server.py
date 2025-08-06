from flask import Flask, request, jsonify
import subprocess
import os
from openai import OpenAI

print("OPENAI_API_KEY_BUILDSERVER =", os.environ.get("OPENAI_API_KEY_BUILDSERVER"))
app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY_BUILDSERVER"))

@app.route("/ue_build", methods=["POST"])
def build():
    data = request.json
    project_path = data.get("project_path")
    project_name = data.get("project_name")
    branch_name = data.get("branch_name")  # 브랜치명 추가

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

        return jsonify({
            "status": "build failed",
            "fix_suggestion": fix_file_path
        }), 200

    return jsonify({"status": "build succeeded"}), 200


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=9000)
    except Exception as e:
        print("서버 실행 중 에러:", e)
        input("엔터를 누르세요")