from typing import Optional

import os
import json



def default_config(config_path: str, filename: Optional[str]="default.conf"): # TODO
    """
    Sets up the bot with a configuration object generated using .env variables and default values
    :param config_path: Path to directory where file will be saved
    :param filename: Optional name for the actual .conf file
    :return: dictionary of config keys to values
    """
    if not os.path.exists(config_path):
        sys.exit("Invalid configuration file directory...")

    default = {
        "config_path": os.path.join(config_path, filename),
        'prefix': os.environ["PREFIX"] or "$",
        "token": os.environ['TOKEN'],
        'permissions': int(os.environ['BOT_PERMISSIONS']) or 8,
        'application_id': int(os.environ['APPLICATION_ID']),
        'sync_commands_globally': os.environ.get("SYNC_GLOBAL") is not None or True,
        "owner": os.environ.get("OWNER") or None
    }

    with open(default['config_path'], 'w') as file:
        file.write(json.dumps(default))

    return defualt



