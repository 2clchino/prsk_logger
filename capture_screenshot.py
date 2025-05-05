import common
from access_adb import connect_adb

serial = connect_adb()
screen = common.capture_screenshot_image(device_serial=serial)
common.save_image_ndarray(screen, "screen.png")