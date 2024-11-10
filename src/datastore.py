import contextlib
import datetime
import json
import os
from pathlib import Path, PosixPath, WindowsPath

import requests

import forelogger as log
from forelogger import format_month_day


@contextlib.contextmanager
def _config_cwd(path_inside_data_dir: Path | None = None):
    oldpwd = os.getcwd()
    if path_inside_data_dir is None:
        os.chdir(_data_dir())
    else:
        os.chdir(os.path.join(_data_dir(), path_inside_data_dir))
    try:
        yield
    finally:
        os.chdir(oldpwd)


@_config_cwd()
def get_location() -> dict[str, str]:
    loc_file = Path("current_loc.json")
    try:
        with loc_file.open() as f:
            cur_loc_json = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        if isinstance(e, json.JSONDecodeError):
            log.warn("Current location file is not a valid JSON!")
        log.info("Downloading the current location data")
        cur_loc_json = _download_location()
        with loc_file.open("w") as f:
            json.dump(cur_loc_json, f, indent=4)
        log.info("Downloaded and saved current location to file")

    return cur_loc_json


def get_daytime(date: datetime.date) -> dict[str, str]:
    daytime_file = Path(f"{date.month}_{date.day}.json")
    with _config_cwd(_location_dir()):
        try:
            with daytime_file.open() as f:
                daytime_json = json.load(f)
            log.info(f"Loaded daytime data for {format_month_day(date)} from file")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if isinstance(e, json.JSONDecodeError):
                log.warn(f"Daytime file for {format_month_day(date)} is not a valid JSON!")
            log.info(f"Downloading daytime data for {format_month_day(date)}")
            daytime_json = _download_daytime(date, get_location())
            with daytime_file.open("w") as f:
                json.dump(daytime_json, f, indent=4)
            log.info(f"Downloaded and saved daytime data for {format_month_day(date)} to file")

    return daytime_json


def _download_location() -> dict:
    resp = requests.get("https://api.ip2location.io/")
    if resp.status_code != 200:
        raise Exception(
            f"Failed to get current location by the IP address. Error is {resp.status_code} - '{resp.text}'"
        )
    loc_json = resp.json()
    return {
        "country": loc_json["country_name"],
        "city": loc_json["city_name"],
        "lat": loc_json["latitude"],
        "lng": loc_json["longitude"],
    }


def _download_daytime(date: datetime.date, location: dict[str, str]) -> dict[str, str]:
    download_url = (
        "https://api.sunrise-sunset.org/json"
        f"?lat={location["lat"]}&lng={location["lng"]}"
        f"&date={date.year}-{date.month}-{date.day}&formatted=0"
    )
    resp = requests.get(download_url)
    if resp.status_code != 200:
        raise Exception(
            f"Failed to get daytime data for {format_month_day(date)}. Error is {resp.status_code} - '{resp.text}'"
        )

    container = resp.json()["results"]
    return {
        "sunrise": container["sunrise"],
        "sunset": container["sunset"],
        "civil_twilight_morning_begin": container["civil_twilight_begin"],
        "civil_twilight_evening_end": container["civil_twilight_end"],
    }


def _location_dir() -> Path:
    location = get_location()
    return Path(f"{location["country"]}_{location["city"]}")


def _data_dir() -> Path:
    if os.name == "nt":
        return WindowsPath(os.path.expandvars("%APPDATA%\\keyboard-forecast"))
    else:
        return PosixPath("~/.config/keyboard-forecast").expanduser()


def _init():
    path = _data_dir()
    os.makedirs(path, exist_ok=True)


_init()
