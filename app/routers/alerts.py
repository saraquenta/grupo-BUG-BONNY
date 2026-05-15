from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.core.deps import get_current_user
from app.schemas.alert import AlertResponse, AlertListResponse

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
def list_alerts(
    skip:       int            = Query(0, ge=0),
    limit:      int            = Query(50, ge=1, le=200),
    is_read:    Optional[bool] = Query(None),
    is_resolved:Optional[bool] = Query(False),
    severity:   Optional[str]  = Query(None),
    db:         Session        = Depends(get_db),
    _:          User           = Depends(get_current_user),
):
    """Lista alertas del sistema con filtros."""
    query = db.query(Alert)

    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    if severity:
        query = query.filter(Alert.severity == severity)

    total = query.count()
    items = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    return AlertListResponse(total=total, items=items)


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    """Retorna el conteo de alertas no leídas (para el badge de notificaciones)."""
    count = db.query(Alert).filter(
        Alert.is_read == False,
        Alert.is_resolved == False,
    ).count()
    return {"unread": count}


@router.post("/{alert_id}/mark-read")
def mark_alert_read(
    alert_id: int,
    db:       Session = Depends(get_db),
    _:        User    = Depends(get_current_user),
):
    """Marca una alerta como leída."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")

    alert.is_read = True
    db.commit()
    return {"message": "Alerta marcada como leída."}


@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    """Marca todas las alertas como leídas."""
    db.query(Alert).filter(Alert.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "Todas las alertas marcadas como leídas."}


@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db:       Session = Depends(get_db),
    current:  User    = Depends(get_current_user),
):
    """Marca una alerta como resuelta."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")

    alert.is_resolved = True
    alert.is_read     = True
    alert.resolved_by = current.id
    alert.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": "Alerta resuelta."}
