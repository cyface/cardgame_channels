REM This updates an already in-place virtualenv to match the current requirements_dev.txt file.
REM It will not upgrade package versions.
call .virtualenv\Scripts\activate.bat
pip install -r requirements_dev.txt