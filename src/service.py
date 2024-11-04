import sys
import threading
import win32serviceutil

import servicemanager
import win32event
import win32service

import forecaster as forecaster
from forelogger import error


class KeyboardForecastService(win32serviceutil.ServiceFramework):

    _svc_name_ = "KeyboardForecastService"
    _svc_display_name_ = "Keyboard Forecast Service"
    _svc_description_ = "Controls the backlight based on the time of day and the current weather forecast"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        try:
            forecaster.validate()
        except Exception as e:
            error(str(e))
            raise e

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ""))
        app_thread = threading.Thread(target=forecaster.main, daemon=True) # TODO signal the thread to stop instead
        app_thread.start()
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STOPPED, (self._svc_name_, ""))

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)


if __name__ == "__main__":
    # win32serviceutil.HandleCommandLine(KeyboardForecastService)
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(KeyboardForecastService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(KeyboardForecastService)