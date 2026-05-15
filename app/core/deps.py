from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ── Dependencia base: usuario autenticado ───────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extrae y valida el token JWT del header Authorization.
    Retorna el usuario activo correspondiente.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado. Por favor inicia sesión nuevamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_active == True,
    ).first()

    if user is None:
        raise credentials_exception

    return user


# ── Solo administrador ──────────────────────────────────────────────────────
def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol Administrador.",
        )
    return current_user


# ── Administrador o Supervisor ──────────────────────────────────────────────
def require_supervisor_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ("admin", "supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol Supervisor o Administrador.",
        )
    return current_user


# ── Cualquier rol (solo verifica que esté activo) ───────────────────────────
def require_any_role(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
