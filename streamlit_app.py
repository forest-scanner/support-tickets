import os
import bcrypt
import jwt
import datetime
import pandas as pd
import altair as alt
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Support Tickets", page_icon="🎫")

# Configuración desde secrets.toml
SECRET = st.secrets.get("COOKIE_SECRET", "default_secret_key_32_chars_long_1234")
ADMIN_USERNAME = st.secrets.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD_HASH", "").encode()

# Simulación de base de datos de usuarios
users_db = {
    ADMIN_USERNAME: ADMIN_PASSWORD_HASH,
}

# Verificar usuario y contraseña
def verificar_login(usuario, contraseña):
    if usuario in users_db:
        hashed = users_db[usuario]
        return bcrypt.checkpw(contraseña.encode(), hashed)
    return False

# Interfaz de login
def login():
    st.title("🔐 Login")
    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if verificar_login(usuario, contraseña):
            token = crear_token(usuario)
            st.session_state.token = token
            st.session_state.logged_in = True
            st.session_state.usuario = usuario
            st.success(f"✅ Bienvenido/a, {usuario}")
            st.balloons()
        else:
            st.error("❌ Usuario o contraseña incorrectos")

# Archivo CSV para guardar tickets
CSV_FILE = "tickets.csv"

# Función para crear token JWT
def crear_token(username):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

# Función para verificar token JWT
def verificar_token(token):
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        return data["sub"]
    except jwt.PyJWTError:
        return None

# Guardar tickets en CSV
def save_to_csv(dataframe):
    dataframe.to_csv(CSV_FILE, index=False)

# Interfaz principal de la app
def app():
    st.title("🎫 Support Tickets")
    st.write("Gestión de tickets de soporte con almacenamiento en CSV.")

    # Columnas iniciales (incluyendo las nuevas)
    initial_columns = [
        "ID", "Issue", "Status", "Priority", "Date Submitted", 
        "Procedencia", "Fecha Límite", "Asignado a"
    ]

    # Cargar datos
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Asegurar que todas las columnas necesarias existan
        for col in initial_columns:
            if col not in df.columns:
                df[col] = None
        
        # Convertir fechas a datetime
        date_columns = ['Date Submitted', 'Fecha Límite']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
    else:
        df = pd.DataFrame(columns=initial_columns)

    st.session_state.df = df

    # Añadir ticket
    st.header("Añadir nuevo ticket")
    with st.form("add_ticket_form"):
        issue = st.text_area("Descripción del problema")
        priority = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
        procedencia = st.text_input("Procedencia (Persona que solicita)")
        fecha_limite = st.date_input("Fecha límite de realización", 
                                   min_value=datetime.date.today())
        asignado_a = st.selectbox("Asignado a", ["Equipo A", "Equipo B", "Equipo C", "Sin asignar"])
        submitted = st.form_submit_button("Enviar ticket")

    if submitted and issue.strip():
        if len(st.session_state.df) == 0:
            recent_ticket_number = 1000
        else:
            # Manejar caso cuando no hay tickets aún
            try:
                recent_ticket_number = int(max(st.session_state.df['ID'].dropna()).split("-")[1])
            except:
                recent_ticket_number = 1000

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        df_new = pd.DataFrame([{
            "ID": f"TICKET-{recent_ticket_number+1}",
            "Issue": issue,
            "Status": "Abierto",
            "Priority": priority,
            "Date Submitted": today,
            "Procedencia": procedencia,
            "Fecha Límite": fecha_limite.strftime("%Y-%m-%d"),
            "Asignado a": asignado_a
        }])

        st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0, ignore_index=True)
        save_to_csv(st.session_state.df)

        st.success("✅ Ticket enviado correctamente!")
        st.dataframe(df_new, use_container_width=True, hide_index=True)

    # Filtros - Solo mostrar si hay datos
    st.header("Filtrar Tickets")
    
    if not st.session_state.df.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_options = st.session_state.df['Status'].dropna().unique()
            filter_status = st.multiselect(
                "Estado",
                options=status_options,
                default=["Abierto"] if "Abierto" in status_options else []
            )
        
        with col2:
            if 'Procedencia' in st.session_state.df.columns:
                procedencia_options = st.session_state.df['Procedencia'].dropna().unique()
                filter_procedencia = st.multiselect(
                    "Procedencia",
                    options=procedencia_options,
                    default=procedencia_options
                )
            else:
                filter_procedencia = []
                st.warning("No hay datos de procedencia")
        
        with col3:
            if 'Fecha Límite' in st.session_state.df.columns:
                min_date = st.session_state.df['Fecha Límite'].min().date()
                max_date = st.session_state.df['Fecha Límite'].max().date()
                date_range = st.date_input(
                    "Rango de fechas límite",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                date_range = []
                st.warning("No hay datos de fechas límite")
        
        # Aplicar filtros
        filtered_df = st.session_state.df.copy()
        
        if filter_status:
            filtered_df = filtered_df[filtered_df['Status'].isin(filter_status)]
        
        if 'Procedencia' in filtered_df.columns and filter_procedencia:
            filtered_df = filtered_df[filtered_df['Procedencia'].isin(filter_procedencia)]
        
        if 'Fecha Límite' in filtered_df.columns and len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['Fecha Límite'] >= pd.to_datetime(start_date)) & 
                (filtered_df['Fecha Límite'] <= pd.to_datetime(end_date))
            ]
    else:
        filtered_df = pd.DataFrame(columns=initial_columns)
        st.warning("No hay tickets disponibles")

    # Editar tickets
    st.header("Tickets existentes")
    st.write(f"Número de tickets: `{len(filtered_df)}` (de `{len(st.session_state.df)}` totales)")

    if not filtered_df.empty:
        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Estado", options=["Abierto", "En progreso", "Cerrado"], required=True),
                "Priority": st.column_config.SelectboxColumn(
                    "Prioridad", options=["Alta", "Media", "Baja"], required=True),
                "Fecha Límite": st.column_config.DateColumn(
                    "Fecha Límite", format="YYYY-MM-DD", required=True),
                "Asignado a": st.column_config.SelectboxColumn(
                    "Asignado a", options=["Equipo A", "Equipo B", "Equipo C", "Sin asignar"], required=True),
            },
            disabled=["ID", "Date Submitted", "Procedencia"],
        )

        if not edited_df.equals(filtered_df):
            # Actualizar el dataframe original con los cambios
            updated_df = st.session_state.df.copy()
            for idx, row in edited_df.iterrows():
                mask = updated_df['ID'] == row['ID']
                updated_df.loc[mask, ['Status', 'Priority', 'Fecha Límite', 'Asignado a']] = row[['Status', 'Priority', 'Fecha Límite', 'Asignado a']]
            
            st.session_state.df = updated_df
            save_to_csv(updated_df)
            st.info("💾 Cambios guardados correctamente.")
    else:
        st.warning("No hay tickets para mostrar con los filtros actuales")

    # Estadísticas
    st.header("Estadísticas")
    
    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        
        # Tickets abiertos
        num_open = len(filtered_df[filtered_df['Status'] == "Abierto"]) if 'Status' in filtered_df.columns else 0
        col1.metric("Tickets abiertos", num_open)
        
        # Días hasta fecha límite
        if 'Fecha Límite' in filtered_df.columns:
            today = pd.to_datetime(datetime.date.today())
            filtered_df['Días Restantes'] = (pd.to_datetime(filtered_df['Fecha Límite']) - today).dt.days
            avg_days_remaining = filtered_df['Días Restantes'].mean()
            col2.metric("Días promedio hasta límite", f"{avg_days_remaining:.1f}")
        else:
            col2.metric("Días promedio hasta límite", "N/A")
        
        # Tickets vencidos
        if 'Fecha Límite' in filtered_df.columns and 'Status' in filtered_df.columns:
            overdue = filtered_df[(filtered_df['Status'] != 'Cerrado') & 
                                 (filtered_df['Fecha Límite'] < pd.to_datetime(datetime.date.today()))]
            col3.metric("Tickets vencidos", len(overdue))
        else:
            col3.metric("Tickets vencidos", "N/A")

        # Gráficos
        if len(filtered_df) > 0:
            st.write("##### Tickets por estado (mensual)")
            if 'Date Submitted' in filtered_df.columns:
                status_plot = (
                    alt.Chart(filtered_df)
                    .mark_bar()
                    .encode(
                        x="month(Date Submitted):O",
                        y="count():Q",
                        xOffset="Status:N",
                        color="Status:N",
                    )
                )
                st.altair_chart(status_plot, use_container_width=True)

            st.write("##### Distribución de prioridades")
            priority_plot = (
                alt.Chart(filtered_df)
                .mark_arc()
                .encode(theta="count():Q", color="Priority:N")
                .properties(height=300)
            )
            st.altair_chart(priority_plot, use_container_width=True)

            if 'Procedencia' in filtered_df.columns:
                st.write("##### Tickets por procedencia")
                procedencia_plot = (
                    alt.Chart(filtered_df)
                    .mark_bar()
                    .encode(
                        x="count():Q",
                        y="Procedencia:N",
                        color="Status:N"
                    )
                )
                st.altair_chart(procedencia_plot, use_container_width=True)
    else:
        st.warning("No hay datos para mostrar estadísticas")

# Verificar token si existe
if "token" in st.session_state:
    usuario = verificar_token(st.session_state.token)
    if usuario:
        st.session_state.logged_in = True
        st.session_state.usuario = usuario
    else:
        st.session_state.logged_in = False

# Mostrar login o app
if st.session_state.get("logged_in", False):
    app()
else:
    login()
