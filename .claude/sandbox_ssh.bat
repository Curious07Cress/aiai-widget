@echo off
REM Sandbox SSH Helper - Run commands on sandbox VM
REM Usage: sandbox_ssh.bat "command to run"

set KEY_PATH=C:/Users/yiv/.ssh/AccessKeyDEVOPSYIVWVBL23215154.pem
set BASTION=ows-148-253-122-84.eu-west-2.compute.outscale.com
set TARGET=10.0.152.241
set USER=root

if "%~1"=="" (
    echo Usage: sandbox_ssh.bat "command"
    echo Example: sandbox_ssh.bat "ps aux | grep python"
    exit /b 1
)

ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 -i "%KEY_PATH%" -o "ProxyCommand=ssh -o StrictHostKeyChecking=no -i %KEY_PATH% -W %%h:%%p %USER%@%BASTION%" %USER%@%TARGET% %*
