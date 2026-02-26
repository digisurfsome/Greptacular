@echo off
echo ===================================
echo  VoxType Setup (Windows)
echo ===================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

:: Create venv
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

:: Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

:: Check for GPU
echo.
echo Checking for NVIDIA GPU...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo No NVIDIA GPU detected. Using CPU mode (medium model recommended).
    echo If you have a GPU, install CUDA toolkit and run:
    echo   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo NVIDIA GPU detected! Installing PyTorch with CUDA...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    echo GPU mode enabled - large-v3 model recommended for best accuracy.
)

echo.
echo ===================================
echo  Setup complete!
echo ===================================
echo.
echo To start VoxType:
echo   venv\Scripts\activate
echo   python main.py
echo.
echo To list microphones:
echo   python main.py --list-devices
echo.
echo Hotkeys:
echo   Ctrl+Shift+Space = Toggle on/off
echo   Ctrl+Shift+P     = Pause/resume
echo.
pause
