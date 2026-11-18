@echo off
cd /d "%~dp0"
if not exist .build mkdir .build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=.build SPR_IoT.tex
if errorlevel 1 exit /b 1
bibtex .build/SPR_IoT
if errorlevel 1 exit /b 1
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=.build SPR_IoT.tex
if errorlevel 1 exit /b 1
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=.build SPR_IoT.tex
if errorlevel 1 exit /b 1
copy /y .build\SPR_IoT.pdf SPR_IoT.pdf >nul
if errorlevel 1 (
 echo Close SPR_IoT.pdf in its reader, then run this command again.
 exit /b 1
)
del /q .build\SPR_IoT.pdf
