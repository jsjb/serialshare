"""
functions for translating keycodes for serial transmission
"""
import sys

try:
    # Windows doesn't have _CursesScreen
    from asciimatics.screen import _WindowsScreen as AsciimaticsScreen
except:
    # all other platforms do though
    from asciimatics.screen import _CursesScreen as AsciimaticsScreen

_key_map = {v: k for k, v in AsciimaticsScreen._KEY_MAP.items()}
_key_map[AsciimaticsScreen.KEY_BACK] = 0x08


def lookup(code):
    """
    returns the ASCII character for an asciimatics key_code
    if the code isn't in the dict, assume it was untranslated by asciimatics,
    so doesn't need to be translated back
    """
    if code in _key_map:
        return _key_map[code]
    return code
