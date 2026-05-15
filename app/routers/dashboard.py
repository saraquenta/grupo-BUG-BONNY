"""
dashboard.py — Jayu Mendoza (Día 5-6)
Dashboard con KPIs en tiempo real. Redis caché de 2 minutos.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta, datetime
import logging

from app.database import get_db
from app.models.user import User
from app.models.product import Product, ProductBatch
from app.models.movement import Movement
from app.models.alert import Alert
from app.core.deps import get_current_user
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
def get_dashboard(
    db:      Session = Depends(get_db),
    current: User    = Depends(get_current_user),
):
    """
    Retorna todos los KPIs del dashboard.
    Los datos se cachean en Redis por 2 minutos para aligerar la BD.
    """
    # Intentar obtener del caché
    cached = redis_service.get_dashboard(current.id)
    if cached:
        cached["from_cache"] = True
        return cached

    # ── Calcular KPIs ────────────────────────────────────────────────────────
    today      = date.today()
    week_start = today - timedelta(days=7)
    month_start = today.replace(day=1)

    # Total productos activos
    total_products = db.query(func.count(Product.id)).filter(
        Product.is_active == True
    ).scalar() or 0

    # Productos con stock crítico (≤ stock mínimo)
    critical_stock = db.query(func.count(Product.id)).filter(
        Product.is_active == True,
        Product.current_stock <= Product.min_stock,
    ).scalar() or 0

    # Valor total del inventario (stock × precio_unitario)
    inventory_value = db.query(
        func.sum(Product.current_stock * Product.unit_price)
    ).filter(
        Product.is_active == True,
        Product.unit_price != None,
    ).scalar() or 0.0

    # Movimientos de hoy
    today_movements = db.query(func.count(Movement.id)).filter(
        func.date(Movement.created_at) == today
    ).scalar() or 0

    # Movimientos de esta semana
    week_movements = db.query(func.count(Movement.id)).filter(
        Movement.created_at >= datetime.combine(week_start, datetime.min.time())
    ).scalar() or 0

    # Ingresos vs Salidas del mes
    month_ingresos = db.query(func.sum(Movement.quantity)).filter(
        Movement.movement_type == "ingreso",
        Movement.created_at >= datetime.combine(month_start, datetime.min.time()),
    ).scalar() or 0.0

    month_salidas = db.query(func.sum(Movement.quantity)).filter(
        Movement.movement_type.in_(["salida", "baja"]),
        Movement.created_at >= datetime.combine(month_start, datetime.min.time()),
    ).scalar() or 0.0

    # Alertas activas
    active_alerts = db.query(func.count(Alert.id)).filter(
        Alert.is_resolved == False,
    ).scalar() or 0

    unread_alerts = db.query(func.count(Alert.id)).filter(
        Alert.is_resolved == False,
        Alert.is_read == False,
    ).scalar() or 0

    # Productos que vencen en ≤ 30 días
    cutoff_30 = today + timedelta(days=30)
    expiring_soon = db.query(func.count(ProductBatch.id)).filter(
        ProductBatch.is_active == True,
        ProductBatch.expiry_date <= cutoff_30,
        ProductBatch.expiry_date >= today,
    ).scalar() or 0

    expiring_critical = db.query(func.count(ProductBatch.id)).filter(
        ProductBatch.is_active == True,
        ProductBatch.expiry_date <= today + timedelta(days=7),
        ProductBatch.expiry_date >= today,
    ).scalar() or 0

    # Top 5 productos con más movimientos este mes
    top_products = (
        db.query(
            Product.name,
            Product.code,
            func.count(Movement.id).label("movements_count"),
        )
        .join(Movement, Movement.product_id == Product.id)
        .filter(
            Movement.created_at >= datetime.combine(month_start, datetime.min.time())
        )
        .group_by(Product.id, Product.name, Product.code)
        .order_by(func.count(Movement.id).desc())
        .limit(5)
        .all()
    )

    # Movimientos por tipo en los últimos 7 días
    movements_by_type = (
        db.query(
            Movement.movement_type,
            func.count(Movement.id).label("count"),
        )
        .filter(Movement.created_at >= datetime.combine(week_start, datetime.min.time()))
        .group_by(Movement.movement_type)
        .all()
    )

    # ── Armar respuesta ──────────────────────────────────────────────────────
    dashboard_data = {
        "from_cache": False,
        "generated_at": datetime.utcnow().isoformat(),
        "user": {
            "id":       current.id,
            "name":     current.full_name,
            "role":     current.role,
        },

        # KPIs principales
        "kpis": {
            "total_products":     total_products,
            "critical_stock":     critical_stock,
            "today_movements":    today_movements,
            "week_movements":     week_movements,
            "inventory_value":    round(float(inventory_value), 2),
            "active_alerts":      active_alerts,
            "unread_alerts":      unread_alerts,
            "expiring_soon":      expiring_soon,
            "expiring_critical":  expiring_critical,
        },

        # Movimientos del mes
        "monthly": {
            "ingresos": round(float(month_ingresos), 2),
            "salidas":  round(float(month_salidas), 2),
            "balance":  round(float(month_ingresos) - float(month_salidas), 2),
        },

        # Top productos
        "top_products": [
            {"name": p.name, "code": p.code, "movements": p.movements_count}
            for p in top_products
        ],

        # Movimientos por tipo (para gráfica)
        "movements_by_type": {
            m.movement_type: m.count for m in movements_by_type
        },

        # Semáforo general del inventario
        "health": _calculate_health(critical_stock, total_products, expiring_critical, unread_alerts),
    }

    # Cachear en Redis 2 minutos
    redis_service.cache_dashboard(current.id, dashboard_data)

    return dashboard_data


def _calculate_health(critical: int, total: int, expiring: int, alerts: int) -> str:
    """Determina el estado general del inventario."""
    if total == 0:
        return "sin_datos"
    ratio_critico = critical / total
    if ratio_critico > 0.2 or expiring > 5 or alerts > 10:
        return "critico"
    if ratio_critico > 0.1 or expiring > 2 or alerts > 3:
        return "advertencia"
    return "saludable"


@router.get("/alerts-summary")
def alerts_summary(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    """Resumen de alertas por severidad. Cacheable independientemente."""
    # Intentar Redis
    cached = redis_service.get_alerts()
    if cached:
        return {"from_cache": True, "alerts": cached}

    today = date.today()

    # Stock bajo
    low_stock = db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock <= Product.min_stock,
    ).limit(20).all()

    # Vencimientos
    batches_7  = db.query(ProductBatch).filter(
        ProductBatch.is_active == True,
        ProductBatch.expiry_date <= today + timedelta(days=7),
        ProductBatch.expiry_date >= today,
    ).all()

    batches_30 = db.query(ProductBatch).filter(
        ProductBatch.is_active == True,
        ProductBatch.expiry_date <= today + timedelta(days=30),
        ProductBatch.expiry_date > today + timedelta(days=7),
    ).all()

    alerts_data = {
        "low_stock": [
            {
                "id":            p.id,
                "name":          p.name,
                "code":          p.code,
                "current_stock": float(p.current_stock),
                "min_stock":     float(p.min_stock),
                "unit":          p.unit,
            }
            for p in low_stock
        ],
        "expiring_7_days":  [
            {
                "batch_id":    b.id,
                "product_id":  b.product_id,
                "expiry_date": b.expiry_date.isoformat(),
                "quantity":    float(b.quantity),
            }
            for b in batches_7
        ],
        "expiring_30_days": [
            {
                "batch_id":    b.id,
                "product_id":  b.product_id,
                "expiry_date": b.expiry_date.isoformat(),
                "quantity":    float(b.quantity),
            }
            for b in batches_30
        ],
        "counts": {
            "low_stock":     len(low_stock),
            "expiring_7":    len(batches_7),
            "expiring_30":   len(batches_30),
        },
    }

    # Cachear 60 segundos
    redis_service.cache_alerts([alerts_data], ttl=60)
    return {"from_cache": False, "alerts": alerts_data}
