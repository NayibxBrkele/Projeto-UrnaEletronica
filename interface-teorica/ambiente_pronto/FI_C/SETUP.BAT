@echo off
set FI=C:
set FC=D:
set DQ=A:
:inicio
diskfix %FI% /vs > nul
if errorlevel 1 goto TentaRecuperar
ckpack %FI%\raiz.crc %FI%\ > nul
if errorlevel 1 goto ebatger
tipurna > nul
if errorlevel 32 goto urna_invalida
if errorlevel 4 goto ue2000
:ue2000
arqcmp %FI%\estgeral.ctr %FI%\aplic\estados\estados 1 0 0 > nul
call e:\roda_v1.bat
goto fim
:TentaRecuperar
:ebatger
:urna_invalida
gecho &&ERRO DE INTEGRIDADE NA URNA!
:fim
