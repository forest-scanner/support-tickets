import os
import bcrypt
import jwt
import datetime
import pandas as pd
import altair as alt
import streamlit as st
from datetime import date

# Configuración de la página
st.set_page_config(page_title="Sistema de Tickets", page_icon="🎫", layout="wide")

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
    st.title("🔐 Acceso al Sistema de Tickets")
    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Iniciar sesión"):
            if verificar_login(usuario, contraseña):
                token = crear_token(usuario)
                st.session_state.token = token
                st.session_state.logged_in = True
                st.session_state.usuario = usuario
                st.success(f"✅ Bienvenido/a, {usuario}")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")

# Archivo CSV para guardar tickets
CSV_FILE = "ticket_tabla.csv"

# Función para crear token JWT
def crear_token(username):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

# Función para verificar token JWT
def verificar_token(token):
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        return data["sub"]
    except jwt.PyJWTError:
        return None

# Inicializar DataFrame
def init_dataframe():
    columns = [
        "ID", 
        "Título", 
        "Descripción", 
        "Estado", 
        "Prioridad", 
        "Fecha Creación", 
        "Fecha Límite",
        "Solicitante",
        "Departamento",
        "Asignado a",
        "Categoría",
        "Comentarios",
        "Tiempo Resolución (horas)"
    ]
    return pd.DataFrame(columns=columns)

# Guardar tickets en CSV
def save_to_csv(dataframe):
    dataframe.to_csv(CSV_FILE, index=False)

# Cargar datos o inicializar nuevo DataFrame
def load_or_init_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # Convertir fechas a datetime
            date_cols = ['Fecha Creación', 'Fecha Límite']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            return df
        except:
            return init_dataframe()
    return init_dataframe()

# Interfaz principal de la app
def app():
    st.title("🎫 Sistema de Gestión de Tickets")
    st.write("Plataforma completa para seguimiento de tickets de soporte")
    
    # Cargar o inicializar datos
    if 'df' not in st.session_state:
        st.session_state.df = load_or_init_data()
    
    # Menú lateral
    with st.sidebar:
        st.header("Opciones")
        menu = st.radio("Seleccione una opción:", 
                        ["Nuevo Ticket", "Ver Tickets", "Estadísticas", "Configuración"])
    
    # Sección de Nuevo Ticket
    if menu == "Nuevo Ticket":
        st.header("📝 Crear Nuevo Ticket")
        with st.form("nuevo_ticket_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                titulo = st.text_input("Título del Ticket*")
                descripcion = st.text_area("Descripción detallada*")
                solicitante = st.text_input("Solicitante*")
                departamento = st.selectbox("Departamento", 
                                          ["TI", "Ventas", "Operaciones", "RRHH", "Finanzas"])
            
            with col2:
                prioridad = st.selectbox("Prioridad*", ["Alta", "Media", "Baja"])
                categoria = st.selectbox("Categoría", 
                                        ["Hardware", "Software", "Redes", "Consulta", "Otro"])
                fecha_limite = st.date_input("Fecha Límite*", 
                                           min_value=date.today(),
                                           value=date.today() + datetime.timedelta(days=3))
                asignado_a = st.selectbox("Asignado a*", 
                                        ["Equipo TI", "Equipo Soporte", "Equipo Desarrollo", "Sin asignar"])
            
            submitted = st.form_submit_button("Guardar Ticket")
            
            if submitted:
                if not titulo or not descripcion or not solicitante:
                    st.error("Por favor complete los campos obligatorios (*)")
                else:
                    # Generar ID único
                    if st.session_state.df.empty:
                        nuevo_id = 1000
                    else:
                        try:
                            nuevo_id = int(st.session_state.df['ID'].str.split('-').str[1].astype(int).max() + 1)
                        except:
                            nuevo_id = 1000
                    
                    nuevo_ticket = pd.DataFrame([{
                        "ID": f"TKT-{nuevo_id}",
                        "Título": titulo,
                        "Descripción": descripcion,
                        "Estado": "Abierto",
                        "Prioridad": prioridad,
                        "Fecha Creación": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "Fecha Límite": fecha_limite.strftime("%Y-%m-%d"),
                        "Solicitante": solicitante,
                        "Departamento": departamento,
                        "Asignado a": asignado_a,
                        "Categoría": categoria,
                        "Comentarios": "",
                        "Tiempo Resolución (horas)": 0
                    }])
                    
                    st.session_state.df = pd.concat([nuevo_ticket, st.session_state.df], ignore_index=True)
                    save_to_csv(st.session_state.df)
                    st.success(f"✅ Ticket TKT-{nuevo_id} creado exitosamente!")
                    st.balloons()
    
    # Sección de Ver Tickets
    elif menu == "Ver Tickets":
        st.header("📋 Listado de Tickets")
        
        # Filtros
        with st.expander("🔍 Filtros Avanzados"):
            cols = st.columns(3)
            with cols[0]:
                filtro_estado = st.multiselect(
                    "Estado",
                    options=st.session_state.df['Estado'].unique() if 'Estado' in st.session_state.df else [],
                    default=["Abierto"] if 'Estado' in st.session_state.df else []
                )
            with cols[1]:
                filtro_prioridad = st.multiselect(
                    "Prioridad",
                    options=st.session_state.df['Prioridad'].unique() if 'Prioridad' in st.session_state.df else [],
                    default=st.session_state.df['Prioridad'].unique() if 'Prioridad' in st.session_state.df else []
                )
            with cols[2]:
                filtro_departamento = st.multiselect(
                    "Departamento",
                    options=st.session_state.df['Departamento'].unique() if 'Departamento' in st.session_state.df else [],
                    default=st.session_state.df['Departamento'].unique() if 'Departamento' in st.session_state.df else []
                )
        
        # Aplicar filtros
        filtered_df = st.session_state.df.copy()
        if filtro_estado:
            filtered_df = filtered_df[filtered_df['Estado'].isin(filtro_estado)]
        if filtro_prioridad:
            filtered_df = filtered_df[filtered_df['Prioridad'].isin(filtro_prioridad)]
        if filtro_departamento:
            filtered_df = filtered_df[filtered_df['Departamento'].isin(filtro_departamento)]
        
        # Mostrar tickets
        if not filtered_df.empty:
            st.write(f"Mostrando {len(filtered_df)} de {len(st.session_state.df)} tickets")
            
            # Editor de tickets
            edited_df = st.data_editor(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Estado": st.column_config.SelectboxColumn(
                        "Estado", 
                        options=["Abierto", "En Progreso", "Resuelto", "Cerrado"], 
                        required=True
                    ),
                    "Prioridad": st.column_config.SelectboxColumn(
                        "Prioridad", 
                        options=["Alta", "Media", "Baja"], 
                        required=True
                    ),
                    "Fecha Límite": st.column_config.DateColumn(
                        "Fecha Límite", 
                        format="YYYY-MM-DD", 
                        required=True
                    ),
                    "Asignado a": st.column_config.SelectboxColumn(
                        "Asignado a", 
                        options=["Equipo TI", "Equipo Soporte", "Equipo Desarrollo", "Sin asignar"], 
                        required=True
                    ),
                },
                disabled=["ID", "Fecha Creación", "Solicitante", "Departamento"],
                key="ticket_editor"
            )
            
            # Guardar cambios
            if not edited_df.equals(filtered_df):
                st.session_state.df.update(edited_df)
                save_to_csv(st.session_state.df)
                st.success("✅ Cambios guardados correctamente")
        else:
            st.warning("No se encontraron tickets con los filtros aplicados")
    
    # Sección de Estadísticas
    elif menu == "Estadísticas":
        st.header("📊 Estadísticas de Tickets")
        
        if not st.session_state.df.empty:
            # Métricas rápidas
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tickets", len(st.session_state.df))
            col2.metric("Tickets Abiertos", 
                        len(st.session_state.df[st.session_state.df['Estado'] == "Abierto"]))
            
            # Calcular tickets vencidos
            if 'Fecha Límite' in st.session_state.df.columns:
                hoy = pd.to_datetime(date.today())
                vencidos = st.session_state.df[
                    (st.session_state.df['Estado'] != "Cerrado") & 
                    (pd.to_datetime(st.session_state.df['Fecha Límite']) < hoy)
                ]
                col3.metric("Tickets Vencidos", len(vencidos))
            
            # Gráficos
            tab1, tab2, tab3 = st.tabs(["Por Estado", "Por Prioridad", "Por Departamento"])
            
            with tab1:
                st.altair_chart(
                    alt.Chart(st.session_state.df).mark_bar().encode(
                        x="count():Q",
                        y="Estado:N",
                        color="Estado:N"
                    ).properties(height=400),
                    use_container_width=True
                )
            
            with tab2:
                st.altair_chart(
                    alt.Chart(st.session_state.df).mark_arc().encode(
                        theta="count():Q",
                        color="Prioridad:N"
                    ).properties(height=400),
                    use_container_width=True
                )
            
            with tab3:
                st.altair_chart(
                    alt.Chart(st.session_state.df).mark_bar().encode(
                        x="count():Q",
                        y="Departamento:N",
                        color="Prioridad:N"
                    ).properties(height=400),
                    use_container_width=True
                )
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
