from logging.config import fileConfig

from alembic import context
from sqlalchemy import text

from app.config import get_settings, DatabaseConfig
from app.common.database import Database
from app.common.models import Base
from app.utils.import_submodules import import_submodules

import_submodules("app.models")

config = context.config

postgres_config: DatabaseConfig = get_settings()["database"]
database_url = postgres_config["sync_database_uri"]

postgres_schema: str = postgres_config["schema"]

if postgres_schema:
    Base.metadata.schema = postgres_schema

config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

db = Database(postgres_config)


def create_schema():
    engine = db._sync_engine
    with engine.begin() as connection:
        query = f"""CREATE SCHEMA IF NOT EXISTS {postgres_schema};"""
        connection.execute(text(query))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=postgres_schema,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = db._sync_engine
    with engine.begin() as connection:
        if postgres_schema:
            safe_schema = postgres_schema.replace('"', '""')
            connection.execute(text(f'SET search_path TO "{safe_schema}"'))
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=postgres_schema,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    create_schema()
    run_migrations_offline()
else:
    create_schema()
    run_migrations_online()
