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
            "password": "$2b$12$UnXKo29nl.4qx1d4i7WuUOdzqdlE/rX/FLF2P7VrTL/pdQmn6ShQ2"  # Contraseña: Admin123
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "ticket_app_cookie",
    "abcdef123456",  # Cambia por una clave secreta más larga en producción
    30  # Días de expiración de la cookie
)

# --- LOGIN EN LA BARRA LATERAL ---
name, authentication_status, username = authenticator.login("Login", "sidebar")

# --- VERIFICACIÓN DE AUTENTICACIÓN ---
if authentication_status is False:
    st.sidebar.error("Usuario/contraseña incorrectos")
    st.stop()

if authentication_status is None:
    st.sidebar.warning("Ingresa tus credenciales")
    st.stop()

# --- APP PRINCIPAL (solo accesible si está autenticado) ---
st.sidebar.success(f"Bienvenido {name} 👋")
authenticator.logout("Cerrar sesión", "sidebar")

# =============================================
#           SISTEMA DE TICKETS
# =============================================
st.title("🎫 Support tickets")
st.write("Sistema de tickets con persistencia en CSV")

# --- CONFIGURACIÓN DEL ARCHIVO CSV ---
CSV_FILE = "tickets.csv"

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["ID", "Issue", "Status", "Priority", "Date Submitted", "Assigned To"])
else:
    df = pd.read_csv(CSV_FILE)

# --- FUNCIÓN PARA GUARDAR ---
def save_to_csv(dataframe):
    dataframe.to_csv(CSV_FILE, index=False)

# --- FORMULARIO PARA NUEVOS TICKETS ---
st.header("🆕 Añadir ticket")
with st.form("nuevo_ticket"):
    issue = st.text_area("Descripción del problema*", height=150)
    priority = st.selectbox("Prioridad*", ["Alta", "Media", "Baja"])
    assigned_to = st.text_input("Asignado a (opcional)")
    
    submitted = st.form_submit_button("Crear ticket")
    
    if submitted and issue.strip():
        # Generar ID único
        last_id = df["ID"].max() if not df.empty else "TICKET-999"
        new_id = f"TICKET-{int(last_id.split('-')[1]) + 1}" if df.empty else f"TICKET-{int(last_id.split('-')[1]) + 1}"
        
        new_ticket = {
            "ID": new_id,
            "Issue": issue,
            "Status": "Abierto",
            "Priority": priority,
            "Date Submitted": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Assigned To": assigned_to if assigned_to else "Sin asignar"
        }
        
        df = pd.concat([df, pd.DataFrame([new_ticket])], ignore_index=True)
        save_to_csv(df)
        st.success(f"Ticket {new_id} creado correctamente!")

# --- VISUALIZACIÓN/EDICIÓN DE TICKETS ---
st.header("📋 Tickets existentes")
st.write(f"Total de tickets: {len(df)}")

if not df.empty:
    # Editor interactivo
    edited_df = st.data_editor(
        df,
        column_config={
            "ID": st.column_config.TextColumn("ID", disabled=True),
            "Status": st.column_config.SelectboxColumn(
                "Estado",
                options=["Abierto", "En progreso", "Resuelto", "Cerrado"],
                required=True
            ),
            "Priority": st.column_config.SelectboxColumn(
                "Prioridad",
                options=["Alta", "Media", "Baja"],
                required=True
            ),
            "Date Submitted": st.column_config.DateColumn("Fecha", disabled=True)
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Guardar cambios
    if not edited_df.equals(df):
        df = edited_df
        save_to_csv(df)
        st.rerun()

# --- ESTADÍSTICAS ---
st.header("📊 Estadísticas")

if not df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tickets abiertos", len(df[df["Status"] == "Abierto"]))
    with col2:
        st.metric("Tickets de alta prioridad", len(df[df["Priority"] == "Alta"]))
    with col3:
        st.metric("Tickets sin asignar", len(df[df["Assigned To"] == "Sin asignar"]))

    # Gráficos
    st.subheader("Distribución por estado")
    status_chart = alt.Chart(df).mark_bar().encode(
        x="Status:N",
        y="count():Q",
        color="Status:N"
    )
    st.altair_chart(status_chart, use_container_width=True)

else:
    st.warning("No hay tickets registrados aún")




