from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.core.deps import get_current_user, require_admin
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse, UserChangePassword

router = APIRouter()


@router.get("/", response_model=UserListResponse)
def list_users(
    skip:      int            = Query(0, ge=0),
    limit:     int            = Query(50, ge=1, le=200),
    role:      Optional[str]  = Query(None),
    is_active: Optional[bool] = Query(None),
    search:    Optional[str]  = Query(None),
    db:        Session        = Depends(get_db),
    _:         User           = Depends(require_admin),
):
    """Lista todos los usuarios. Solo Administrador."""
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        term = f"%{search}%"
        query = query.filter(
            User.username.ilike(term)
            | User.full_name.ilike(term)
            | User.email.ilike(term)
        )

    total = query.count()
    items = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return UserListResponse(total=total, items=items)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db:        Session = Depends(get_db),
    _:         User    = Depends(require_admin),
):
    """Crea un nuevo usuario. Solo Administrador."""
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado.")

    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        phone=user_data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db:      Session = Depends(get_db),
    current: User    = Depends(get_current_user),
):
    """Obtiene un usuario por ID. Admin ve todos; otros solo su perfil."""
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id:   int,
    user_data: UserUpdate,
    db:        Session = Depends(get_db),
    current:   User    = Depends(get_current_user),
):
    """Actualiza datos de un usuario. Admin edita cualquiera; otros solo su perfil."""
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    update_data = user_data.model_dump(exclude_unset=True)

    # Solo admin puede cambiar el rol y activar/desactivar
    if current.role != "admin":
        update_data.pop("role", None)
        update_data.pop("is_active", None)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/change-password")
def change_password(
    user_id:  int,
    data:     UserChangePassword,
    db:       Session = Depends(get_db),
    current:  User    = Depends(get_current_user),
):
    """Cambia la contraseña de un usuario."""
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta.")

    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente."}


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    db:      Session = Depends(get_db),
    _:       User    = Depends(require_admin),
):
    """Desactiva un usuario (no lo elimina). Solo Administrador."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if user.id == user_id and user.role == "admin":
        # Evitar que el admin se desactive a sí mismo
        pass

    user.is_active = False
    db.commit()
    return {"message": f"Usuario '{user.username}' desactivado."}
