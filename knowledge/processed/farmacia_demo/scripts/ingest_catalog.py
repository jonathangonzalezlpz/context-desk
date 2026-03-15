#!/usr/bin/env python
"""
Script: ingest_catalog.py

Reads the catalog CSV for this domain from domain_config.json
and inserts all bot-allowed products into PostgreSQL.

The column mapping is fully config-driven: no hardcoded schema assumptions.

Usage (from project root):
    python knowledge/processed/farmacia_demo/scripts/ingest_catalog.py
    python knowledge/processed/farmacia_demo/scripts/ingest_catalog.py --config knowledge/processed/farmacia_demo/domain_config.json
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Add project root (4 levels up from this script) to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker, Session  # noqa: E402

from backend.src.app.infrastructure.database.models import ProductModel  # noqa: E402
from backend.src.app.infrastructure.database.session import Base  # noqa: E402

# Default config path is the domain_config.json sitting next to this script
DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "domain_config.json"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/contextdesk_db")


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def parse_price_cents(price_str: str) -> int:
    try:
        return round(float(price_str.strip()) * 100)
    except ValueError:
        return 0


def load_catalog(session: Session, config: dict) -> None:
    catalog_cfg = config.get("catalog", {})
    csv_path = PROJECT_ROOT / catalog_cfg["source_csv"]
    col = catalog_cfg["column_map"]

    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        sys.exit(1)

    print(f"Reading catalog from: {csv_path}")

    # Idempotent: clear before re-ingesting
    existing = session.query(ProductModel).count()
    if existing > 0:
        print(f"⚠️  Deleting {existing} existing products before re-ingestion...")
        session.query(ProductModel).delete()
        session.commit()

    rows_inserted = 0
    rows_skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bot_allowed_field = col.get("bot_allowed_field")
            if bot_allowed_field and not parse_bool(row.get(bot_allowed_field, "true")):
                rows_skipped += 1
                continue

            in_stock_field = col.get("in_stock_field", "availability")
            in_stock_values: list[str] = col.get("in_stock_values", [])
            in_stock = row.get(in_stock_field, "").strip() in in_stock_values

            product = ProductModel(
                name=row.get(col["name"], "").strip(),
                category=row.get(col["category"], "").strip(),
                brand=row.get(col.get("brand", ""), "").strip() or None,
                description=row.get(col.get("description", ""), "").strip() or None,
                price_cents=parse_price_cents(row.get(col.get("price_eur", "price_eur"), "0")),
                in_stock=in_stock,
            )
            session.add(product)
            rows_inserted += 1

    session.commit()
    print(f"✅ Inserted {rows_inserted} products. Skipped {rows_skipped} (bot_allowed=false).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest product catalog into PostgreSQL")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to domain_config.json")
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Domain: {config.get('domain_id', 'unknown')}")

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        load_catalog(session, config)


if __name__ == "__main__":
    main()
