@echo off
title Refresh YouTube Token - Long Sleepy Story
cd /d "%~dp0"
echo ====================================================================
echo  REFRESH YOUTUBE TOKEN: Long Sleepy Story (@longsleepystory)
echo ====================================================================
echo.
echo 1. A browser window will open.
echo 2. Sign in and select 'Long Sleepy Story' brand channel.
echo 3. Click 'Advanced' -> 'Go to app (unsafe)' -> 'Allow'.
echo.
python get_youtube_token.py
echo.
echo ====================================================================
echo Next step: Copy the token above and update YOUTUBE_OAUTH_TOKEN in:
echo https://github.com/Terryohana/-long-sleepy-story/settings/secrets/actions
echo ====================================================================
echo.
pause
