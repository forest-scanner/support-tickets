import os
import json
import bcrypt
import jwt
import datetime
import pandas as pd
import altair as alt
import streamlit as st
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ================= Configuración página =================
st.set_page_config(page_title="Sistema de Tickets", page_icon="🎫", layout="wide")

# ================= Configuración Google Sheets =================
gs_secrets = st.secrets["google_sheets"]
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_JSON = json.loads(gs_secrets["credentials_json"])
SHEET_ID = gs_secrets["sheet_id"]

def get_gsheet():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_JSON, SCOPE)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        st.warning(f"No se pudo conectar a Google Sheets: {e}")
        return None

def load_data():
    sheet = get_gsheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                for col in ["Fecha Creación", "Fecha Límite"]:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                return df
        except Exception as e:
            st.warning(f"Error al leer Google Sheets: {e}")
    return init_dataframe()

def save_data(df):
    sheet = get_gsheet()
    if sheet:
        try:
            df_to_save = df.copy()
            for col in ["Fecha Creación", "Fecha Límite"]:
                if col in df_to_save.columns:
                    df_to_save[col] = df_to_save[col].dt.strftime("%Y-%m-%d")  # Convertir a string
            sheet.clear()
            sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        except Exception as e:
            st.error(f"No se pudo guardar en Google Sheets: {e}")


# ================= Configuración JWT y usuarios =================
SECRET = st.secrets.get("COOKIE_SECRET", "default_secret_key_32_chars_long_1234")
ADMIN_USERNAME = st.secrets.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD_HASH", "").encode()

users_db = {ADMIN_USERNAME: ADMIN_PASSWORD_HASH}

def verificar_login(usuario, contraseña):
    if usuario in users_db:
        return bcrypt.checkpw(contraseña.encode(), users_db[usuario])
    return False

def crear_token(username):
    payload = {"sub": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)}
    return jwt.encode(payload, SECRET, algorithm="HS256")

def verificar_token(token):
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        return data["sub"]
    except jwt.PyJWTError:
        return None

# ================= Inicialización DataFrame =================
def init_dataframe():
    columns = [
        "ID", "Título", "Descripción", "Estado", "Prioridad",
        "Fecha Creación", "Fecha Límite", "Solicitante", "Departamento",
        "Asignado a", "Categoría", "Comentarios", "Tiempo Resolución (horas)"
    ]
    return pd.DataFrame(columns=columns)

# ================= CSV local de respaldo =================
CSV_FILE = "ticket_tabla.csv"

def save_to_csv(df):
    df.to_csv(CSV_FILE, index=False)

def load_or_init_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            for col in ["Fecha Creación", "Fecha Límite"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            return df
        except:
            return init_dataframe()
    return init_dataframe()

# ================= Función para obtener asignaciones =================
def get_asignaciones(df):
    base = ["Rubén/Sandra", "Equipo Topografia", "Francisco Sanchez",
            "Estefania", "Equipo TI", "Equipo Soporte", "Equipo Desarrollo", "Sin asignar"]
    if df is not None and "Asignado a" in df.columns:
        return sorted(set(base + df['Asignado a'].dropna().unique().tolist()))
    return sorted(base)

# ================= Interfaz Login =================
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

# ================= Interfaz Principal =================
def app():
    st.title("🎫 Sistema de Gestión de Tickets")
    st.write("Plataforma completa para seguimiento de tickets de soporte")

    if 'df' not in st.session_state:
        df_sheets = load_data()
        if not df_sheets.empty:
            st.session_state.df = df_sheets
        else:
            st.session_state.df = load_or_init_data()

    asignaciones = get_asignaciones(st.session_state.df)
    estado_opciones = ["Abierto", "En Progreso", "Resuelto", "Cerrado"]
    prioridad_opciones = ["Alta", "Media", "Baja"]

    # Menú lateral
    with st.sidebar:
        st.header("Opciones")
        menu = st.radio("Seleccione una opción:", ["Nuevo Ticket", "Ver Tickets", "Estadísticas", "Configuración"])

    # ===== Nuevo Ticket =====
    if menu == "Nuevo Ticket":
        st.header("📝 Crear Nuevo Ticket")
        with st.form("nuevo_ticket_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                titulo = st.text_input("Título del Ticket*")
                descripcion = st.text_area("Descripción detallada*")
                solicitante = st.text_input("Solicitante*")
                departamento = st.selectbox("Departamento", ["GIS", "TOPOGRAFIA", "REVISION CAMPO", "ARBORICULTURA", "SERVICIOS"])
            with col2:
                prioridad = st.selectbox("Prioridad*", prioridad_opciones)
                categoria = st.selectbox("Categoría", ["Corrección_GIS", "Revision_Campo", "Plantaciones/Talas", "Actuaciones", "Otro"])
                fecha_limite = st.date_input("Fecha Límite*", min_value=date.today(), value=date.today() + datetime.timedelta(days=3))
                asignado_a = st.selectbox("Asignado a*", asignaciones)

            if st.form_submit_button("Guardar Ticket"):
                if not titulo or not descripcion or not solicitante:
                    st.error("Por favor complete los campos obligatorios (*)")
                else:
                    nuevo_id = 1000
                    if not st.session_state.df.empty:
                        try:
                            nuevo_id = int(st.session_state.df['ID'].str.split('-').str[1].astype(int).max() + 1)
                        except:
                            nuevo_id = 1000
                    nuevo_ticket = pd.DataFrame([{
                        "ID": f"TKT-{nuevo_id}", "Título": titulo, "Descripción": descripcion,
                        "Estado": "Abierto", "Prioridad": prioridad,
                        "Fecha Creación": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "Fecha Límite": fecha_limite.strftime("%Y-%m-%d"),
                        "Solicitante": solicitante, "Departamento": departamento,
                        "Asignado a": asignado_a, "Categoría": categoria,
                        "Comentarios": "", "Tiempo Resolución (horas)": 0
                    }])
                    st.session_state.df = pd.concat([nuevo_ticket, st.session_state.df], ignore_index=True)
                    save_data(st.session_state.df)
                    save_to_csv(st.session_state.df)
                    st.success(f"✅ Ticket TKT-{nuevo_id} creado exitosamente!")
                    st.balloons()

    # ===== Ver Tickets =====
    elif menu == "Ver Tickets":
        st.header("📋 Listado de Tickets")
        if st.session_state.df.empty:
            st.warning("No hay tickets registrados")
            return

        with st.expander("🔍 Filtros Avanzados"):
            cols = st.columns(3)
            with cols[0]:
                filtro_estado = st.multiselect("Estado", estado_opciones, default=["Abierto"])
            with cols[1]:
                filtro_prioridad = st.multiselect("Prioridad", prioridad_opciones, default=prioridad_opciones)
            with cols[2]:
                opciones_departamento = st.session_state.df.get('Departamento', pd.Series()).dropna().unique().tolist()
                filtro_departamento = st.multiselect("Departamento", opciones_departamento, default=opciones_departamento)

        filtered_df = st.session_state.df.copy()
        if filtro_estado: filtered_df = filtered_df[filtered_df['Estado'].isin(filtro_estado)]
        if filtro_prioridad: filtered_df = filtered_df[filtered_df['Prioridad'].isin(filtro_prioridad)]
        if filtro_departamento: filtered_df = filtered_df[filtered_df['Departamento'].isin(filtro_departamento)]

        # Normalizar tipos y valores antes de data_editor
        filtered_df["Fecha Límite"] = pd.to_datetime(filtered_df["Fecha Límite"], errors="coerce")
        filtered_df["Fecha Límite"] = filtered_df["Fecha Límite"].fillna(pd.Timestamp.today())
        filtered_df["Estado"] = filtered_df["Estado"].where(filtered_df["Estado"].isin(estado_opciones), "Abierto")
        filtered_df["Prioridad"] = filtered_df["Prioridad"].where(filtered_df["Prioridad"].isin(prioridad_opciones), "Media")
        filtered_df["Asignado a"] = filtered_df["Asignado a"].where(filtered_df["Asignado a"].isin(asignaciones), "Sin asignar")

        if not filtered_df.empty:
            st.write(f"Mostrando {len(filtered_df)} de {len(st.session_state.df)} tickets")
            edited_df = st.data_editor(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Estado": st.column_config.SelectboxColumn("Estado", options=estado_opciones, required=True),
                    "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=prioridad_opciones, required=True),
                    "Fecha Límite": st.column_config.DateColumn("Fecha Límite", format="YYYY-MM-DD", required=True),
                    "Asignado a": st.column_config.SelectboxColumn("Asignado a", options=asignaciones, required=True),
                },
                disabled=["ID", "Fecha Creación", "Solicitante", "Departamento"],
                key="ticket_editor"
            )
            if not edited_df.equals(filtered_df):
                st.session_state.df.update(edited_df)
                save_data(st.session_state.df)
                save_to_csv(st.session_state.df)
                st.success("✅ Cambios guardados correctamente")
        else:
            st.warning("No se encontraron tickets con los filtros aplicados")

    # ===== Estadísticas =====
    elif menu == "Estadísticas":
        st.header("📊 Estadísticas de Tickets")
        if st.session_state.df.empty:
            st.warning("No hay datos para mostrar")
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tickets", len(st.session_state.df))
        col2.metric("Tickets Abiertos", len(st.session_state.df[st.session_state.df['Estado'] == "Abierto"]))
        hoy = pd.to_datetime(date.today())
        vencidos = st.session_state.df[(st.session_state.df['Estado'] != "Cerrado") & (pd.to_datetime(st.session_state.df['Fecha Límite']) < hoy)]
        col3.metric("Tickets Vencidos", len(vencidos))

        tab1, tab2, tab3 = st.tabs(["Por Estado", "Por Prioridad", "Por Departamento"])
        with tab1:
            st.altair_chart(
                alt.Chart(st.session_state.df).mark_bar().encode(
                    x="count():Q", y="Estado:N", color="Estado:N"
                ).properties(height=400), use_container_width=True
            )
        with tab2:
            st.altair_chart(
                alt.Chart(st.session_state.df).mark_arc().encode(
                    theta="count():Q", color="Prioridad:N"
                ).properties(height=400), use_container_width=True
            )
        with tab3:
            st.altair_chart(
                alt.Chart(st.session_state.df).mark_bar().encode(
                    x="count():Q", y="Departamento:N", color="Prioridad:N"
                ).properties(height=400), use_container_width=True
            )

# ================= Lógica de login =================
if "token" in st.session_state:
    usuario = verificar_token(st.session_state.token)
    if usuario:
        st.session_state.logged_in = True
        st.session_state.usuario = usuario
    else:
        st.session_state.logged_in = False

if st.session_state.get("logged_in", False):
    app()
else:
    login()
