import datetime
import random
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import os

# Nombre del archivo CSV
CSV_FILE = "tickets.csv"

# Configuración de la página
st.set_page_config(page_title="Support tickets", page_icon="🎫")
st.title("🎫 Support tickets")
st.write(
    """
    Esta aplicación permite crear, editar y visualizar tickets de soporte.
    Ahora los datos se guardan en un archivo CSV para que no se pierdan al reiniciar.
    """
)

# Cargar datos desde CSV si existe
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["ID", "Issue", "Status", "Priority", "Date Submitted"])

st.session_state.df = df.copy()

# Función para guardar en CSV
def save_to_csv(dataframe):
    dataframe.to_csv(CSV_FILE, index=False)

# Sección para agregar un nuevo ticket
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
        [
            {
                "ID": f"TICKET-{recent_ticket_number+1}",
                "Issue": issue,
                "Status": "Open",
                "Priority": priority,
                "Date Submitted": today,
            }
        ]
    )

    st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0)
    save_to_csv(st.session_state.df)

    st.success("✅ Ticket submitted!")
    st.dataframe(df_new, use_container_width=True, hide_index=True)

# Sección para ver y editar tickets
st.header("Existing tickets")
st.write(f"Number of tickets: `{len(st.session_state.df)}`")

edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Ticket status",
            options=["Open", "In Progress", "Closed"],
            required=True,
        ),
        "Priority": st.column_config.SelectboxColumn(
            "Priority",
            help="Priority",
            options=["High", "Medium", "Low"],
            required=True,
        ),
    },
    disabled=["ID", "Date Submitted"],
)

# Guardar cambios en el CSV cuando se edite
if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df
    save_to_csv(edited_df)
    st.info("💾 Changes saved to CSV.")

# Métricas y gráficos
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






