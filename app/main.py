from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os

from app.config import settings
from app.database import Base, engine, check_db_connection

# ── Importar modelos ──────────────────────────────────────────────────────────
from app.models import (  # noqa: F401
    User, Supplier, Client, Category, Product,
    ProductBatch, Movement, Alert, AuditLog, OfflineSyncQueue,
)

# ── Routers de Sara (base) ────────────────────────────────────────────────────
from app.routers import auth, users, categories, products, movements, alerts, suppliers, clients
from app.routers import reports          # Reportes PDF — Sara

# ── Routers de Jayu ───────────────────────────────────────────────────────────
from app.routers.dashboard     import router as dashboard_router
from app.routers.notifications import router as notifications_router
from app.routers.sync          import router as sync_router
from app.routers.utils         import router as utils_router

# ── Scheduler de alertas automáticas — Sara ───────────────────────────────────
from app.scheduler import start_scheduler

# ── Logger ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("medstock")

# ── Crear tablas en la BD ─────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Directorio para imágenes subidas (Jayu) ───────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Instancia FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## MedStock Pro API — EA Medical S.R.L.

Sistema Inteligente de Gestión de Inventario Médico | UNIFRANZ 2026

### Equipo BUG-BONNY
- **Sara (Katerin Quenta)** — Backend Lead: FastAPI, MySQL, Reportes PDF, Scheduler
- **Jayu Mendoza** — DevOps/API: Redis, Firebase FCM, Sync Offline, Dashboard, QR
- **Adiel Pabon** — Mobile Lead: Flutter app
- **Eric Luna** — Frontend Web: React + Vite

### Módulos disponibles
- 🔐 **Auth** — Login JWT, gestión de sesión
- 👥 **Users** — CRUD de usuarios con roles
- 📦 **Products** — Catálogo con QR automático
- 🏷️ **Categories** — Categorías de productos
- 🔄 **Movements** — Ingresos, salidas, ajustes y bajas
- 🔔 **Alerts** — Alertas automáticas cada hora (APScheduler)
- 📊 **Reports** — PDFs: kardex, stock valorizado, vencimientos
- 🏢 **Suppliers** — Proveedores
- 🏥 **Clients** — Clientes e instituciones
- 📈 **Dashboard** — KPIs en tiempo real con caché Redis
- 🔔 **Notifications** — Push notifications Firebase FCM
- 🔁 **Sync** — Sincronización offline M08
- 🖼️ **Utils** — Upload de imágenes, QR y barcode
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

# ── Servir imágenes estáticas (Jayu) ─────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ── Routers Sara ──────────────────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/api/auth",       tags=["🔐 Autenticación"])
app.include_router(users.router,      prefix="/api/users",      tags=["👥 Usuarios"])
app.include_router(categories.router, prefix="/api/categories", tags=["🏷️ Categorías"])
app.include_router(products.router,   prefix="/api/products",   tags=["📦 Productos"])
app.include_router(movements.router,  prefix="/api/movements",  tags=["🔄 Movimientos"])
app.include_router(alerts.router,     prefix="/api/alerts",     tags=["🔔 Alertas"])
app.include_router(suppliers.router,  prefix="/api/suppliers",  tags=["🏢 Proveedores"])
app.include_router(clients.router,    prefix="/api/clients",    tags=["🏥 Clientes"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["📊 Reportes PDF"])

# ── Routers Jayu ──────────────────────────────────────────────────────────────
app.include_router(dashboard_router,     prefix="/api/dashboard",     tags=["📈 Dashboard"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["🔔 Notificaciones FCM"])
app.include_router(sync_router,          prefix="/api/sync",          tags=["🔁 Sync Offline M08"])
app.include_router(utils_router,         prefix="/api",               tags=["🖼️ Utils QR/Imágenes"])

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
    """Verifica API, MySQL y Redis."""
    from app.services.redis_service import redis_service
    db_ok    = check_db_connection()
    redis_ok = redis_service.health_check()
    return JSONResponse(
        status_code=200 if db_ok else 503,
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
        logger.info("✅ MySQL conectado.")
    else:
        logger.error("❌ No se pudo conectar a MySQL.")

    from app.services.redis_service import redis_service
    r_status = redis_service.health_check()
    if r_status["status"] == "ok":
        logger.info(f"✅ Redis conectado. Memoria: {r_status.get('memory_used', '?')}")
    else:
        logger.warning("⚠️ Redis no disponible. La app funciona sin caché.")

    # Scheduler de alertas automáticas (Sara)
    try:
        start_scheduler()
        logger.info("✅ Scheduler de alertas iniciado (cada hora).")
    except Exception as e:
        logger.error(f"❌ Error al iniciar scheduler: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 MedStock API apagándose...")