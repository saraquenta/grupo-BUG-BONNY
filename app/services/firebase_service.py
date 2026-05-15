"""
firebase_service.py — Jayu Mendoza
Envío de notificaciones push con Firebase Cloud Messaging (FCM).
"""
import logging
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Intentar importar firebase_admin (opcional) ──────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _firebase_available = True
except ImportError:
    _firebase_available = False
    logger.warning("firebase-admin no instalado. Push notifications deshabilitadas.")


@dataclass
class NotificationResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class FirebaseService:
    """Wrapper sobre Firebase Admin SDK para envío de push notifications."""

    def __init__(self, credentials_path: str = ""):
        self._initialized = False

        if not _firebase_available:
            logger.warning("firebase-admin no disponible.")
            return

        if not credentials_path:
            logger.warning("FIREBASE_CREDENTIALS_PATH no configurado. FCM deshabilitado.")
            return

        try:
            import os
            if os.path.exists(credentials_path):
                cred = credentials.Certificate(credentials_path)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                self._initialized = True
                logger.info("✅ Firebase inicializado correctamente.")
            else:
                logger.warning(f"⚠️ Archivo de credenciales no encontrado: {credentials_path}")
        except Exception as e:
            logger.error(f"❌ Error inicializando Firebase: {e}")

    # ── Envío individual ─────────────────────────────────────────────────────
    def send_to_token(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> NotificationResult:
        """Envía notificación a un dispositivo específico."""
        if not self._initialized:
            logger.info(f"[FCM MOCK] → {title}: {body}")
            return NotificationResult(success=True, message_id="mock-fcm-id")

        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        icon="ic_notification",
                        color="#1565C0",
                        sound="default",
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default", badge=1)
                    )
                ),
            )
            msg_id = messaging.send(message)
            logger.info(f"✅ Notificación enviada: {msg_id}")
            return NotificationResult(success=True, message_id=msg_id)
        except Exception as e:
            logger.error(f"❌ Error enviando FCM: {e}")
            return NotificationResult(success=False, error=str(e))

    # ── Envío múltiple ───────────────────────────────────────────────────────
    def send_multicast(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> dict:
        """Envía a múltiples dispositivos a la vez (máximo 500 por lote)."""
        if not tokens:
            return {"success": 0, "failure": 0}

        if not self._initialized:
            logger.info(f"[FCM MOCK MULTICAST] {len(tokens)} dispositivos → {title}")
            return {"success": len(tokens), "failure": 0}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                tokens=tokens[:500],
                android=messaging.AndroidConfig(priority="high"),
            )
            response = messaging.send_each_for_multicast(message)
            return {
                "success": response.success_count,
                "failure": response.failure_count,
            }
        except Exception as e:
            logger.error(f"❌ Error en multicast FCM: {e}")
            return {"success": 0, "failure": len(tokens)}

    # ── Notificaciones predefinidas para MedStock ────────────────────────────
    def notify_low_stock(self, token: str, product_name: str, current_stock: float) -> NotificationResult:
        return self.send_to_token(
            token=token,
            title="⚠️ Stock Crítico",
            body=f"{product_name} tiene solo {current_stock} unidades disponibles.",
            data={"type": "stock_minimo", "product": product_name},
        )

    def notify_expiry_soon(self, token: str, product_name: str, days: int) -> NotificationResult:
        emoji = "🔴" if days <= 7 else "🟡"
        return self.send_to_token(
            token=token,
            title=f"{emoji} Vencimiento Próximo",
            body=f"{product_name} vence en {days} días.",
            data={"type": "vencimiento", "product": product_name, "days": str(days)},
        )

    def notify_movement_registered(self, token: str, movement_type: str, product_name: str) -> NotificationResult:
        tipo = "ingreso" if movement_type == "ingreso" else "salida"
        return self.send_to_token(
            token=token,
            title="📦 Movimiento Registrado",
            body=f"Se registró un {tipo} de {product_name}.",
            data={"type": "movement", "movement_type": movement_type},
        )


# ── Instancia global ─────────────────────────────────────────────────────────
from app.config import settings
firebase_service = FirebaseService(credentials_path=settings.FIREBASE_CREDENTIALS_PATH)
