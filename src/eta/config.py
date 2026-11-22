from pathlib import Path

from dotenv import load_dotenv

ENV_DIR_PATH = Path(".secrets")

DB_DIR_PATH = Path(".cache")

class ConfigError(Exception):
    pass

def load_env(file_name: str) -> None:

    load_dotenv(ENV_DIR_PATH / file_name)

def path_db(file_name: str) -> Path:

    DB_DIR_PATH.mkdir(parents=True, exist_ok=True)

    return DB_DIR_PATH / file_name
