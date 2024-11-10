import queue
import re
import sys
import threading
import typing

import servicemanager
import win32con
import win32event
import win32gui
import win32gui_struct
import win32service
import win32serviceutil
from servicemanager import EVENTLOG_INFORMATION_TYPE, PYS_SERVICE_STARTED, PYS_SERVICE_STOPPED
from win32con import DBT_DEVICEARRIVAL, DBT_DEVICEREMOVECOMPLETE, PBT_APMRESUMESUSPEND

import forecaster as forecaster
import forelogger as log
import keyboard
from events import EventListener, IncomingEvent

GUID_DEVINTERFACE_USB_DEVICE = "{A5DCBF10-6530-11D2-901F-00C04FB951ED}"


class KeyboardForecastService(win32serviceutil.ServiceFramework):

    _svc_name_ = "KeyboardForecastService"
    _svc_display_name_ = "Keyboard Forecast Service"
    _svc_description_ = "Controls the backlight based on the time of day and the current weather forecast"

    def __init__(self, args):
        try:
            self.__init_service(args)
            forecaster.validate()
        except Exception as e:
            log.error(f"Exception during initialization! {e}")
            if self.hWaitStop is not None:
                win32event.SetEvent(self.hWaitStop)

    def __init_service(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        event_filter = win32gui_struct.PackDEV_BROADCAST_DEVICEINTERFACE(GUID_DEVINTERFACE_USB_DEVICE)
        self.win_event_handle = win32gui.RegisterDeviceNotification(
            self.ssh, event_filter, win32con.DEVICE_NOTIFY_SERVICE_HANDLE
        )
        self.__queue = queue.PriorityQueue()

    def GetAcceptedControls(self):
        control_events = win32serviceutil.ServiceFramework.GetAcceptedControls(self)
        control_events |= (
            win32service.SERVICE_CONTROL_DEVICEEVENT
            | win32service.SERVICE_ACCEPT_POWEREVENT
            | win32service.SERVICE_ACCEPT_SESSIONCHANGE
        )
        return control_events

    def SvcOtherEx(self, control, event_type, data):
        if control == win32service.SERVICE_CONTROL_DEVICEEVENT:
            self.__handle_device_event(event_type, data)
        elif control == win32service.SERVICE_CONTROL_POWEREVENT:
            self.__handle_power_event(event_type)

    @typing.no_type_check
    def __handle_device_event(self, event_type, data):
        info = win32gui_struct.UnpackDEV_BROADCAST(data)
        if info.name is not None:
            device_id_match = re.search(r"#(.*?)#", info.name)
            if device_id_match is not None and self.__is_keyboard(device_id_match.group(1)):
                if event_type == DBT_DEVICEARRIVAL:
                    log.info("Keyboard connected, sending event")
                    self.__queue.put(IncomingEvent.KEYBOARD_CONNECTED)
                elif event_type == DBT_DEVICEREMOVECOMPLETE:
                    log.info("Keyboard disconnected, expecting forecaster to go to sleep")
                else:
                    log.info(f"Unknown keyboard event type: {event_type}")

    def __is_keyboard(self, device_id: str) -> bool:
        return keyboard.VENDOR_ID in device_id and keyboard.PRODUCT_ID in device_id

    def __handle_power_event(self, event_type):
        if event_type == PBT_APMRESUMESUSPEND:
            log.info("Resumed from sleep, sending event")
            self.__queue.put(IncomingEvent.SYSTEM_RESUME)

    def SvcDoRun(self):
        servicemanager.LogMsg(EVENTLOG_INFORMATION_TYPE, PYS_SERVICE_STARTED, (self._svc_name_, ""))
        log.info("Starting forecaster")
        forecaster_thread = threading.Thread(target=forecaster.run, args=(EventListener(self.__queue),))
        forecaster_thread.start()

        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        log.info("Stopping forecaster")
        self.__queue.put(IncomingEvent.TERMINATION)
        forecaster_thread.join()
        servicemanager.LogMsg(EVENTLOG_INFORMATION_TYPE, PYS_SERVICE_STOPPED, (self._svc_name_, ""))

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)


if __name__ == "__main__":
    # This sequence is crucial if we want to package the service with pyinstaller
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(KeyboardForecastService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(KeyboardForecastService)
