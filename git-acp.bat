@echo off
setlocal
:: Usage: & ".\git-acp.bat" "CommitMessage"
:: This script stages, commits, and pushes changes to the current git branch.
:: Check if commit message was provided
if "%~1"=="" (
    echo Usage: %0 "commit message"
    echo Example: %0 "Added new feature"
    exit /b 1
)

:: Store the commit message
set "commit_msg=%~1"

echo Adding all changes...
git add .
if errorlevel 1 (
    echo Error: Failed to add files
    exit /b 1
)

echo Committing changes...
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo Error: Failed to commit changes
    exit /b 1
)

echo Getting current branch...
for /f "tokens=*" %%i in ('git branch --show-current') do set current_branch=%%i

echo Pushing to remote origin/%current_branch%...
git push origin %current_branch%
if errorlevel 1 (
    echo Error: Failed to push to remote
    exit /b 1
)

echo Successfully added, committed, and pushed changes!
echo Commit message: "%commit_msg%"