"""
functions for translating keycodes for serial transmission
"""

try:
    # Windows doesn't have _CursesScreen
    from asciimatics.screen import _WindowsScreen as AsciimaticsScreen
except ImportError:
    # all other platforms do though
    from asciimatics.screen import _CursesScreen as AsciimaticsScreen


# 'escape' constant to make multichar sequences more readable
_ESC = b'\x1b'

# translation map to turn Asciimatics keys into ASCII keys
_key_map = {}

_key_map[AsciimaticsScreen.KEY_ESCAPE] = b'\x1b'
_key_map[AsciimaticsScreen.KEY_F1] = _ESC + b'OP'
_key_map[AsciimaticsScreen.KEY_F2] = _ESC + b'OQ'
_key_map[AsciimaticsScreen.KEY_F3] = _ESC + b'OR'
_key_map[AsciimaticsScreen.KEY_F4] = _ESC + b'OS'
_key_map[AsciimaticsScreen.KEY_F5] = _ESC + b'[15'
_key_map[AsciimaticsScreen.KEY_F6] = _ESC + b'[17'
_key_map[AsciimaticsScreen.KEY_F7] = _ESC + b'[18'
_key_map[AsciimaticsScreen.KEY_F8] = _ESC + b'[19'
_key_map[AsciimaticsScreen.KEY_F9] = _ESC + b'[20'
_key_map[AsciimaticsScreen.KEY_F10] = _ESC + b'[21'
_key_map[AsciimaticsScreen.KEY_F11] = _ESC + b'[23'
_key_map[AsciimaticsScreen.KEY_F12] = _ESC + b'[24'
_key_map[AsciimaticsScreen.KEY_F13] = _ESC + b'[25'
_key_map[AsciimaticsScreen.KEY_F13] = _ESC + b'[1;2P'
_key_map[AsciimaticsScreen.KEY_F14] = _ESC + b'[1;2Q'
_key_map[AsciimaticsScreen.KEY_F15] = _ESC + b'[1;2R'
_key_map[AsciimaticsScreen.KEY_F16] = _ESC + b'[1;2S'
_key_map[AsciimaticsScreen.KEY_F17] = _ESC + b'[15;2~'
_key_map[AsciimaticsScreen.KEY_F18] = _ESC + b'[17;2~'
_key_map[AsciimaticsScreen.KEY_F19] = _ESC + b'[18;2~'
_key_map[AsciimaticsScreen.KEY_F20] = _ESC + b'[19;2~'
_key_map[AsciimaticsScreen.KEY_F21] = _ESC + b'[20;2~'
_key_map[AsciimaticsScreen.KEY_F22] = _ESC + b'[21;2~'
_key_map[AsciimaticsScreen.KEY_F23] = _ESC + b'[23;2~'
_key_map[AsciimaticsScreen.KEY_F24] = _ESC + b'[24;2~'
# terminal can't read print screen, since os captures it
_key_map[AsciimaticsScreen.KEY_PRINT_SCREEN] = b''
_key_map[AsciimaticsScreen.KEY_INSERT] = _ESC + b'[4h'
_key_map[AsciimaticsScreen.KEY_DELETE] = _ESC + b'[P'
_key_map[AsciimaticsScreen.KEY_HOME] = _ESC + b'[H'
_key_map[AsciimaticsScreen.KEY_END] = _ESC + b'[4~'
_key_map[AsciimaticsScreen.KEY_LEFT] = _ESC + b'[D'
_key_map[AsciimaticsScreen.KEY_UP] = _ESC + b'[A'
_key_map[AsciimaticsScreen.KEY_RIGHT] = _ESC + b'[C'
_key_map[AsciimaticsScreen.KEY_DOWN] = _ESC + b'[B'
_key_map[AsciimaticsScreen.KEY_PAGE_UP] = _ESC + b'[5~'
_key_map[AsciimaticsScreen.KEY_PAGE_DOWN] = _ESC + b'[5~'
_key_map[AsciimaticsScreen.KEY_BACK] = b'\x7f'
_key_map[AsciimaticsScreen.KEY_TAB] = b'\x09'
_key_map[AsciimaticsScreen.KEY_BACK_TAB] = _ESC + b'[Z' # ISO left tab
_key_map[AsciimaticsScreen.KEY_NUMPAD0] = _ESC + b'Op'
_key_map[AsciimaticsScreen.KEY_NUMPAD1] = _ESC + b'Oq'
_key_map[AsciimaticsScreen.KEY_NUMPAD2] = _ESC + b'Or'
_key_map[AsciimaticsScreen.KEY_NUMPAD3] = _ESC + b'Os'
_key_map[AsciimaticsScreen.KEY_NUMPAD4] = _ESC + b'Ot'
_key_map[AsciimaticsScreen.KEY_NUMPAD5] = _ESC + b'Ou'
_key_map[AsciimaticsScreen.KEY_NUMPAD6] = _ESC + b'Ov'
_key_map[AsciimaticsScreen.KEY_NUMPAD7] = _ESC + b'Ow'
_key_map[AsciimaticsScreen.KEY_NUMPAD8] = _ESC + b'Ox'
_key_map[AsciimaticsScreen.KEY_NUMPAD9] = _ESC + b'Oy'
_key_map[AsciimaticsScreen.KEY_MULTIPLY] = _ESC + b'Oj'
_key_map[AsciimaticsScreen.KEY_ADD] = _ESC + b'Ok'
_key_map[AsciimaticsScreen.KEY_SUBTRACT] = _ESC + b'Om'
_key_map[AsciimaticsScreen.KEY_DECIMAL] = _ESC + b'On'
_key_map[AsciimaticsScreen.KEY_DIVIDE] = _ESC + b'Oo'
# the modifiers and lock keys can not be transmitted on a serial line
_key_map[AsciimaticsScreen.KEY_CAPS_LOCK] = b''
_key_map[AsciimaticsScreen.KEY_NUM_LOCK] = b''
_key_map[AsciimaticsScreen.KEY_SCROLL_LOCK] = b''
_key_map[AsciimaticsScreen.KEY_SHIFT] = b''
_key_map[AsciimaticsScreen.KEY_CONTROL] = b''
_key_map[AsciimaticsScreen.KEY_MENU] = b''

_key_map[ord('\n')] = b'\r'


def lookup(code):
    """
    returns the ASCII character for an asciimatics key_code
    if the code isn't in the dict, assume it was untranslated by asciimatics,
    so doesn't need to be translated back
    """
    if code in _key_map:
        return _key_map[code]
    return code.to_bytes(1, 'big', signed=False)
