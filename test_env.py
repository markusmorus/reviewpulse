@echo off
chcp 65001 > nul
cd /d "C:\xampp\htdocs\dashboard\progetti\reviewpulse"

echo ============================================
echo     ReviewPulse - Test con attesa
echo ============================================

echo [1] Attivazione ambiente virtuale...
call venv\Scripts\activate

echo [2] Cancellazione database (test pulito)...
del /q app\reviews.db 2>nul
if exist app\reviews.db (
    echo ERRORE: Impossibile cancellare il database. Chiudi altri terminali.
    pause
    exit /b
) else (
    echo Database cancellato.
)

echo [3] Avvio Flask in una nuova finestra...
start "ReviewPulse Flask" cmd /k "cd /d C:\xampp\htdocs\dashboard\progetti\reviewpulse && venv\Scripts\activate && python run.py"

echo [4] Attendo che il server sia pronto (porta 5000)...
:wait
timeout /t 2 /nobreak > nul
netstat -ano | findstr ":5000.*LISTENING" > nul
if %errorlevel% neq 0 goto wait
echo Server Flask in ascolto su http://127.0.0.1:5000

echo [5] Apro il browser...
start http://127.0.0.1:5000

echo.
echo ============================================
echo Ora nella dashboard:
echo  - Accedi (admin@reviewpulse.com / admin123)
echo  - Aggiungi un locale (Place ID o URL)
echo ============================================
echo.

pause

echo [6] Eseguo controllo recensioni...
python force_check.py

echo [7] Ricarico la dashboard...
start http://127.0.0.1:5000/dashboard

echo.
echo Controllo completato! Controlla la dashboard.
pause