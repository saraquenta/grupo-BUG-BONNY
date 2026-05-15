from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Text, Numeric, ForeignKey, Date,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer,     primary_key=True, autoincrement=True)
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text,        nullable=True)
    color       = Column(String(7),   nullable=True)   # Hex: #3B82F6
    icon        = Column(String(50),  nullable=True)   # Nombre del ícono
    is_active   = Column(Boolean,     nullable=False, default=True)
    created_at  = Column(DateTime,    nullable=False, server_default=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    products = relationship("Product", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name}>"


class Product(Base):
    __tablename__ = "products"

    id                   = Column(Integer,       primary_key=True, autoincrement=True)
    code                 = Column(String(50),    nullable=False, unique=True, index=True)
    barcode              = Column(String(100),   nullable=True,  unique=True, index=True)
    qr_code              = Column(String(500),   nullable=True)
    name                 = Column(String(200),   nullable=False)
    description          = Column(Text,          nullable=True)
    category_id          = Column(Integer,       ForeignKey("categories.id"), nullable=True)
    unit                 = Column(String(30),    nullable=False)
    current_stock        = Column(Numeric(10, 2), nullable=False, default=0.00)
    min_stock            = Column(Numeric(10, 2), nullable=False, default=5.00)
    unit_price           = Column(Numeric(12, 2), nullable=True)
    location             = Column(String(100),   nullable=True)
    image_url            = Column(String(500),   nullable=True)
    technical_sheet_url  = Column(String(500),   nullable=True)
    requires_expiry      = Column(Boolean,       nullable=False, default=True)
    is_active            = Column(Boolean,       nullable=False, default=True)
    created_at           = Column(DateTime,      nullable=False, server_default=func.now())
    updated_at           = Column(DateTime,      nullable=True,  onupdate=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    category  = relationship("Category",     back_populates="products")
    batches   = relationship("ProductBatch", back_populates="product", cascade="all, delete-orphan")
    movements = relationship("Movement",     back_populates="product")
    alerts    = relationship("Alert",        back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} code={self.code} name={self.name}>"

    @property
    def is_low_stock(self) -> bool:
        return float(self.current_stock) <= float(self.min_stock)


class ProductBatch(Base):
    __tablename__ = "product_batches"

    id             = Column(Integer,        primary_key=True, autoincrement=True)
    product_id     = Column(Integer,        ForeignKey("products.id"), nullable=False)
    supplier_id    = Column(Integer,        ForeignKey("suppliers.id"), nullable=True)
    batch_number   = Column(String(100),    nullable=True)
    serial_number  = Column(String(100),    nullable=True)
    quantity       = Column(Numeric(10, 2), nullable=False, default=0.00)
    expiry_date    = Column(Date,           nullable=True)
    entry_date     = Column(Date,           nullable=False)
    purchase_price = Column(Numeric(12, 2), nullable=True)
    is_active      = Column(Boolean,        nullable=False, default=True)
    notes          = Column(Text,           nullable=True)
    created_at     = Column(DateTime,       nullable=False, server_default=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    product  = relationship("Product",  back_populates="batches")
    supplier = relationship("Supplier", back_populates="product_batches")

    def __repr__(self) -> str:
        return f"<ProductBatch id={self.id} product_id={self.product_id} lot={self.batch_number}>"
