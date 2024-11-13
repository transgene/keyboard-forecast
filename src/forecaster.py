import datetime
import os
import sys
from datetime import timedelta

import requests

import datastore
import daytime
import forelogger as log
import keyboard
import location
import weather
from events import Event, EventListener, IncomingEvent
from forelogger import format_month_day


def validate():
    datastore.validate_config()


def run(event_listener: EventListener):
    while True:
        try:
            _do_run(event_listener)
        except keyboard.DisconnectedException:
            log.warn("Sleeping until the keyboard is reconnected")
            event_listener.sleep_forever()
        except Exception as e:
            log.error(f"Unhandled exception: {str(e)}")
            _retry_fault(event_listener)


def _do_run(event_listener: EventListener):
    while True:
        current_location = location.get()
        daytime_info = daytime.get_today()
        now = daytime.now()

        log.info(f"We are in {current_location}")
        log.info(
            f"Today is {format_month_day(now)}: sunrise at {daytime_info.sunrise}, sunset at {daytime_info.sunset}"
        )

        sunrise = daytime_info.sunrise
        sunset = daytime_info.sunset
        if now < sunrise:
            log.info(f"{now} is too early - entering sleep state")
            if _sleep_until(event_listener, sunrise):
                continue

        next_run = daytime.now()
        while next_run < sunset:
            _check_weather(current_location)
            next_run = next_run + timedelta(minutes=datastore.get_weather_check_interval_minutes())
            if _sleep_until(event_listener, next_run):
                break
        else:
            log.info(f"The sun is down - turning on the backlight and entering sleep state")
            keyboard.toggle_backlight(True, force=True)
            daytime.get_tomorrow()  # So we won't waste time tomorrow morning
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            _sleep_until(event_listener, midnight)


def _check_weather(cur_loc: location.Location):
    check_result = weather.is_dark(cur_loc)
    if check_result:
        keyboard.toggle_backlight(True)
    else:
        keyboard.toggle_backlight(False)


def _sleep_until(event_listener: EventListener, until: datetime.datetime) -> bool:
    log.info(f"Sleeping until {until}")
    wake_event = event_listener.sleep_until(until)
    _process_termination(wake_event)
    if wake_event is not None:
        log.info(
            f"Woke up prematurely at {daytime.now()} because of {wake_event.type} event."
            f"{'Restarting the main loop' if wake_event.restart else 'Continuing execution'}"
        )
        return wake_event.restart
    else:
        log.info(f"Woke up at {daytime.now()}. Continuing execution")
    return False


def _retry_fault(event_listener: EventListener):
    minutes_to_sleep = 5  # TODO exponentially increase the timeout
    sleep_duration = timedelta(minutes=minutes_to_sleep)
    log.info(f"Sleeping for {minutes_to_sleep} minutes and restarting the main loop")
    wake_event = event_listener.sleep_for(sleep_duration)
    _process_termination(wake_event)
    if wake_event is not None:
        log.info(f"Fault timer ended prematurely at {daytime.now()} because of {wake_event.type} event")


def _process_termination(event: Event | None):
    if event is not None and event.type == IncomingEvent.TERMINATION:
        log.info("Received termination event. Exiting...")
        sys.exit(0)
