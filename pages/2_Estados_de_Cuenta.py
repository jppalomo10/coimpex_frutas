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

c1, c2 = st.columns(2)

cliente = c1.selectbox("Cliente", opciones_clientes, format_func=lambda x: opciones_clientes[x])
estado = c2.multiselect("Estado", ["Pagada", "Pendiente de pago", "Pagada parcialmente", "Anulada"], default=["Pendiente de pago", "Pagada parcialmente"])

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
        e.estado,
        e.pagado
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
    st.warning("No hay datos")
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
    
    total_comprado = float(df["subtotal"].sum())
    total_pagado = float((
        df[["id_transaccion", "pagado"]]
        .drop_duplicates()
        ["pagado"]
        .sum()
    ))
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

    st.divider()

    tabs = st.tabs(["Ingresar un pago del cliente", "Actualizar Transacción"])

    with tabs[0]:
        st.subheader("Ingresar un pago del cliente")

        c1, c2 = st.columns(2)
        monto_pagado = c1.number_input("Monto pagado", min_value=0, value=0, step=10)

        facturas = (
            df[["fecha", "id_transaccion", "total", "pagado", "estado"]]
            .drop_duplicates()
            .sort_values("fecha")
        )

        st.dataframe(facturas, width="stretch", column_config={
                "fecha": "Fecha",
                "id_transaccion": "ID Factura",
                "total": "Total",
                "pagado": "Pagado",
                "estado": "Estado"
            })

        if c2.button("Ingresar Pago", width="stretch", icon="➕"):
            for _, row in facturas.iterrows():
                if monto_pagado <= 0:
                    break

                if row["estado"] == "Pagada" or row["estado"] == "Anulada":
                    continue

                pendiente = float(row["total"]) - float(row["pagado"])

                if monto_pagado >= pendiente:
                    # Se paga completa
                    run_query(
                        """
                        UPDATE encabezados
                        SET pagado = %s,
                            estado = 'Pagada'
                        WHERE id_transaccion = %s
                        """,
                        (row["total"], row["id_transaccion"]),
                        fetch="none"
                    )
                    monto_pagado -= pendiente

                else:
                    # Se paga parcialmente
                    run_query(
                        """
                        UPDATE encabezados
                        SET pagado = pagado + %s,
                            estado = 'Pagada parcialmente'
                        WHERE id_transaccion = %s
                        """,
                        (monto_pagado, row["id_transaccion"]),
                        fetch="none"
                    )
                    monto_pagado = 0

            st.rerun()
                    
    with tabs[1]:
        st.subheader("Actualizar Transacción")

        transacciones = df["id_transaccion"].unique()

        c1, c2 = st.columns(2)
        id_transaccion = c1.selectbox("ID de Transacción", ["", *transacciones])

        if id_transaccion != "":
            df_actualizar = df[df["id_transaccion"] == id_transaccion]
            df_actualizar = df_actualizar[["fecha", "producto", "cantidad", "precio", "subtotal", "estado"]]

            st.dataframe(df_actualizar, width="stretch", column_config={
                "fecha": "Fecha",
                "producto": "Producto",
                "cantidad": "Cantidad",
                "precio": "Precio Unitario",
                "subtotal": "Subtotal",
                "estado": "Estado"
            })

            nuevo_estado = c2.selectbox("Nuevo Estado", ["", "Pagada", "Pendiente de pago", "Pagada parcialmente", "Anulada"])
            observaciones = st.text_area("Observaciones")

            c3, c4, c5 = st.columns(3)

            c3.info(f"Estado actual: {df_actualizar['estado'].iloc[0]}")
            c4.success(f"Nuevo estado: {nuevo_estado}")

            if c5.button("Actualizar", width="stretch", icon="🔄"):
                run_query("UPDATE encabezados SET estado = %s, observaciones = %s WHERE id_transaccion = %s", (nuevo_estado, observaciones, int(id_transaccion)), fetch="none")
                st.success("Transacción actualizada exitosamente")
                st.rerun()

            



