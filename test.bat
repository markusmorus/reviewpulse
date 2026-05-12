@echo off
chcp 65001 > nul
cd /d "C:\xampp\htdocs\dashboard\progetti\reviewpulse"

echo ============================================
echo     ReviewPulse - Avvio Test
echo ============================================

echo [1] Attivazione ambiente virtuale...
call venv\Scripts\activate

echo [2] Cancellazione database (test pulito)...
del /q app\reviews.db 2>nul
if exist app\reviews.db (
    echo ERRORE: Impossibile cancellare il database. Chiudi eventuali altri terminali.
    pause
    exit /b
) else (
    echo Database cancellato con successo.
)

echo [3] Avvio applicazione...
start "ReviewPulse Flask" cmd /k "cd /d C:\xampp\htdocs\dashboard\progetti\reviewpulse && venv\Scripts\activate && python run.py"

echo [4] Attendi 5 secondi per l'avvio del server...
timeout /t 5 /nobreak > nul

echo [5] Forzatura controllo recensioni...
echo from app import create_app; from app.scheduler import check_all_reviews; app = create_app(); check_all_reviews(app) | python

echo ============================================
echo     Test completato!
echo     Apri http://127.0.0.1:5000 nel browser
echo     Accedi con admin@reviewpulse.com / admin123
echo ============================================
pause