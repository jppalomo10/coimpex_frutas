import streamlit as st
from database import crear_tablas

import streamlit as st

USER = st.secrets["auth"]["username"]
PASS = st.secrets["auth"]["password"]

st.title("Login")

user = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if st.button("Ingresar"):
    if user == USER and password == PASS:
        st.success("Bienvenido")
        st.session_state["logged"] = True
    else:
        st.error("Credenciales incorrectas")

if st.session_state.get("logged"):
    st.write("Aquí va tu app 🔐")

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

