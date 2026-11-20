"""Лёгкие ALTER при старте (Railway без Shell)."""
import logging

from sqlalchemy import text

from app.core.database import engine

logger = logging.getLogger(__name__)


async def ensure_schema_patches() -> None:
    statements = [
        "ALTER TABLE contract_line_items ADD COLUMN IF NOT EXISTS cost_price NUMERIC(15, 2)",
        "ALTER TABLE contract_line_items ADD COLUMN IF NOT EXISTS share_half BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE contract_line_items ADD COLUMN IF NOT EXISTS salary_paid BOOLEAN NOT NULL DEFAULT FALSE",
    ]
    async with engine.begin() as conn:
        for sql in statements:
            await conn.execute(text(sql))
    logger.info("Schema patches OK (payroll columns)")
