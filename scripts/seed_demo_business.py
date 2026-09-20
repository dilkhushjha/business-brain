"""Seed the deterministic electrical-wholesaler demo through the real ingestion stack."""
from pathlib import Path
import os
from uuid import UUID

from sqlalchemy import delete, select, text
from pwdlib import PasswordHash

from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import BusinessModel, CustomerModel, ProductModel, SaleLineModel, SaleModel
from packages.shared.database.session import SessionLocal

BUSINESS_ID = UUID("11111111-1111-1111-1111-111111111111")
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "electrical_wholesaler_demo.csv"
DEMO_USERNAME = os.getenv("BUSINESS_BRAIN_DEMO_USERNAME", "demo")
DEMO_EMAIL = os.getenv("BUSINESS_BRAIN_DEMO_EMAIL", "demo@businessbrain.local")


def seed() -> None:
    db = SessionLocal()
    try:
        business = db.get(BusinessModel, BUSINESS_ID)
        if business is None:
            business = BusinessModel(id=BUSINESS_ID, name="Demo Electrical Wholesaler", industry="distribution")
            db.add(business)
            db.commit()

        demo_password = os.getenv("BUSINESS_BRAIN_DEMO_PASSWORD")
        if demo_password:
            user = db.execute(
                text("SELECT id FROM users WHERE lower(username)=:username"),
                {"username": DEMO_USERNAME},
            ).scalar_one_or_none()
            if user is None:
                from uuid import uuid4
                user_id = uuid4()
                db.execute(
                    text("INSERT INTO users (id, username, email, password_hash) VALUES (:id, :username, :email, :password_hash)"),
                    {"id": str(user_id), "username": DEMO_USERNAME, "email": DEMO_EMAIL, "password_hash": PasswordHash.recommended().hash(demo_password)},
                )
                db.execute(
                    text("INSERT INTO user_businesses (user_id, business_id, role) VALUES (:user_id, :business_id, 'owner')"),
                    {"user_id": str(user_id), "business_id": str(BUSINESS_ID)},
                )
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
