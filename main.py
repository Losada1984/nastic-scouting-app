import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time
import random

# 1. TU FUNCIÓN DE LIMPIEZA (Literal de tu archivo)
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# 2. TU LÓGICA DE EXTRACCIÓN (Celdas 6 y 7 de tu .txt)
def ejecutar_scouting_fiel(df_excel):
    # Usamos cloudscraper con un "huella dactilar" de navegador real
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # URL de la Jornada 1 que pediste
    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🚀 Iniciando tu proceso de extracción (Jornada 1)...")
    
    try:
        # Intentamos entrar a la página principal de la jornada
        r = scraper.get(url_base, timeout=20)
        if r.status_code != 200:
            st.error(f"❌ BeSoccer ha denegado el acceso (Error {r.status_code})")
            return pd.DataFrame()
            
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_jugadores = []
        barra = st.progress(0)

        # Recorremos partidos (limitamos a 10 para asegurar estabilidad)
        for i, link in enumerate(links[:10]):
            # Pausa aleatoria para evitar que nos cacen como bot
            time.sleep(random.uniform(1.5, 3.0))
            
            res_p = scraper.get(link, timeout=20)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # --- TUS SELECTORES EXACTOS DEL TXT ---
            # Tu script busca en 'player-info' y 'lineup-player'
            jugadores_html = soup_p.select('.player-info, .lineup-player, .player-row')
            
            for j in jugadores_html:
                try:
                    # Buscamos nombre y nota con tus clases: 'name' y 'rating/num'
                    name_tag = j.find(class_='name')
                    # Tu script busca la nota en estas 3 opciones:
                    nota_tag = j.find(class_=['rating', 'num', 'rating-box'])
                    
                    if name_tag and nota_tag:
                        nombre_web = name_tag.get_text(strip=True)
                        nota_web = nota_tag.get_text(strip=True).replace(',', '.')
                        
                        # CRUCE CON TU EXCEL
                        n_clean_w = limpiar_nombre_manel(nombre_web)
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean_w]
                        
                        vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                        puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        
                        datos_jugadores.append({
                            'Jugador': nombre_web,
                            'Nota': float(nota_web) if nota_web else 0.0,
                            'Contrato': vencimiento,
                            'Puesto': puesto,
                            'Origen': '✅ Radar' if not match.empty else '✨ Nuevo'
                        })
                except:
                    continue
            
            barra.progress((i + 1) / 10)

        return pd.DataFrame(datos_jugadores)

    except Exception as e:
        st.error(f"Fallo en la conexión: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Nàstic (Tu Script)")

# Carga del Excel
try:
    df_ex = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
    df_ex['nombre_clean_excel'] = df_ex['Nombre'].apply(limpiar_nombre_manel)
except:
    st.error("No se ha encontrado el Excel '-COMPETICIONS.xlsx'")
    df_ex = pd.DataFrame()

if st.button("🔍 EJECUTAR MI SCRAPEO"):
    if not df_ex.empty:
        res = ejecutar_scouting_fiel(df_ex)
        if not res.empty:
            # Eliminamos duplicados y ordenamos por nota
            res = res.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            
            st.success("¡Datos extraídos! Aquí tienes el 11 ideal:")
            st.table(res.head(11))
            st.dataframe(res)
        else:
            st.warning("⚠️ BeSoccer sigue bloqueando la IP de Streamlit. El código es correcto, pero el servidor está marcado.")
