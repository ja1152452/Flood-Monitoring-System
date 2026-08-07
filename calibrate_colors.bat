@echo off
echo === Color Calibration Tool ===
echo.
echo Make sure your flood marker is visible in the camera
echo You'll calibrate each color band separately:
echo   - Yellow (Monitor level)
echo   - Orange (Alert level) 
echo   - Red (Evacuation level)
echo   - Purple (Critical level)
echo.
pause

cd flood_ai
python 4_tune_colors.py
pause