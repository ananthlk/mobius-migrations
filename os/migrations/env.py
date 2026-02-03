"""
Alembic migration environment for Mobius OS.
Builds database URL from environment (DATABASE_MODE, POSTGRES_*_LOCAL / POSTGRES_*_CLOUD).
Adds mobius-os/backend to path so app.db.postgres.Base and app.models are available.
"""
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool, create_engine
from alembic import context

# Add mobius-os/backend to path so "app" resolves
_this_dir = Path(__file__).resolve().parent
_os_dir = _this_dir.parent
_migrations_root = _os_dir.parent
_repo_root = _migrations_root.parent
_backend = _repo_root / "mobius-os" / "backend"
if _backend.is_dir() and str(_backend) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_backend))

from app.db.postgres import Base
from app import models  # noqa: F401 - registers models with Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url_from_env():
    """Build PostgreSQL URL from env (same logic as mobius-os backend app.config)."""
    mode = os.getenv("DATABASE_MODE", "local")
    if mode == "cloud" and os.getenv("CLOUDSQL_CONNECTION_NAME"):
        user = os.getenv("POSTGRES_USER_CLOUD", "postgres")
        password = os.getenv("POSTGRES_PASSWORD_CLOUD", "")
        db = os.getenv("POSTGRES_DB_CLOUD", "mobius")
        socket_path = f"/cloudsql/{os.getenv('CLOUDSQL_CONNECTION_NAME')}"
        if password:
            url = f"postgresql://{user}:{password}@/{db}?host={socket_path}"
        else:
            url = f"postgresql://{user}@/{db}?host={socket_path}"
    elif mode == "cloud":
        host = os.getenv("POSTGRES_HOST_CLOUD", "")
        port = os.getenv("POSTGRES_PORT_CLOUD", "5432")
        db = os.getenv("POSTGRES_DB_CLOUD", "mobius")
        user = os.getenv("POSTGRES_USER_CLOUD", "postgres")
        password = os.getenv("POSTGRES_PASSWORD_CLOUD", "")
        if password:
            url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        else:
            url = f"postgresql://{user}@{host}:{port}/{db}"
    else:
        host = os.getenv("POSTGRES_HOST_LOCAL", "localhost")
        port = os.getenv("POSTGRES_PORT_LOCAL", "5432")
        db = os.getenv("POSTGRES_DB_LOCAL", "mobius")
        user = os.getenv("POSTGRES_USER_LOCAL", "postgres")
        password = os.getenv("POSTGRES_PASSWORD_LOCAL", "")
        if password:
            url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        else:
            url = f"postgresql://{user}@{host}:{port}/{db}"
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://")
    return url


def run_migrations_offline():
    url = _get_url_from_env()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(_get_url_from_env(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
