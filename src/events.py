import datetime
import enum
import queue

import daytime


class IncomingEvent(enum.Enum):
    TERMINATION = 0  # Termination event has the highest priority
    SYSTEM_RESUME = 1
    KEYBOARD_CONNECTED = 2


class Event:
    def __init__(self, type: IncomingEvent, restart: bool = True):
        self.type = type
        self.restart = restart


class EventListener:
    def __init__(self, queue: queue.PriorityQueue):
        self.__queue = queue

    def sleep_until(self, until: datetime.datetime) -> Event | None:
        sleep_timeout = until - daytime.now()
        try:
            incoming_event = self.__queue.get(timeout=sleep_timeout.total_seconds())
            return Event(incoming_event)
        except queue.Empty:
            pass

    def sleep_for(self, duration: datetime.timedelta) -> Event | None:
        try:
            incoming_event = self.__queue.get(timeout=duration.total_seconds())
            return Event(incoming_event)
        except queue.Empty:
            pass

    def sleep_forever(self) -> Event:
        return Event(self.__queue.get())
