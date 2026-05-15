from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import date, timedelta
import logging

from app.database import SessionLocal
from app.models.product import Product, ProductBatch
from app.models.alert import Alert

logger = logging.getLogger("medstock.scheduler")


def check_stock_alerts(db: Session):
    """Detecta productos con stock igual o menor al mínimo y crea alertas."""
    productos_bajos = db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock <= Product.min_stock,
    ).all()

    for product in productos_bajos:
        # Evitar duplicar alertas no resueltas del mismo producto
        existe = db.query(Alert).filter(
            Alert.product_id == product.id,
            Alert.alert_type == "stock_minimo",
            Alert.is_resolved == False,
        ).first()

        if not existe:
            alerta = Alert(
                product_id  = product.id,
                alert_type  = "stock_minimo",
                title       = f"Stock mínimo: {product.name}",
                message     = (
                    f"El producto '{product.name}' (código: {product.code}) "
                    f"tiene stock actual de {product.current_stock} {product.unit}, "
                    f"igual o por debajo del mínimo de {product.min_stock} {product.unit}."
                ),
                severity    = "critical" if float(product.current_stock) == 0 else "warning",
                stock_value = product.current_stock,
            )
            db.add(alerta)
            logger.info(f"Alerta de stock mínimo creada: {product.name}")

    db.commit()


def check_expiry_alerts(db: Session):
    """Detecta lotes próximos a vencer (7, 15 y 30 días) y crea alertas."""
    hoy = date.today()

    umbrales = [
        (7,  "vencimiento_7",  "critical"),
        (15, "vencimiento_15", "warning"),
        (30, "vencimiento_30", "info"),
    ]

    for dias, alert_type, severity in umbrales:
        fecha_limite = hoy + timedelta(days=dias)

        lotes = db.query(ProductBatch).filter(
            ProductBatch.is_active == True,
            ProductBatch.expiry_date != None,
            ProductBatch.expiry_date <= fecha_limite,
            ProductBatch.expiry_date >= hoy,
            ProductBatch.quantity > 0,
        ).all()

        for lote in lotes:
            existe = db.query(Alert).filter(
                Alert.batch_id   == lote.id,
                Alert.alert_type == alert_type,
                Alert.is_resolved == False,
            ).first()

            if not existe:
                dias_restantes = (lote.expiry_date - hoy).days
                alerta = Alert(
                    product_id  = lote.product_id,
                    batch_id    = lote.id,
                    alert_type  = alert_type,
                    title       = f"Vence en {dias_restantes} días: lote {lote.batch_number or lote.id}",
                    message     = (
                        f"El lote '{lote.batch_number or lote.id}' del producto ID {lote.product_id} "
                        f"vence el {lote.expiry_date.strftime('%d/%m/%Y')} "
                        f"({dias_restantes} días restantes). "
                        f"Cantidad disponible: {lote.quantity}."
                    ),
                    severity    = severity,
                    expiry_date = lote.expiry_date,
                    stock_value = lote.quantity,
                )
                db.add(alerta)
                logger.info(f"Alerta de vencimiento creada: lote {lote.id} — {dias_restantes} días")

        db.commit()


def run_all_checks():
    """Ejecuta todos los chequeos de alertas. Llamado por el scheduler."""
    db: Session = SessionLocal()
    try:
        logger.info("Ejecutando chequeo automático de alertas...")
        check_stock_alerts(db)
        check_expiry_alerts(db)
        logger.info("Chequeo de alertas completado.")
    except Exception as e:
        logger.error(f"Error en el chequeo de alertas: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    """
    Inicia el scheduler en segundo plano.
    Corre cada hora automáticamente.
    """
    scheduler = BackgroundScheduler(timezone="America/La_Paz")

    scheduler.add_job(
        func    = run_all_checks,
        trigger = IntervalTrigger(hours=1),
        id      = "check_alerts",
        name    = "Chequeo automático de alertas",
        replace_existing = True,
    )

    scheduler.start()
    logger.info("Scheduler de alertas iniciado. Próxima ejecución: en 1 hora.")

    # Ejecutar inmediatamente al arrancar para detectar alertas existentes
    run_all_checks()

    return scheduler
