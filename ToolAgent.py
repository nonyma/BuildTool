import argparse
import subprocess
import os

def run_codex_cli(project_path, prompt_path):
    # 프롬프트 파일 읽기
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    wsl_codex_cmd = [
        'wsl', '-e', 'bash', '-i', '-c',
        'codex',
        '--full-auto',
        '-C', project_path,
        prompt
    ]
    print("[ToolAgent] Codex CLI 실행:", " ".join(wsl_codex_cmd))
    result = subprocess.run(wsl_codex_cmd, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    return result.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_path", type=str, required=True)
    parser.add_argument("--prompt_path", type=str, required=True)
    args = parser.parse_args()
    rc = run_codex_cli(args.project_path, args.prompt_path)
    exit(rc)
