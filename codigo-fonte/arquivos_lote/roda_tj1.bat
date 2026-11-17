@echo off
REM ============================================================
REM ARQUIVO : E:\RODA_TJ1.BAT (Treinamento Justificativa 1o Turno - disco5)
REM ============================================================
cd %FI%\aplic
%FI%\virtuos\log 30
%FI%\virtuos\gecho &&Iniciando Treinamento Justificativa 1o Turno ... /I
%FI%\virtuos\arqcmp %FI%\estgeral.ctr %FI%\aplic\estados\disco5 1 1 1 > nul
if errorlevel 1 goto erro_estado
%FI%\aplic\vjustif.exe
if errorlevel 2 goto erro_fatal
if errorlevel 1 goto recupera_bu
%FI%\aplic\desbloq -w > nul
goto fim_runner

:recupera_bu
%FI%\aplic\vred.exe
goto fim_runner

:erro_estado
%FI%\virtuos\gecho &&ERRO: Estado incompativel com disco5!
goto fim_runner

:erro_fatal
%FI%\virtuos\gecho &&ERRO CRITICO em vjustif.exe!

:fim_runner
cd %FI%\
