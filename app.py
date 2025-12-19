import streamlit as st
from db import run_query

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
