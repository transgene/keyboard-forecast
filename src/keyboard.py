from pywinusb import hid

import forelogger as log

VENDOR_ID = "1EA7"
PRODUCT_ID = "6A62"

_VENDOR_ID = 0x1EA7
_PRODUCT_ID = 0x6A62


class DisconnectedException(Exception):
    pass


_BACKLIGHT_IS_ON = None


def toggle_backlight(turn_on: bool, force=False):
    global _BACKLIGHT_IS_ON
    if not force and _BACKLIGHT_IS_ON == turn_on:
        log.info("Backlight is already " + ("ON" if _BACKLIGHT_IS_ON else "OFF"))
        return

    hid_devices = hid.HidDeviceFilter(vendor_id=_VENDOR_ID, product_id=_PRODUCT_ID).get_devices()
    if not hid_devices:
        raise DisconnectedException("The keyboard is not found. Can't toggle backlight")

    target_usage = hid.get_full_usage_id(0xFF60, 0x63)
    for device in hid_devices:
        try:
            device.open()
            for report in device.find_output_reports():
                if target_usage in report:
                    log.info(f"Sending {'ON' if turn_on else 'OFF'} to the keyboard")
                    data = [0x31 if turn_on else 0x30]
                    report_length = 32
                    request_data = [0x00] * (report_length)  # First byte is Report ID
                    request_data[0 : len(data)] = data
                    report[target_usage] = request_data
                    report.send()

                    _BACKLIGHT_IS_ON = turn_on
                    return
        except Exception as e:
            log.error(f"Failed to send message to the keyboard, error is: {e}")
        finally:
            device.close()
    else:
        log.warn("The keyboard can't receive HID messages")
