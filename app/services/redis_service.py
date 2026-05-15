"""
redis_service.py — Jayu Mendoza
Caché de alertas, sesiones y datos de alta frecuencia.
"""
import json
import logging
from typing import Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# ── Intentar importar Redis (graceful degradation si no está disponible) ───
try:
    import redis
    _redis_available = True
except ImportError:
    _redis_available = False
    logger.warning("redis no instalado. Corriendo sin caché.")


class RedisService:
    """Wrapper sobre Redis con manejo de errores y serialización JSON."""

    def __init__(self, url: str = "redis://localhost:6379", prefix: str = "medstock"):
        self.prefix = prefix
        self._client: Optional[Any] = None

        if _redis_available:
            try:
                self._client = redis.from_url(url, decode_responses=True, socket_timeout=2)
                self._client.ping()
                logger.info("✅ Redis conectado correctamente.")
            except Exception as e:
                logger.warning(f"⚠️ Redis no disponible: {e}. Continuando sin caché.")
                self._client = None

    # ── Helpers internos ────────────────────────────────────────────────────
    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def _serialize(self, value: Any) -> str:
        return json.dumps(value, default=str)

    def _deserialize(self, raw: str) -> Any:
        return json.loads(raw)

    # ── CRUD básico ─────────────────────────────────────────────────────────
    def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            raw = self._client.get(self._key(key))
            return self._deserialize(raw) if raw else None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Guarda un valor con TTL en segundos (default 5 min)."""
        if not self._client:
            return False
        try:
            self._client.setex(self._key(key), ttl, self._serialize(value))
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            self._client.delete(self._key(key))
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Elimina todas las claves que coincidan con el patrón."""
        if not self._client:
            return 0
        try:
            keys = self._client.keys(self._key(pattern))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE PATTERN error: {e}")
            return 0

    def exists(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            return bool(self._client.exists(self._key(key)))
        except Exception:
            return False

    # ── TTLs predefinidos ───────────────────────────────────────────────────
    def cache_dashboard(self, user_id: int, data: dict) -> bool:
        """Cachea el dashboard 2 minutos (datos en tiempo casi real)."""
        return self.set(f"dashboard:{user_id}", data, ttl=120)

    def get_dashboard(self, user_id: int) -> Optional[dict]:
        return self.get(f"dashboard:{user_id}")

    def cache_products_list(self, cache_key: str, data: list) -> bool:
        """Cachea lista de productos 5 minutos."""
        return self.set(f"products:{cache_key}", data, ttl=300)

    def get_products_list(self, cache_key: str) -> Optional[list]:
        return self.get(f"products:{cache_key}")

    def invalidate_products(self):
        """Invalida TODO el caché de productos (llamar tras ingresos/salidas)."""
        deleted = self.delete_pattern("products:*")
        self.delete_pattern("dashboard:*")
        logger.info(f"Caché invalidado: {deleted} claves eliminadas.")

    def cache_alerts(self, data: list, ttl: int = 60) -> bool:
        """Cachea alertas 1 minuto (se recalculan frecuente)."""
        return self.set("alerts:active", data, ttl=ttl)

    def get_alerts(self) -> Optional[list]:
        return self.get("alerts:active")

    def store_fcm_token(self, user_id: int, token: str) -> bool:
        """Guarda el token FCM de un usuario (24h)."""
        return self.set(f"fcm:{user_id}", token, ttl=86400)

    def get_fcm_token(self, user_id: int) -> Optional[str]:
        return self.get(f"fcm:{user_id}")

    def health_check(self) -> dict:
        if not self._client:
            return {"status": "unavailable", "message": "Redis no configurado"}
        try:
            self._client.ping()
            info = self._client.info()
            return {
                "status": "ok",
                "memory_used": info.get("used_memory_human", "?"),
                "connected_clients": info.get("connected_clients", "?"),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ── Instancia global ─────────────────────────────────────────────────────────
from app.config import settings
redis_service = RedisService(url=settings.REDIS_URL)
