from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.sql import func
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id             = Column(Integer,     primary_key=True, autoincrement=True)
    name           = Column(String(200), nullable=False)
    client_type    = Column(
                         SAEnum("publico", "privado", name="client_type_enum"),
                         nullable=False,
                         default="publico",
                     )
    contact_person = Column(String(150), nullable=True)
    phone          = Column(String(30),  nullable=True)
    email          = Column(String(100), nullable=True)
    address        = Column(Text,        nullable=True)
    nit            = Column(String(20),  nullable=True)
    is_active      = Column(Boolean,     nullable=False, default=True)
    notes          = Column(Text,        nullable=True)
    created_at     = Column(DateTime,    nullable=False, server_default=func.now())
    updated_at     = Column(DateTime,    nullable=True,  onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name} type={self.client_type}>"
