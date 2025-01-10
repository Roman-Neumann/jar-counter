@echo off


%~d0
cd %~dp0..

if exist .venv\ (
    set python_=.venv\Scripts\python.exe
) else (
    set python_=py
)

call %python_% -m jar_counter %1

:: don't change back to previous directory: unlikely that Windows users will 
:: call this file from the terminal
