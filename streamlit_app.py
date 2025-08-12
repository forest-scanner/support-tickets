import datetime
import os
import pandas as pd
import altair as alt
import streamlit as st
import streamlit_authenticator as stauth

# Credenciales con contraseña ya encriptada (bcrypt)
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            # Esta es la contraseña "gispro1977" hasheada (no se ve la clave en texto plano)
            "password": "$2b$12$UnXKo29nl.4qx1d4i7WuUOdzqdlE/rX/FLF2P7VrTL/pdQmn6ShQ2"
        }
    }
}

# Crear autenticador
authenticator = stauth.Authenticate(
    credentials,
    "ticket_app_cookie",   # nombre de la cookie
    "abcdef",              # clave secreta para la cookie
    cookie_expiry_days=1
)

# Mostrar formulario de login
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.success(f"Bienvenido {name} 👋")
    authenticator.logout("Cerrar sesión", "sidebar")

    # ======= APP DE TICKETS =======
    st.title("🎫 Support tickets")
    st.write("Sistema de tickets con persistencia en CSV y autenticación segura.")

    CSV_FILE = "tickets.csv"

    # Cargar datos si existe
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame(columns=["ID", "Issue", "Status", "Priority", "Date Submitted"])

    st.session_state.df = df.copy()

    def save_to_csv(dataframe):
        dataframe.to_csv(CSV_FILE, index=False)

    # Agregar ticket
    st.header("Add a ticket")
    with st.form("add_ticket_form"):
        issue = st.text_area("Describe the issue")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Submit")

    if submitted and issue.strip():
        if len(st.session_state.df) == 0:
            recent_ticket_number = 1000
        else:
            recent_ticket_number = int(max(st.session_state.df.ID).split("-")[1])

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        df_new = pd.DataFrame(
            [{
                "ID": f"TICKET-{recent_ticket_number+1}",
                "Issue": issue,
                "Status": "Open",
                "Priority": priority,
                "Date Submitted": today,
            }]
        )

        st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0)
        save_to_csv(st.session_state.df)
        st.success("✅ Ticket submitted!")
        st.dataframe(df_new, use_container_width=True, hide_index=True)

    # Editar tickets
    st.header("Existing tickets")
    st.write(f"Number of tickets: `{len(st.session_state.df)}`")

    edited_df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status", options=["Open", "In Progress", "Closed"], required=True
            ),
            "Priority": st.column_config.SelectboxColumn(
                "Priority", options=["High", "Medium", "Low"], required=True
            ),
        },
        disabled=["ID", "Date Submitted"],
    )

    if not edited_df.equals(st.session_state.df):
        st.session_state.df = edited_df
        save_to_csv(edited_df)
        st.info("💾 Changes saved to CSV.")

    # Estadísticas
    st.header("Statistics")
    col1, col2, col3 = st.columns(3)
    num_open_tickets = len(st.session_state.df[st.session_state.df.Status == "Open"])
    col1.metric(label="Number of open tickets", value=num_open_tickets)
    col2.metric(label="First response time (hours)", value=5.2)
    col3.metric(label="Average resolution time (hours)", value=16)

    if len(st.session_state.df) > 0:
        st.write("##### Ticket status per month")
        status_plot = (
            alt.Chart(st.session_state.df)
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
            alt.Chart(st.session_state.df)
            .mark_arc()
            .encode(theta="count():Q", color="Priority:N")
            .properties(height=300)
        )
        st.altair_chart(priority_plot, use_container_width=True)

elif authentication_status is False:
    st.error("Usuario o contraseña incorrectos")
elif authentication_status is None:
    st.warning("Por favor ingresa tus credenciales")



