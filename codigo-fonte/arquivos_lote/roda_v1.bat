@echo off
REM ============================================================
REM ARQUIVO : E:\RODA_V1.BAT (Eleicao Oficial 1o Turno - disco15)
REM ============================================================
cd %FI%\aplic
%FI%\virtuos\log 30
%FI%\virtuos\gecho &&Iniciando Eleicao Oficial 1o Turno ... /I
%FI%\virtuos\arqcmp %FI%\estgeral.ctr %FI%\aplic\estados\disco15 1 1 1 > nul
if errorlevel 1 goto erro_estado
%FI%\aplic\vvota.exe
if errorlevel 2 goto erro_fatal
if errorlevel 1 goto recupera_bu
%FI%\aplic\desbloq -z > nul
goto fim_runner

:recupera_bu
%FI%\aplic\vred.exe
goto fim_runner

:erro_estado
%FI%\virtuos\gecho &&ERRO: Estado incompativel com disco15!
goto fim_runner

:erro_fatal
%FI%\virtuos\gecho &&ERRO CRITICO em vvota.exe!

:fim_runner
cd %FI%\
