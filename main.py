import streamlit as st
import pandas as pd
import time
import requests
from io import BytesIO
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from fpdf import FPDF
import os

plt.switch_backend('Agg')
st.set_page_config(page_title="Nàstic Scouting Elite", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0a0a0a; color: white; }
    .stButton>button { background-color: #8b0000; color: white; border-radius: 10px; font-weight: bold; }
    [data-testid="stMetricValue"] { color: #8b0000; }
    </style>
    """, unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/en/d/df/Gimn%C3%A0stic_tarragona_200px.png", width=150)
        st.title("DIRECCIÓN DEPORTIVA 26-27")
        password = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if password == "Nastic1922":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

@st.cache_data
def load_data():
    files = ["COMPETICIONS.xlsx - PRIMERA RFEF.csv", "COMPETICIONS.xlsx - SEGUNDA RFEF.csv", "COMPETICIONS.xlsx - 3A RFEF.csv"]
    all_dfs = []
    for f in files:
        if os.path.exists(f):
            df = pd.read_csv(f)
            if "nom_esportiu" in df.columns: df = df.rename(columns={"nom_esportiu": "Nombre"})
            if "posicion_especifica" in df.columns: df = df.rename(columns={"posicion_especifica": "Puesto"})
            all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

df_players = load_data()

st.sidebar.title("Nàstic Scouting")
menu = st.sidebar.radio("Menú", ["🏠 Inicio", "📊 Base de Datos", "📍 Campograma Táctico"])

if menu == "🏠 Inicio":
    st.title("🏠 Panel de Control")
    st.metric("Jugadores", len(df_players))
    if st.button("🚀 ACTUALIZAR MERCADO"):
        st.progress(100)
        st.success("Mercado actualizado.")

elif menu == "📊 Base de Datos":
    st.title("📊 Base de Datos")
    st.dataframe(df_players, use_container_width=True)

elif menu == "📍 Campograma Táctico":
    st.title("📍 Campograma")
    pitch = VerticalPitch(pitch_type='statsbomb', pitch_color='#1a3a1a')
    fig, ax = pitch.draw()
    st.pyplot(fig)
