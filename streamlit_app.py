import os
import bcrypt
import jwt
import datetime
import pandas as pd
import altair as alt
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Support Tickets", page_icon="🎫")

# Clave secreta para JWT (en producción, usar variable de entorno)
SECRET = "tu_clave_secreta_muy_larga"

# Simulación de base de datos de usuarios
users_db = {
    "estefania": bcrypt.hashpw("miClaveSegura".encode(), bcrypt.gensalt()),
    "admin": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
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
            st.success(f"✅ Bienvenida, {usuario}")
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

    # Cargar datos
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Convertir fechas a datetime si ya existen
        if 'Date Submitted' in df.columns:
            df['Date Submitted'] = pd.to_datetime(df['Date Submitted'])
        if 'Fecha Límite' in df.columns:
            df['Fecha Límite'] = pd.to_datetime(df['Fecha Límite'])
    else:
        df = pd.DataFrame(columns=[
            "ID", "Issue", "Status", "Priority", "Date Submitted", 
            "Procedencia", "Fecha Límite"
        ])

    st.session_state.df = df.copy()

    # Añadir ticket
    st.header("Add a ticket")
    with st.form("add_ticket_form"):
        issue = st.text_area("Describe the issue")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        procedencia = st.text_input("Procedencia (Persona que solicita)")
        fecha_limite = st.date_input("Fecha límite de realización", 
                                   min_value=datetime.date.today())
        submitted = st.form_submit_button("Submit")

    if submitted and issue.strip():
        if len(st.session_state.df) == 0:
            recent_ticket_number = 1000
        else:
            recent_ticket_number = int(max(st.session_state.df.ID).split("-")[1])

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        df_new = pd.DataFrame([{
            "ID": f"TICKET-{recent_ticket_number+1}",
            "Issue": issue,
            "Status": "Open",
            "Priority": priority,
            "Date Submitted": today,
            "Procedencia": procedencia,
            "Fecha Límite": fecha_limite.strftime("%Y-%m-%d"),
        }])

        st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0)
        save_to_csv(st.session_state.df)

        st.success("✅ Ticket submitted!")
        st.dataframe(df_new, use_container_width=True, hide_index=True)

    # Filtros
    st.header("Filtrar Tickets")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.multiselect(
            "Filtrar por Estado",
            options=st.session_state.df['Status'].unique(),
            default=st.session_state.df['Status'].unique()
        )
    
    with col2:
        filter_procedencia = st.multiselect(
            "Filtrar por Procedencia",
            options=st.session_state.df['Procedencia'].unique(),
            default=st.session_state.df['Procedencia'].unique()
        )
    
    with col3:
        min_date = st.session_state.df['Fecha Límite'].min() if 'Fecha Límite' in st.session_state.df else datetime.date.today()
        max_date = st.session_state.df['Fecha Límite'].max() if 'Fecha Límite' in st.session_state.df else datetime.date.today() + datetime.timedelta(days=30)
        date_range = st.date_input(
            "Filtrar por Rango de Fechas Límite",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
    # Aplicar filtros
    filtered_df = st.session_state.df.copy()
    
    if filter_status:
        filtered_df = filtered_df[filtered_df['Status'].isin(filter_status)]
    
    if filter_procedencia:
        filtered_df = filtered_df[filtered_df['Procedencia'].isin(filter_procedencia)]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['Fecha Límite'] >= pd.to_datetime(start_date)) & 
            (filtered_df['Fecha Límite'] <= pd.to_datetime(end_date))
        ]

    # Editar tickets
    st.header("Existing tickets")
    st.write(f"Number of tickets: `{len(filtered_df)}` (de `{len(st.session_state.df)}` totales)")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status", options=["Open", "In Progress", "Closed"], required=True),
            "Priority": st.column_config.SelectboxColumn(
                "Priority", options=["High", "Medium", "Low"], required=True),
            "Fecha Límite": st.column_config.DateColumn(
                "Fecha Límite", format="YYYY-MM-DD", required=True),
        },
        disabled=["ID", "Date Submitted", "Procedencia"],
    )

    if not edited_df.equals(filtered_df):
        # Actualizar el dataframe original con los cambios
        updated_df = st.session_state.df.copy()
        for idx, row in edited_df.iterrows():
            updated_df.loc[updated_df['ID'] == row['ID'], ['Status', 'Priority', 'Fecha Límite']] = row[['Status', 'Priority', 'Fecha Límite']]
        
        st.session_state.df = updated_df
        save_to_csv(updated_df)
        st.info("💾 Changes saved to CSV.")

    # Estadísticas
    st.header("Statistics")
    col1, col2, col3 = st.columns(3)
    num_open = len(filtered_df[filtered_df.Status == "Open"])
    col1.metric("Open tickets", num_open)
    
    # Calcular días hasta fecha límite para tickets abiertos
    if not filtered_df.empty:
        today = pd.to_datetime(datetime.date.today())
        filtered_df['Días Restantes'] = (pd.to_datetime(filtered_df['Fecha Límite']) - today).dt.days
        avg_days_remaining = filtered_df['Días Restantes'].mean()
        col2.metric("Avg days to deadline", f"{avg_days_remaining:.1f}")
    else:
        col2.metric("Avg days to deadline", "N/A")
    
    col3.metric("Avg resolution time (hrs)", 16)

    if len(filtered_df) > 0:
        st.write("##### Ticket status per month")
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

        st.write("##### Current ticket priorities")
        priority_plot = (
            alt.Chart(filtered_df)
            .mark_arc()
            .encode(theta="count():Q", color="Priority:N")
            .properties(height=300)
        )
        st.altair_chart(priority_plot, use_container_width=True)

        st.write("##### Tickets by Procedencia")
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
