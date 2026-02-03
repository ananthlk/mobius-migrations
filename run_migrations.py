#!/usr/bin/env python3
"""
Single entrypoint to run Mobius DB migrations for chat, rag, os, user.
Usage: python run_migrations.py --env dev|prod [--module chat|rag|os|user]
Env vars must be set by caller (see README.md). Optional: load .env from mobius-config or repo root.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Paths
MIGRATIONS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = MIGRATIONS_ROOT.parent


def _load_env():
    """Optionally load .env from mobius-config and repo root so dev runs work without pre-set env."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for p in [REPO_ROOT / "mobius-config" / ".env", REPO_ROOT / ".env", MIGRATIONS_ROOT / ".env"]:
        if p.exists():
            load_dotenv(p, override=False)


def _split_statements(sql: str):
    """Split SQL into statements by semicolon at end of line. Skip comment-only lines."""
    out = []
    current = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        current.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                out.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            out.append(stmt)
    return out


def run_chat():
    """Run chat SQL migrations from chat/schema/ in order."""
    url = (os.environ.get("CHAT_RAG_DATABASE_URL") or os.environ.get("RAG_DATABASE_URL") or "").strip()
    if not url:
        print("  [chat] CHAT_RAG_DATABASE_URL not set; skipping.")
        return
    schema_dir = MIGRATIONS_ROOT / "chat" / "schema"
    if not schema_dir.is_dir():
        print("  [chat] No chat/schema dir; skipping.")
        return
    files = sorted(schema_dir.glob("*.sql"))
    if not files:
        print("  [chat] No .sql files; skipping.")
        return
    import psycopg2
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        for path in files:
            sql = path.read_text()
            for stmt in _split_statements(sql):
                if stmt:
                    cur.execute(stmt)
            print(f"  [chat] Applied {path.name}")
    finally:
        cur.close()
        conn.close()


def run_rag():
    """Run RAG Python migrations via rag/run_rag_migrations.py (requires DATABASE_URL)."""
    if not os.environ.get("DATABASE_URL"):
        print("  [rag] DATABASE_URL not set; skipping.")
        return
    script = MIGRATIONS_ROOT / "rag" / "run_rag_migrations.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        env=os.environ,
    )
    if result.returncode != 0:
        raise RuntimeError(f"rag migrations exited with {result.returncode}")


def run_os():
    """Run mobius-os Alembic (requires DATABASE_MODE and POSTGRES_* env)."""
    ini = MIGRATIONS_ROOT / "os" / "alembic.ini"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini), "upgrade", "head"],
        cwd=REPO_ROOT,
        env=os.environ,
    )
    if result.returncode != 0:
        raise RuntimeError(f"os alembic exited with {result.returncode}")


def run_user():
    """Run Mobius-user Alembic (requires USER_DATABASE_URL)."""
    ini = MIGRATIONS_ROOT / "user" / "alembic.ini"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini), "upgrade", "head"],
        cwd=REPO_ROOT,
        env=os.environ,
    )
    if result.returncode != 0:
        raise RuntimeError(f"user alembic exited with {result.returncode}")


def main():
    _load_env()
    parser = argparse.ArgumentParser(description="Run Mobius DB migrations")
    parser.add_argument("--env", required=True, choices=["dev", "prod"], help="Environment (dev or prod)")
    parser.add_argument("--module", choices=["chat", "rag", "os", "user"], help="Run only this module; default all")
    args = parser.parse_args()

    modules = [args.module] if args.module else ["chat", "rag", "os", "user"]
    runners = {"chat": run_chat, "rag": run_rag, "os": run_os, "user": run_user}

    for name in modules:
        print(f"[{name}] Running migrations...")
        try:
            runners[name]()
        except Exception as e:
            print(f"[{name}] Failed: {e}", file=sys.stderr)
            sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
