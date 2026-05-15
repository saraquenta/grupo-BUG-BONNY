from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional

from app.database import get_db
from app.models.product import Product, ProductBatch
from app.models.user import User
from app.core.deps import get_current_user, require_admin, require_supervisor_or_admin
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductBatchCreate, ProductBatchResponse,
)

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
def list_products(
    skip:        int            = Query(0, ge=0),
    limit:       int            = Query(50, ge=1, le=200),
    search:      Optional[str]  = Query(None, description="Buscar por nombre, código o barcode"),
    category_id: Optional[int]  = Query(None),
    low_stock:   Optional[bool] = Query(None, description="Solo productos con stock bajo"),
    is_active:   Optional[bool] = Query(True),
    db:          Session        = Depends(get_db),
    _:           User           = Depends(get_current_user),
):
    """Lista productos con filtros y paginación."""
    query = db.query(Product).options(joinedload(Product.category))

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.code.ilike(term),
                Product.barcode.ilike(term),
            )
        )
    if low_stock:
        query = query.filter(Product.current_stock <= Product.min_stock)

    total = query.count()
    items = query.order_by(Product.name).offset(skip).limit(limit).all()

    return ProductListResponse(total=total, items=items)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_supervisor_or_admin),
):
    """Crea un nuevo producto. Supervisor o Admin."""
    if db.query(Product).filter(Product.code == data.code).first():
        raise HTTPException(status_code=400, detail=f"Ya existe un producto con el código '{data.code}'.")
    if data.barcode and db.query(Product).filter(Product.barcode == data.barcode).first():
        raise HTTPException(status_code=400, detail="El barcode ya está registrado.")

    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product


@router.get("/by-code/{code}", response_model=ProductResponse)
def get_product_by_code(
    code: str,
    db:   Session = Depends(get_db),
    _:    User    = Depends(get_current_user),
):
    """Busca un producto por código interno o barcode. Útil para el scanner QR."""
    product = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(or_(Product.code == code, Product.barcode == code))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail=f"No se encontró producto con código '{code}'.")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data:       ProductUpdate,
    db:         Session = Depends(get_db),
    _:          User    = Depends(require_supervisor_or_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def deactivate_product(
    product_id: int,
    db:         Session = Depends(get_db),
    _:          User    = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    product.is_active = False
    db.commit()
    return {"message": f"Producto '{product.name}' desactivado."}


# ── Lotes ────────────────────────────────────────────────────────────────────
@router.get("/{product_id}/batches", response_model=list[ProductBatchResponse])
def list_batches(
    product_id: int,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    """Lista los lotes de un producto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    return (
        db.query(ProductBatch)
        .filter(ProductBatch.product_id == product_id, ProductBatch.is_active == True)
        .order_by(ProductBatch.expiry_date)
        .all()
    )


@router.post("/{product_id}/batches", response_model=ProductBatchResponse, status_code=201)
def create_batch(
    product_id: int,
    data:       ProductBatchCreate,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    """Registra un nuevo lote para un producto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    batch_data = data.model_dump()
    batch_data["product_id"] = product_id
    batch = ProductBatch(**batch_data)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch
