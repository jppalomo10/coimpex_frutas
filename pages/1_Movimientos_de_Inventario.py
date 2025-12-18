import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from database import get_connection

# ---------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------
st.set_page_config(
    page_title="Movimientos de Inventario",
    layout="centered",
    page_icon="🍎"
)

# ---------------------------------
# UTILIDADES
# ---------------------------------
def _to_iso_date(d):
    """Convierte datetime/date/string a 'YYYY-MM-DD' (SQLite friendly)."""
    try:
        return d.isoformat()  # date o datetime
    except Exception:
        return str(d)

def _db_error_box(exc: Exception):
    st.error("❌ No se pudo guardar en la base de datos.")
    st.exception(exc)

# ---------------------------------
# CARGA DE EXCEL (CATÁLOGOS)
# ---------------------------------
BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = (BASE_DIR / "../db.xlsx").resolve()

if not EXCEL_PATH.exists():
    st.error(f"No encuentro el archivo Excel en: {EXCEL_PATH}")
    st.stop()

try:
    df_clientes = pd.read_excel(EXCEL_PATH, sheet_name="Clientes")
    df_proveedores = pd.read_excel(EXCEL_PATH, sheet_name="Proveedores")
    df_productos = pd.read_excel(EXCEL_PATH, sheet_name="Productos")
except Exception as e:
    st.error("No pude leer db.xlsx. Revisa nombres de hojas (Clientes/Proveedores/Productos) y el formato del archivo.")
    st.exception(e)
    st.stop()

# Normaliza columna de producto (por si viene con mayúsculas distintas)
col_prod = None
for c in df_productos.columns:
    if str(c).strip().lower() == "producto":
        col_prod = c
        break
if col_prod is None:
    st.error("En la hoja 'Productos' no existe una columna llamada 'Producto'.")
    st.write("Columnas encontradas:", list(df_productos.columns))
    st.stop()

productos_lista = df_productos[col_prod].dropna().astype(str).tolist()

# ---------------------------------
# SESSION STATE
# ---------------------------------
if "carrito" not in st.session_state:
    st.session_state.carrito = []

if "expand_producto" not in st.session_state:
    st.session_state.expand_producto = True

# banderas para mensaje post-guardar
if "guardado_ok" not in st.session_state:
    st.session_state.guardado_ok = False
if "guardado_id" not in st.session_state:
    st.session_state.guardado_id = None

# versión para "recargar" SOLO el formulario (sin reiniciar sesión)
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# ---------------------------------
# FUNCIONES DE CARRITO
# ---------------------------------
def _agregar_item_carrito(item: dict):
    st.session_state.carrito.append(item)
    st.session_state.expand_producto = False
    st.rerun()

def _vaciar_carrito():
    st.session_state.carrito = []
    st.session_state.expand_producto = True
    st.rerun()

def _quitar_ultimo():
    if st.session_state.carrito:
        st.session_state.carrito.pop()
    st.rerun()

# ---------------------------------
# FORMULARIO (CONTAINER VERSIONADO)
# ---------------------------------
with st.container(key=f"form_{st.session_state.form_version}"):

    st.title("📄 Registro de Movimientos")

    # ---------------------------------
    # SECCIÓN 1: TIPO DE MOVIMIENTO
    # ---------------------------------
    st.subheader("Tipos de Movimientos")
    transaccion = st.selectbox(
        "Tipo de Movimiento",
        ["Venta", "Compra", "Transferencia"],
        key=f"transaccion_{st.session_state.form_version}"
    )

    st.divider()

    # ---------------------------------
    # SECCIÓN 2: ENCABEZADO
    # ---------------------------------
    fecha = None
    correlativo = ""
    tipo = ""
    pago = ""
    bodega = ""
    cliente = ""
    proveedor = ""
    bodega_entrada = ""
    bodega_salida = ""

    if transaccion == "Venta":
        st.subheader("Datos de la Venta")

        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)

        fecha = c1.date_input("Fecha", datetime.now(), key=f"fecha_{st.session_state.form_version}")
        correlativo = c2.text_input("No. Envío", key=f"correlativo_{st.session_state.form_version}")

        tipo = c3.selectbox(
            "Tipo de Venta",
            ["", "Venta al contado", "Venta al crédito"],
            key=f"tipo_{st.session_state.form_version}"
        )

        if tipo == "Venta al contado":
            opciones_pago = ["Efectivo", "Tarjeta", "Transferencia"]
        elif tipo == "Venta al crédito":
            opciones_pago = ["Pendiente de pago"]
        else:
            opciones_pago = [""]  # evita selectbox vacío

        pago = c4.selectbox("Forma de Pago", opciones_pago, key=f"pago_{st.session_state.form_version}")

        bodega = st.selectbox("Punto de venta", ["", "Roosevelt", "Predio Z11"], key=f"bodega_{st.session_state.form_version}")
        cliente = st.text_input("Nombre del Cliente", key=f"cliente_{st.session_state.form_version}")

    elif transaccion == "Compra":
        st.subheader("Datos de la Compra")

        c1, c2 = st.columns(2)
        fecha = c1.date_input("Fecha", datetime.now(), key=f"fecha_{st.session_state.form_version}")
        correlativo = c2.text_input("No. Envío", key=f"correlativo_{st.session_state.form_version}")

        bodega = st.selectbox("Bodega", ["", "Roosevelt", "Predio Z11"], key=f"bodega_{st.session_state.form_version}")
        proveedor = st.text_input("Nombre del Proveedor", key=f"proveedor_{st.session_state.form_version}")

    elif transaccion == "Transferencia":
        st.subheader("Datos de la Transferencia")

        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)

        fecha = c1.date_input("Fecha", datetime.now(), key=f"fecha_{st.session_state.form_version}")
        correlativo = c2.text_input("No. Envío", key=f"correlativo_{st.session_state.form_version}")

        bodega_entrada = c3.selectbox("Bodega de entrada", ["", "Roosevelt", "Predio Z11"], key=f"bodega_entrada_{st.session_state.form_version}")
        bodega_salida = c4.selectbox("Bodega de salida", ["", "Roosevelt", "Predio Z11"], key=f"bodega_salida_{st.session_state.form_version}")

    st.divider()

    # ---------------------------------
    # SECCIÓN 3: DETALLE (CARRITO)
    # ---------------------------------
    st.subheader(f"Detalle de la {transaccion}")

    # -------- Venta / Compra --------
    if transaccion in ["Venta", "Compra"]:

        with st.expander("Agregar producto", expanded=st.session_state.expand_producto):
            c1, c2, c3 = st.columns([3, 1, 1])

            prod_nom = c1.selectbox("Producto", productos_lista, key=f"prod_nom_{transaccion}_{st.session_state.form_version}")
            prod_cant = c2.number_input("Cantidad", min_value=1, step=1, key=f"prod_cant_{transaccion}_{st.session_state.form_version}")
            prod_precio = c3.number_input("Precio", min_value=0.0, step=0.5, key=f"prod_precio_{transaccion}_{st.session_state.form_version}")

            if st.button("Agregar al detalle", key=f"btn_add_{transaccion}_{st.session_state.form_version}"):
                subtotal = float(prod_cant) * float(prod_precio)
                _agregar_item_carrito({
                    "Producto": str(prod_nom),
                    "Cantidad": int(prod_cant),
                    "Precio": float(prod_precio),
                    "Subtotal": float(subtotal)
                })

        if st.session_state.carrito:
            df_detalle = pd.DataFrame(st.session_state.carrito)
            st.dataframe(df_detalle, use_container_width=True)

            total = float(df_detalle["Subtotal"].sum())
            st.markdown(f"### 💰 Total: **Q {total:,.2f}**")

            c1, c2, c3 = st.columns(3)

            if c1.button("🗑️ Quitar último", key=f"btn_quitar_{st.session_state.form_version}"):
                _quitar_ultimo()

            if c2.button("🧹 Vaciar detalle", key=f"btn_vaciar_{st.session_state.form_version}"):
                _vaciar_carrito()

            if c3.button("💾 Guardar", key=f"btn_guardar_vc_{st.session_state.form_version}"):
                try:
                    if not st.session_state.carrito:
                        st.warning("Agrega al menos un producto antes de guardar.")
                        st.stop()

                    fecha_sql = _to_iso_date(fecha)

                    conn = get_connection()
                    cursor = conn.cursor()

                    if transaccion == "Venta":
                        cursor.execute("""
                            INSERT INTO encabezado_transaccion (
                                fecha, transaccion, no_envio, tipo_venta, metodo_pago,
                                bodega1, bodega2, id_cliente, proveedor, total
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            fecha_sql,
                            1,
                            correlativo or None,
                            tipo or None,
                            pago or None,
                            bodega or None,
                            None,
                            cliente or None,
                            None,
                            float(total)
                        ))

                    elif transaccion == "Compra":
                        cursor.execute("""
                            INSERT INTO encabezado_transaccion (
                                fecha, transaccion, no_envio, tipo_venta, metodo_pago,
                                bodega1, bodega2, id_cliente, proveedor, total
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            fecha_sql,
                            2,
                            correlativo or None,
                            None,
                            None,
                            bodega or None,
                            None,
                            None,
                            proveedor or None,
                            float(total)
                        ))

                    id_transaccion = cursor.lastrowid

                    for item in st.session_state.carrito:
                        cursor.execute("""
                            INSERT INTO detalle_transaccion (
                                id_transaccion, fecha, sku, cantidad, precio, subtotal
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            int(id_transaccion),
                            fecha_sql,
                            str(item["Producto"]),
                            int(item["Cantidad"]),
                            float(item["Precio"]),
                            float(item["Subtotal"])
                        ))

                    conn.commit()
                    cursor.close()
                    conn.close()

                    # mensaje + "recarga" del formulario sin reiniciar sesión
                    st.session_state.guardado_ok = True
                    st.session_state.guardado_id = int(id_transaccion)

                    st.session_state.carrito = []
                    st.session_state.expand_producto = True
                    st.session_state.form_version += 1

                    st.rerun()

                except Exception as e:
                    _db_error_box(e)
                    try:
                        conn.rollback()
                    except Exception:
                        pass

        else:
            st.info("No hay productos agregados aún.")

    # -------- Transferencia --------
    elif transaccion == "Transferencia":

        with st.expander("Agregar producto", expanded=st.session_state.expand_producto):
            c1, c2 = st.columns([3, 1])

            prod_nom = c1.selectbox("Producto", productos_lista, key=f"prod_nom_transfer_{st.session_state.form_version}")
            prod_cant = c2.number_input("Cantidad", min_value=1, step=1, key=f"prod_cant_transfer_{st.session_state.form_version}")

            if st.button("Agregar al detalle", key=f"btn_add_transfer_{st.session_state.form_version}"):
                _agregar_item_carrito({
                    "Producto": str(prod_nom),
                    "Cantidad": int(prod_cant)
                })

        if st.session_state.carrito:
            df_detalle = pd.DataFrame(st.session_state.carrito)
            st.dataframe(df_detalle, use_container_width=True)

            total = int(df_detalle["Cantidad"].sum())
            st.markdown(f"### Total de cajas: {total}")

            c1, c2, c3 = st.columns(3)

            if c1.button("🗑️ Quitar último", key=f"btn_quitar_transfer_{st.session_state.form_version}"):
                _quitar_ultimo()

            if c2.button("🧹 Vaciar detalle", key=f"btn_vaciar_transfer_{st.session_state.form_version}"):
                _vaciar_carrito()

            if c3.button("💾 Guardar", key=f"btn_guardar_transfer_{st.session_state.form_version}"):
                try:
                    if not st.session_state.carrito:
                        st.warning("Agrega al menos un producto antes de guardar.")
                        st.stop()

                    fecha_sql = _to_iso_date(fecha)

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO encabezado_transaccion (
                            fecha, transaccion, no_envio, tipo_venta, metodo_pago,
                            bodega1, bodega2, id_cliente, proveedor, total
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        fecha_sql,
                        3,
                        correlativo or None,
                        None,
                        None,
                        bodega_entrada or None,
                        bodega_salida or None,
                        None,
                        None,
                        int(total)
                    ))

                    id_transaccion = cursor.lastrowid

                    for item in st.session_state.carrito:
                        cursor.execute("""
                            INSERT INTO detalle_transaccion (
                                id_transaccion, fecha, sku, cantidad, precio, subtotal
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            int(id_transaccion),
                            fecha_sql,
                            str(item["Producto"]),
                            int(item["Cantidad"]),
                            None,
                            None
                        ))

                    conn.commit()
                    cursor.close()
                    conn.close()

                    st.session_state.guardado_ok = True
                    st.session_state.guardado_id = int(id_transaccion)

                    st.session_state.carrito = []
                    st.session_state.expand_producto = True
                    st.session_state.form_version += 1

                    st.rerun()

                except Exception as e:
                    _db_error_box(e)
                    try:
                        conn.rollback()
                    except Exception:
                        pass

        else:
            st.info("No hay productos agregados aún.")

# ---------------------------------
# MENSAJE POST-GUARDADO (se muestra al final, después del "reload" del form)
# ---------------------------------
if st.session_state.guardado_ok:
    tid = st.session_state.guardado_id
    st.success(f"✅ Movimiento guardado exitosamente. ID transacción: {tid}")
    st.session_state.guardado_ok = False
    st.session_state.guardado_id = None
