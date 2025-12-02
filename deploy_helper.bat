@echo off
echo ===================================================
echo      SUPER AGENT CLOUD DEPLOYMENT HELPER
echo ===================================================
echo.
echo I have prepared your code for the Cloud.
echo Now we need to upload it to your GitHub.
echo.
echo [STEP 1] Go to https://github.com/new
echo [STEP 2] Create a new repository name (e.g., "super-agent-cloud")
echo [STEP 3] Copy the HTTPS URL (e.g., https://github.com/YourName/super-agent-cloud.git)
echo.
set /p REPO_URL="Paste the Repository URL here: "

echo.
echo Linking to %REPO_URL%...
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main

echo.
echo ===================================================
echo             DEPLOYMENT COMPLETE
echo ===================================================
echo.
echo Now follow the instructions in the Walkthrough to:
echo 1. Enable GitHub Pages
echo 2. Generate your Token
echo 3. Configure Android_App/index.html
echo.
pause
