productos = {
    "U001": 'Uva Roja "JR" a granel',
    "U002": 'Uva Verde "Queen of the Valley"',
    "U003": 'Uva Roja "RAR" sin semilla',
    "U004": 'Uva Negra "RAR" sin semilla',
    "U005": 'Uva Roja "UVA VA" a granel',
    "U006": 'Uva Roja "UVA VA" caja de cartón',
    "U007": 'Uva Roja "RAR" red globe',
    "U008": 'Uva Roja "Delano Export" red globe',
    "U009": 'Uva Roja "Las Glorias" red globe',
    "U010": 'Uva Verde "RVR Agro"',
    "U011": 'Uva Roja "UVA VA" caja 7L',
    "U012": 'Uva Roja peruana L',
    "U013": 'Uva Roja peruana XL',
    "U014": 'Uva Roja peruana J',
    "G150": "Manzana Gala 150",
    "G163": "Manzana Gala 163",
    "G175": "Manzana Gala 175",
    "G198": "Manzana Gala 198",
    "M80": "Manzana Roja 80",
    "M88": "Manzana Roja 88",
    "M100": "Manzana Roja 100",
    "M113": "Manzana Roja 113",
    "M150": "Manzana Roja 150",
    "M163": "Manzana Roja 163",
    "M175": "Manzana Roja 175",
    "M198": "Manzana Roja 198"
}

bodegas = ["COIMPEX", "Predio Z11", "Villa Nueva", "El Tejar (Berry Fresh)", "Parramos", "CENMA"]

#####################################################
# Funciones para generar PDF
#####################################################

from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generar_estado_cuenta_pdf(df, cliente_nombre, total_comprado, total_pagado, total_pendiente):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    elementos = []

    # Título
    elementos.append(Paragraph("<b>Estado de Cuenta</b>", styles["Title"]))
    elementos.append(Paragraph(f"<b>Cliente:</b> {cliente_nombre}", styles["Normal"]))

    # Fecha
    elementos.append(Paragraph(f"<b>Fecha Inicial:</b> {df['fecha'].min()}", styles["Normal"]))
    elementos.append(Paragraph(f"<b>Fecha Final:</b> {df['fecha'].max()}", styles["Normal"]))
    
    elementos.append(Paragraph("", styles["Normal"]))

    elementos.append(Spacer(1, 12))

    # Tabla
    tabla_data = [
        ["Fecha", "ID", "Producto", "Cantidad", "Precio", "Subtotal", "Estado"]
    ]

    for _, row in df.iterrows():
        tabla_data.append([
            row["fecha"],
            row["id_transaccion"],
            row["producto"],
            row["cantidad"],
            f"Q {row['precio']:,.2f}",
            f"Q {row['subtotal']:,.2f}",
            row["estado"],
        ])

    tabla = Table(tabla_data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (3, 1), (-2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elementos.append(tabla)
    elementos.append(Paragraph("<br/>", styles["Normal"]))

    # Totales
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"<b>Total Comprado:</b> Q {total_comprado:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"<b>Total Pagado:</b> Q {total_pagado:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"<b>Total Pendiente:</b> Q {total_pendiente:,.2f}", styles["Normal"]))

    doc.build(elementos)
    buffer.seek(0)

    return buffer
