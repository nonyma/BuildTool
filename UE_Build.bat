@echo off
chcp 65001 >nul
REM === Unreal C++ 컴파일 확인용 빌드 스크립트 ===

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

set "PROJECT_PATH=%~1"
set "PROJECT_NAME=%~2"
set "BRANCH_NAME=%~3"

REM === 타겟: 기본적으로 Editor 빌드만 ===
set "TARGET_NAME=%PROJECT_NAME%Editor"
set "TARGET_PLATFORM=Win64"
set "TARGET_CONFIG=Development"
set "UE_PATH=C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe"
set "UPROJECT_PATH=%PROJECT_PATH%\%PROJECT_NAME%.uproject"
set "LOG_PATH=%PROJECT_PATH%\build.log"
set "FIX_PATH=%PROJECT_PATH%\codex_fix.txt"

echo [빌드 시작] %DATE% %TIME%
echo 프로젝트 경로: %PROJECT_PATH%
echo 프로젝트 이름: %PROJECT_NAME%
echo 브랜치: %BRANCH_NAME%
echo ----------------------------------------

REM === 빌드 실행 (컴파일 확인만) ===
"%UE_PATH%" %TARGET_NAME% %TARGET_PLATFORM% %TARGET_CONFIG% "%UPROJECT_PATH%" -build > "%LOG_PATH%" 2>&1

REM === 빌드 결과 체크 ===
IF %ERRORLEVEL% NEQ 0 (
    echo [빌드 실패] Codex 컨텍스트 준비
    if exist "%FIX_PATH%" del /f "%FIX_PATH%"
    findstr /i /c:"error" "%LOG_PATH%" > "%FIX_PATH%"
    echo. >> "%FIX_PATH%"
    echo --- Full context from build log --- >> "%FIX_PATH%"
    type "%LOG_PATH%" >> "%FIX_PATH%"
    cd /d "%PROJECT_PATH%"
    git add codex_fix.txt
    git commit -m "Add Codex context after build failure"
    git push origin "%BRANCH_NAME%"
    exit /b 1
)

REM === 빌드 성공 시 codex_fix.txt 제거 ===
if exist "%FIX_PATH%" (
    cd /d "%PROJECT_PATH%"
    git rm -f --ignore-unmatch codex_fix.txt
    git commit -m "Remove Codex context after successful build"
    git push origin "%BRANCH_NAME%"
)

echo [빌드 성공] %DATE% %TIME%
exit /b 0
