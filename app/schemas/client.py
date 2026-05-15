from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClientBase(BaseModel):
    name:           str
    client_type:    str = "publico"   # publico | privado
    contact_person: Optional[str] = None
    phone:          Optional[str] = None
    email:          Optional[str] = None
    address:        Optional[str] = None
    nit:            Optional[str] = None
    notes:          Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name:           Optional[str]  = None
    client_type:    Optional[str]  = None
    contact_person: Optional[str]  = None
    phone:          Optional[str]  = None
    email:          Optional[str]  = None
    address:        Optional[str]  = None
    nit:            Optional[str]  = None
    notes:          Optional[str]  = None
    is_active:      Optional[bool] = None


class ClientResponse(ClientBase):
    id:         int
    is_active:  bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    total: int
    items: list[ClientResponse]
