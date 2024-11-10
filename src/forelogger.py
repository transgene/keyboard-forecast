import datetime
import enum

import servicemanager


class SinkType(enum.Enum):
    STD_OUT = enum.auto()
    EVENT_LOG = enum.auto()


_SINK_TYPE = SinkType.EVENT_LOG

_EVENT_LOG_GENERIC_MESSAGE_TYPE = 0xF000


class _LogLevel(enum.Enum):
    INFO = enum.auto()
    WARN = enum.auto()
    ERROR = enum.auto()


_LOG_LEVEL_DATA = {
    _LogLevel.INFO: {
        SinkType.STD_OUT: "INFO",
        SinkType.EVENT_LOG: servicemanager.EVENTLOG_INFORMATION_TYPE,
    },
    _LogLevel.WARN: {
        SinkType.STD_OUT: "WARN",
        SinkType.EVENT_LOG: servicemanager.EVENTLOG_WARNING_TYPE,
    },
    _LogLevel.ERROR: {
        SinkType.STD_OUT: "ERROR",
        SinkType.EVENT_LOG: servicemanager.EVENTLOG_ERROR_TYPE,
    },
}


def init(sink_type: SinkType = SinkType.EVENT_LOG):
    global _SINK_TYPE
    _SINK_TYPE = sink_type
    info(f"Logging initialized with type {sink_type}")


def info(msg: str):
    _do_log(_LogLevel.INFO, msg)


def warn(msg: str):
    _do_log(_LogLevel.WARN, msg)


def error(msg: str):
    _do_log(_LogLevel.ERROR, msg)


def format_month_day(date: datetime.date) -> str:
    return date.strftime("%b, %d")


def _do_log(level: _LogLevel, msg: str):
    global _SINK_TYPE
    level_concrete = _LOG_LEVEL_DATA[level][_SINK_TYPE]
    match _SINK_TYPE:
        case SinkType.STD_OUT:
            print(f"[{level_concrete}] {msg}")
        case SinkType.EVENT_LOG:
            servicemanager.LogMsg(level_concrete, _EVENT_LOG_GENERIC_MESSAGE_TYPE, (msg, ""))
