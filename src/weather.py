import requests

import datastore
import forelogger as log
import location


def is_dark(cur_loc: location.Location) -> bool | None:
    return _check_openweathermap(cur_loc, datastore.get_weather_api_key())


def _check_weatherapi(cur_loc: location.Location, api_key: str) -> bool | None:
    resp = requests.get(
        f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={cur_loc.lat},{cur_loc.lng}&aqi=no"
    )
    if resp.status_code != 200:
        log.error(f"Failed to get weather data. Error is {resp.status_code} - '{resp.text}'")
        return

    weather = resp.json()["current"]
    log.info(f"Weather forecast: {weather}")

    conditions = (
        1135,  # Fog
        1147,  # Freezing fog
    )
    cloud_pct = weather["cloud"]
    condition_code = weather["condition"]["code"]
    return cloud_pct >= 70 or condition_code in conditions


def _check_openweathermap(cur_loc: location.Location, api_key: str) -> bool | None:
    resp = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?units=metric&lat={cur_loc.lat}&lon={cur_loc.lng}&appid={api_key}"
    )
    if resp.status_code != 200:
        log.error(f"Failed to get weather data. Error is {resp.status_code} - '{resp.text}'")
        return

    forecast = resp.json()
    log.info(f"Weather forecast: {forecast}")

    condition_code = forecast["weather"][0]["id"]
    cloud_pct = forecast["clouds"]["all"]
    if _openweathermap_clear(condition_code) or cloud_pct < 70:
        return False

    if (
        _openweathermap_foggy(condition_code)
        or _openweathermap_snowy(condition_code)
        or _openweathermap_rainy(condition_code)
        or _openweathermap_thunderstorm(condition_code)
    ):
        return True


def _openweathermap_clear(condition_id: int) -> bool:
    return condition_id == 800


def _openweathermap_foggy(condition_id: int) -> bool:
    return 711 <= condition_id <= 781  # From smoke to tornado (lol)


def _openweathermap_snowy(condition_id: int) -> bool:
    return 600 <= condition_id <= 622


def _openweathermap_rainy(condition_id: int) -> bool:
    return 502 <= condition_id <= 531  # From heavy intensity to ragged shower rain


def _openweathermap_thunderstorm(condition_id: int) -> bool:
    return 200 <= condition_id <= 232
