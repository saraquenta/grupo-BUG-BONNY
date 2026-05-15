from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SupplierBase(BaseModel):
    name:           str
    contact_person: Optional[str] = None
    phone:          Optional[str] = None
    email:          Optional[str] = None
    address:        Optional[str] = None
    nit:            Optional[str] = None
    notes:          Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name:           Optional[str]  = None
    contact_person: Optional[str]  = None
    phone:          Optional[str]  = None
    email:          Optional[str]  = None
    address:        Optional[str]  = None
    nit:            Optional[str]  = None
    notes:          Optional[str]  = None
    is_active:      Optional[bool] = None


class SupplierResponse(SupplierBase):
    id:         int
    is_active:  bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SupplierListResponse(BaseModel):
    total: int
    items: list[SupplierResponse]
