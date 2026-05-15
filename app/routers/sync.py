"""
sync.py — Jayu Mendoza (Día 6 — Módulo M08)
Sincronización offline: la app Flutter sube operaciones realizadas sin internet.
POST /sync/batch → procesa la cola en orden cronológico.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.movement import Movement
from app.models.alert import OfflineSyncQueue
from app.core.deps import get_current_user
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class SyncOperation(BaseModel):
    """Una operación pendiente realizada offline."""
    local_id:   str            # ID único generado en Flutter (UUID)
    table_name: str            # products | movements | alerts
    operation:  str            # INSERT | UPDATE | DELETE
    payload:    dict           # Datos de la operación
    created_at: str            # ISO datetime de cuando se realizó offline

class SyncBatchRequest(BaseModel):
    device_id:  str
    operations: List[SyncOperation]

class SyncOperationResult(BaseModel):
    local_id: str
    success:  bool
    error:    Optional[str] = None
    server_id: Optional[int] = None  # ID generado en servidor (para INSERTs)


# ── Procesadores por tabla ────────────────────────────────────────────────────

def _process_movement(op: SyncOperation, db: Session, current_user: User) -> dict:
    """Procesa un movimiento de stock generado offline."""
    payload = op.payload

    product = db.query(Product).filter(
        Product.id == payload.get("product_id"),
        Product.is_active == True,
    ).first()

    if not product:
        raise ValueError(f"Producto {payload.get('product_id')} no encontrado.")

    movement_type = payload.get("movement_type")
    quantity = float(payload.get("quantity", 0))
    stock_before = float(product.current_stock)

    if movement_type == "ingreso":
        stock_after = stock_before + quantity
    elif movement_type in ("salida", "baja"):
        if quantity > stock_before:
            raise ValueError(
                f"Stock insuficiente al sincronizar. "
                f"Disponible: {stock_before}, solicitado: {quantity}."
            )
        stock_after = stock_before - quantity
    elif movement_type == "ajuste":
        stock_after = quantity
    else:
        raise ValueError(f"Tipo de movimiento inválido: {movement_type}")

    product.current_stock = stock_after

    movement = Movement(
        product_id     = payload["product_id"],
        batch_id       = payload.get("batch_id"),
        responsible_id = current_user.id,
        client_id      = payload.get("client_id"),
        movement_type  = movement_type,
        reason         = payload.get("reason"),
        quantity       = quantity,
        stock_before   = stock_before,
        stock_after    = stock_after,
        unit_price     = payload.get("unit_price"),
        destination    = payload.get("destination"),
        reference_doc  = payload.get("reference_doc"),
        notes          = f"[SYNC OFFLINE] {payload.get('notes', '')}",
    )
    db.add(movement)
    db.flush()  # Obtener ID sin commitear aún
    return {"server_id": movement.id}


def _process_product_update(op: SyncOperation, db: Session) -> dict:
    """Procesa actualización de un producto realizada offline."""
    payload = op.payload
    product_id = payload.get("id")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Producto {product_id} no encontrado.")

    # Campos que se pueden actualizar offline
    updatable = ["location", "notes", "min_stock"]
    for field in updatable:
        if field in payload:
            setattr(product, field, payload[field])

    return {"server_id": product.id}


# ── Procesador principal ──────────────────────────────────────────────────────

def _process_operation(op: SyncOperation, db: Session, current_user: User) -> SyncOperationResult:
    """Despacha la operación al procesador correcto."""
    try:
        if op.table_name == "movements" and op.operation == "INSERT":
            result = _process_movement(op, db, current_user)
        elif op.table_name == "products" and op.operation == "UPDATE":
            result = _process_product_update(op, db)
        else:
            # Operación no soportada → ignorar con warning
            logger.warning(f"Operación offline no soportada: {op.table_name}/{op.operation}")
            return SyncOperationResult(local_id=op.local_id, success=True, server_id=None)

        return SyncOperationResult(
            local_id=op.local_id,
            success=True,
            server_id=result.get("server_id"),
        )
    except ValueError as e:
        return SyncOperationResult(local_id=op.local_id, success=False, error=str(e))
    except Exception as e:
        logger.error(f"Error procesando sync op {op.local_id}: {e}")
        return SyncOperationResult(local_id=op.local_id, success=False, error="Error interno del servidor.")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/batch")
def sync_batch(
    req:     SyncBatchRequest,
    db:      Session = Depends(get_db),
    current: User    = Depends(get_current_user),
):
    """
    Recibe una lista de operaciones realizadas offline, las procesa en orden
    cronológico y retorna el resultado de cada una.

    La app Flutter envía esto cuando recupera la conexión a internet.
    """
    if not req.operations:
        return {
            "message":    "No hay operaciones para sincronizar.",
            "processed":  0,
            "results":    [],
        }

    # Ordenar por fecha de creación (orden cronológico)
    sorted_ops = sorted(req.operations, key=lambda o: o.created_at)

    results: List[SyncOperationResult] = []
    success_count = 0
    error_count   = 0

    # Registrar en la cola de sync (para auditoría)
    for op in sorted_ops:
        queue_entry = OfflineSyncQueue(
            device_id  = req.device_id,
            user_id    = current.id,
            operation  = op.operation,
            table_name = op.table_name,
            payload    = json.dumps(op.payload),
            is_synced  = False,
        )
        db.add(queue_entry)

    # Procesar cada operación
    for op in sorted_ops:
        result = _process_operation(op, db, current)
        results.append(result)

        if result.success:
            success_count += 1
        else:
            error_count += 1

    # Marcar cola como sincronizada para las operaciones exitosas
    db.query(OfflineSyncQueue).filter(
        OfflineSyncQueue.device_id == req.device_id,
        OfflineSyncQueue.is_synced == False,
    ).update({"is_synced": True, "synced_at": datetime.utcnow()})

    # Commit de toda la transacción
    try:
        db.commit()
        # Invalidar caché de productos tras sync
        redis_service.invalidate_products()
    except Exception as e:
        db.rollback()
        logger.error(f"Error en commit de sync batch: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar las operaciones sincronizadas.")

    logger.info(
        f"Sync completado: device={req.device_id} user={current.username} "
        f"ops={len(sorted_ops)} ok={success_count} err={error_count}"
    )

    return {
        "message":       f"Sincronización completada. {success_count} éxitos, {error_count} errores.",
        "processed":     len(sorted_ops),
        "success_count": success_count,
        "error_count":   error_count,
        "results": [
            {
                "local_id":  r.local_id,
                "success":   r.success,
                "server_id": r.server_id,
                "error":     r.error,
            }
            for r in results
        ],
    }


@router.get("/status")
def sync_status(
    db:      Session = Depends(get_db),
    current: User    = Depends(get_current_user),
):
    """Retorna el estado del servidor para que la app valide la conexión antes de sincronizar."""
    from app.database import check_db_connection
    return {
        "server_online": True,
        "database_ok":   check_db_connection(),
        "user_id":       current.id,
        "timestamp":     datetime.utcnow().isoformat(),
    }


@router.get("/queue/pending")
def get_pending_queue(
    device_id: Optional[str] = None,
    db:        Session       = Depends(get_db),
    _:         User          = Depends(get_current_user),
):
    """Lista operaciones en cola pendientes de sincronizar (útil para debugging)."""
    from sqlalchemy import String
    query = db.query(OfflineSyncQueue).filter(OfflineSyncQueue.is_synced == False)

    if device_id:
        query = query.filter(OfflineSyncQueue.device_id == device_id)

    items = query.order_by(OfflineSyncQueue.created_at).limit(100).all()

    return {
        "pending": len(items),
        "items": [
            {
                "id":         i.id,
                "device_id":  i.device_id,
                "operation":  i.operation,
                "table_name": i.table_name,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ],
    }
