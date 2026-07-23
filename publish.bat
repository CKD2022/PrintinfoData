@echo off
chcp 65001 >nul
echo ========================================
echo   印务生产数据 - 自动发布到 GitHub
echo ========================================
echo.

echo [1/4] 正在生成网站...
D:\djangoProject\untitled\venv\Scripts\python.exe build_增加真人验证功能_自动生成验证背景.py
if %errorlevel% neq 0 (
    echo [错误] 生成失败！
    pause
    exit /b 1
)
echo [完成] 网站生成成功
echo.

echo [2/4] 正在添加文件...
git add .
echo [完成] 文件已暂存
echo.

set /p COMMIT_MSG="请输入提交说明（直接回车使用默认）: "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=更新报告网站
git commit -m "%COMMIT_MSG%"
echo.

echo [3/4] 正在推送到 GitHub...
git push
if %errorlevel% neq 0 (
    echo [错误] 推送失败，请检查网络或 Git 配置！
    pause
    exit /b 1
)
echo [完成] 推送成功
echo.

echo ========================================
echo   网站已发布！
echo ========================================
pause