from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class MovementCreate(BaseModel):
    product_id:    int
    movement_type: str                 # ingreso | salida | ajuste | baja
    quantity:      Decimal
    reason:        Optional[str]     = None
    batch_id:      Optional[int]     = None
    client_id:     Optional[int]     = None
    unit_price:    Optional[Decimal] = None
    destination:   Optional[str]     = None
    reference_doc: Optional[str]     = None
    notes:         Optional[str]     = None


class MovementResponse(BaseModel):
    id:             int
    product_id:     int
    movement_type:  str
    reason:         Optional[str]     = None
    quantity:       Decimal
    stock_before:   Decimal
    stock_after:    Decimal
    unit_price:     Optional[Decimal] = None
    destination:    Optional[str]     = None
    reference_doc:  Optional[str]     = None
    notes:          Optional[str]     = None
    responsible_id: int
    client_id:      Optional[int]     = None
    batch_id:       Optional[int]     = None
    created_at:     datetime

    model_config = {"from_attributes": True}


class MovementListResponse(BaseModel):
    total: int
    items: list[MovementResponse]
