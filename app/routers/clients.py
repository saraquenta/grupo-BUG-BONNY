from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.core.deps import get_current_user, require_supervisor_or_admin
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientListResponse

router = APIRouter()


@router.get("/", response_model=ClientListResponse)
def list_clients(
    skip:        int            = Query(0, ge=0),
    limit:       int            = Query(50, ge=1, le=200),
    search:      Optional[str]  = Query(None),
    client_type: Optional[str]  = Query(None),
    db:          Session        = Depends(get_db),
    _:           User           = Depends(get_current_user),
):
    query = db.query(Client).filter(Client.is_active == True)

    if client_type:
        query = query.filter(Client.client_type == client_type)
    if search:
        term = f"%{search}%"
        query = query.filter(
            Client.name.ilike(term) | Client.nit.ilike(term)
        )

    total = query.count()
    items = query.order_by(Client.name).offset(skip).limit(limit).all()
    return ClientListResponse(total=total, items=items)


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate,
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_supervisor_or_admin),
):
    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db:        Session = Depends(get_db),
    _:         User    = Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    data:      ClientUpdate,
    db:        Session = Depends(get_db),
    _:         User    = Depends(require_supervisor_or_admin),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def deactivate_client(
    client_id: int,
    db:        Session = Depends(get_db),
    _:         User    = Depends(require_supervisor_or_admin),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    client.is_active = False
    db.commit()
    return {"message": f"Cliente '{client.name}' desactivado."}
