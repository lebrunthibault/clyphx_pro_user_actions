from a_protocol_0.enums.AbstractEnum import AbstractEnum


class CommandEnum(AbstractEnum):
    SEND_KEYS = "SEND_KEYS"
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    FOCUS_WINDOW = "FOCUS_WINDOW"
    SHOW_WINDOWS = "SHOW_WINDOWS"
    TOGGLE_ABLETON_BUTTON = "TOGGLE_ABLETON_BUTTON"
    PIXEL_HAS_COLOR = "PIXEL_HAS_COLOR"
    ACTIVATE_REV2_EDITOR = "ACTIVATE_REV2_EDITOR"
    RELOAD_ABLETON = "RELOAD_ABLETON"
    IS_PLUGIN_WINDOW_VISIBLE = "IS_PLUGIN_WINDOW_VISIBLE"
    SEARCH_SET = "SEARCH_SET"
    SYNC_PRESETS = "SYNC_PRESETS"
    SHOW_PLUGINS = "SHOW_PLUGINS"
    SETUP_HOTKEYS = "SETUP_HOTKEYS"
    SHOW_HIDE_PLUGINS = "SHOW_HIDE_PLUGINS"
    HIDE_PLUGINS = "HIDE_PLUGINS"
    ARROW_UP = "ARROW_UP"