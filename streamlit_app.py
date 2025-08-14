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
    """Carga datos desde Google Sheets"""
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
    """Guarda DataFrame en Google Sheets"""
    sheet = get_gsheet()
    if sheet:
        try:
            sheet.clear()
            sheet.update([df.columns.values.tolist()] + df.values.tolist())
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
        "ID", "Título", "Descripc
