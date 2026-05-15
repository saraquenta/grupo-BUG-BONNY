# Importar todos los modelos para que SQLAlchemy los registre
# y Alembic pueda detectarlos en las migraciones.
from app.models.user import User
from app.models.supplier import Supplier
from app.models.client import Client
from app.models.product import Category, Product, ProductBatch
from app.models.movement import Movement
from app.models.alert import Alert, AuditLog, OfflineSyncQueue

__all__ = [
    "User",
    "Supplier",
    "Client",
    "Category",
    "Product",
    "ProductBatch",
    "Movement",
    "Alert",
    "AuditLog",
    "OfflineSyncQueue",
]
