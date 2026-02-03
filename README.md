# Mobius Migrations

Single entrypoint to run database migrations for all Mobius modules (chat, rag, os, user) in dev or prod.

## Contract

- **CLI:** `python run_migrations.py --env dev|prod [--module chat|rag|os|user]`
  - `--env` (required): `dev` or `prod`.
  - `--module` (optional): run only this module; if omitted, run all four (chat, rag, os, user).
- **Layout:** See directory structure below. The runner resolves paths relative to `mobius-migrations/`.
- **Env vars:** Caller must set the appropriate env vars for the chosen env (see below). Use [mobius-config](../mobius-config/) or `.env`; the runner does not load env files itself for security (deploy pipelines set env explicitly).

## Layout

```
mobius-migrations/
  README.md           # This file
  run_migrations.py   # Entrypoint
  VERSION             # Optional package version
  chat/schema/        # SQL files (from mobius-chat/db/schema/)
  rag/                # RAG Python migrations (runs mobius-rag/app/migrations via path)
    run_rag_migrations.py
  os/                 # mobius-os Alembic (alembic.ini, migrations/)
  user/               # Mobius-user Alembic (alembic.ini, migrations/)
```

## Env vars per module

| Module | Env vars | Notes |
|--------|----------|--------|
| **chat** | `CHAT_RAG_DATABASE_URL` | PostgreSQL URL for mobius_chat DB. |
| **rag** | `DATABASE_URL` | PostgreSQL URL for mobius_rag DB (e.g. `postgresql+asyncpg://...` or `postgresql://...`). |
| **os** | `DATABASE_MODE` (`local` \| `cloud`), `POSTGRES_HOST_LOCAL`, `POSTGRES_PORT_LOCAL`, `POSTGRES_DB_LOCAL`, `POSTGRES_USER_LOCAL`, `POSTGRES_PASSWORD_LOCAL`; for cloud: `POSTGRES_HOST_CLOUD`, etc., or `CLOUDSQL_CONNECTION_NAME`. | Same as [mobius-os backend](mobius-os/backend/app/config.py). |
| **user** | `USER_DATABASE_URL` | PostgreSQL URL for mobius_user DB. |

For **prod**, set the same variable names with values pointing at production databases (e.g. prod host, prod password). The runner does not switch env vars by name; it only uses whatever is set in the environment.

See [docs/DATA_SCHEMA_AND_CREDENTIALS.md](docs/DATA_SCHEMA_AND_CREDENTIALS.md) for full reference.

## How to run

From repo root, with env vars set (e.g. from mobius-config or `.env`):

```bash
# Run all migrations (all four modules) for dev
python mobius-migrations/run_migrations.py --env dev

# Run all migrations for prod
python mobius-migrations/run_migrations.py --env prod

# Run only chat migrations for dev
python mobius-migrations/run_migrations.py --env dev --module chat

# Run only RAG migrations for prod
python mobius-migrations/run_migrations.py --env prod --module rag
```

Using mobius-config shared env:

```bash
./mobius-config/run_with_shared_env.sh . python mobius-migrations/run_migrations.py --env dev
```

## Runner behavior

1. Parses `--env` and `--module`.
2. For each selected module (chat, rag, os, user):
   - **chat:** Runs SQL files in `chat/schema/` in sorted order using `CHAT_RAG_DATABASE_URL`.
   - **rag:** Runs RAG Python migrations (via `rag/run_rag_migrations.py`) with `DATABASE_URL` set.
   - **os:** Runs `alembic -c os/alembic.ini upgrade head` with OS Postgres config in env.
   - **user:** Runs `alembic -c user/alembic.ini upgrade head` with `USER_DATABASE_URL` set.
3. Exits 0 if all succeeded; non-zero and a clear message on first failure.

## Versioning

Optional: set `VERSION` in this directory (e.g. `1.0.0`) so deploy pipelines can record which migration package was applied.
