from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime, date

from app.database import get_db
from app.models.product import Product
from app.models.movement import Movement
from app.models.user import User
from app.core.deps import get_current_user, require_supervisor_or_admin
from app.schemas.movement import MovementCreate, MovementResponse, MovementListResponse

router = APIRouter()

TIPOS_INGRESO = ("ingreso",)
TIPOS_SALIDA  = ("salida", "baja", "ajuste")


@router.get("/", response_model=MovementListResponse)
def list_movements(
    skip:          int            = Query(0, ge=0),
    limit:         int            = Query(50, ge=1, le=200),
    product_id:    Optional[int]  = Query(None),
    movement_type: Optional[str]  = Query(None),
    date_from:     Optional[date] = Query(None),
    date_to:       Optional[date] = Query(None),
    db:            Session        = Depends(get_db),
    _:             User           = Depends(get_current_user),
):
    """Lista movimientos con filtros de producto, tipo y rango de fechas."""
    query = db.query(Movement)

    if product_id:
        query = query.filter(Movement.product_id == product_id)
    if movement_type:
        query = query.filter(Movement.movement_type == movement_type)
    if date_from:
        query = query.filter(Movement.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Movement.created_at <= datetime.combine(date_to, datetime.max.time()))

    total = query.count()
    items = query.order_by(Movement.created_at.desc()).offset(skip).limit(limit).all()

    return MovementListResponse(total=total, items=items)


@router.post("/", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(
    data:    MovementCreate,
    db:      Session = Depends(get_db),
    current: User    = Depends(get_current_user),
):
    """
    Registra un movimiento de stock (ingreso, salida, ajuste o baja).
    Actualiza el stock del producto automáticamente.
    """
    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.is_active == True,
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    stock_before = float(product.current_stock)

    # Calcular nuevo stock según el tipo
    if data.movement_type == "ingreso":
        stock_after = stock_before + float(data.quantity)
    elif data.movement_type in ("salida", "baja"):
        if float(data.quantity) > stock_before:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente. Disponible: {stock_before}, solicitado: {data.quantity}.",
            )
        stock_after = stock_before - float(data.quantity)
    elif data.movement_type == "ajuste":
        # En ajuste, quantity es el nuevo stock absoluto
        stock_after = float(data.quantity)
    else:
        raise HTTPException(status_code=400, detail="Tipo de movimiento inválido.")

    # Actualizar stock del producto
    product.current_stock = stock_after

    # Crear el registro de movimiento
    movement = Movement(
        product_id     = data.product_id,
        batch_id       = data.batch_id,
        responsible_id = current.id,
        client_id      = data.client_id,
        movement_type  = data.movement_type,
        reason         = data.reason,
        quantity       = data.quantity,
        stock_before   = stock_before,
        stock_after    = stock_after,
        unit_price     = data.unit_price,
        destination    = data.destination,
        reference_doc  = data.reference_doc,
        notes          = data.notes,
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/{movement_id}", response_model=MovementResponse)
def get_movement(
    movement_id: int,
    db:          Session = Depends(get_db),
    _:           User    = Depends(get_current_user),
):
    movement = db.query(Movement).filter(Movement.id == movement_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado.")
    return movement
