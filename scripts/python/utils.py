import os
import sys
from datetime import datetime

import win32api
import win32con

# noinspection PyUnresolvedReferences
from PIL import ImageGrab
from typing import Tuple

from a_protocol_0.enums.ColorEnum import InterfaceColorEnum

LOG_DIRECTORY = "C:\\Users\\thiba\\OneDrive\\Documents\\protocol0_logs"


def click_and_restore_pos(x, y):
    # type: (int, int) -> None
    (orig_x, orig_y) = win32api.GetCursorPos()
    _click(x, y)
    win32api.SetCursorPos((orig_x, orig_y))


def _click(x, y):
    # type: (int, int) -> None
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)


def get_pixel_color(x, y):
    # type: (int, int) -> Tuple[int, int, int]
    image = ImageGrab.grab()
    pixel_color = image.getpixel((x, y))
    log("pixel_color: %s" % InterfaceColorEnum.get_string_from_tuple(pixel_color))
    return pixel_color


def _get_log_filename():
    # type: () -> str
    return os.path.join(LOG_DIRECTORY, os.path.basename(sys.argv[0])).replace(".py", ".txt")


def setup_logs():
    # type: () -> None
    if os.path.exists(_get_log_filename()):
        os.remove(_get_log_filename())


def log(message):
    # type: (str) -> None
    """ expecting sequential script execution """
    message = "%s : %s\n" % (datetime.now(), message)
    print(message)
    with open(_get_log_filename(), "a") as f:
        f.write(message)
