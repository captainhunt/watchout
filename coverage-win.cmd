@echo off
rem this script runs all unit tests through coverage and creates an html report in htmlcov/index.html
coverage erase
echo "run all unit tests"
for /R %%i in (test_*.py) do (
  coverage run -a "%%i"
)
echo "update coverage index, look at htmlcov/index.html"
coverage html --omit=test_*