from pathlib import Path
import tomllib
from typing import Any

from dotenv import load_dotenv

from eta.errors import ConfigError

ENV_DIR_PATH = Path(".secrets")
DB_DIR_PATH = Path(".cache")
CONFIG_DIR_PATH = Path(".eta")

def load_env(file_name: str) -> None:

    load_dotenv(ENV_DIR_PATH / file_name)

def load_toml(file_name: str) -> dict[str, Any]:

    path = CONFIG_DIR_PATH / file_name

    try:

        with path.open("rb") as file:
            return tomllib.load(file)

    except FileNotFoundError as error:

        raise ConfigError(f"{path} not found") from error

def path_db(file_name: str) -> Path:

    DB_DIR_PATH.mkdir(parents=True, exist_ok=True)

    return DB_DIR_PATH / file_name
