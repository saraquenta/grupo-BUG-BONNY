"""
utils.py — Jayu Mendoza (Día 3)
Generación de QR, Códigos de Barras y Upload de Imágenes de productos.
"""
import io
import os
import uuid
import base64
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.core.deps import get_current_user, require_supervisor_or_admin

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Directorio de uploads ─────────────────────────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 5


# ═══════════════════════════════════════════════════════════════════════════════
# QR CODE
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_qr_bytes(data: str, size: int = 300) -> bytes:
    """Genera imagen PNG de QR en memoria."""
    try:
        import qrcode
        from qrcode.image.pil import PilImage

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1565C0", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    except ImportError:
        # Fallback: QR en texto ASCII si qrcode no está instalado
        raise HTTPException(
            status_code=500,
            detail="Librería 'qrcode' no instalada. Ejecuta: pip install qrcode[pil]"
        )


@router.get("/products/{product_id}/qr")
def get_product_qr(
    product_id: int,
    format: str = Query("png", description="Formato: png | base64"),
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    """
    Genera y devuelve el código QR de un producto.
    - **format=png** → imagen PNG directa (para mostrar en app)
    - **format=base64** → string base64 (para guardar en BD)
    """
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    # El QR contiene el código interno del producto
    qr_data = product.code
    png_bytes = _generate_qr_bytes(qr_data)

    if format == "base64":
        encoded = base64.b64encode(png_bytes).decode("utf-8")
        # Guardar en BD si no tiene QR
        if not product.qr_code:
            product.qr_code = f"data:image/png;base64,{encoded}"
            db.commit()
        return {
            "product_id":   product_id,
            "product_code": product.code,
            "qr_base64":    f"data:image/png;base64,{encoded}",
        }

    # Default: imagen PNG
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="qr_{product.code}.png"'},
    )


@router.post("/products/{product_id}/qr/generate")
def generate_and_save_qr(
    product_id: int,
    db: Session = Depends(get_db),
    _:  User    = Depends(require_supervisor_or_admin),
):
    """Genera el QR y lo guarda permanentemente en el campo qr_code del producto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    png_bytes = _generate_qr_bytes(product.code)
    encoded = base64.b64encode(png_bytes).decode("utf-8")
    product.qr_code = f"data:image/png;base64,{encoded}"
    db.commit()

    return {
        "message":    f"QR generado y guardado para '{product.name}'.",
        "product_id": product_id,
        "qr_code":    product.qr_code,
    }


@router.post("/products/qr/bulk-generate")
def bulk_generate_qr(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_supervisor_or_admin),
):
    """Genera QR para TODOS los productos que aún no tienen QR."""
    products = db.query(Product).filter(
        Product.is_active == True,
        (Product.qr_code == None) | (Product.qr_code == ""),
    ).all()

    generated = 0
    errors = 0
    for product in products:
        try:
            png_bytes = _generate_qr_bytes(product.code)
            encoded = base64.b64encode(png_bytes).decode("utf-8")
            product.qr_code = f"data:image/png;base64,{encoded}"
            generated += 1
        except Exception as e:
            logger.error(f"Error QR producto {product.id}: {e}")
            errors += 1

    db.commit()
    return {
        "message":   f"QR generados: {generated}, errores: {errors}",
        "generated": generated,
        "errors":    errors,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BARCODE
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_barcode_bytes(code: str) -> bytes:
    """Genera imagen PNG de código de barras Code128."""
    try:
        import barcode
        from barcode.writer import ImageWriter

        CODE = barcode.get_barcode_class("code128")
        buf = io.BytesIO()
        bc = CODE(code, writer=ImageWriter())
        bc.write(buf, options={
            "module_width":  0.8,
            "module_height": 10.0,
            "font_size":     8,
            "text_distance": 2.0,
            "quiet_zone":    2.5,
            "write_text":    True,
        })
        return buf.getvalue()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Librería 'python-barcode' no instalada. Ejecuta: pip install python-barcode[images]"
        )


@router.get("/products/{product_id}/barcode")
def get_product_barcode(
    product_id: int,
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    """Devuelve el código de barras del producto en formato PNG."""
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    # Usar barcode propio del producto si existe, sino generar con su código interno
    code_to_use = product.barcode if product.barcode else product.code
    png_bytes = _generate_barcode_bytes(code_to_use)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="barcode_{product.code}.png"'},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/products/{product_id}/image")
async def upload_product_image(
    product_id: int,
    file:       UploadFile = File(..., description="Imagen del producto (JPG, PNG, WEBP)"),
    db:         Session    = Depends(get_db),
    _:          User       = Depends(require_supervisor_or_admin),
):
    """
    Sube una imagen para un producto.
    Formatos aceptados: JPG, PNG, WEBP. Tamaño máximo: 5MB.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    # Validar tipo de archivo
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Solo: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Imagen demasiado grande. Máximo {MAX_IMAGE_SIZE_MB}MB."
        )

    # Validar que sea imagen real con Pillow
    try:
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Archivo de imagen inválido o corrupto.")

    # Eliminar imagen anterior si existe
    if product.image_url and product.image_url.startswith("uploads/"):
        old_path = product.image_url
        if os.path.exists(old_path):
            os.remove(old_path)

    # Guardar nueva imagen
    ext = file.content_type.split("/")[-1].replace("jpeg", "jpg")
    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    # Actualizar URL en BD
    product.image_url = filepath
    db.commit()

    logger.info(f"Imagen guardada para producto {product_id}: {filepath}")
    return {
        "message":    f"Imagen subida correctamente para '{product.name}'.",
        "image_url":  filepath,
        "product_id": product_id,
        "file_size":  f"{len(content) / 1024:.1f} KB",
    }


@router.delete("/products/{product_id}/image")
def delete_product_image(
    product_id: int,
    db: Session = Depends(get_db),
    _:  User    = Depends(require_supervisor_or_admin),
):
    """Elimina la imagen de un producto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    if not product.image_url:
        raise HTTPException(status_code=400, detail="El producto no tiene imagen.")

    if product.image_url.startswith("uploads/") and os.path.exists(product.image_url):
        os.remove(product.image_url)

    product.image_url = None
    db.commit()
    return {"message": "Imagen eliminada correctamente."}


# ═══════════════════════════════════════════════════════════════════════════════
# BÚSQUEDA AVANZADA (complementa el router de products)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/products/search/advanced")
def advanced_search(
    q:           Optional[str]  = Query(None, description="Texto libre (nombre, código, barcode, descripción)"),
    category_id: Optional[int]  = Query(None),
    low_stock:   Optional[bool] = Query(None),
    expiring_in: Optional[int]  = Query(None, description="Productos que vencen en N días"),
    location:    Optional[str]  = Query(None),
    skip:        int            = Query(0, ge=0),
    limit:       int            = Query(50, ge=1, le=200),
    db:          Session        = Depends(get_db),
    _:           User           = Depends(get_current_user),
):
    """
    Búsqueda avanzada de productos con múltiples filtros combinables.
    """
    from sqlalchemy import or_, and_
    from app.models.product import ProductBatch
    from datetime import date, timedelta

    query = db.query(Product).filter(Product.is_active == True)

    # Texto libre
    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.code.ilike(term),
                Product.barcode.ilike(term),
                Product.description.ilike(term),
            )
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if low_stock:
        query = query.filter(Product.current_stock <= Product.min_stock)

    if location:
        query = query.filter(Product.location.ilike(f"%{location}%"))

    # Productos con lotes que vencen pronto
    if expiring_in:
        cutoff = date.today() + timedelta(days=expiring_in)
        products_with_expiry = (
            db.query(ProductBatch.product_id)
            .filter(
                ProductBatch.expiry_date <= cutoff,
                ProductBatch.expiry_date >= date.today(),
                ProductBatch.is_active == True,
            )
            .distinct()
            .subquery()
        )
        query = query.filter(Product.id.in_(products_with_expiry))

    total = query.count()
    items = query.order_by(Product.name).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id":            p.id,
                "code":          p.code,
                "name":          p.name,
                "current_stock": float(p.current_stock),
                "min_stock":     float(p.min_stock),
                "is_low_stock":  p.is_low_stock,
                "unit":          p.unit,
                "location":      p.location,
                "category_id":   p.category_id,
                "image_url":     p.image_url,
                "has_qr":        bool(p.qr_code),
            }
            for p in items
        ],
    }
