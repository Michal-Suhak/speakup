@echo off
rem Messages are ASCII on purpose: cmd shows Polish letters wrongly with the default code page.
setlocal
title SpeakUp
set "SPEAKUP_DIR=%USERPROFILE%\SpeakUp"
set "SPEAKUP_ZIP=https://github.com/Michal-Suhak/speakup/archive/refs/heads/main.zip"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo Pobieram najnowsza wersje SpeakUp...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $dir=$env:SPEAKUP_DIR; $tmp=Join-Path $env:TEMP 'speakup-update'; if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }; New-Item -ItemType Directory $tmp | Out-Null; $zip=Join-Path $tmp 'main.zip'; Invoke-WebRequest $env:SPEAKUP_ZIP -OutFile $zip -UseBasicParsing; Expand-Archive $zip $tmp; New-Item -ItemType Directory -Force $dir | Out-Null; Get-ChildItem $dir -Force | Where-Object { $_.Name -notin '.env','profiles','.venv' } | Remove-Item -Recurse -Force; Get-ChildItem (Join-Path $tmp 'speakup-main') -Force | Where-Object { $_.Name -ne 'start.cmd' } | Copy-Item -Destination $dir -Recurse -Force; Remove-Item $tmp -Recurse -Force"
if errorlevel 1 (
  if not exist "%SPEAKUP_DIR%\app.py" (
    echo Nie udalo sie pobrac SpeakUp. Sprawdz internet i sprobuj jeszcze raz.
    goto :fail
  )
  echo Nie udalo sie pobrac nowej wersji, uruchamiam poprzednia.
)
cd /d "%SPEAKUP_DIR%"

where uv >nul 2>nul || (
  echo Instaluje uv, to potrwa chwile...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
)
where uv >nul 2>nul || (
  echo Nie udalo sie zainstalowac uv. Sprawdz internet i sprobuj jeszcze raz.
  goto :fail
)

echo Przygotowuje aplikacje, za pierwszym razem to potrwa kilka minut...
uv sync --quiet || goto :fail

if exist .env goto :run
:ask_key
echo.
set "KEY="
set /p "KEY=Wklej klucz OpenAI (zaczyna sie od sk-) i nacisnij Enter: "
if not defined KEY goto :ask_key
> .env echo OPENAI_API_KEY=%KEY%
uv run python config.py || (
  del .env
  echo Klucz nie dziala. Uruchom SpeakUp jeszcze raz i wklej poprawny klucz.
  goto :fail
)

:run
echo.
echo SpeakUp dziala. Przegladarka otworzy sie sama.
echo Zeby wylaczyc SpeakUp, zamknij to okno.
start "" /min cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:8000"
uv run uvicorn app:app --port 8000
echo SpeakUp sie zatrzymal.

:fail
echo.
pause
