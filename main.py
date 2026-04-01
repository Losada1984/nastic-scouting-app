import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import requests
import os
import pickle
import unicodedata
from mplsoccer import VerticalPitch

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Nàstic Scouting - Manel Losada", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0a0a0a; color: white; }
    .stButton>button { background-color: #8b0000; color: white; border-radius: 10px; font-weight: bold; width: 100%; }
    [data-testid="stMetricValue"] { color: #8b0000; }
    .card { background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #8b0000; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE PERSISTENCIA ---
def guardar_datos(df):
    with open('base_datos_maestra.pkl', 'wb') as f:
        pickle.dump(df, f)

def cargar_datos_maestros():
    if os.path.exists('base_datos_maestra.pkl'):
        with open('base_datos_maestra.pkl', 'rb') as f:
            return pickle.load(f)
    else:
        # Si no hay backup, cargamos el Excel de contratos
        archivo_excel = "-COMPETICIONS.xlsx"
        if os.path.exists(archivo_excel):
            df1 = pd.read_excel(archivo_excel, sheet_name="PRIMERA RFEF")
            df2 = pd.read_excel(archivo_excel, sheet_name="SEGUNDA RFEF")
            df3 = pd.read_excel(archivo_excel, sheet_name="3A RFEF")
            df = pd.concat([df1, df2, df3], ignore_index=True)
            # Normalizar columnas
            cols_map = {'nom_esportiu': 'Nombre', 'posicion_especifica': 'Puesto', 'vencimiento_contrato': 'Contrato'}
            df.rename(columns=cols_map, inplace=True)
            # Inicializar columnas de scraping si no existen
            for col in ['Nota', 'Minutos', 'Foto_Url', 'Onces_Ideales']:
                if col not in df.columns: df[col] = 0 if col == 'Onces_Ideales' else (None if col == 'Foto_Url' else 5.0)
            return df
    return pd.DataFrame()

# --- LÓGICA DE SCRAPING JORNADA A JORNADA ---
def normalizar(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

def ejecutar_scraping_total(df):
    scraper = cloudscraper.create_scraper()
    urls_once = {
        "1ª RFEF": "https://es.besoccer.com/competicion/once_ideal/primera_rfef/2026/jornada",
        "2ª RFEF": "https://es.besoccer.com/competicion/once_ideal/segunda_rfef/2026/jornada",
        "3ª RFEF": "https://es.besoccer.com/competicion/once_ideal/tercera_rfef/2026/jornada"
    }
    
    progreso = st.progress(0)
    status = st.empty()
    
    # Reset de Onces Ideales para recalcular sumatorio total
    df['Onces_Ideales'] = 0

    for idx, (liga, url_base) in enumerate(urls_once.items()):
        for jor in range(1, 39): # Escanea hasta la jornada 38 o hasta que no haya más datos
            status.write(f"🕵️‍♂️ {liga} | Analizando Jornada {jor}...")
            try:
                r = scraper.get(f"{url_base}{jor}", timeout=10)
                if r.status_code != 200: break
                
                soup = BeautifulSoup(r.text, 'html.parser')
                # Encontrar nombres en el Once Ideal
                nombres_once = [n.get_text(strip=True) for n in soup.find_all('div', class_='name')]
                
                for n_web in nombres_once:
                    n_norm = normalizar(n_web)
                    # Comparar con nuestra lista de contratos
                    for i, row in df.iterrows():
                        if n_norm in normalizar(row['Nombre']):
                            df.at[i, 'Onces_Ideales'] += 1
            except: break
        progreso.progress((idx + 1) / len(urls_once))
    
    guardar_datos(df) # Guardar permanentemente
    return df

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/en/d/df/Gimn%C3%A0stic_tarragona_200px.png", width=120)
        pwd = st.text_input("Contraseña Elite", type="password")
        if st.button("ACCEDER"):
            if pwd == "Nastic1922":
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- CARGA DE DATOS ---
df_players = cargar_datos_maestros()

# --- MENÚ ---
menu = st.sidebar.radio("DIRECCIÓN DEPORTIVA", ["🏠 Inicio", "📊 Base de Datos", "📍 Campograma Táctico"])
st.sidebar.markdown(f"**Usuario:** Manel Losada")

if menu == "🏠 Inicio":
    st.title("🏟️ Panel de Control Scouting")
    col1, col2 = st.columns(2)
    col1.metric("Jugadores en Seguimiento", len(df_players))
    
    if st.button("🚀 ACTUALIZAR DATOS (SCRAPING JORNADAS)"):
        df_players = ejecutar_scraping_total(df_players)
        st.success("¡Base de datos actualizada y guardada!")
        st.rerun()

elif menu == "📊 Base de Datos":
    st.title("📊 Contratos y Rendimiento")
    st.dataframe(df_players, use_container_width=True, hide_index=True)

elif menu == "📍 Campograma Táctico":
    st.title("📍 Análisis de Posiciones y Onces Ideales")
    
    coords = {
        'Portero': [105, 40], 'Lateral Derecho': [80, 70], 'Lateral Izquierdo': [80, 10],
        'Central': [92, 40], 'Central Derecho': [92, 55], 'Central Izquierdo': [92, 25],
        'Pivote': [65, 40], 'Mediocentro': [55, 40], 'Extremo Derecho': [25, 75],
        'Extremo Izquierdo': [25, 5], 'Delantero Centro': [12, 40]
    }

    c_campo, c_info = st.columns([2, 1.2])

    with c_campo:
        pitch = VerticalPitch(pitch_type='statsbomb', pitch_color='#1a3a1a', line_color='white')
        fig, ax = pitch.draw(figsize=(11, 9))
        for _, row in df_players.iterrows():
            if row['Puesto'] in coords:
                y, x = coords[row['Puesto']]
                # Burbuja de datos
                ax.scatter(x, y, s=800, c='#8b0000', edgecolors='white', zorder=3)
                ax.text(x, y-6, f"{row['Nombre']}\n{row.get('Nota', 5.0)} | {row.get('Contrato', '')}", 
                        color='white', fontsize=8, ha='center', fontweight='bold', bbox=dict(facecolor='black', alpha=0.6))
                # ⭐ ESTRELLA ONCES IDEALES
                onces = int(row.get('Onces_Ideales', 0))
                ax.text(x+5, y+5, f"⭐{onces}", color='black', fontsize=9, fontweight='bold', 
                        bbox=dict(facecolor='#ffd700', boxstyle='circle'))
        st.pyplot(fig)

    with c_info:
        st.subheader("🔝 TOP 5 POR POSICIÓN")
        pos_sel = st.selectbox("Seleccionar Puesto:", list(coords.keys()))
        top5 = df_players[df_players['Puesto'] == pos_sel].sort_values(by='Nota', ascending=False).head(5)
        
        for i, (_, t) in enumerate(top5.iterrows()):
            st.markdown(f"""
            <div class="card">
                <h4 style="margin:0;">{i+1}. {t['Nombre']} <span style="color:#ffd700;">⭐{int(t['Onces_Ideales'])}</span></h4>
                <p style="margin:0; font-size:0.9em;">📝 Contrato: <b>{t.get('Contrato', 'N/A')}</b></p>
                <p style="margin:0; font-size:0.9em;">📊 Nota: {t['Nota']} | ⏱️ {t.get('Minutos', 0)}'</p>
            </div>
            """, unsafe_allow_html=True)
