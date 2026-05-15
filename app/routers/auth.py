from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.alert import AuditLog
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.deps import get_current_user
from app.schemas.auth import Token, UserCreate, UserResponse

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Inicio de sesión con usuario y contraseña.
    Retorna token JWT + datos del usuario.
    """
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario desactivado. Contacta al administrador.",
        )

    # Actualizar last_login
    user.last_login = datetime.utcnow()
    db.commit()

    # Registrar en auditoría
    audit = AuditLog(
        user_id=user.id,
        action="LOGIN",
        table_name="users",
        record_id=user.id,
    )
    db.add(audit)
    db.commit()

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "username": user.username}
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user={
            "id":        user.id,
            "username":  user.username,
            "full_name": user.full_name,
            "email":     user.email,
            "role":      user.role,
        },
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return current_user


@router.post("/setup-admin", response_model=UserResponse)
def setup_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Crea el primer usuario administrador.
    Solo funciona si no existe ningún usuario en la BD.
    """
    if db.query(User).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El setup inicial ya fue realizado.",
        )
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
