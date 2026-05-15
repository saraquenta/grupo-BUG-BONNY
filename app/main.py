from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os

from app.config import settings
from app.database import Base, engine, check_db_connection

# Importar modelos para que SQLAlchemy los registre
from app.models import User, Supplier, Client, Category, Product, ProductBatch, Movement, Alert, AuditLog, OfflineSyncQueue  # noqa: F401

# Importar routers
from app.routers import auth, users, categories, products, movements, alerts, suppliers, clients
from app.routers import reports          # Reportes PDF — Sara

# ── Routers de Jayu ───────────────────────────────────────────────────────────
from app.routers.dashboard     import router as dashboard_router
from app.routers.notifications import router as notifications_router
from app.routers.sync          import router as sync_router
from app.routers.utils         import router as utils_router

# ── Scheduler de alertas automáticas — Sara ───────────────────────────────────
from app.scheduler import start_scheduler

# ── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("medstock")

# ── Crear tablas en la BD ─────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Instancia FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## MedStock Pro API — EA Medical S.R.L.

Sistema Inteligente de Gestión de Inventario Médico  
**Caso:** EA Medical S.R.L. | **UNIFRANZ 2026**

### Módulos disponibles
- 🔐 **Auth** — Login JWT, gestión de sesión
- 👥 **Users** — CRUD de usuarios con roles
- 📦 **Products** — Catálogo de productos y lotes
- 🏷️ **Categories** — Categorías de productos
- 🔄 **Movements** — Ingresos, salidas y ajustes de stock
- 🔔 **Alerts** — Alertas de stock mínimo y vencimiento
- 🏢 **Suppliers** — Proveedores
- 🏥 **Clients** — Clientes e instituciones
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

# ── Registrar routers ─────────────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/api/auth",       tags=["🔐 Autenticación"])
app.include_router(users.router,      prefix="/api/users",      tags=["👥 Usuarios"])
app.include_router(categories.router, prefix="/api/categories", tags=["🏷️ Categorías"])
app.include_router(products.router,   prefix="/api/products",   tags=["📦 Productos"])
app.include_router(movements.router,  prefix="/api/movements",  tags=["🔄 Movimientos"])
app.include_router(alerts.router,     prefix="/api/alerts",     tags=["🔔 Alertas"])
app.include_router(suppliers.router,  prefix="/api/suppliers",  tags=["🏢 Proveedores"])
app.include_router(clients.router,    prefix="/api/clients",    tags=["🏥 Clientes"])

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
    """
    Verifica que la API y la base de datos MySQL estén operativas.
    Útil para monitoreo en producción (Railway/Render).
    """
    db_ok = check_db_connection()
    status_code = 200 if db_ok else 503

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
        logger.info("✅ Conexión a MySQL establecida correctamente.")
    else:
        logger.error("❌ No se pudo conectar a MySQL. Verifica las credenciales en .env")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 MedStock API apagándose...")
