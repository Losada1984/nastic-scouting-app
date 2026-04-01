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

# 2. TU LÓGICA DE EXTRACCIÓN (CLONADA DEL TXT CON CABECERAS HUMANAS)
def ejecutar_tu_script_final(df_excel):
    # Configuramos el scraper para que parezca un usuario real de Windows
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # Cabeceras que envían los navegadores reales
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("📡 Conectando con 'Disfraz de Navegador'...")
    
    try:
        # Petición con cabeceras completas
        r = scraper.get(url_base, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        if not links:
            st.error("🚫 No se ven partidos. BeSoccer ha bloqueado la IP del servidor de Streamlit.")
            return pd.DataFrame()

        datos_jugadores = []
        barra = st.progress(0)

        # Procesamos partidos
        for i, link in enumerate(links[:6]): # Test con 6 partidos
            time.sleep(random.uniform(1, 2)) # Pausa humana aleatoria
            
            res_p = scraper.get(link, headers=headers, timeout=15)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # TU LÓGICA EXACTA DE CLASES
            jugadores_html = soup_p.find_all(class_=['player-info', 'lineup-player'])
            
            for j in jugadores_html:
                try:
                    name_tag = j.find(class_='name')
                    # Buscamos la nota en tus clases de confianza
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
            
            barra.progress((i + 1) / 6)

        return pd.DataFrame(datos_jugadores)

    except Exception as e:
        st.error(f"Fallo de conexión: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Nàstic: Rompiendo el Bloqueo")

# Cargar Excel
try:
    df_ex = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
    df_ex['nombre_clean_excel'] = df_ex['Nombre'].apply(limpiar_nombre_manel)
except:
    st.error("No se pudo cargar el Excel.")
    df_ex = pd.DataFrame()

if st.button("🚀 INICIAR ESCANEO FORZADO"):
    if not df_ex.empty:
        res = ejecutar_tu_script_final(df_ex)
        if not res.empty:
            res = res.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            st.success("¡Datos extraídos con éxito!")
            st.table(res.head(11))
            st.dataframe(res)
        else:
            st.warning("El servidor sigue bloqueado. Prueba a esperar 1 minuto o reinicia la App.")
