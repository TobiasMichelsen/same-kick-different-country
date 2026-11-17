@echo off
rem Opens the annotation tool for one annotator.
rem Windows: double-click this file (it asks which annotator you are), or from a terminal:
rem     annotate.bat 2            annotate.bat annotator-2
rem (Mac users: annotate.command instead.)

cd /d "%~dp0"
echo === Techno annotator ===

rem With an argument we were started from a terminal: no "press any key" pauses.
set "P=pause"
set "n=%~1"
if not "%n%"=="" (
  set "P=rem"
  goto normalise
)
set /p "n=Which annotator are you? Type 1, 2 or 3 and press Enter: "

:normalise
rem "annotator-2", "annotator_2" or "2" -> "2"
set "n=%n:annotator-=%"
set "n=%n:annotator_=%"
set "n=%n:annotator=%"
if "%n%"=="1" goto ok
if "%n%"=="2" goto ok
if "%n%"=="3" goto ok
echo Please type 1, 2 or 3 (for example: annotate.bat 2).
%P%
exit /b 1

:ok
set "sheet=annotator_%n%"

rem Get the latest sheets (only if this folder is a git checkout).
if not exist ".git" goto pulled
where git >nul 2>nul
if errorlevel 1 goto pulled
echo Getting the latest version...
git pull --ff-only
if errorlevel 1 echo Couldn't update automatically (you probably have unsaved local changes). Carrying on with the files you have.
:pulled

if not exist "annotations\sheets\%sheet%.csv" (
  echo Can't find annotations\sheets\%sheet%.csv
  %P%
  exit /b 1
)

rem Preferred: a small local server (Python standard library) that opens the sheet
rem automatically and saves straight into it, in any browser. Runs until Ctrl+C.
set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY (
  where py >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if defined PY (
  %PY% src\02_annotation\04_serve_annotator.py %sheet%
  %P%
  exit /b 0
)

rem Fallback without Python: open the page as a file; the sheet has to be picked by hand.
echo Python 3 not found, so the sheet can't open automatically.
set "here=%CD:\=/%"
set "url=file:///%here%/annotations/annotator.html?sheet=%sheet%"

rem Chrome or Edge can save straight back into the CSV.
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>nul && goto chrome
reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>nul && goto chrome
start "" msedge "%url%"
goto opened
:chrome
start "" chrome "%url%"
:opened

echo.
echo The tool is open in your browser.
echo Click "choose file..." and pick: annotations\sheets\%sheet%.csv
echo When you're done: save, then commit and push your sheet.
%P%
