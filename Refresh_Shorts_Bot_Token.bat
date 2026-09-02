@echo off
title Refresh YouTube Token - Shorts Bot
cd /d "%~dp0"
echo ====================================================================
echo  REFRESH YOUTUBE TOKEN: YouTube Shorts Bot (@apponthespot)
echo ====================================================================
echo.
echo 1. A browser window will open.
echo 2. Sign in and select 'App On The Spot' channel.
echo 3. Click 'Advanced' -> 'Go to app (unsafe)' -> 'Allow'.
echo.
python "C:\Users\Dell\.gemini\antigravity\brain\52720948-acc5-40b5-9091-aa6f4d1e2fd7\scratch\refresh_shorts_bot_token.py"
echo.
echo ====================================================================
echo Next step: Copy the Base64 token above and update GOOGLE_TOKEN_PICKLE_BASE64 in:
echo https://github.com/Terryohana/YouTube-Shorts-Bot/settings/secrets/actions
echo ====================================================================
echo.
pause
