from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class AlertResponse(BaseModel):
    id:          int
    product_id:  Optional[int]     = None
    batch_id:    Optional[int]     = None
    alert_type:  str
    title:       str
    message:     str
    severity:    str
    is_read:     bool
    is_resolved: bool
    expiry_date: Optional[date]    = None
    stock_value: Optional[Decimal] = None
    created_at:  datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    total: int
    items: list[AlertResponse]


class AlertResolve(BaseModel):
    alert_id: int
