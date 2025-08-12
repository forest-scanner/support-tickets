import os
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime

# ========================================
# 1. CONFIGURACIÓN DE AUTENTICACIÓN (SECRETS)
# ========================================

# Configuración desde secrets.toml (Streamlit Cloud)
credentials = {
    "usernames": {
        os.environ["ADMIN_USERNAME"]: {  # Usuario: "user"
            "name": "Usuario GIS",
            "password": os.environ["ADMIN_PASSWORD_HASH"]  # Hash de "gispro1977"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="gispro_auth_cookie",
    key=os.environ["COOKIE_SECRET"],  # Clave de 32 caracteres
    cookie_expiry_days=7
)

# Login en sidebar
name, auth_status, _ = authenticator.login("Acceso Sistema GIS", "sidebar")

# Validación de acceso
if auth_status is False:
    st.sidebar.error("❌ Usuario/contraseña incorrectos")
    st.stop()
elif auth_status is None:
    st.sidebar.warning("🔑 Ingrese sus credenciales")
    st.stop()

# ========================================
# 2. APLICACIÓN PRINCIPAL (TICKETS)
# ========================================

st.sidebar.success(f"👋 ¡Bienvenido {name}!")
authenticator.logout("Cerrar sesión", "sidebar")

# --- Configuración del CSV ---
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
st.title("🗺️ Sistema de Tickets GIS Pro")
st.divider()

# Formulario nuevo ticket
with st.expander("➕ Crear Nuevo Ticket", expanded=True):
    with st.form(key="nuevo_ticket_form"):
        titulo = st.text_input("Título*", placeholder="Problema con capas WMS...")
        descripcion = st.text_area("Descripción técnica*", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            prioridad = st.selectbox("Prioridad*", ["Alta", "Media", "Baja"])
        with col2:
            asignado = st.text_input("Asignado a", "Equipo GIS")
        
        if st.form_submit_button("📤 Guardar Ticket"):
            if titulo and descripcion:
                nuevo_id = f"GIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                nuevo_ticket = {
                    "ID": nuevo_id,
                    "Título": titulo,
                    "Descripción": descripcion,
                    "Estado": "Abierto",
                    "Prioridad": prioridad,
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Asignado a": asignado
                }
                df = pd.concat([df, pd.DataFrame([nuevo_ticket])], ignore_index=True)
                save_data()
                st.success(f"✅ Ticket {nuevo_id} creado!")
                st.rerun()
            else:
                st.warning("⚠️ Complete los campos obligatorios")

# Listado de tickets
st.header("📋 Tickets Registrados")
st.caption(f"Total: {len(df)} tickets")

if not df.empty:
    # Filtros
    estados = df["Estado"].unique()
    prioridades = df["Prioridad"].unique()
    
    cols = st.columns(2)
    with cols[0]:
        filtro_estado = st.multiselect("Filtrar por estado", estados, default=["Abierto"])
    with cols[1]:
        filtro_prioridad = st.multiselect("Filtrar por prioridad", prioridades)

    # Aplicar filtros
    df_filtrado = df.copy()
    if filtro_estado:
        df_filtrado = df_filtrado[df_filtrado["Estado"].isin(filtro_estado)]
    if filtro_prioridad:
        df_filtrado = df_filtrado[df_filtrado["Prioridad"].isin(filtro_prioridad)]

    # Editor de datos
    edited_df = st.data_editor(
        df_filtrado,
        key="ticket_editor",
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.TextColumn(disabled=True),
            "Fecha": st.column_config.DatetimeColumn(
                "Fecha Creación",
                format="DD/MM/YYYY HH:mm",
                disabled=True
            ),
            "Estado": st.column_config.SelectboxColumn(
                options=["Abierto", "En progreso", "Resuelto", "Cerrado"]
            ),
            "Prioridad": st.column_config.SelectboxColumn(
                options=["Alta", "Media", "Baja"]
            )
        }
    )

    # Guardar cambios
    if not edited_df.equals(df_filtrado):
        df.update(edited_df)
        save_data()
        st.rerun()

# Métricas
st.header("📊 Dashboard")
if not df.empty:
    cols = st.columns(3)
    cols[0].metric("Tickets Abiertos", len(df[df["Estado"] == "Abierto"]))
    cols[1].metric("Alta Prioridad", len(df[df["Prioridad"] == "Alta"]))
    cols[2].metric("Asignados a TI", len(df[df["Asignado a"].str.contains("GIS"))])

    # Gráficos
    tab1, tab2 = st.tabs(["Estados", "Prioridades"])
    with tab1:
        st.altair_chart(
            alt.Chart(df).mark_bar().encode(
                x="Estado:N",
                y="count():Q",
                color="Estado:N"
            ),
            use_container_width=True
        )
    with tab2:
        st.altair_chart(
            alt.Chart(df).mark_arc().encode(
                theta="count():Q",
                color="Prioridad:N"
            ),
            use_container_width=True
        )
else:
    st.info("No hay tickets registrados aún")






