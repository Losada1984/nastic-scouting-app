import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import os
import pickle
from mplsoccer import VerticalPitch

# --- FUNCIONES AUXILIARES ---
def normalizar(t):
    return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower().strip()

def cargar_excel_contratos():
    try:
        # Cargamos solo la pestaña de Primera RFEF para la prueba
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        df.rename(columns={'nom_esportiu': 'Nombre', 'posicion_especifica': 'Puesto', 'vencimiento_contrato': 'Contrato'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return pd.DataFrame()

# --- MOTOR DE SCRAPING DE PRUEBA (JORNADA 1) ---
def test_scraping_jornada_1(df_contratos):
    scraper = cloudscraper.create_scraper()
    # URL de resultados de la Jornada 1
    url_jornada = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    status = st.empty()
    status.info("🔍 Accediendo a la Jornada 1 de Primera RFEF...")
    
    lista_jugadores_web = []
    
    try:
        r = scraper.get(url_jornada)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. Buscamos los links de los partidos de esa jornada
        links_partidos = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        progreso = st.progress(0)
        for i, link in enumerate(links_partidos[:3]): # Probamos con los 3 primeros partidos para ir rápido
            status.write(f"🏟️ Analizando partido {i+1}...")
            # Entramos en la ficha del partido para ver alineaciones y notas
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            # Buscamos filas de jugadores (titulares y suplentes)
            for player_row in soup_p.find_all('tr', class_='player-row'):
                nombre = player_row.find('span', class_='name').get_text(strip=True) if player_row.find('span', class_='name') else "Desconocido"
                nota = player_row.find('div', class_='rating').get_text(strip=True) if player_row.find('div', class_='rating') else "5.0"
                minutos = "90" # Simplificación para la prueba
                
                lista_jugadores_web.append({
                    'Nombre': nombre,
                    'Nota': nota,
                    'Minutos': minutos
                })
            progreso.progress((i + 1) / 3)
            
        df_web = pd.DataFrame(lista_jugadores_web)
        
        # 2. CRUCE CON EXCEL (Vencimiento Contrato)
        # Hacemos el merge por nombre normalizado
        df_contratos['nombre_norm'] = df_contratos['Nombre'].apply(normalizar)
        df_web['nombre_norm'] = df_web['Nombre'].apply(normalizar)
        
        df_final = pd.merge(df_web, df_contratos[['nombre_norm', 'Contrato', 'Puesto']], on='nombre_norm', how='inner')
        
        status.success(f"✅ Prueba completada. Se han cruzado {len(df_final)} jugadores de tu radar que jugaron en la Jornada 1.")
        return df_final

    except Exception as e:
        st.error(f"Error en el scraping: {e}")
        return pd.DataFrame()

# --- INTERFAZ APP ---
st.title("🧪 Modo Prueba: Jornada 1 - Primera RFEF")

df_excel = cargar_excel_contratos()

if st.button("▶️ INICIAR PRUEBA DE CRUCE"):
    resultados = test_scraping_jornada_1(df_excel)
    
    if not resultados.empty:
        st.subheader("📋 Resultados del Cruce (BeSoccer + Tu Excel)")
        st.write("Estos son los jugadores que el scraper ha encontrado en la Jornada 1 y que coinciden con tu lista de contratos:")
        
        # Mostramos tabla con los datos que pediste
        st.dataframe(resultados[['Nombre', 'Puesto', 'Nota', 'Contrato']], use_container_width=True)
        
        # Visualización tipo Ficha
        st.markdown("### 🗂️ Vista Previa de Fichas")
        for _, row in resultados.head(5).iterrows():
            st.markdown(f"""
            <div style="background-color:#1a1a1a; padding:15px; border-radius:10px; border-left:5px solid #8b0000; margin-bottom:10px;">
                <h4 style="margin:0; color:#8b0000;">{row['Nombre']}</h4>
                <p style="margin:0;">📍 Posición: <b>{row['Puesto']}</b> | ⭐ Nota J1: <b>{row['Nota']}</b></p>
                <p style="margin:0; color:#ffd700;">📅 Vencimiento Contrato: <b>{row['Contrato']}</b></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No se encontraron coincidencias. Asegúrate de que los nombres en el Excel coincidan con los de BeSoccer.")
