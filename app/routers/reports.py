from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime
from io import BytesIO
from decimal import Decimal

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.database import get_db
from app.models.product import Product, ProductBatch
from app.models.movement import Movement
from app.models.user import User
from app.core.deps import get_current_user, require_supervisor_or_admin

router = APIRouter()

# ── Colores corporativos ──────────────────────────────────────────────────────
AZUL         = colors.HexColor("#1565C0")
AZUL_CLARO   = colors.HexColor("#E3F2FD")
GRIS         = colors.HexColor("#6B7280")
ROJO         = colors.HexColor("#C62828")
VERDE        = colors.HexColor("#2E7D32")
NARANJA      = colors.HexColor("#F57C00")


def _header_paragraph(title: str, subtitle: str = "") -> list:
    """Genera el encabezado estándar de todos los reportes."""
    styles = getSampleStyleSheet()
    elementos = []

    style_title = ParagraphStyle(
        "titulo",
        parent    = styles["Title"],
        fontSize  = 18,
        textColor = AZUL,
        spaceAfter= 4,
        alignment = TA_CENTER,
    )
    style_sub = ParagraphStyle(
        "subtitulo",
        parent    = styles["Normal"],
        fontSize  = 10,
        textColor = GRIS,
        alignment = TA_CENTER,
        spaceAfter= 2,
    )
    style_fecha = ParagraphStyle(
        "fecha",
        parent    = styles["Normal"],
        fontSize  = 9,
        textColor = GRIS,
        alignment = TA_RIGHT,
    )

    elementos.append(Paragraph("MedStock Pro", style_title))
    elementos.append(Paragraph("EA Medical S.R.L.", style_sub))
    if subtitle:
        elementos.append(Paragraph(subtitle, style_sub))
    elementos.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        style_fecha,
    ))
    elementos.append(HRFlowable(width="100%", thickness=1.5, color=AZUL, spaceAfter=12))
    return elementos


def _make_pdf(elements: list, title: str = "reporte") -> BytesIO:
    """Construye el PDF y retorna el buffer."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize    = A4,
        rightMargin = 2 * cm,
        leftMargin  = 2 * cm,
        topMargin   = 2 * cm,
        bottomMargin= 2 * cm,
        title       = title,
        author      = "MedStock Pro",
    )
    doc.build(elements)
    buffer.seek(0)
    return buffer


def _tabla_style(header_color=AZUL) -> TableStyle:
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  header_color),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",       (0, 0), (-1, 0),  "CENTER"),
    ])


# ── Reporte 1: Kardex por producto ────────────────────────────────────────────
@router.get("/kardex/{product_id}")
def report_kardex(
    product_id: int,
    date_from:  Optional[date] = Query(None),
    date_to:    Optional[date] = Query(None),
    db:         Session        = Depends(get_db),
    current:    User           = Depends(require_supervisor_or_admin),
):
    """Genera PDF del kardex de un producto (historial de movimientos)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        from fastapi import HTTPException
        raise HTTPException(404, "Producto no encontrado.")

    query = db.query(Movement).filter(Movement.product_id == product_id)
    if date_from:
        query = query.filter(Movement.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Movement.created_at <= datetime.combine(date_to, datetime.max.time()))

    movimientos = query.order_by(Movement.created_at).all()

    styles = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=9)

    elementos = _header_paragraph(
        "Kardex de Producto",
        f"Reporte de movimientos: {product.name} (Código: {product.code})"
    )

    # Info del producto
    info_data = [
        ["Código:", product.code,     "Unidad:", product.unit],
        ["Stock actual:", str(product.current_stock), "Stock mínimo:", str(product.min_stock)],
        ["Ubicación:", product.location or "—", "Categoría:", product.category.name if product.category else "—"],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), AZUL),
        ("TEXTCOLOR", (2,0), (2,-1), AZUL),
        ("TOPPADDING",(0,0),(-1,-1), 3),
    ]))
    elementos.append(info_table)
    elementos.append(Spacer(1, 12))

    # Tabla de movimientos
    encabezado = ["Fecha", "Tipo", "Motivo", "Cantidad", "Stock Antes", "Stock Después", "Responsable"]
    filas = [encabezado]

    for mov in movimientos:
        tipo_color = {
            "ingreso": "▲ Ingreso",
            "salida":  "▼ Salida",
            "ajuste":  "↔ Ajuste",
            "baja":    "✕ Baja",
        }.get(mov.movement_type, mov.movement_type)

        filas.append([
            mov.created_at.strftime("%d/%m/%Y %H:%M"),
            tipo_color,
            mov.reason or "—",
            str(mov.quantity),
            str(mov.stock_before),
            str(mov.stock_after),
            f"ID {mov.responsible_id}",
        ])

    if len(filas) == 1:
        filas.append(["Sin movimientos en el período seleccionado", "", "", "", "", "", ""])

    tabla = Table(filas, colWidths=[3*cm, 2.5*cm, 3*cm, 2*cm, 2.5*cm, 2.5*cm, 2*cm])
    tabla.setStyle(_tabla_style())
    elementos.append(Paragraph(f"Movimientos ({len(filas)-1} registros)", styles["Heading3"]))
    elementos.append(Spacer(1, 6))
    elementos.append(tabla)

    buffer = _make_pdf(elementos, f"kardex_{product.code}")
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=kardex_{product.code}.pdf"},
    )


# ── Reporte 2: Stock valorizado ───────────────────────────────────────────────
@router.get("/stock-value")
def report_stock_value(
    db:      Session = Depends(get_db),
    current: User    = Depends(require_supervisor_or_admin),
):
    """Genera PDF con el valor total del inventario (cantidad × precio unitario)."""
    productos = db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock > 0,
    ).order_by(Product.name).all()

    elementos = _header_paragraph(
        "Reporte de Stock Valorizado",
        f"Inventario valorizado al {date.today().strftime('%d/%m/%Y')}"
    )

    encabezado = ["Código", "Producto", "Unidad", "Stock", "Precio Unit.", "Valor Total"]
    filas = [encabezado]
    total_valor = Decimal("0")

    for p in productos:
        precio  = p.unit_price or Decimal("0")
        valor   = Decimal(str(p.current_stock)) * precio
        total_valor += valor
        filas.append([
            p.code,
            p.name[:35],
            p.unit,
            str(p.current_stock),
            f"Bs {precio:,.2f}" if precio else "—",
            f"Bs {valor:,.2f}" if precio else "—",
        ])

    # Fila de total
    filas.append(["", "", "", "", "TOTAL:", f"Bs {total_valor:,.2f}"])

    tabla = Table(filas, colWidths=[2.5*cm, 6.5*cm, 2*cm, 2*cm, 3*cm, 3*cm])
    estilo = _tabla_style()
    # Resaltar fila de total
    estilo.add("BACKGROUND",  (0, len(filas)-1), (-1, len(filas)-1), AZUL_CLARO)
    estilo.add("FONTNAME",    (0, len(filas)-1), (-1, len(filas)-1), "Helvetica-Bold")
    estilo.add("TEXTCOLOR",   (4, len(filas)-1), (-1, len(filas)-1), AZUL)
    tabla.setStyle(estilo)

    elementos.append(Paragraph(f"Productos con stock: {len(productos)}", getSampleStyleSheet()["Heading3"]))
    elementos.append(Spacer(1, 6))
    elementos.append(tabla)

    buffer = _make_pdf(elementos, "stock_valorizado")
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=stock_valorizado.pdf"},
    )


# ── Reporte 3: Vencimientos próximos ─────────────────────────────────────────
@router.get("/expiry")
def report_expiry(
    days: int     = Query(30, description="Días de anticipación (7, 15 o 30)"),
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_supervisor_or_admin),
):
    """Genera PDF de lotes que vencen en los próximos N días."""
    hoy         = date.today()
    fecha_limite= hoy + timedelta(days=days)

    from datetime import timedelta
    lotes = db.query(ProductBatch).filter(
        ProductBatch.is_active == True,
        ProductBatch.expiry_date != None,
        ProductBatch.expiry_date >= hoy,
        ProductBatch.expiry_date <= fecha_limite,
        ProductBatch.quantity > 0,
    ).order_by(ProductBatch.expiry_date).all()

    elementos = _header_paragraph(
        f"Reporte de Vencimientos — {days} días",
        f"Lotes que vencen entre {hoy.strftime('%d/%m/%Y')} y {fecha_limite.strftime('%d/%m/%Y')}"
    )

    encabezado = ["Producto", "Lote", "Cantidad", "Vence", "Días restantes", "Criticidad"]
    filas = [encabezado]

    for lote in lotes:
        dias_rest = (lote.expiry_date - hoy).days
        crit = "🔴 CRÍTICO" if dias_rest <= 7 else "🟡 ADVERTENCIA" if dias_rest <= 15 else "🔵 INFO"
        producto = db.query(Product).filter(Product.id == lote.product_id).first()
        filas.append([
            producto.name[:30] if producto else f"ID {lote.product_id}",
            lote.batch_number or str(lote.id),
            str(lote.quantity),
            lote.expiry_date.strftime("%d/%m/%Y"),
            str(dias_rest),
            crit,
        ])

    if len(filas) == 1:
        filas.append(["No hay lotes próximos a vencer", "", "", "", "", ""])

    tabla = Table(filas, colWidths=[5*cm, 2.5*cm, 2*cm, 2.5*cm, 2.5*cm, 3*cm])
    tabla.setStyle(_tabla_style())
    elementos.append(Paragraph(f"Lotes próximos a vencer: {len(filas)-1}", getSampleStyleSheet()["Heading3"]))
    elementos.append(Spacer(1, 6))
    elementos.append(tabla)

    buffer = _make_pdf(elementos, "vencimientos")
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=vencimientos.pdf"},
    )


# ── Reporte 4: Movimientos por período ───────────────────────────────────────
@router.get("/movements")
def report_movements(
    date_from: Optional[date] = Query(None),
    date_to:   Optional[date] = Query(None),
    db:        Session        = Depends(get_db),
    _:         User           = Depends(require_supervisor_or_admin),
):
    """Genera PDF con todos los movimientos en un período."""
    from datetime import timedelta
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    movimientos = db.query(Movement).filter(
        Movement.created_at >= datetime.combine(date_from, datetime.min.time()),
        Movement.created_at <= datetime.combine(date_to, datetime.max.time()),
    ).order_by(Movement.created_at.desc()).all()

    elementos = _header_paragraph(
        "Reporte de Movimientos",
        f"Período: {date_from.strftime('%d/%m/%Y')} al {date_to.strftime('%d/%m/%Y')}"
    )

    encabezado = ["Fecha", "Producto", "Tipo", "Cantidad", "Stock Post", "Responsable"]
    filas = [encabezado]

    for mov in movimientos:
        producto = db.query(Product).filter(Product.id == mov.product_id).first()
        filas.append([
            mov.created_at.strftime("%d/%m/%Y"),
            producto.name[:28] if producto else f"ID {mov.product_id}",
            mov.movement_type.upper(),
            str(mov.quantity),
            str(mov.stock_after),
            f"ID {mov.responsible_id}",
        ])

    if len(filas) == 1:
        filas.append(["Sin movimientos en el período seleccionado", "", "", "", "", ""])

    tabla = Table(filas, colWidths=[2.5*cm, 6*cm, 2.5*cm, 2*cm, 2.5*cm, 3*cm])
    tabla.setStyle(_tabla_style())
    elementos.append(Paragraph(f"Total movimientos: {len(filas)-1}", getSampleStyleSheet()["Heading3"]))
    elementos.append(Spacer(1, 6))
    elementos.append(tabla)

    buffer = _make_pdf(elementos, "movimientos")
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=movimientos.pdf"},
    )
