REM You must have virtualenv installed, and the virtualenv command in your path for this to work.
REM This should be run from the project directory, not inside the socialprofile dir
REM the pypm command below assumes you are using the ActiveState Community Python installer from here:
REM http://www.activestate.com/activepython/downloads
pypm --non-interactive distribute
pypm --non-interactive install pip
pypm --non-interactive install virtualenv
pypm --non-interactive install pil
virtualenv --system-site-packages --distribute .env
call .virtualenv\Scripts\activate.bat
pip install -r requirements_dev.txt