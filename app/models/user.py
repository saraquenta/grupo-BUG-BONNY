from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer,      primary_key=True, autoincrement=True)
    username         = Column(String(50),   nullable=False, unique=True, index=True)
    email            = Column(String(100),  nullable=False, unique=True)
    full_name        = Column(String(150),  nullable=False)
    hashed_password  = Column(String(255),  nullable=False)
    role             = Column(
                           SAEnum("admin", "supervisor", "almacenero", name="user_role"),
                           nullable=False,
                           default="almacenero",
                       )
    is_active        = Column(Boolean,      nullable=False, default=True)
    phone            = Column(String(20),   nullable=True)
    avatar_url       = Column(String(500),  nullable=True)
    firebase_token   = Column(String(500),  nullable=True)   # Token FCM para notificaciones push
    last_login       = Column(DateTime,     nullable=True)
    created_at       = Column(DateTime,     nullable=False, server_default=func.now())
    updated_at       = Column(DateTime,     nullable=True,  onupdate=func.now())

    # ── Relaciones ─────────────────────────────────────────────────────────
    movements  = relationship(
        "Movement",
        back_populates="responsible",
        foreign_keys="Movement.responsible_id",
    )
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"

    @property
    def role_label(self) -> str:
        labels = {
            "admin":      "Administrador",
            "supervisor": "Supervisor",
            "almacenero": "Almacenero",
        }
        return labels.get(self.role, self.role)
