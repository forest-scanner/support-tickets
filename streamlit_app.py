import datetime
import os
import pandas as pd
import altair as alt
import streamlit as st
import streamlit_authenticator as stauth

# =============================================
#           CONFIGURACIÓN DE AUTENTICACIÓN
# =============================================

# Credenciales (usuario: admin / contraseña: Admin123)
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": "$2b$12$UnXKo29nl.4qx1d4i7WuUOdzqdlE/rX/FLF2P7VrTL/pdQmn6ShQ2"  # Hash de "Admin123"
        }
    }
}

# Configuración del autenticador (versión 0.2.3)
authenticator = stauth.Authenticate(
    credentials,
    cookie_name="tickets_app",
    key="clave_secreta_aleatoria_123456789",  # ¡Cambia esto en producción!
    cookie_expiry_days=1
)

# Login en sidebar (sintaxis correcta para v0.2.3)
name, authentication_status, username = authenticator.login("Login", "sidebar")

# =============================================
#           VERIFICACIÓN DE ACCESO
# =============================================

if authentication_status is False:
    st.sidebar.error("❌ Usuario/contraseña incorrectos")
    st.stop()  # Detiene la app si las credenciales son inválidas

if authentication_status is None:
    st.sidebar.warning("🔒 Ingrese sus credenciales")
    st.stop()  # Detiene la app si no se ingresaron credenciales

# =============================================
#           APLICACIÓN PRINCIPAL (TICKETS)
# =============================================

st.sidebar.success(f"👋 ¡Bienvenido {name}!")
authenticator.logout("Cerrar sesión", "sidebar")

# --- Configuración del CSV ---
CSV_FILE = "tickets.csv"

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=[
        "ID", "Título", "Descripción", "Estado", 
        "Prioridad", "Fecha", "Asignado a"
    ])
else:
    df = pd.read_csv(CSV_FILE)

# --- Función para guardar datos ---
def save_data():
    df.to_csv(CSV_FILE, index=False)

# --- Interfaz de tickets ---
st.title("🎫 Sistema de Tickets")
st.markdown("**Gestión de tickets con autenticación segura**")

with st.expander("➕ Crear nuevo ticket", expanded=True):
    with st.form("nuevo_ticket_form"):
        titulo = st.text_input("Título*")
        descripcion = st.text_area("Descripción*")
        prioridad = st.selectbox("Prioridad*", ["Alta", "Media", "Baja"])
        asignado = st.text_input("Asignado a (opcional)")
        
        if st.form_submit_button("📤 Enviar ticket"):
            if titulo and descripcion:
                nuevo_id = f"TKT-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
                nuevo_ticket = {
                    "ID": nuevo_id,
                    "Título": titulo,
                    "Descripción": descripcion,
                    "Estado": "Abierto",
                    "Prioridad": prioridad,
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Asignado a": asignado if asignado else "Sin asignar"
                }
                df.loc[len(df)] = nuevo_ticket  # Añade el nuevo ticket
                save_data()
                st.success(f"✅ Ticket {nuevo_id} creado!")
            else:
                st.warning("⚠️ Completa los campos obligatorios")

# --- Listado de tickets ---
st.header("📋 Tickets existentes")
st.caption(f"Total: {len(df)} tickets")

if not df.empty:
    # Filtros
    estados = df["Estado"].unique()
    filtro_estado = st.multiselect("Filtrar por estado", estados, default=["Abierto"])
    
    # Aplicar filtros
    df_filtrado = df[df["Estado"].isin(filtro_estado)] if filtro_estado else df
    
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
            "Fecha": st.column_config.DatetimeColumn("Fecha", disabled=True)
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

# --- Estadísticas ---
st.header("📊 Métricas")
if not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Abiertos", len(df[df["Estado"] == "Abierto"]))
    col2.metric("Alta prioridad", len(df[df["Prioridad"] == "Alta"]))
    col3.metric("Sin asignar", len(df[df["Asignado a"] == "Sin asignar"]))
    
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
    st.warning("No hay tickets registrados")






