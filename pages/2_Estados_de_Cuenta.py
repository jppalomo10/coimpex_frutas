import streamlit as st
import pandas as pd
from db import run_query
from data import productos, bodegas, generar_estado_cuenta_pdf

st.set_page_config(page_title="Consultas",
                   page_icon="📊", 
                   layout="wide")

clientes = run_query("SELECT * FROM clientes")
proveedores = run_query("SELECT * FROM proveedores")
encabezados = run_query("SELECT * FROM encabezados")
detalle = run_query("SELECT * FROM detalles")

st.title("Estado de Cuenta")

opciones_clientes = {None: ""} | {c["id_cliente"]: c["nombre"] for c in clientes}

c1, c2, c3, c4 = st.columns(4)

cliente = c1.selectbox("Cliente", opciones_clientes, format_func=lambda x: opciones_clientes[x])
estado = c3.multiselect("Estado", ["Pagada", "Pendiente de pago", "Pagada parcialmente", "Anulada"], default=["Pagada", "Pendiente de pago"])

result = run_query(
    """
    SELECT
        c.nombre AS cliente,
        e.id_transaccion,
        e.fecha,
        e.factura,
        d.sku,
        d.cantidad,
        d.precio,
        d.subtotal,
        e.total,
        e.estado
    FROM clientes c
    JOIN encabezados e ON e.id_cliente = c.id_cliente
    JOIN detalles d ON d.id_transaccion = e.id_transaccion
    WHERE c.id_cliente = %s
    ORDER BY e.fecha, e.id_transaccion;
    """,
    params=(cliente,),
    fetch="all"
)

df = pd.DataFrame(result)

if df.empty:
    st.write("No hay datos")
else:
    if estado:
        df = df[df["estado"].isin(estado)]

    # Ingresar nombre del producto
    df["producto"] = df["sku"].map(productos).fillna(df["sku"])

    # Convertir los tipos de datos
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%d/%m/%Y")
    df["cantidad"] = df["cantidad"].astype(int)
    for col in ["precio", "subtotal", "total"]:
        df[col] = df[col].astype(float)

    df_print = df[["fecha", "id_transaccion", "producto", "cantidad", "precio", "subtotal", "estado"]]
    df_print["precio"] = df_print["precio"].map(lambda x: f"Q {x:,.2f}")
    df_print["subtotal"] = df_print["subtotal"].map(lambda x: f"Q {x:,.2f}")

    st.dataframe(df_print, width="stretch", column_config={
        "fecha": "Fecha",
        "id_transaccion": "ID",
        "producto": "Producto",
        "cantidad": "Cantidad",
        "precio": "Precio Unitario",
        "subtotal": "Subtotal",
        "estado": "Estado"
    })
    
    total_comprado = df["subtotal"].sum()
    total_pagado = df[df["estado"] == "Pagada"]["total"].sum()
    total_pendiente = total_comprado - total_pagado

    c5, c6, c7 = st.columns(3)

    c5.write(f"**Total Comprado:** Q {total_comprado:,.2f}")
    c6.write(f"**Total Pagado:** Q {total_pagado:,.2f}")
    c7.write(f"**Total Pendiente:** Q {total_pendiente:,.2f}")


    cliente_nombre = opciones_clientes.get(cliente, "")

    pdf_buffer = generar_estado_cuenta_pdf(
        df,
        cliente_nombre,
        total_comprado,
        total_pagado,
        total_pendiente
    )

    st.download_button(
        label="📄 Descargar Estado de Cuenta (PDF)",
        data=pdf_buffer,
        file_name=f"estado_cuenta_{cliente_nombre}.pdf",
        mime="application/pdf"
    )