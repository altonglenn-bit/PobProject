@echo off
setlocal

echo ================================================================
echo POB AI PROJECT - SMOKE TEST
echo ================================================================

echo [1/4] Python version
python --version
if errorlevel 1 goto :fail

echo.
echo [2/4] Validate archetypes
python validate_archetypes.py
if errorlevel 1 goto :fail

echo.
echo [3/4] Run recommendation regression tests
python run_regression_tests.py
if errorlevel 1 goto :fail

echo.
echo [4/4] Run end-to-end regression tests
python run_regression_tests.py --e2e
if errorlevel 1 goto :fail

echo.
echo ================================================================
echo SMOKE TEST PASSED
echo ================================================================
exit /b 0

:fail
echo.
echo ================================================================
echo SMOKE TEST FAILED
echo ================================================================
exit /b 1
