"""Seed the deterministic electrical-wholesaler demo through the real ingestion stack."""
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select

from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import BusinessModel, CustomerModel, ProductModel, SaleLineModel, SaleModel
from packages.shared.database.session import SessionLocal

BUSINESS_ID = UUID("11111111-1111-1111-1111-111111111111")
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "electrical_wholesaler_demo.csv"


def seed() -> None:
    db = SessionLocal()
    try:
        business = db.get(BusinessModel, BUSINESS_ID)
        if business is None:
            business = BusinessModel(id=BUSINESS_ID, name="Demo Electrical Wholesaler", industry="distribution")
            db.add(business)
            db.commit()

        sale_ids = select(SaleModel.id).where(SaleModel.business_id == BUSINESS_ID)
        db.execute(delete(SaleLineModel).where(SaleLineModel.sale_id.in_(sale_ids)))
        db.execute(delete(SaleModel).where(SaleModel.business_id == BUSINESS_ID))
        db.execute(delete(CustomerModel).where(CustomerModel.business_id == BUSINESS_ID))
        db.execute(delete(ProductModel).where(ProductModel.business_id == BUSINESS_ID))
        db.commit()

        result, prepared = prepare_file(FIXTURE)
        if result.rows_rejected:
            raise RuntimeError(f"Demo fixture has {result.rows_rejected} rejected rows: {result.issues[:3]}")
        created = persist_sales(db, BUSINESS_ID, [row.values for row in prepared])
        print(f"Seeded {business.name}: {created} sales, {result.rows_read} source rows")
        print(f"Business ID: {BUSINESS_ID}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
