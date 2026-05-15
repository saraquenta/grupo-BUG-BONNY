from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id             = Column(Integer,     primary_key=True, autoincrement=True)
    name           = Column(String(200), nullable=False)
    contact_person = Column(String(150), nullable=True)
    phone          = Column(String(30),  nullable=True)
    email          = Column(String(100), nullable=True)
    address        = Column(Text,        nullable=True)
    nit            = Column(String(20),  nullable=True)
    is_active      = Column(Boolean,     nullable=False, default=True)
    notes          = Column(Text,        nullable=True)
    created_at     = Column(DateTime,    nullable=False, server_default=func.now())
    updated_at     = Column(DateTime,    nullable=True,  onupdate=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    product_batches = relationship("ProductBatch", back_populates="supplier")

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name={self.name}>"
