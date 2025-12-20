import streamlit as st
import pandas as pd
from datetime import datetime
from db import run_query
from data import productos, bodegas


st.set_page_config(
    page_title="Movimientos de Inventario",
    layout="centered",
    page_icon="🍎"
)

if "carrito" not in st.session_state:
    st.session_state.carrito = []

# Obtener las bases de datos
clientes = run_query("SELECT * FROM clientes")
proveedores = run_query("SELECT * FROM proveedores")

st.title("Formulario de Registro de Movimientos")

#####################################################
# SECCIÓN 1: TIPO DE MOVIMIENTO
#####################################################
st.subheader("Tipo de Transacción")

opciones = {
    1: "Venta",
    2: "Compra",
    3: "Transferencia"
}

transaccion = st.selectbox(
    "Tipo de Transacción",
    options=list(opciones.keys()),
    format_func=lambda x: opciones[x]
)

st.divider()

#####################################################
# SECCIÓN 2: Encabezado
#####################################################
st.subheader("Datos de la transacción")

if transaccion == 1: # Venta

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    fecha = c1.date_input("Fecha de la venta", value=datetime.now())
    envio = c2.text_input("No. Envío")
    tipo = c3.selectbox("Tipo de Venta", ["", "Venta al contado", "Venta al crédito"])

    if tipo == "Venta al contado":
        pago = c4.selectbox("Forma de Pago", ["", "Efectivo", "Tarjeta", "Transferencia"])
    elif tipo == "Venta al crédito":
        pago = c4.selectbox("Forma de Pago", ["", "Pendiente de pago", "Vale"])
    else:
        pago = c4.selectbox("Forma de Pago", [""])

    bodega = st.selectbox("Punto de venta", ["", *bodegas])

    c5, c6 = st.columns(2)

    estado = c5.selectbox("Estado de la venta", ["", "Pagada", "Pendiente de pago", "Anulada"])
    factura = c6.checkbox("Necesita Factura")

    opciones_clientes = {None: ""} | {c["id_cliente"]: c["nombre"] for c in clientes}

    with st.expander("Crear nuevo Cliente"):
        nombre = st.text_input("Nombre del Cliente")
        nit = st.text_input("NIT/CUI")
        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")

        if st.button("Guardar Cliente"):
            run_query("INSERT INTO clientes (nombre, nit, telefono, email, direccion) VALUES (%s, %s, %s, %s, %s)", (nombre, nit, telefono, correo, direccion), fetch="none")
            st.success("Cliente guardado exitosamente")

    cliente = st.selectbox("Cliente", opciones_clientes, format_func=lambda x: opciones_clientes[x])

    st.write("Cliente seleccionado:", cliente)

    observaciones = st.text_area("Observaciones")

elif transaccion == 2: # Compra

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    fecha = c1.date_input("Fecha de la compra", value=datetime.now())
    envio = c2.text_input("No. Envío")
    bodega = c3.selectbox("Punto de venta", ["", *bodegas])
    estado = c4.selectbox("Estado de la compra", ["", "En tránsito", "En Bodega"])
    opciones_proveedores = {None: ""} | {p["id_proveedor"]: p["nombre"] for p in proveedores}

    observaciones = st.text_area("Observaciones")

    with st.expander("Crear nuevo Proveedor"):
        nombre = st.text_input("Nombre del Proveedor")
        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo")

        if st.button("Guardar Proveedor"):
            run_query("INSERT INTO proveedores (nombre, telefono, email) VALUES (%s, %s, %s)", (nombre, telefono, correo), fetch="none")
            st.success("Proveedor guardado exitosamente")

    proveedor = st.selectbox("Proveedor", opciones_proveedores, format_func=lambda x: opciones_proveedores[x])
    
    st.write("Proveedor seleccionado:", proveedor)

elif transaccion == 3: # Transferencia
    fecha = st.date_input("Fecha de la transferencia", value=datetime.now())
    envio = st.text_input("No. Envío")
    bodega_entrada = st.selectbox("Bodega de entrada", ["", *bodegas])
    bodega_salida = st.selectbox("Bodega de salida", ["", *bodegas])
    observaciones = st.text_area("Observaciones")

st.divider()

###############################
# SECCIÓN 3: DETALLE
###############################



st.subheader("Detalle de la transacción")

if transaccion == 1 or transaccion == 2: # Venta o Compra
    with st.expander("Agregar Producto"):
        c1, c2, c3 = st.columns(3)
        
        prod_sku = c1.selectbox("Producto", productos.keys(), format_func=lambda x: productos[x])
        prod_nom = productos[prod_sku]
        prod_cant = c2.number_input("Cantidad", min_value=1, value=1, step=1)
        prod_precio = c3.number_input("Precio", min_value=0, value=300, step=5)
        prod_subtotal = prod_cant * prod_precio

        st.write("Subtotal:", f"GTQ {prod_subtotal}")

        if st.button("Agregar Producto"):
            st.session_state.carrito.append({"sku": prod_sku, "nombre": prod_nom, "cantidad": prod_cant, "precio": prod_precio, "subtotal": prod_subtotal})
            st.rerun()

    if st.session_state.carrito:
        df = pd.DataFrame(st.session_state.carrito)

        df = df.rename(columns={
            "sku": "SKU",
            "nombre": "Producto",
            "cantidad": "Cantidad",
            "precio": "Precio",
            "subtotal": "Subtotal"
        })

        total = df["Subtotal"].sum()

        st.subheader("Carrito")
        st.dataframe(df, width="stretch")

        st.markdown(f"### 💰 Total: **Q {total:,.2f}**")
    else:
        st.info("No hay productos en el carrito")

elif transaccion == 3: # Transferencia
    with st.expander("Agregar Producto"):
        c1, c2 = st.columns(2)
        
        prod_sku = c1.selectbox("Producto", productos.keys(), format_func=lambda x: productos[x])
        prod_nom = productos[prod_sku]
        prod_cant = c2.number_input("Cantidad", min_value=1, value=1, step=1)

        if st.button("Agregar Producto"):
            st.session_state.carrito.append({"sku": prod_sku, "nombre": prod_nom, "cantidad": prod_cant})
            st.rerun()

    if st.session_state.carrito:
        df = pd.DataFrame(st.session_state.carrito)

        df = df.rename(columns={
            "sku": "SKU",
            "nombre": "Producto",
            "cantidad": "Cantidad"
        })

        total = df["Cantidad"].sum()

        st.subheader("Carrito")
        st.dataframe(df, width="stretch")

        st.markdown(f"### 💰 Total: **Q {total:,.2f}**")
    else:
        st.info("No hay productos en el carrito")

c1, c2, c3 = st.columns(3)

if c1.button("💾 Guardar"):
    if transaccion == 1 or transaccion == 2: # Venta o Compra
        
        if transaccion == 1:
            row = run_query("INSERT INTO encabezados (fecha, no_envio, transaccion, tipo_venta, metodo_pago, bodega_origen, id_cliente, total, observaciones, estado, factura) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_transaccion", (fecha, envio, int(transaccion), tipo, pago, bodega, int(cliente), float(total), observaciones, estado, bool(factura)), fetch="one")
        
        if transaccion == 2:
            row = run_query("INSERT INTO encabezados (fecha, no_envio, transaccion, bodega_destino, id_proveedor, total, observaciones, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_transaccion", (fecha, envio, int(transaccion), bodega, int(proveedor), float(total), observaciones, estado), fetch="one")

        id_transaccion = row["id_transaccion"]

        for item in st.session_state.carrito:
            run_query("INSERT INTO detalles (id_transaccion, fecha, sku, cantidad, precio, subtotal) VALUES (%s, %s, %s, %s, %s, %s)", (id_transaccion, fecha, str(item["sku"]), int(item["cantidad"]), float(item["precio"]), float(item["subtotal"])), fetch="none")

    if transaccion == 3: # Transferencia
        row = run_query("INSERT INTO encabezados (fecha, no_envio, transaccion, bodega_origen, bodega_destino, total, observaciones) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_transaccion", (fecha, envio, int(transaccion), bodega_entrada, bodega_salida, float(total), observaciones), fetch="one")
        id_transaccion = row["id_transaccion"]

        for item in st.session_state.carrito:
            run_query("INSERT INTO detalles (id_transaccion, fecha, sku, cantidad) VALUES (%s, %s, %s, %s)", (id_transaccion, fecha, str(item["sku"]), int(item["cantidad"])), fetch="none")    

    st.success("Transacción guardada exitosamente")

    st.session_state.carrito = []
    st.rerun()
    
if c2.button("🧹 Vaciar detalle"):
    st.session_state.carrito = []
    st.rerun()

if c3.button("🗑️ Quitar último producto"):
    st.session_state.carrito.pop()
    st.rerun()

st.write("Recargar página para reiniciar el formulario")