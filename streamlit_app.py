import os
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime

# ========================================
# 1. CONFIGURACIÓN DE AUTENTICACIÓN (CON SECRETS)
# ========================================

# Carga automática desde secrets.toml en Streamlit Cloud
credentials = {
    "usernames": {
        os.environ["ADMIN_USERNAME"]: {  # "user" (definido en secrets.toml)
            "name": "Usuario GIS",
            "password": os.environ["ADMIN_PASSWORD_HASH"]  # Hash de "gispro1977"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="gispro_auth",
    key=os.environ["COOKIE_SECRET"],  # Clave desde secrets.toml
    cookie_expiry_days=30
)

# Login en sidebar
name, auth_status, _ = authenticator.login("Acceso GIS Pro", "sidebar")

# Bloquear app si no está autenticado
if auth_status is False:
    st.sidebar.error("❌ Credenciales incorrectas")
    st.stop()
elif auth_status is None:
    st.sidebar.warning("🔑 Ingrese usuario y contraseña")
    st.stop()

# ========================================
# 2. APLICACIÓN PRINCIPAL (TICKETS)
# ========================================

st.sidebar.success(f"👋 ¡Bienvenido {name}!")
authenticator.logout("Cerrar sesión", "sidebar")

# --- Configuración CSV ---
CSV_FILE = "tickets_gispro.csv"
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=[
        "ID", "Título", "Descripción", "Estado", 
        "Prioridad", "Fecha", "Asignado a"
    ])
else:
    df = pd.read_csv(CSV_FILE)

# --- Funciones clave ---
def save_data():
    df.to_csv(CSV_FILE, index=False)

# --- Interfaz de usuario ---
st.title("🗺️ GIS Pro - Sistema de Tickets")
st.markdown(f"**Usuario:** `{name}` | **Ultima actualización:** `{datetime.now().strftime('%Y-%m-%d %H:%M')}`")

with st.expander("➕ Nuevo Ticket", expanded=True):
    with st.form("form_ticket"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título*")
            prioridad = st.selectbox("Prioridad*", ["Alta", "Media", "Baja"])
        with col2:
            asignado = st.text_input("Asignado a", "Equipo GIS")
            estado = st.selectbox("Estado", ["Abierto", "En progreso"])
        
        descripcion = st.text_area("Descripción técnica*")
        
        if st.form_submit_button("📤 Guardar Ticket"):
            if titulo and descripcion:
                nuevo_id = f"GIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                nuevo_ticket = {
                    "ID": nuevo_id,
                    "Título": titulo,
                    "Descripción": descripcion,
                    "Estado": estado,
                    "Prioridad": prioridad,
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Asignado a": asignado
                }
                df.loc[len(df)] = nuevo_ticket
                save_data()
                st.success(f"Ticket {nuevo_id} creado!")
            else:
                st.warning("⚠️ Complete los campos obligatorios")

# --- Listado de tickets ---
st.header("📋 Tickets Activos")
st.data_editor(
    df,
    key="ticket_editor",
    hide_index=True,
    use_container_width=True,
    column_config={
        "ID": st.column_config.TextColumn(width="small"),
        "Fecha": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
        "Estado": st.column_config.SelectboxColumn(options=["Abierto", "En progreso", "Resuelto"]),
        "Prioridad": st.column_config.SelectboxColumn(options=["Alta", "Media", "Baja"])
    },
    disabled=["ID", "Fecha"]
)

# Guardar cambios
if st.session_state.get("ticket_editor"):
    df = st.session_state.ticket_editor["edited_rows"]
    save_data()

# --- Estadísticas ---
st.header("📊 Métricas GIS")
if not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Tickets Abiertos", len(df[df["Estado"] == "Abierto"]))
    col2.metric("Alta Prioridad", len(df[df["Prioridad"] == "Alta"]))
    col3.metric("Asignados a TI", len(df[df["Asignado a"] == "Equipo GIS"]))






