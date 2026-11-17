@echo off
%FI%\desbloq -m > nul
copy %FI%\setup.mnt %FI%\SETUP.BAT /v > nul
del %FI%\setup.mnt > nul
