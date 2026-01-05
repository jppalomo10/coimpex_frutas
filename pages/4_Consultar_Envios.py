import streamlit as st
import pandas as pd
from db import run_query
from data import productos, bodegas

st.set_page_config(page_title="Envios",
                   page_icon=":paperclip:", 
                   layout="wide")

clientes = run_query("SELECT * FROM clientes")
proveedores = run_query("SELECT * FROM proveedores")
encabezados = pd.DataFrame(run_query("SELECT * FROM encabezados"))
detalle = pd.DataFrame(run_query("SELECT * FROM detalles"))

envios = encabezados["no_envio"].unique()

st.subheader("Envios")

col1, placeholder = st.columns([1, 2])


no_envio = col1.selectbox("No. Envio", envios)

if no_envio != None:

    result = pd.DataFrame(run_query(
        """
        SELECT
            c.nombre AS cliente,
            e.id_transaccion,
            e.fecha,
            e.factura,
            e.no_envio,
            d.sku,
            d.cantidad,
            d.precio,
            d.subtotal,
            e.total,
            e.estado,
            e.pagado
        FROM clientes c
        JOIN encabezados e ON e.id_cliente = c.id_cliente
        JOIN detalles d ON d.id_transaccion = e.id_transaccion
        WHERE e.no_envio = %s
        ORDER BY e.fecha, e.id_transaccion;
        """,
        params=(no_envio,),
        fetch="all"
    ))

    encabezado = result.iloc[0]

    st.markdown("## 🧾 Factura / Envío")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Cliente")
        st.write(encabezado["cliente"])
        st.write(f"**Fecha:** {encabezado['fecha']}")


    with col2:
        st.markdown("### Factura")
        st.write(f"**Estado:** {encabezado['estado']}")
        st.write(f"**No. Envío:** {encabezado['no_envio']}")

    st.markdown("### Detalle de productos")

    detalle = result[["sku", "cantidad", "precio", "subtotal"]]

    detalle["precio"] = detalle["precio"].map(lambda x: f"Q {x:,.2f}")
    detalle["subtotal"] = detalle["subtotal"].map(lambda x: f"Q {x:,.2f}")
    detalle["productos"] = detalle["sku"].map(productos)

    st.dataframe(detalle, width="stretch", column_config={
        "sku": "SKU",
        "productos": "Producto",
        "cantidad": "Cantidad",
        "precio": "Precio Unitario",
        "subtotal": "Subtotal"
    })

            