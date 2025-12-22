import streamlit as st
import pandas as pd
from db import run_query
from data import productos

st.set_page_config(
    page_title="COIMPEX S.A.",
    page_icon="🍇",
    layout="wide"
)

st.title("🏠 Menú principal")

st.markdown("""
Bienvenido a la aplicación.
Selecciona una sección desde el menú lateral.
""")

st.subheader("Estado de la base de datos")

row = run_query("select now() as ahora;", fetch="one")
st.write("Conectado ✅", row["ahora"])

clientes = run_query("SELECT * FROM clientes")
proveedores = run_query("SELECT * FROM proveedores")
encabezados = run_query("SELECT * FROM encabezados")
detalle = run_query("SELECT * FROM detalles")

query_inventario = """
SELECT
    d.sku,
    SUM(CASE WHEN e.transaccion = 2 THEN d.cantidad ELSE 0 END) AS entradas,
    SUM(CASE WHEN e.transaccion = 1 THEN d.cantidad ELSE 0 END) AS salidas,
    SUM(
        CASE
            WHEN e.transaccion = 2 THEN d.cantidad
            WHEN e.transaccion = 1 THEN -d.cantidad
            ELSE 0
        END
    ) AS stock_actual
FROM detalles d
JOIN encabezados e ON d.id_transaccion = e.id_transaccion
GROUP BY d.sku
ORDER BY d.sku;
"""

inventario = run_query(query_inventario, fetch="all")

st.subheader("Inventario Actual")

inventario = pd.DataFrame(inventario)
inventario["productos"] = inventario["sku"].map(productos)
inventario = inventario[["sku", "productos", "entradas", "salidas", "stock_actual"]]

st.dataframe(inventario, width="stretch", column_config={
    "sku": "SKU",
    "productos": "Producto",
    "entradas": "Entradas",
    "salidas": "Salidas",
    "stock_actual": "Stock Actual"
})


