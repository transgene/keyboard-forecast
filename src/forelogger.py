import servicemanager

def info(msg: str):
    servicemanager.LogMsg(
        servicemanager.EVENTLOG_INFORMATION_TYPE, 
        0xF000,  #  generic message
        (msg, "")
    )

def error(msg: str):
    servicemanager.LogMsg(
        servicemanager.EVENTLOG_ERROR_TYPE, 
        0xF000, #  generic message
        (msg, "")
    )
