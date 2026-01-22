@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set "PYTHON_EXE=C:\develop\tools\python3_14\python3.exe"
echo 使用指定 Python: %PYTHON_EXE%

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
    echo [提示] 未找到指定路径的 Python，尝试使用系统默认 python...
)


echo ======================================================
echo   Win10 优化工具 - 自动打包脚本 (PyInstaller)
echo ======================================================
echo.

:: 检查是否安装了 PyInstaller
"%PYTHON_EXE%" -m pip show pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未找到 pyinstaller，正在尝试通过 pip 安装...
    "%PYTHON_EXE%" -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [错误] 安装 pyinstaller 失败，请检查网络和 Python 环境。
        pause
        exit /b 1
    )
)

echo [1/3] 清理旧的构建目录...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist "Win10优化工具.spec" del /f /q "Win10优化工具.spec"

echo [2/3] 开始打包 (单文件模式, 无控制台)...
:: 注意：如果以后有了图标，可以添加 --icon "ui/icon.ico"
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onefile --windowed ^
    --name "Win10优化工具" ^
    --add-data "config/win10_optimize_profile.json;config" ^
    main.py



if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo [成功] 打包完成！
    echo 可执行文件位于: dist\Win10优化工具.exe
    echo ======================================================
) else (
    echo.
    echo [错误] 打包过程中出现问题，请检查上方日志。
)

pause
