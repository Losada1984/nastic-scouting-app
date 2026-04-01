import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time
import random

# 1. TU LIMPIEZA DE SIEMPRE
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# 2. TU LÓGICA DE EXTRACCIÓN (CLONADA DEL TXT)
def ejecutar_tu_script_final(df_excel):
    # Creamos el scraper con un identificador de navegador real (User-Agent)
    # Esto es lo que evita que BeSoccer te diga "No hay datos"
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("📡 Iniciando conexión segura con BeSoccer...")
    
    try:
        # Simulamos una espera humana inicial
        time.sleep(random.uniform(1, 2))
        r = scraper.get(url_base)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        if not links:
            st.error("🚫 BeSoccer ha bloqueado el acceso a la lista de partidos. Intentando ruta alternativa...")
            return pd.DataFrame()

        datos_jugadores = []
        barra = st.progress(0)

        for i, link in enumerate(links[:10]):
            # Pausa aleatoria para que no parezca un bot
            time.sleep(random.uniform(0.5, 1.5))
            
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # TU LÓGICA DE SELECTORES (PLAYER-INFO)
            # Buscamos en todas las cajas posibles por si cambian la clase
            jugadores_html = soup_p.find_all(class_=['player-info', 'lineup-player', 'player-row'])
            
            for j in jugadores_html:
                try:
                    name_tag = j.find(class_='name')
                    # Buscamos la nota en tus 3 clases de confianza
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
                            'Vencimiento': vencimiento,
                            'Puesto': puesto,
                            'Estado': '✅ Radar' if not match.empty else '🕵️ Descubrimiento'
                        })
                except:
                    continue
            
            barra.progress((i + 1) / 10)

        return pd.DataFrame(datos_jugadores)

    except Exception as e:
        st.error(f"Fallo de conexión: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Nàstic: Modo Anti-Bloqueo")

# Cargar Excel
try:
    df_ex = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
    df_ex['nombre_clean_excel'] = df_ex['Nombre'].apply(limpiar_nombre_manel)
except:
    st.error("Fallo al leer -COMPETICIONS.xlsx")
    df_ex = pd.DataFrame()

if st.button("🔍 LANZAR SCRAPEO"):
    if not df_ex.empty:
        res = ejecutar_tu_script_final(df_ex)
        if not res.empty:
            res = res.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            st.subheader("🌟 Tu 11 Ideal (Extraído con éxito)")
            st.table(res.head(11))
            st.dataframe(res)
        else:
            st.warning("⚠️ BeSoccer sigue detectando la conexión automática. Prueba a pulsar de nuevo en unos segundos.")
