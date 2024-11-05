from datetime import datetime, timedelta, tzinfo
from multiprocessing import Process
from pywinusb import hid
import json
import os
import pause
import requests
from forelogger import info, error

BACKLIGHT_IS_ON = None

def check_weather(cur_loc: dict, api_key: str):
    resp = requests.get(f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={cur_loc['lat']},{cur_loc['lng']}&aqi=no")
    if resp.status_code != 200:
        error(f"Failed to get weather data. Error is {resp.status_code} - '{resp.text}'")
        return
    weather = resp.json()["current"]
    cloud_pct = weather["cloud"]
    condition = weather["condition"]
    info(f"Cloud percentage: {cloud_pct}, condition: {condition['text']} ({condition['code']})")
    if cloud_pct >= 70:
        toggle_backlight(True)
    else:
        toggle_backlight(False)


def main():
    now = get_now()
    info(f"Today is {now}")
    if os.name == "nt":
        data_dir = os.path.expandvars("%APPDATA%\\keyboard-forecast")
    else:
        data_dir = os.path.expanduser("~/.config/keyboard-forecast")
    os.makedirs(data_dir, exist_ok=True)
    

    # Getting current location
    try:
        current_loc_path = os.path.join(data_dir, "current_loc.json")
        with open(current_loc_path) as f:
            current_location = json.load(f)
    except FileNotFoundError: # TODO re-download in case of general Exception during file read
        info("Current location is not defined. Attempting to download")
        loc_resp = requests.get("https://api.ip2location.io/")
        if loc_resp.status_code != 200:
            raise Exception(f"Failed to get current location by the IP address. Error is {loc_resp.status_code} - '{loc_resp.text}'")
        
        current_location = {
            "country": loc_resp.json()["country_name"],
            "city": loc_resp.json()["city_name"],
            "lat": loc_resp.json()["latitude"],
            "lng": loc_resp.json()["longitude"]
        }
        with open(current_loc_path, "w") as f:
            json.dump(current_location, f, indent=4)

    info(f"We are in {current_location['city']}, {current_location['country']}")

    daytime_dir_name = f"{current_location['country']}_{current_location['city']}".lower()
    daytime_dir_path = os.path.join(data_dir, daytime_dir_name)
    os.makedirs(daytime_dir_path, exist_ok=True)

    while True:
        # Getting today's daytime
        daytime = get_daytime(now, current_location, daytime_dir_path)


        # Waiting till sunrise
        sunrise = datetime.strptime(daytime["sunrise"], "%Y-%m-%dT%H:%M:%S%z") # TODO get the next sunrise (today or tomorrow's)
        sunrise = sunrise.astimezone(get_timezone(sunrise))
        # sunset = datetime.strptime(daytime["civil_twilight_evening_end"], "%Y-%m-%dT%H:%M:%S%z") 
        sunset = datetime.strptime(daytime["sunset"], "%Y-%m-%dT%H:%M:%S%z") 
        sunset = sunset.astimezone(get_timezone(sunset))
        now = get_now()
        if now < sunrise:
            info(f"Too early! Waiting until {sunrise}")
            pause.until(sunrise)
            info("Woke up")
        elif now > sunset:
            toggle_backlight(True)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            info(f"Too late! Waiting until {midnight} to reset the day")
            pause.until(midnight)
            continue


        # Downloading tomorrow
        tomorrow = now + timedelta(days=1)
        p = Process(target=get_daytime, args=(tomorrow, current_location, daytime_dir_path))
        p.daemon = True
        p.start()
        

        # Scheduling the weather task
        api_key = os.getenv("WEATHER_API_KEY")
        next_run = get_now()
        while next_run <= sunset:
            check_weather(current_location, api_key) # type: ignore
            next_run = next_run + timedelta(minutes=5)
            info(f"Next weather check: {next_run}")
            pause.until(next_run)


def get_daytime(date: datetime, current_location: dict, daytime_dir_path: str):
    try:
        daytime_json_path = os.path.join(daytime_dir_path, f"{date.month}_{date.day}.json")
        with open(daytime_json_path) as f:
            daytime = json.load(f)
    except FileNotFoundError:
        info(f"Daytime data for {date.month}-{date.day} not found. Attempting to download") # TODO format date as Nov, 1
        daytime = download_daytime(date, current_location, daytime_json_path)
    except Exception as e:
        error(f"Failed to load daytime data for {date.month}-{date.day} from file. Attempting to download")
        error(str(e))
        daytime = download_daytime(date, current_location, daytime_json_path)
    return daytime


def download_daytime(date: datetime, current_location: dict, daytime_json_path: str):
    resp = requests.get(f"https://api.sunrise-sunset.org/json?lat={current_location['lat']}&lng={current_location['lng']}&date={date.year}-{date.month}-{date.day}&formatted=0")
    if resp.status_code != 200:
        raise Exception(f"Failed to get daytime data. Error is {resp.status_code} - '{resp.text}'")
        
    container = resp.json()["results"]
    daytime = {
        "sunrise": container["sunrise"],
        "sunset": container["sunset"],
        "civil_twilight_morning_begin": container["civil_twilight_begin"],
        "civil_twilight_evening_end": container["civil_twilight_end"]
    }
    
    with open(daytime_json_path, "w") as f:
        json.dump(daytime, f, indent=4)

    return daytime


def get_timezone(date: datetime | None = None) -> tzinfo:
    if date is None:
        date = datetime.now()
    tz = date.astimezone().tzinfo
    if tz is None:
        raise Exception("Failed to get timezone")
    return tz

# def get_tz_name(date: datetime):
#     return get_timezone(date).tzname(date) # type: ignore

def get_now():
    return datetime.now(get_timezone())

def toggle_backlight(turn_on: bool):
    global BACKLIGHT_IS_ON
    if BACKLIGHT_IS_ON == turn_on:
        info("Backlight is already " + ("ON" if BACKLIGHT_IS_ON else "OFF"))
        return

    hid_devices = hid.HidDeviceFilter(vendor_id=0x1EA7, product_id=0x6A62).get_devices()
    if not hid_devices:
        info("The keyboard is not found") # TODO warn
        return

    target_usage = hid.get_full_usage_id(0xFF60, 0x63)
    for device in hid_devices:
        try:
            device.open()
            for report in device.find_output_reports():
                if target_usage in report:
                    info(f"Found output report, writing {'ON' if turn_on else 'OFF'} to it")
                    data = [0x31 if turn_on else 0x30]
                    report_length = 32
                    request_data = [0x00] * (report_length) # First byte is Report ID
                    request_data[0:len(data)] = data
                    # report[target_usage] = bytes(request_data)
                    report[target_usage] = request_data
                    report.send()

                    BACKLIGHT_IS_ON = turn_on
                    return
        except Exception as e:
            error(f"Failed to send output report, error is: {e}")
        finally:
            device.close()
    else:
        info("Failed to find output report") # TODO warn
    

def validate():
    if os.getenv("WEATHER_API_KEY") is None:
        raise Exception("Missing API key for WeatherAPI (WEATHER_API_KEY)")

if __name__ == "__main__":
    main()