import streamlit as st
import pandas as pd
from db import run_query
from data import productos, bodegas, generar_estado_cuenta_pdf

st.set_page_config(page_title="Inventarios",
                   page_icon="📦", 
                   layout="wide")

tabs = st.tabs(["Inventarios", "Kardex"])

clientes = run_query("SELECT * FROM clientes")
proveedores = run_query("SELECT * FROM proveedores")
encabezados = run_query("SELECT * FROM encabezados")
detalle = run_query("SELECT * FROM detalles")

with tabs[0]:
    st.subheader("Inventarios")

    

with tabs[1]:

    st.subheader("Kardex")

    st.sidebar.subheader("Filtros")
    sku = st.sidebar.selectbox("SKU", [None] + list(productos.values()))
    cliente = st.sidebar.selectbox("Cliente", [None] + [c["nombre"] for c in clientes])
    proveedor = st.sidebar.selectbox("Proveedor", [None] + [p["nombre"] for p in proveedores])
    transaccion = st.sidebar.selectbox("Transaccion", [None] + ["Venta", "Compra", "Transferencia"])
    bodega_origen = st.sidebar.selectbox("Bodega Origen", [None] + bodegas)
    bodega_destino = st.sidebar.selectbox("Bodega Destino", [None] + bodegas)

    result = run_query(
        """
        SELECT
            c.nombre AS cliente,
            p.nombre AS proveedor,
            e.id_transaccion,
            e.fecha,
            d.sku,
            d.cantidad,
            e.no_envio,
            e.bodega_origen,
            e.bodega_destino,
            e.transaccion
        FROM encabezados e
        LEFT JOIN clientes c ON e.id_cliente = c.id_cliente
        LEFT JOIN proveedores p ON e.id_proveedor = p.id_proveedor
        JOIN detalles d ON d.id_transaccion = e.id_transaccion
        ORDER BY e.fecha, e.no_envio;
        """,
        fetch="all"
    )

    df = pd.DataFrame(result)

    df["tercero"] = df["cliente"].combine_first(df["proveedor"])
    df["tercero"] = df["tercero"].fillna("N/A")
    df["no_envio"] = df["no_envio"].fillna("N/A")
    df["bodega_origen"] = df["bodega_origen"].fillna("N/A")
    df["bodega_destino"] = df["bodega_destino"].fillna("N/A")
    df["sku"] = df["sku"].map(productos)
    df["transaccion"] = df["transaccion"].map({
        1: "Venta",
        2: "Compra",
        3: "Transferencia"
    })

    if sku:
        df = df[df["sku"] == sku]
    if cliente:
        df = df[df["cliente"] == cliente]
    if proveedor:
        df = df[df["proveedor"] == proveedor]
    if transaccion:
        df = df[df["transaccion"] == transaccion]
    if bodega_origen:
        df = df[df["bodega_origen"] == bodega_origen]
    if bodega_destino:
        df = df[df["bodega_destino"] == bodega_destino]

    df_print = df[["fecha",
                    "id_transaccion",
                    "transaccion",
                    "no_envio",
                    "tercero",
                    "bodega_origen",
                    "bodega_destino",
                    "sku",
                    "cantidad"]]

    st.dataframe(df_print, width="stretch", column_config={
        "fecha": "Fecha",
        "id_transaccion": "ID",
        "transaccion": "Tipo de Transaccion",
        "no_envio": "No. Envio",
        "tercero": "Cliente/Proveedor",
        "bodega_origen": "Bodega Origen",
        "bodega_destino": "Bodega Destino",
        "sku": "SKU",
        "cantidad": "Cantidad"
    })