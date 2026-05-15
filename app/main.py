from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os

from app.config import settings
from app.database import Base, engine, check_db_connection

# Importar modelos para que SQLAlchemy los registre
from app.models import (  # noqa: F401
    User, Supplier, Client, Category, Product,
    ProductBatch, Movement, Alert, AuditLog, OfflineSyncQueue,
)

# ── Routers de Katerin (base) ─────────────────────────────────────────────────
from app.routers import auth, users, categories, products, movements, alerts, suppliers, clients

# ── Routers de Jayu ───────────────────────────────────────────────────────────
from app.routers.utils         import router as utils_router
from app.routers.notifications import router as notifications_router
from app.routers.sync          import router as sync_router
from app.routers.dashboard     import router as dashboard_router

# ── Logger ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("medstock")

# ── Crear tablas en la BD ─────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Directorio de uploads (servir imágenes estáticas) ─────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Instancia FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## MedStock Pro API

Sistema Inteligente de Gestión de Inventario Médico
**Caso:** EA Medical S.R.L. | **UNIFRANZ 2026**

### Equipo BUG-BONNY
- **Katerin Quenta** — Backend Lead (FastAPI, MySQL, Reportes)
- **Jayu Mendoza** — DevOps / API Complementaria (Redis, Firebase, Deploy, QR, Sync)
- **Adiel Pabon** — Mobile Lead (Flutter)
- **Eric Luna** — Frontend Web (React + Vite)

### Módulos disponibles
- **Auth** — Login JWT, gestión de sesión
- **Users** — CRUD de usuarios con roles
- **Products** — Catálogo de productos y lotes
- **Categories** — Categorías de productos
- **Movements** — Ingresos, salidas y ajustes de stock
- **Alerts** — Alertas de stock mínimo y vencimiento
- **Suppliers** — Proveedores
- **Clients** — Clientes e instituciones
- **Dashboard** — KPIs en tiempo real con caché Redis
- **QR & Barcode** — Generación de códigos QR y de barras
- **Notifications** — Push notifications Firebase FCM
- **Sync** — Sincronización offline (Módulo M08)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Servir imágenes estáticas ─────────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ── Routers base (Katerin) ────────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/api/auth",       tags=["Autenticación"])
app.include_router(users.router,      prefix="/api/users",      tags=["Usuarios"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categorías"])
app.include_router(products.router,   prefix="/api/products",   tags=["Productos"])
app.include_router(movements.router,  prefix="/api/movements",  tags=["Movimientos"])
app.include_router(alerts.router,     prefix="/api/alerts",     tags=["Alertas"])
app.include_router(suppliers.router,  prefix="/api/suppliers",  tags=["Proveedores"])
app.include_router(clients.router,    prefix="/api/clients",    tags=["Clientes"])

# ── Routers de Jayu ───────────────────────────────────────────────────────────
app.include_router(dashboard_router,     prefix="/api/dashboard",     tags=["Dashboard (Jayu)"])
app.include_router(utils_router,         prefix="/api",               tags=["QR & Imágenes (Jayu)"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notificaciones FCM (Jayu)"])
app.include_router(sync_router,          prefix="/api/sync",          tags=["Sync Offline M08 (Jayu)"])

# ── Endpoints raíz ────────────────────────────────────────────────────────────
@app.get("/", tags=["Sistema"])
def root():
    return {
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status":  "online",
        "team":    "BUG-BONNY | UNIFRANZ 2026",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Sistema"])
def health():
    """Verifica API, base de datos MySQL y Redis."""
    from app.services.redis_service import redis_service

    db_ok    = check_db_connection()
    redis_ok = redis_service.health_check()

    status_code = 200 if db_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "api":      "ok",
            "database": "ok" if db_ok else "error",
            "redis":    redis_ok,
            "version":  settings.APP_VERSION,
        },
    )


# ── Ciclo de vida ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} iniciando...")

    if check_db_connection():
        logger.info("MySQL conectado.")
    else:
        logger.error("No se pudo conectar a MySQL.")

    from app.services.redis_service import redis_service
    r_status = redis_service.health_check()
    if r_status["status"] == "ok":
        logger.info(f"Redis conectado. Memoria: {r_status.get('memory_used', '?')}")
    else:
        logger.warning(f"⚠️ Redis: {r_status.get('message', 'No disponible')} (la app funciona sin caché)")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("MedStock API apagándose...")
