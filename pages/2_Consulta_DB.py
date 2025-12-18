import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from io import BytesIO

# ---------------------------------
# CONFIGURACIÓN
# ---------------------------------
st.set_page_config(
    page_title="Consulta Base de Datos",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Consulta y Exportación de Movimientos")

# ---------------------------------
# CONEXIÓN DB
# ---------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db.sqlite"

if not DB_PATH.exists():
    st.error(f"No se encontró la base de datos en: {DB_PATH}")
    st.stop()

conn = sqlite3.connect(DB_PATH)

# ---------------------------------
# CARGA DE TABLAS
# ---------------------------------
df_enc = pd.read_sql("SELECT * FROM encabezado_transaccion", conn)
df_det = pd.read_sql("SELECT * FROM detalle_transaccion", conn)

conn.close()

if df_enc.empty:
    st.warning("La tabla de encabezados está vacía.")
    st.stop()

# ---------------------------------
# MAPEO TIPO TRANSACCIÓN
# ---------------------------------
tipo_map = {
    1: "Venta",
    2: "Compra",
    3: "Transferencia"
}

df_enc["tipo_movimiento"] = df_enc["transaccion"].map(tipo_map)

# ---------------------------------
# FILTROS
# ---------------------------------
st.sidebar.header("🔎 Filtros")

tipo_filtro = st.sidebar.multiselect(
    "Tipo de movimiento",
    ["Venta", "Compra", "Transferencia"],
    default=["Venta", "Compra", "Transferencia"]
)

df_filtrado = df_enc[df_enc["tipo_movimiento"].isin(tipo_filtro)]

# ---------------------------------
# TABLAS EN PANTALLA
# ---------------------------------
st.subheader("📌 Encabezado de Transacciones")
st.dataframe(df_filtrado, use_container_width=True)

st.subheader("📦 Detalle de Transacciones")
df_det_filtrado = df_det[df_det["id_transaccion"].isin(df_filtrado["id_transaccion"])]
st.dataframe(df_det_filtrado, use_container_width=True)

# ---------------------------------
# DATASETS PARA EXCEL
# ---------------------------------
df_ventas = df_enc[df_enc["transaccion"] == 1]
df_compras = df_enc[df_enc["transaccion"] == 2]
df_transferencias = df_enc[df_enc["transaccion"] == 3]

# ---------------------------------
# EXPORTAR A EXCEL (MULTI-HOJA)
# ---------------------------------
def generar_excel():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_enc.to_excel(writer, sheet_name="Encabezado", index=False)
        df_det.to_excel(writer, sheet_name="Detalle", index=False)
        df_ventas.to_excel(writer, sheet_name="Ventas", index=False)
        df_compras.to_excel(writer, sheet_name="Compras", index=False)
        df_transferencias.to_excel(writer, sheet_name="Transferencias", index=False)

    output.seek(0)
    return output

st.divider()

st.download_button(
    label="⬇️ Descargar Excel completo",
    data=generar_excel(),
    file_name="movimientos_inventario.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
