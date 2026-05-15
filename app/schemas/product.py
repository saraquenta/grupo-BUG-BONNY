from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


# ── Category ────────────────────────────────────────────────────────────────
class CategoryBase(BaseModel):
    name:        str
    description: Optional[str]   = None
    color:       Optional[str]   = None
    icon:        Optional[str]   = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name:        Optional[str]  = None
    description: Optional[str]  = None
    color:       Optional[str]  = None
    icon:        Optional[str]  = None
    is_active:   Optional[bool] = None


class CategoryResponse(CategoryBase):
    id:        int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Product ─────────────────────────────────────────────────────────────────
class ProductBase(BaseModel):
    code:                str
    name:                str
    unit:                str
    min_stock:           Decimal = Decimal("5.00")
    category_id:         Optional[int]     = None
    barcode:             Optional[str]     = None
    description:         Optional[str]     = None
    unit_price:          Optional[Decimal] = None
    location:            Optional[str]     = None
    image_url:           Optional[str]     = None
    technical_sheet_url: Optional[str]     = None
    requires_expiry:     bool              = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name:                Optional[str]     = None
    barcode:             Optional[str]     = None
    description:         Optional[str]     = None
    category_id:         Optional[int]     = None
    unit:                Optional[str]     = None
    min_stock:           Optional[Decimal] = None
    unit_price:          Optional[Decimal] = None
    location:            Optional[str]     = None
    image_url:           Optional[str]     = None
    technical_sheet_url: Optional[str]     = None
    requires_expiry:     Optional[bool]    = None
    is_active:           Optional[bool]    = None


class ProductResponse(ProductBase):
    id:            int
    current_stock: Decimal
    is_active:     bool
    is_low_stock:  bool
    qr_code:       Optional[str]      = None
    category:      Optional[CategoryResponse] = None
    created_at:    datetime
    updated_at:    Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    total: int
    items: list[ProductResponse]


# ── ProductBatch ─────────────────────────────────────────────────────────────
class ProductBatchBase(BaseModel):
    product_id:     int
    entry_date:     date
    quantity:       Decimal
    supplier_id:    Optional[int]     = None
    batch_number:   Optional[str]     = None
    serial_number:  Optional[str]     = None
    expiry_date:    Optional[date]    = None
    purchase_price: Optional[Decimal] = None
    notes:          Optional[str]     = None


class ProductBatchCreate(ProductBatchBase):
    pass


class ProductBatchResponse(ProductBatchBase):
    id:         int
    is_active:  bool
    created_at: datetime

    model_config = {"from_attributes": True}
