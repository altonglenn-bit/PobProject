@echo off
setlocal

echo ========================================================
echo FULL PROJECT CHECK
echo ========================================================
echo.

echo [1/4] pytest
pytest -q
if errorlevel 1 (
    echo.
    echo FAILED: pytest
    exit /b 1
)

echo.
echo [2/4] validate_archetypes.py
python validate_archetypes.py
if errorlevel 1 (
    echo.
    echo FAILED: validate_archetypes.py
    exit /b 1
)

echo.
echo [3/4] run_regression_tests.py
python run_regression_tests.py
if errorlevel 1 (
    echo.
    echo FAILED: run_regression_tests.py
    exit /b 1
)

echo.
echo [4/4] run_regression_tests.py --e2e
python run_regression_tests.py --e2e
if errorlevel 1 (
    echo.
    echo FAILED: run_regression_tests.py --e2e
    exit /b 1
)

echo.
echo ========================================================
echo ALL CHECKS PASSED
echo ========================================================
exit /b 0
