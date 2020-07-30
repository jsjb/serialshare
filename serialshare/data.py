""" configuration, including last used variables """
import json
import os
import pathlib

from appdirs import AppDirs

# determine the location of the config file
_dirs = AppDirs("serialshare", "Jadon Bennett")
_config_dir = _dirs.user_config_dir
_profile = os.path.join(_config_dir, "last_profile.json")

DEFAULT_PROFILE = {
    "device": None,
    "baudrate": 9600,
    "hostname": None,
}


def read_profile():
    """ returns the last used profile, or the default if it does not exist """
    if os.path.isdir(_config_dir) and os.path.exists(_profile):
        with open(_profile, "r") as profile:
            return json.load(profile)
    return DEFAULT_PROFILE


def write_profile(config):
    """ saves the data in `config` as the last used profile """
    # create the config folder if it does not exist
    pathlib.Path(_config_dir).mkdir(parents=True, exist_ok=True)

    with open(_profile, "w") as profile:
        json.dump(config, profile)
