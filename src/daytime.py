from datetime import datetime, timedelta, timezone

import datastore


class Daytime:

    def __init__(self, daytime_dict: dict):
        self.__daytime = daytime_dict

    @property
    def sunrise(self) -> datetime:
        return _to_datetime(self.__daytime["sunrise"])

    @property
    def sunset(self) -> datetime:
        return _to_datetime(self.__daytime["sunset"])


def _to_datetime(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


def get_today() -> Daytime:
    daytime_dict = datastore.get_daytime(now())
    return Daytime(daytime_dict)


def get_tomorrow() -> Daytime:
    tomorrow = now() + timedelta(days=1)
    daytime_dict = datastore.get_daytime(tomorrow)
    return Daytime(daytime_dict)


def now() -> datetime:
    return datetime.now(timezone.utc)
