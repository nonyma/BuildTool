@echo off
chcp 65001 >nul   
REM 코드페이지를 UTF-8로 변경

REM === 파라미터 확인 ===
IF "%~1"=="" (
    echo [오류] 프로젝트 경로를 입력하세요.
    exit /b 1
)
IF "%~2"=="" (
    echo [오류] 프로젝트 이름을 입력하세요.
    exit /b 1
)
IF "%~3"=="" (
    echo [오류] 브랜치명을 입력하세요.
    exit /b 1
)

set PROJECT_PATH=%~1
set PROJECT_NAME=%~2
set BRANCH_NAME=%~3

set UE_PATH="C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe"
set TARGET_PLATFORM=Win64
set TARGET_CONFIG=Development
set LOG_PATH=%PROJECT_PATH%\build.log
set FIX_PATH=%PROJECT_PATH%\codex_fix.txt

echo [빌드 시작] %DATE% %TIME%
echo 프로젝트 경로: %PROJECT_PATH%
echo 프로젝트 이름: %PROJECT_NAME%
echo 브랜치: %BRANCH_NAME%
echo ----------------------------------------

REM === 빌드 실행 ===
%UE_PATH% %TARGET_CONFIG% %TARGET_PLATFORM% "%PROJECT_PATH%\%PROJECT_NAME%.uproject" -build > "%LOG_PATH%" 2>&1

REM === 빌드 결과 체크 ===
IF %ERRORLEVEL% NEQ 0 (
    echo [빌드 실패] Codex 컨텍스트 준비
    REM 기존 codex_fix.txt 삭제
    if exist "%FIX_PATH%" del /f "%FIX_PATH%"
    REM 빌드 로그에서 에러 라인만 추출
    findstr /i /c:"error" "%LOG_PATH%" > "%FIX_PATH%"
    echo. >> "%FIX_PATH%"
    echo --- Full context from build log --- >> "%FIX_PATH%"
    type "%LOG_PATH%" >> "%FIX_PATH%"
    REM Git 처리 (codex_fix.txt만)
    cd /d %PROJECT_PATH%
    git add codex_fix.txt
    git commit -m "Add Codex context after build failure"
    git push origin %BRANCH_NAME%
    exit /b 1
)

REM === 빌드 성공 시 codex_fix.txt 제거 ===
if exist "%FIX_PATH%" (
    cd /d %PROJECT_PATH%
    git rm -f --ignore-unmatch codex_fix.txt
    git commit -m "Remove Codex context after successful build"
    git push origin %BRANCH_NAME%
)

echo [빌드 성공] %DATE% %TIME%
exit /b 0
