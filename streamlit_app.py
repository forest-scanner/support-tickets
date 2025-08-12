import os
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import altair as alt
from datetime import datetime

# ========================================
# 1. CONFIGURACIÓN DE AUTENTICACIÓN
# ========================================

# Configuración desde secrets.toml
credentials = {
    "usernames": {
        os.environ["ADMIN_USERNAME"]: {
            "name": "Usuario GIS",
            "password": os.environ["ADMIN_PASSWORD_HASH"]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="gispro_auth",
    key=os.environ["COOKIE_SECRET"],
    cookie_expiry_days=7
)

# Login
name, auth_status, _ = authenticator.login("Acceso GIS Pro", "sidebar")

if auth_status is False:
    st.sidebar.error("❌ Credenciales incorrectas")
    st.stop()
elif auth_status is None:
    st.sidebar.warning("🔑 Ingrese credenciales")
    st.stop()

# ========================================
# 2. APLICACIÓN PRINCIPAL
# ========================================

st.sidebar.success(f"👋 ¡Bienvenido {name}!")
authenticator.logout("Cerrar sesión", "sidebar")

# --- Configuración CSV ---
CSV_FILE = "tickets_gispro.csv"
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["ID", "Título", "Descripción", "Estado", "Prioridad", "Fecha", "Asignado a"])
else:
    df = pd.read_csv(CSV_FILE)

def save_data():
    df.to_csv(CSV_FILE, index=False)

# --- Interfaz ---
st.title("🗺️ Sistema de Tickets GIS Pro")

# Formulario nuevo ticket
with st.expander("➕ Nuevo Ticket", expanded=True):
    with st.form("nuevo_ticket_form"):
        titulo = st.text_input("Título*")
        descripcion = st.text_area("Descripción*", height=150)
        col1, col2 = st.columns(2)
        with col1:
            prioridad = st.selectbox("Prioridad*", ["Alta", "Media", "Baja"])
        with col2:
            asignado = st.text_input("Asignado a", "Equipo GIS")
        
        if st.form_submit_button("📤 Guardar"):
            if titulo and descripcion:
                nuevo_id = f"GIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                df.loc[len(df)] = {
                    "ID": nuevo_id,
                    "Título": titulo,
                    "Descripción": descripcion,
                    "Estado": "Abierto",
                    "Prioridad": prioridad,
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Asignado a": asignado
                }
                save_data()
                st.success(f"✅ Ticket {nuevo_id} creado!")
                st.rerun()

# Listado de tickets
st.header("📋 Tickets Registrados")
if not df.empty:
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_estado = st.multiselect("Estado", df["Estado"].unique(), default=["Abierto"])
    with col2:
        filtro_prioridad = st.multiselect("Prioridad", df["Prioridad"].unique())
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if filtro_estado:
        df_filtrado = df_filtrado[df_filtrado["Estado"].isin(filtro_estado)]
    if filtro_prioridad:
        df_filtrado = df_filtrado[df_filtrado["Prioridad"].isin(filtro_prioridad)]

    # Editor
    edited_df = st.data_editor(
        df_filtrado,
        column_config={
            "ID": st.column_config.TextColumn(disabled=True),
            "Fecha": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm", disabled=True),
            "Estado": st.column_config.SelectboxColumn(options=["Abierto", "En progreso", "Resuelto"]),
            "Prioridad": st.column_config.SelectboxColumn(options=["Alta", "Media", "Baja"])
        },
        hide_index=True,
        use_container_width=True
    )

    # Guardar cambios
    if not edited_df.equals(df_filtrado):
        df.update(edited_df)
        save_data()
        st.rerun()

# Métricas CORREGIDAS
st.header("📊 Dashboard")
if not df.empty:
    cols = st.columns(3)
    cols[0].metric("Abiertos", len(df[df["Estado"] == "Abierto"]))
    cols[1].metric("Alta Prioridad", len(df[df["Prioridad"] == "Alta"]))
    cols[2].metric("Asignados", len(df[df["Asignado a"] == "Equipo GIS"]))  # Versión simplificada y corregida

    # Gráficos
    st.altair_chart(
        alt.Chart(df).mark_bar().encode(
            x="Estado:N",
            y="count():Q",
            color="Estado:N"
        ),
        use_container_width=True
    )
else:
    st.info("No hay tickets registrados")

# ========================================
# CONFIGURACIÓN REQUERIDA
# ========================================

"""
# 📁 secrets.toml
ADMIN_USERNAME = "user"
ADMIN_PASSWORD_HASH = "$2b$12$..."  # Hash de tu contraseña
COOKIE_SECRET = "clave-secreta-32-caracteres"

# 📝 requirements.txt
streamlit==1.32.0
streamlit-authenticator==0.2.3
pandas==2.1.4
altair==5.2.0
"""





