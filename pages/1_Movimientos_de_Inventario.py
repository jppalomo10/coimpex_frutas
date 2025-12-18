import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from database import get_connection

# ---------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------
st.set_page_config(
    page_title="Registro",
    layout="centered",
    page_icon="🍎"
)

# ---------------------------------
# BASES DE DATOS
# ---------------------------------

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "../db.xlsx"

df_clientes = pd.read_excel(EXCEL_PATH, sheet_name="Clientes")
df_proveedores = pd.read_excel(EXCEL_PATH, sheet_name="Proveedores")
df_productos = pd.read_excel(EXCEL_PATH, sheet_name="Productos")

productos_lista = df_productos["Producto"].tolist()

# ---------------------------------
# SESSION STATE
# ---------------------------------
if "carrito" not in st.session_state:
    st.session_state.carrito = []

if "reset_form" not in st.session_state:
    st.session_state.reset_form = False

if "expand_producto" not in st.session_state:
    st.session_state.expand_producto = True

# ---------------------------------
# TÍTULO
# ---------------------------------
st.title("📄 Formulario de Registro")

# ---------------------------------
# SECCIÓN 1: TIPO DE MOVIMIENTO
# ---------------------------------
st.subheader("Tipos de Movimientos")
transaccion = st.selectbox(
    "Tipo de Movimiento",
    ["Venta", "Compra", "Transferencia"],
    key="transaccion"
)

st.divider()

# ---------------------------------
# SECCIÓN 2: ENCABEZADO
# ---------------------------------
if transaccion == "Venta":
    st.subheader("Datos de la Venta")

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    fecha = c1.date_input("Fecha", datetime.now(), key="fecha")
    correlativo = c2.text_input("No. Envío", key="correlativo")

    tipo = c3.selectbox(
        "Tipo de Venta",
        ["", "Venta al contado", "Venta al crédito"],
        key="tipo"
    )

    if tipo == "Venta al contado":
        opciones_pago = ["Efectivo", "Tarjeta", "Transferencia"]
    elif tipo == "Venta al crédito":
        opciones_pago = ["Pendiente de pago"]
    else:
        opciones_pago = []

    pago = c4.selectbox("Forma de Pago", opciones_pago, key="pago")

    bodega = st.selectbox("Punto de venta", ["", "Roosevelt", "Predio Z11"], key="bodega")
    cliente = st.text_input("Nombre del Cliente", key="cliente")

elif transaccion == "Compra":
    st.subheader("Datos de la Compra")

    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", datetime.now(), key="fecha")
    correlativo = c2.text_input("No. Envío", key="correlativo")

    bodega = st.selectbox("Bodega", ["", "Roosevelt", "Predio Z11"], key="bodega")
    proveedor = st.text_input("Nombre del Proveedor", key="proveedor")

elif transaccion == "Transferencia":
    st.subheader("Datos de la Transferencia")

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    fecha = c1.date_input("Fecha", datetime.now(), key="fecha")
    correlativo = c2.text_input("No. Envío", key="correlativo")

    bodega_entrada = c3.selectbox("Bodega de entrada", ["", "Roosevelt", "Predio Z11"], key="bodega_entrada")
    bodega_salida = c4.selectbox("Bodega de salida", ["", "Roosevelt", "Predio Z11"], key="bodega_salida")

st.divider()

# ---------------------------------
# SECCIÓN 3: DETALLE (CARRITO)
# ---------------------------------
st.subheader(f"Detalle de la {transaccion}")

if transaccion in ["Venta", "Compra"]:
    

    with st.expander("Agregar producto", expanded=st.session_state.expand_producto):
        c1, c2, c3 = st.columns([3, 1, 1])

        prod_nom = c1.selectbox("Producto", productos_lista, key="prod_nom")
        prod_cant = c2.number_input("Cantidad", min_value=1, step=1, key="prod_cant")
        prod_precio = c3.number_input("Precio", min_value=0.0, step=0.5, key="prod_precio")

        if st.button("Agregar al detalle"):
            subtotal = prod_cant * prod_precio
            st.session_state.carrito.append({
                "Producto": prod_nom,
                "Cantidad": prod_cant,
                "Precio": prod_precio,
                "Subtotal": subtotal
            })

            st.session_state.expand_producto = False
            st.rerun()

    # ---------------------------------
    # TABLA DETALLE
    # ---------------------------------
    if st.session_state.carrito:
        df_detalle = pd.DataFrame(st.session_state.carrito)

        st.dataframe(df_detalle, use_container_width=True)

        total = df_detalle["Subtotal"].sum()
        st.markdown(f"### 💰 Total: **Q {total:,.2f}**")

        c1, c2, c3 = st.columns(3)

        if c1.button("🗑️ Quitar último"):
            st.session_state.carrito.pop()

        if c2.button("🧹 Vaciar detalle"):
            st.session_state.carrito = []
        
        if c3.button("💾 Guardar"):

            conn = get_connection()
            cursor = conn.cursor()

            if transaccion == "Venta":
                cursor.execute("""
                    INSERT INTO encabezado_transaccion (
                        fecha,
                        transaccion,
                        no_envio,
                        tipo_venta,
                        metodo_pago,
                        bodega1,
                        bodega2,
                        id_cliente,
                        proveedor,
                        total
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fecha,
                    1,
                    correlativo,
                    tipo,
                    pago,
                    bodega,
                    "nan",
                    cliente,
                    "nan",
                    total
                ))
                
            elif transaccion == "Compra":
                cursor.execute("""
                    INSERT INTO encabezado_transaccion (
                        fecha,
                        transaccion,
                        no_envio,
                        tipo_venta,
                        metodo_pago,
                        bodega1,
                        bodega2,
                        id_cliente,
                        proveedor,
                        total
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fecha,
                    2,
                    correlativo,
                    "nan",
                    "nan",
                    bodega,
                    "nan",
                    "nan",
                    proveedor,
                    total
                ))

            id_transaccion = cursor.lastrowid
            
            for item in st.session_state.carrito:
                cursor.execute("""
                INSERT INTO detalle_transaccion (
                    id_transaccion,
                    fecha,
                    sku,
                    cantidad,
                    precio,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    id_transaccion,
                    fecha,
                    item["Producto"],
                    item["Cantidad"],
                    item["Precio"],
                    item["Subtotal"]
                ))

            conn.commit()
            cursor.close()
            conn.close()

            st.success("Movimiento guardado exitosamente.")

            # limpiar carrito
            st.session_state.carrito = []

            # resetear formulario
            keys_a_borrar = [
                "fecha",
                "correlativo",
                "tipo",
                "pago",
                "cliente",
                "proveedor",
                "bodega",
                "bodega_entrada",
                "bodega_salida"
            ]

            for k in keys_a_borrar:
                if k in st.session_state:
                    del st.session_state[k]

            st.session_state.expand_producto = True

            st.rerun()



    else:
        st.info("No hay productos agregados aún.")

elif transaccion == "Transferencia":
    
    with st.expander("Agregar producto", expanded=st.session_state.expand_producto):
        c1, c2 = st.columns([3, 1])

        prod_nom = c1.selectbox("Producto", productos_lista)
        prod_cant = c2.number_input("Cantidad", min_value=1, step=1)

        if st.button("Agregar al detalle"):
            st.session_state.carrito.append({
                "Producto": prod_nom,
                "Cantidad": prod_cant
            })

            st.session_state.expand_producto = False
            st.rerun()

    # ---------------------------------
    # TABLA DETALLE
    # ---------------------------------
    if st.session_state.carrito:

        df_detalle = pd.DataFrame(st.session_state.carrito)

        st.dataframe(df_detalle, use_container_width=True)

        total = df_detalle["Cantidad"].sum()
        st.markdown(f"### Total de cajas: {total}")

        c1, c2, c3 = st.columns(3)

        if c1.button("🗑️ Quitar último"):
            st.session_state.carrito.pop()

        if c2.button("🧹 Vaciar detalle"):
            st.session_state.carrito = []   

        if c3.button("💾 Guardar"):

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO encabezado_transaccion (
                    fecha,
                    transaccion,
                    no_envio,
                    tipo_venta,
                    metodo_pago,
                    bodega1,
                    bodega2,
                    id_cliente,
                    proveedor,
                    total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fecha,
                3,
                correlativo,
                "nan",
                "nan",
                bodega_entrada,
                bodega_salida,
                "nan",
                "nan",
                total
            ))
            
            id_transaccion = cursor.lastrowid
            
            for item in st.session_state.carrito:
                cursor.execute("""
                INSERT INTO detalle_transaccion (
                    id_transaccion,
                    fecha,
                    sku,
                    cantidad,
                    precio,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    id_transaccion,
                    fecha,
                    item["Producto"],
                    item["Cantidad"],
                    "nan",
                    "nan"
                ))

            conn.commit()
            cursor.close()
            conn.close()

            st.success("Movimiento guardado exitosamente.")

            # limpiar carrito
            st.session_state.carrito = []

            # resetear formulario
            keys_a_borrar = [
                "fecha",
                "correlativo",
                "tipo",
                "pago",
                "cliente",
                "proveedor",
                "bodega",
                "bodega_entrada",
                "bodega_salida"
            ]

            for k in keys_a_borrar:
                if k in st.session_state:
                    del st.session_state[k]

            st.session_state.expand_producto = True

            st.rerun()

    else:
        st.info("No hay productos agregados aún.")
