from sqlalchemy import (
    Column, Integer, String, DateTime, Text,
    Numeric, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Movement(Base):
    __tablename__ = "movements"

    id             = Column(Integer,        primary_key=True, autoincrement=True)
    product_id     = Column(Integer,        ForeignKey("products.id"),       nullable=False)
    batch_id       = Column(Integer,        ForeignKey("product_batches.id"), nullable=True)
    responsible_id = Column(Integer,        ForeignKey("users.id"),           nullable=False)
    client_id      = Column(Integer,        ForeignKey("clients.id"),         nullable=True)

    movement_type  = Column(
                         SAEnum("ingreso", "salida", "ajuste", "baja", name="movement_type_enum"),
                         nullable=False,
                     )
    reason         = Column(
                         SAEnum(
                             "compra",
                             "devolucion",
                             "venta",
                             "consumo_interno",
                             "prestamo",
                             "baja_danio",
                             "baja_vencimiento",
                             "ajuste_manual",
                             "transferencia",
                             name="movement_reason_enum",
                         ),
                         nullable=True,
                     )

    quantity       = Column(Numeric(10, 2), nullable=False)
    stock_before   = Column(Numeric(10, 2), nullable=False)
    stock_after    = Column(Numeric(10, 2), nullable=False)
    unit_price     = Column(Numeric(12, 2), nullable=True)
    destination    = Column(String(200),    nullable=True)
    reference_doc  = Column(String(100),    nullable=True)
    notes          = Column(Text,           nullable=True)
    created_at     = Column(DateTime,       nullable=False, server_default=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    product     = relationship("Product", back_populates="movements")
    responsible = relationship("User",    back_populates="movements", foreign_keys=[responsible_id])
    client      = relationship("Client")
    batch       = relationship("ProductBatch")

    def __repr__(self) -> str:
        return f"<Movement id={self.id} type={self.movement_type} qty={self.quantity}>"
