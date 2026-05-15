"""
notifications.py — Jayu Mendoza (Día 5)
Endpoints para envío de push notifications con Firebase FCM.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, timedelta
import logging

from app.database import get_db
from app.models.user import User
from app.models.product import Product, ProductBatch
from app.models.alert import Alert
from app.core.deps import get_current_user, require_admin, require_supervisor_or_admin
from app.services.firebase_service import firebase_service
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterTokenRequest(BaseModel):
    firebase_token: str

class SendNotificationRequest(BaseModel):
    user_id:  Optional[int]   = None   # Si None → broadcast a todos
    title:    str
    body:     str
    data:     Optional[dict]  = {}

class BroadcastRequest(BaseModel):
    title:      str
    body:       str
    roles:      Optional[List[str]] = None  # admin, supervisor, almacenero
    data:       Optional[dict] = {}


# ── Registro de token FCM ─────────────────────────────────────────────────────

@router.post("/register-token")
def register_fcm_token(
    req:     RegisterTokenRequest,
    db:      Session = Depends(get_db),
    current: User    = Depends(get_current_user),
):
    """
    Registra el token FCM del dispositivo del usuario.
    La app Flutter llama a este endpoint cada vez que inicia sesión.
    """
    # Guardar en BD
    current.firebase_token = req.firebase_token
    db.commit()

    # Guardar en Redis para acceso rápido
    redis_service.store_fcm_token(current.id, req.firebase_token)

    logger.info(f"Token FCM registrado para usuario {current.username}")
    return {"message": "Token FCM registrado correctamente.", "user_id": current.id}


# ── Envío manual de notificación ──────────────────────────────────────────────

@router.post("/send")
def send_notification(
    req: SendNotificationRequest,
    db:  Session = Depends(get_db),
    _:   User    = Depends(require_supervisor_or_admin),
):
    """
    Envía una notificación push a un usuario específico o a todos.
    Solo Admin y Supervisor pueden enviar.
    """
    if req.user_id:
        # Enviar a usuario específico
        user = db.query(User).filter(User.id == req.user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        # Buscar token: primero Redis, luego BD
        token = redis_service.get_fcm_token(user.id) or user.firebase_token
        if not token:
            raise HTTPException(status_code=400, detail="El usuario no tiene token FCM registrado.")

        result = firebase_service.send_to_token(
            token=token, title=req.title, body=req.body, data=req.data
        )
        return {
            "success": result.success,
            "sent_to": user.username,
            "message_id": result.message_id,
            "error": result.error,
        }
    else:
        # Broadcast a todos los usuarios activos con token
        users = db.query(User).filter(User.is_active == True, User.firebase_token != None).all()
        tokens = [u.firebase_token for u in users if u.firebase_token]

        if not tokens:
            return {"success": False, "message": "No hay usuarios con token FCM."}

        result = firebase_service.send_multicast(
            tokens=tokens, title=req.title, body=req.body, data=req.data
        )
        return {
            "success":  result["success"] > 0,
            "sent_to":  len(tokens),
            "success_count": result["success"],
            "failure_count": result["failure"],
        }


# ── Broadcast por roles ───────────────────────────────────────────────────────

@router.post("/broadcast")
def broadcast_notification(
    req: BroadcastRequest,
    db:  Session = Depends(get_db),
    _:   User    = Depends(require_admin),
):
    """Envía notificación a todos los usuarios con un rol específico (solo Admin)."""
    query = db.query(User).filter(User.is_active == True, User.firebase_token != None)

    if req.roles:
        query = query.filter(User.role.in_(req.roles))

    users = query.all()
    tokens = [u.firebase_token for u in users if u.firebase_token]

    if not tokens:
        return {"message": "No hay usuarios con token FCM en los roles indicados.", "sent": 0}

    result = firebase_service.send_multicast(
        tokens=tokens, title=req.title, body=req.body, data=req.data
    )

    return {
        "sent":          len(tokens),
        "success_count": result["success"],
        "failure_count": result["failure"],
        "roles":         req.roles or ["all"],
    }


# ── Notificaciones automáticas de alertas ─────────────────────────────────────

@router.post("/send-alert-notifications")
def send_alert_notifications(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_supervisor_or_admin),
):
    """
    Detecta alertas activas (stock bajo + vencimientos) y notifica a todos
    los admins y supervisores. Este endpoint es llamado por el scheduler diario.
    """
    # 1) Productos con stock bajo
    low_stock_products = db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock <= Product.min_stock,
    ).all()

    # 2) Productos que vencen en ≤ 30 días
    cutoff_30 = date.today() + timedelta(days=30)
    expiring_batches = db.query(ProductBatch).filter(
        ProductBatch.is_active == True,
        ProductBatch.expiry_date <= cutoff_30,
        ProductBatch.expiry_date >= date.today(),
    ).all()

    # 3) Obtener admins y supervisores con token
    recipients = db.query(User).filter(
        User.is_active == True,
        User.role.in_(["admin", "supervisor"]),
        User.firebase_token != None,
    ).all()

    tokens = [u.firebase_token for u in recipients if u.firebase_token]

    if not tokens:
        return {"message": "No hay destinatarios con token FCM."}

    sent_notifications = []

    # Notificar stock bajo
    for product in low_stock_products:
        result = firebase_service.send_multicast(
            tokens=tokens,
            title="⚠️ Stock Crítico",
            body=f"{product.name}: {float(product.current_stock)} {product.unit} (mín: {float(product.min_stock)})",
            data={"type": "stock_minimo", "product_id": str(product.id)},
        )
        sent_notifications.append({
            "type":    "stock_minimo",
            "product": product.name,
            "sent":    result["success"],
        })

    # Notificar vencimientos (agrupar en un solo mensaje si son muchos)
    if expiring_batches:
        count_7  = sum(1 for b in expiring_batches if b.expiry_date <= date.today() + timedelta(days=7))
        count_15 = sum(1 for b in expiring_batches if b.expiry_date <= date.today() + timedelta(days=15))

        emoji = "🔴" if count_7 > 0 else "🟡"
        result = firebase_service.send_multicast(
            tokens=tokens,
            title=f"{emoji} Productos por Vencer",
            body=f"{len(expiring_batches)} lotes próximos a vencer ({count_7} en ≤7 días).",
            data={"type": "vencimiento", "count": str(len(expiring_batches))},
        )
        sent_notifications.append({
            "type":  "vencimiento",
            "count": len(expiring_batches),
            "sent":  result["success"],
        })

    return {
        "message":       "Notificaciones de alertas enviadas.",
        "recipients":    len(tokens),
        "notifications": sent_notifications,
        "low_stock":     len(low_stock_products),
        "expiring":      len(expiring_batches),
    }
