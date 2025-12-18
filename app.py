import streamlit as st
from database import crear_tablas

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


