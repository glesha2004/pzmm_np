@echo off
echo Закрытие всех процессов SteamCMD.exe...

:: Завершение всех процессов steamcmd.exe
taskkill /IM steamcmd.exe /F

echo Все процессы SteamCMD.exe завершены.
pause
