from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Text, Numeric, ForeignKey, Date, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id          = Column(Integer,        primary_key=True, autoincrement=True)
    product_id  = Column(Integer,        ForeignKey("products.id"),        nullable=True)
    batch_id    = Column(Integer,        ForeignKey("product_batches.id"), nullable=True)
    alert_type  = Column(String(30),     nullable=False)
    # Valores: stock_minimo | vencimiento_7 | vencimiento_15 | vencimiento_30
    title       = Column(String(200),    nullable=False)
    message     = Column(Text,           nullable=False)
    severity    = Column(
                      SAEnum("info", "warning", "critical", name="alert_severity_enum"),
                      nullable=False,
                      default="warning",
                  )
    is_read     = Column(Boolean,        nullable=False, default=False)
    is_resolved = Column(Boolean,        nullable=False, default=False)
    resolved_by = Column(Integer,        ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime,       nullable=True)
    expiry_date = Column(Date,           nullable=True)
    stock_value = Column(Numeric(10, 2), nullable=True)
    created_at  = Column(DateTime,       nullable=False, server_default=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    product = relationship("Product", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} type={self.alert_type} severity={self.severity}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id         = Column(Integer,      primary_key=True, autoincrement=True)
    user_id    = Column(Integer,      ForeignKey("users.id"), nullable=True)
    action     = Column(String(50),   nullable=False)
    # Valores: CREATE | UPDATE | DELETE | LOGIN | LOGOUT
    table_name = Column(String(50),   nullable=True)
    record_id  = Column(Integer,      nullable=True)
    old_values = Column(Text,         nullable=True)   # JSON serializado
    new_values = Column(Text,         nullable=True)   # JSON serializado
    ip_address = Column(String(45),   nullable=True)
    user_agent = Column(String(255),  nullable=True)
    created_at = Column(DateTime,     nullable=False, server_default=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} table={self.table_name}>"


class OfflineSyncQueue(Base):
    __tablename__ = "offline_sync_queue"

    id         = Column(Integer,    primary_key=True, autoincrement=True)
    device_id  = Column(String(100), nullable=False, index=True)
    user_id    = Column(Integer,    ForeignKey("users.id"), nullable=True)
    operation  = Column(
                     SAEnum("INSERT", "UPDATE", "DELETE", name="sync_operation_enum"),
                     nullable=False,
                 )
    table_name = Column(String(50), nullable=False)
    payload    = Column(Text,       nullable=False)   # JSON serializado
    is_synced  = Column(Boolean,    nullable=False, default=False)
    synced_at  = Column(DateTime,   nullable=True)
    error_msg  = Column(Text,       nullable=True)
    created_at = Column(DateTime,   nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<OfflineSyncQueue id={self.id} device={self.device_id} op={self.operation}>"
