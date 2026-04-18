@echo off
REM ============================================================
REM  build.bat  –  compiles run_all.py into a standalone EXE
REM  Run this ONCE on your dev machine before zipping.
REM ============================================================

echo [1/3] Installing / updating required packages...
pip install pyinstaller inspyred numpy
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python is in your PATH.
    pause
    exit /b 1
)

echo.
echo [2/3] Compiling run_all.py with PyInstaller...
pyinstaller ^
    --onefile ^
    --console ^
    --name run_all ^
    --hidden-import=inspyred ^
    --hidden-import=inspyred.ec ^
    --hidden-import=inspyred.ec.analysis ^
    --hidden-import=inspyred.ec.observers ^
    --hidden-import=inspyred.ec.terminators ^
    --hidden-import=numpy ^
    --hidden-import=numpy.random ^
    run_all.py

if errorlevel 1 (
    echo ERROR: PyInstaller failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo [3/3] Copying EXE to project root...
copy /Y dist\run_all.exe run_all.exe

echo.
echo ============================================================
echo  BUILD SUCCESSFUL.
echo  run_all.exe is ready in this folder.
echo  You can now zip the entire master folder and send it.
echo ============================================================
pause