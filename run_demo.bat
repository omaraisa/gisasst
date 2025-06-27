@echo off
echo Starting GIS Copilot Desktop Demo...
echo.

cd /d "e:\GISApp\AI\GIS Assistant\gis_copilot_desktop"

echo Testing Python availability...
python --version
echo.

echo Running interactive demo...
python interactive_demo.py

echo.
echo Demo completed.
pause
