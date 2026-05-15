from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Category
from app.models.user import User
from app.core.deps import get_current_user, require_admin
from app.schemas.product import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter()


@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    """Lista todas las categorías activas."""
    return db.query(Category).filter(Category.is_active == True).all()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_admin),
):
    """Crea una nueva categoría. Solo Administrador."""
    if db.query(Category).filter(Category.name == data.name).first():
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre.")

    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db:          Session = Depends(get_db),
    _:           User    = Depends(get_current_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data:        CategoryUpdate,
    db:          Session = Depends(get_db),
    _:           User    = Depends(require_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db:          Session = Depends(get_db),
    _:           User    = Depends(require_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")

    category.is_active = False
    db.commit()
    return {"message": f"Categoría '{category.name}' desactivada."}
