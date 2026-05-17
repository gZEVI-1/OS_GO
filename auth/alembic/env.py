import asyncio
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Добавляем корень проекта в путь, чтобы импортировать app
sys.path.append('.')

from app.database import Base
from app.config import get_settings
from app.models.user import User  # ← важно! импорт модели, чтобы Alembic увидел таблицы

# Alembic Config
config = context.config

# Логирование из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline mode — для генерации SQL без подключения к БД."""
    settings = get_settings()
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Синхронная функция, которую async run_sync вызовет внутри event loop."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Online mode — стандартный способ для async SQLAlchemy."""
    settings = get_settings()
    
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())