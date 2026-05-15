"""
scheduler.py — Sara (Katerin Quenta) — M06
Job automático que detecta alertas de stock mínimo y vencimientos.
Se integra con firebase_service de Jayu para enviar push notifications.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import date, timedelta
import logging

from app.database import SessionLocal
from app.models.product import Product, ProductBatch
from app.models.alert import Alert
from app.models.user import User

logger = logging.getLogger("medstock.scheduler")


def _get_admin_tokens(db: Session) -> list:
    """Retorna tokens FCM de todos los admins y supervisores activos."""
    users = db.query(User).filter(
        User.is_active == True,
        User.role.in_(["admin", "supervisor"]),
        User.firebase_token != None,
    ).all()
    return [u.firebase_token for u in users if u.firebase_token]


def check_stock_alerts(db: Session):
    """Detecta productos con stock igual o menor al mínimo y crea alertas + push notification."""
    # Importar firebase aquí para evitar import circular
    try:
        from app.services.firebase_service import firebase_service
        firebase_ok = True
    except Exception:
        firebase_ok = False

    productos_bajos = db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock <= Product.min_stock,
    ).all()

    nuevas_alertas = 0
    for product in productos_bajos:
        # Evitar duplicar alertas no resueltas del mismo producto
        existe = db.query(Alert).filter(
            Alert.product_id  == product.id,
            Alert.alert_type  == "stock_minimo",
            Alert.is_resolved == False,
        ).first()

        if not existe:
            severidad = "critical" if float(product.current_stock) == 0 else "warning"
            alerta = Alert(
                product_id  = product.id,
                alert_type  = "stock_minimo",
                title       = f"Stock mínimo: {product.name}",
                message     = (
                    f"El producto '{product.name}' (código: {product.code}) tiene "
                    f"stock actual de {product.current_stock} {product.unit}, "
                    f"igual o por debajo del mínimo de {product.min_stock} {product.unit}."
                ),
                severity    = severidad,
                stock_value = product.current_stock,
            )
            db.add(alerta)
            nuevas_alertas += 1

            # ── Enviar push notification via Firebase (Jayu) ─────────────────
            if firebase_ok:
                try:
                    tokens = _get_admin_tokens(db)
                    if tokens:
                        emoji = "🔴" if severidad == "critical" else "⚠️"
                        firebase_service.send_multicast(
                            tokens=tokens,
                            title=f"{emoji} Stock Crítico — MedStock",
                            body=f"{product.name}: {float(product.current_stock)} {product.unit} (mín: {float(product.min_stock)})",
                            data={"type": "stock_minimo", "product_id": str(product.id), "code": product.code},
                        )
                        logger.info(f"Push enviado: stock bajo en {product.name}")
                except Exception as e:
                    logger.warning(f"No se pudo enviar push de stock: {e}")

        logger.info(f"Alerta stock mínimo creada: {product.name} ({product.current_stock}/{product.min_stock})")

    db.commit()
    if nuevas_alertas:
        logger.info(f"✅ {nuevas_alertas} alertas de stock mínimo registradas.")


def check_expiry_alerts(db: Session):
    """Detecta lotes próximos a vencer (7, 15 y 30 días) y crea alertas + push notification."""
    try:
        from app.services.firebase_service import firebase_service
        firebase_ok = True
    except Exception:
        firebase_ok = False

    hoy     = date.today()
    umbrales = [
        (7,  "vencimiento_7",  "critical"),
        (15, "vencimiento_15", "warning"),
        (30, "vencimiento_30", "info"),
    ]

    nuevas = 0
    for dias, alert_type, severity in umbrales:
        fecha_limite = hoy + timedelta(days=dias)

        lotes = db.query(ProductBatch).filter(
            ProductBatch.is_active   == True,
            ProductBatch.expiry_date != None,
            ProductBatch.expiry_date <= fecha_limite,
            ProductBatch.expiry_date >= hoy,
            ProductBatch.quantity    > 0,
        ).all()

        for lote in lotes:
            existe = db.query(Alert).filter(
                Alert.batch_id    == lote.id,
                Alert.alert_type  == alert_type,
                Alert.is_resolved == False,
            ).first()

            if not existe:
                dias_rest = (lote.expiry_date - hoy).days
                alerta = Alert(
                    product_id  = lote.product_id,
                    batch_id    = lote.id,
                    alert_type  = alert_type,
                    title       = f"Vence en {dias_rest} días: lote {lote.batch_number or lote.id}",
                    message     = (
                        f"El lote '{lote.batch_number or lote.id}' del producto ID {lote.product_id} "
                        f"vence el {lote.expiry_date.strftime('%d/%m/%Y')} "
                        f"({dias_rest} días restantes). "
                        f"Cantidad disponible: {lote.quantity}."
                    ),
                    severity    = severity,
                    expiry_date = lote.expiry_date,
                    stock_value = lote.quantity,
                )
                db.add(alerta)
                nuevas += 1

                # ── Push notification via Firebase (Jayu) ────────────────────
                if firebase_ok and severity in ("critical", "warning"):
                    try:
                        tokens = _get_admin_tokens(db)
                        if tokens:
                            emoji = "🔴" if dias_rest <= 7 else "🟡"
                            firebase_service.send_multicast(
                                tokens=tokens,
                                title=f"{emoji} Vencimiento próximo — MedStock",
                                body=f"Lote {lote.batch_number or lote.id} vence en {dias_rest} días. Cantidad: {float(lote.quantity)}",
                                data={"type": "vencimiento", "batch_id": str(lote.id), "days": str(dias_rest)},
                            )
                    except Exception as e:
                        logger.warning(f"No se pudo enviar push de vencimiento: {e}")

        db.commit()

    if nuevas:
        logger.info(f"✅ {nuevas} alertas de vencimiento registradas.")


def run_all_checks():
    """Ejecuta todos los chequeos. Llamado por el scheduler cada hora."""
    db: Session = SessionLocal()
    try:
        logger.info("🔍 Ejecutando chequeo automático de alertas...")
        check_stock_alerts(db)
        check_expiry_alerts(db)
        logger.info("✅ Chequeo de alertas completado.")
    except Exception as e:
        logger.error(f"❌ Error en chequeo de alertas: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    """Inicia el scheduler en segundo plano. Corre cada hora."""
    scheduler = BackgroundScheduler(timezone="America/La_Paz")

    scheduler.add_job(
        func     = run_all_checks,
        trigger  = IntervalTrigger(hours=1),
        id       = "check_alerts",
        name     = "Chequeo automático de alertas MedStock",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("⏰ Scheduler iniciado — chequeo de alertas cada hora.")

    # Ejecutar inmediatamente al arrancar
    run_all_checks()

    return scheduler