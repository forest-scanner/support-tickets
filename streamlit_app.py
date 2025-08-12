import datetime
import os
import pandas as pd
import altair as alt
import streamlit as st
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN DE AUTENTICACIÓN (Versión 0.2.3) ---
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": "$2b$12$UnXKo29nl.4qx1d4i7WuUOdzqdlE/rX/FLF2P7VrTL/pdQmn6ShQ2"  # Hash de "Admin123"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="ticket_app_cookie",
    key="tu_clave_secreta_aleatoria_123456",  # ¡Cambia esto en producción!
    cookie_expiry_days=1
)

# --- LOGIN (Sintaxis correcta para v0.2.3) ---
name, authentication_status, username = authenticator.login("Login", "sidebar")

# --- VERIFICACIÓN ---
if authentication_status is False:
    st.sidebar.error("❌ Usuario/contraseña incorrectos")
    st.stop()

if authentication_status is None:
    st.sidebar.warning("🔒 Por favor ingresa tus credenciales")
    st.stop()

# --- APP PRINCIPAL (solo visible si autenticado) ---
st.sidebar.success(f"👋 ¡Bienvenido {name}!")
authenticator.logout("Cerrar sesión", "sidebar")

# =============================================
#           SISTEMA DE TICKETS
# =============================================
st.title("🎫 Sistema de Tickets de Soporte")
st.markdown("**Persistencia en CSV | Autenticación segura**")

# --- CONFIGURACIÓN CSV ---
CSV_FILE = "tickets.csv"

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=[
        "ID", "Título", "Descripción", "Estado", 
        "Prioridad", "Fecha Creación", "Asignado a"
    ])
else:
    df = pd.read_csv(CSV_FILE)

# --- FUNCIÓN PARA GUARDAR ---
def save_data():
    df.to_csv(CSV_FILE, index=False)

# --- FORMULARIO NUEVO TICKET ---
with st.expander("➕ Crear nuevo ticket", expanded=True):
    with st.form("nuevo_ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título*")
        with col2:
            prioridad = st.selectbox("Prioridad*", ["Alta", "Media", "Baja"])
        
        descripcion = st.text_area("Descripción detallada*")
        asignado = st.text_input("Asignado a (opcional)")
        
        submitted = st.form_submit_button("📤 Enviar ticket")
        
        if submitted and titulo and descripcion:
            nuevo_id = f"TKT-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            nuevo_ticket = {
                "ID": nuevo_id,
                "Título": titulo,
                "Descripción": descripcion,
                "Estado": "Abierto",
                "Prioridad": prioridad,
                "Fecha Creación": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Asignado a": asignado if asignado else "Sin asignar"
            }
            
            df = pd.concat([df, pd.DataFrame([nuevo_ticket])], ignore_index=True)
            save_data()
            st.success(f"✅ Ticket {nuevo_id} creado correctamente")

# --- VISUALIZACIÓN DE TICKETS ---
st.header("📋 Listado de Tickets")
st.caption(f"Mostrando {len(df)} tickets registrados")

if not df.empty:
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_estado = st.multiselect(
            "Filtrar por estado",
            options=df["Estado"].unique(),
            default=["Abierto"]
        )
    with col2:
        filtro_prioridad = st.multiselect(
            "Filtrar por prioridad",
            options=df["Prioridad"].unique()
        )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if filtro_estado:
        df_filtrado = df_filtrado[df_filtrado["Estado"].isin(filtro_estado)]
    if filtro_prioridad:
        df_filtrado = df_filtrado[df_filtrado["Prioridad"].isin(filtro_prioridad)]
    
    # Editor de datos
    edited_df = st.data_editor(
        df_filtrado,
        column_config={
            "ID": st.column_config.TextColumn("ID", disabled=True),
            "Estado": st.column_config.SelectboxColumn(
                "Estado",
                options=["Abierto", "En progreso", "Resuelto", "Cerrado"],
                required=True
            ),
            "Prioridad": st.column_config.SelectboxColumn(
                "Prioridad",
                options=["Alta", "Media", "Baja"],
                required=True
            ),
            "Fecha Creación": st.column_config.DatetimeColumn(
                "Fecha",
                disabled=True
            )
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # Guardar cambios
    if not edited_df.equals(df_filtrado):
        df.update(edited_df)
        save_data()
        st.rerun()

# --- ESTADÍSTICAS ---
st.header("📊 Métricas")
if not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Tickets abiertos", len(df[df["Estado"] == "Abierto"]))
    col2.metric("Alta prioridad", len(df[df["Prioridad"] == "Alta"]))
    col3.metric("Sin asignar", len(df[df["Asignado a"] == "Sin asignar"]))
    
    # Gráficos
    tab1, tab2 = st.tabs(["📈 Por estado", "📅 Por fecha"])
    
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
            alt.Chart(df).mark_line(point=True).encode(
                x="Fecha Creación:T",
                y="count():Q",
                color="Prioridad:N"
            ),
            use_container_width=True
        )
else:
    st.warning("No hay tickets registrados aún")

# --- REQUIREMENTS.TXT para Streamlit Cloud ---
"""
streamlit==1.32.0
streamlit-authenticator==0.2.3
pandas==2.1.4
altair==5.2.0
numpy==1.26.0
"""




