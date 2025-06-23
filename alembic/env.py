import os
import sys

# add src folder to sys.path (for execution from project root)
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# import Base and models
# from src.ps_camp.sql_models.base import Base
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from ps_camp.db.base import Base

# this is the alembic config object which provides
# access to values within the .ini file in use
config = context.config

# override database url from environment variable
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# set up python logging using config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# set metadata for autogeneration
target_metadata = Base.metadata


# run migrations in 'offline' mode
def run_migrations_offline() -> None:
    """
    configure the context with just a url and no engine.
    useful for generating SQL scripts without a db connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# run migrations in 'online' mode
def run_migrations_online() -> None:
    """
    create an engine and connect to the database to run migrations.
    """
    print("=== tables ===")
    print(target_metadata.tables.keys())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# choose offline or online mode based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
