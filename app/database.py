from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# ── Motor de base de datos ──────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,          # Verifica conexión antes de usar
    pool_recycle=3600,           # Recicla conexiones cada 1 hora
    echo=settings.DEBUG,         # Muestra SQL en consola si DEBUG=True
    connect_args={
        "connect_timeout": 10,
    },
)

# ── Evento: forzar utf8mb4 en cada conexión ─────────────────────────────────
@event.listens_for(engine, "connect")
def set_mysql_charset(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute("SET CHARACTER SET utf8mb4")
    cursor.close()

# ── Sesión ──────────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ── Base para todos los modelos ─────────────────────────────────────────────
Base = declarative_base()


# ── Dependencia FastAPI ─────────────────────────────────────────────────────
def get_db():
    """
    Generador de sesión de base de datos.
    Se inyecta como dependencia en los endpoints con Depends(get_db).
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Error en sesión de BD: {e}")
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verifica que la conexión a MySQL esté activa."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"No se pudo conectar a MySQL: {e}")
        return False
