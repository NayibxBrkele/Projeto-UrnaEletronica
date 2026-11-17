@echo off
xcopy %FI%\temp\aplic\*.* %FI%\aplic\ /v /s > nul
copy %FI%\aplic\marca %FI%\temp\marca /v > nul
