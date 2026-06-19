import sys
from collections.abc import Mapping
from os import environ
from typing import Any, TypedDict
from urllib.parse import quote_plus

from dotenv import load_dotenv


class PolymarketConfig(TypedDict):
    api_key: str
    api_secret: str
    api_passphrase: str
    address: str


class DatabaseConfig(TypedDict):
    async_database_uri: str
    sync_database_uri: str
    host: str
    port: int
    user: str
    password: str
    db_name: str
    schema: str


class SingletonMeta(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    _sync_postgres_uri: str = (
        "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )

    _async_postgres_uri: str = (
        "postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    )

    def __init__(self) -> None:
        self.init_config()

    def init_config(self) -> None:
        self.recent_trades_limit = int(environ.get("RECENT_TRADES_LIMIT", 30))
        self.notify_interval_minutes = int(environ.get("NOTIFY_INTERVAL_MINUTES", 10))
        self.stats_interval_minutes = int(environ.get("STATS_INTERVAL_MINUTES", 20))

        self.__init_telegram()
        self.__init_postgres()
        self.__init_polymarket()

    def __init_telegram(self):
        try:
            var = "TELEGRAM_TOKEN"
            self.telegram_token = environ[var]
        except KeyError:
            print(f"Env variable {var} is not set")
            sys.exit(1)

    def __init_postgres(self):
        try:
            var = "POSTGRES_HOST"
            self.postgres_host = environ[var]
            var = "POSTGRES_PORT"
            self.postgres_port = int(environ[var])
            var = "POSTGRES_DB"
            self.postgres_db = environ[var]
            var = "POSTGRES_USER"
            self.postgres_user = environ[var]
            var = "POSTGRES_PASSWORD"
            self.postgres_password = environ[var]
            var = "POSTGRES_SCHEMA"
            self.postgres_schema = environ.get(var, "public")
        except KeyError:
            print(f"Env variable {var} is not set")
            sys.exit(1)

    def __init_polymarket(self):
        try:
            var = "POLYMARKET_API_KEY"
            self.polymarket_api_key = environ[var]
            var = "POLYMARKET_API_SECRET"
            self.polymarket_api_secret = environ[var]
            var = "POLYMARKET_API_PASSPHRASE"
            self.polymarket_api_passphrase = environ[var]
            var = "POLYMARKET_ADDRESS"
            self.polymarket_address = environ[var]
        except KeyError:
            print(f"Env variable {var} is not set")
            sys.exit(1)

    def sync_postgres_uri(self) -> str:
        return self._sync_postgres_uri.format(
            user=self.postgres_user,
            password=quote_plus(self.postgres_password),
            host=self.postgres_host,
            port=self.postgres_port,
            db=self.postgres_db,
        )

    def async_postgres_uri(self) -> str:
        return self._async_postgres_uri.format(
            user=self.postgres_user,
            password=quote_plus(self.postgres_password),
            host=self.postgres_host,
            port=self.postgres_port,
            db=self.postgres_db,
        )

    @property
    def postgres_config(self) -> DatabaseConfig:
        return {
            "async_database_uri": self.async_postgres_uri(),
            "sync_database_uri": self.sync_postgres_uri(),
            "host": self.postgres_host,
            "port": self.postgres_port,
            "user": self.postgres_user,
            "password": self.postgres_password,
            "db_name": self.postgres_db,
            "schema": self.postgres_schema,
        }

    @property
    def polymarket_config(self) -> PolymarketConfig:
        return {
            "api_key": self.polymarket_api_key,
            "api_secret": self.polymarket_api_secret,
            "api_passphrase": self.polymarket_api_passphrase,
            "address": self.polymarket_address,
        }

    @property
    def settings(self) -> Mapping[str, Any]:
        return {
            "telegram_token": self.telegram_token,
            "database": self.postgres_config,
            "polymarket": self.polymarket_config,
            "recent_trades_limit": self.recent_trades_limit,
            "notify_interval_minutes": self.notify_interval_minutes,
            "stats_interval_minutes": self.stats_interval_minutes,
        }


def get_settings() -> Mapping[str, Any]:
    load_dotenv(environ.get("ENV_FILE"))
    return Config().settings
