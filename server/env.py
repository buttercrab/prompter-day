# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring

import os

default_env = {
    "SECRET": "random-secret",
    "SQL_USER": "postgres",
    "SQL_PASSWORD": "postgres",
    "SQL_HOST": "localhost:5432",
    "SQL_DB": "postgres",
    "SQL_RETRY": "5",
}


def get_env(key: str) -> str:
    if key in os.environ:
        return os.environ[key]
    elif key in default_env:
        return default_env[key]
    else:
        raise KeyError(f"Environment variable {key} not found")
