from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.supplier import Supplier
from app.models.user import User
from app.core.deps import get_current_user, require_supervisor_or_admin
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse, SupplierListResponse

router = APIRouter()


@router.get("/", response_model=SupplierListResponse)
def list_suppliers(
    skip:   int           = Query(0, ge=0),
    limit:  int           = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    db:     Session       = Depends(get_db),
    _:      User          = Depends(get_current_user),
):
    query = db.query(Supplier).filter(Supplier.is_active == True)

    if search:
        term = f"%{search}%"
        query = query.filter(
            Supplier.name.ilike(term) | Supplier.nit.ilike(term)
        )

    total = query.count()
    items = query.order_by(Supplier.name).offset(skip).limit(limit).all()
    return SupplierListResponse(total=total, items=items)


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_supervisor_or_admin),
):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db:          Session = Depends(get_db),
    _:           User    = Depends(get_current_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data:        SupplierUpdate,
    db:          Session = Depends(get_db),
    _:           User    = Depends(require_supervisor_or_admin),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}")
def deactivate_supplier(
    supplier_id: int,
    db:          Session = Depends(get_db),
    _:           User    = Depends(require_supervisor_or_admin),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")

    supplier.is_active = False
    db.commit()
    return {"message": f"Proveedor '{supplier.name}' desactivado."}
