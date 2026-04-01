import streamlit as st
import pandas as pd
import os
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

# Configuración de página y estilo Nàstic
st.set_page_config(page_title="Nàstic Scouting Elite", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0a0a0a; color: white; }
    .stButton>button { background-color: #8b0000; color: white; border-radius: 10px; font-weight: bold; width: 100%; }
    [data-testid="stMetricValue"] { color: #8b0000; }
    .stDataFrame { background-color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/en/d/df/Gimn%C3%A0stic_tarragona_200px.png", width=150)
        st.title("DIRECCIÓN DEPORTIVA 26-27")
        st.subheader("App by Manel Losada")
        password = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if password == "Nastic1922":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

# --- CARGA DE DATOS (EXCEL CON 3 PESTAÑAS) ---
@st.cache_data
def load_data():
    archivo = "-COMPETICIONS.xlsx"
    if os.path.exists(archivo):
        try:
            # Leemos las 3 pestañas del Excel
            df1 = pd.read_excel(archivo, sheet_name="PRIMERA RFEF")
            df2 = pd.read_excel(archivo, sheet_name="SEGUNDA RFEF")
            df3 = pd.read_excel(archivo, sheet_name="3A RFEF")
            
            # Normalizar nombres de columnas
            for df in [df1, df2, df3]:
                if "nom_esportiu" in df.columns: df.rename(columns={"nom_esportiu": "Nombre"}, inplace=True)
                if "posicion_especifica" in df.columns: df.rename(columns={"posicion_especifica": "Puesto"}, inplace=True)
                if "Posición específica" in df.columns: df.rename(columns={"Posición específica": "Puesto"}, inplace=True)

            return pd.concat([df1, df2, df3], ignore_index=True)
        except Exception as e:
            st.error(f"Error al leer el Excel: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

df_players = load_data()

# --- MENÚ LATERAL ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/d/df/Gimn%C3%A0stic_tarragona_200px.png", width=100)
st.sidebar.title("Nàstic Scouting")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Menú", ["🏠 Inicio", "📊 Base de Datos", "📍 Campograma Táctico"])
st.sidebar.markdown("---")
st.sidebar.write("👤 **By Manel Losada**")

# --- SECCIONES ---
if menu == "🏠 Inicio":
    st.title("🏟️ Panel de Control - Nàstic")
    col1, col2, col3 = st.columns(3)
    col1.metric("Jugadores en Radar", len(df_players))
    col2.metric("Temporada", "26-27")
    col3.metric("Estado", "Conectado")

    st.markdown("### Acciones Rápidas")
    if st.button("🚀 ACTUALIZAR MERCADO (SCRAPING)"):
        with st.spinner('Conectando con BeSoccer...'):
            # Aquí iría tu lógica de scraping real
            import time
            time.sleep(2)
            st.success("Mercado actualizado con éxito.")

elif menu == "📊 Base de Datos":
    st.title("📊 Base de Datos de Jugadores")
    if not df_players.empty:
        # Buscador y Filtros
        busqueda = st.text_input("Buscar por nombre o equipo...")
        df_filtrado = df_players[df_players['Nombre'].str.contains(busqueda, case=False, na=False)]
        
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay datos cargados. Verifica el archivo Excel.")

elif menu == "📍 Campograma Táctico":
    st.title("📍 Análisis Visual de Posiciones")
    pitch = VerticalPitch(pitch_type='statsbomb', pitch_color='#1a3a1a', line_color='white')
    fig, ax = pitch.draw(figsize=(10, 7))
    
    # Aquí puedes añadir la lógica para pintar las fotos según 'Puesto'
    st.pyplot(fig)
    st.info("Configura las coordenadas de los jugadores según su puesto en el Excel para ver sus fotos aquí.")
