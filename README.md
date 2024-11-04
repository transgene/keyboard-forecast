# Keyboard Forecast
## A simple service to manage my keyboard's backlight by weather forecast and time of day

# Build

1. Globally install `pywin32`: `python -m pip install --upgrade pywin32` (as admin)
2. Create virtual env
3. Install the dependencies: `pip install -r .\requirements.txt`
4. Build the executable: `python .\package.py --clean`
5. Copy `keebforecast.exe` to the installation folder. Any folder will do - e.g. `%LocalAppData%\Programs\keyboard-forecast`
6. Install the service (as admin):
    - `cd %LocalAppData%\Programs\keyboard-forecast`
    - `.\keebforecast.exe --startup delayed install`
    - `.\keebforecast.exe start`
