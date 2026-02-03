"""
Run RAG Python migrations in order.
Requires DATABASE_URL in environment. Adds mobius-rag to path so app.migrations.* can be imported.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add mobius-rag to path so "app" resolves
MIGRATIONS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = MIGRATIONS_ROOT.parent.parent
MOBIUS_RAG = REPO_ROOT / "mobius-rag"
if MOBIUS_RAG.is_dir() and str(MOBIUS_RAG) not in sys.path:
    sys.path.insert(0, str(MOBIUS_RAG))

# Canonical order (matches main.py / init_db / embedding_worker)
RAG_MIGRATION_ORDER = [
    "add_embedding_tables",
    "add_llm_configs_table",
    "add_category_scores_column",
    "category_scores_to_columns",
    "add_document_pages_text_markdown",
    "add_extracted_facts_reader_fields",
    "add_chunk_start_offset_in_page",
    "add_chunking_job_run_config",
    "add_extracted_facts_verification",
    "add_is_pertinent_field",
    "add_document_authority_level",
    "add_document_effective_termination_dates",
    "add_document_display_name",
    "add_publish_tables",
    "add_publish_verification_columns",
]


async def run_all():
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("DATABASE_URL must be set for RAG migrations")

    for name in RAG_MIGRATION_ORDER:
        mod = __import__(f"app.migrations.{name}", fromlist=["migrate"])
        migrate = getattr(mod, "migrate")
        print(f"  Running {name}...")
        await migrate()
    print("  RAG migrations completed.")


def main():
    asyncio.run(run_all())


if __name__ == "__main__":
    main()
