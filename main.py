import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

# --- 1. TU FUNCIÓN DE LIMPIEZA ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Tus columnas reales) ---
def cargar_excel_real():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        if 'Nombre' in df.columns:
            df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

# --- 3. TU LÓGICA DE SCRAPING (Extraída de tu .txt) ---
def scrapear_jornada_manel(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL de la jornada
    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🚀 Iniciando escaneo con tu lógica de BeSoccer...")
    
    try:
        response = scraper.get(url_base)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Buscamos los links de los partidos como haces tú
        match_links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        resultados_jornada = []
        barara_progreso = st.progress(0)

        for idx, link in enumerate(match_links[:6]): # Prueba con 6 partidos
            st.write(f"Analizando: {link.split('/')[-1]}")
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # Buscamos las tablas de jugadores (titulares y suplentes)
            # Usamos el selector de tu script: 'tr.player-row'
            players = soup_p.select('tr.player-row')
            
            for p in players:
                try:
                    # Extracción de NOMBRE y NOTA tal cual lo haces tú
                    name_tag = p.find('span', class_='name')
                    # En tu script buscas el div 'rating' o el valor numérico
                    nota_tag = p.find('div', class_='rating') or p.find('span', class_='num')
                    
                    if name_tag:
                        nombre_jugador = name_tag.get_text(strip=True)
                        nota_jugador = nota_tag.get_text(strip=True).replace(',', '.') if nota_tag else "0.0"
                        
                        try:
                            nota_final = float(nota_jugador)
                        except:
                            nota_final = 0.0
                            
                        # CRUCE CON TU EXCEL
                        n_clean = limpiar_nombre_manel(nombre_jugador)
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean]
                        
                        vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                        puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        
                        resultados_jornada.append({
                            'Jugador': nombre_jugador,
                            'Nota': nota_final,
                            'Contrato': vencimiento,
                            'Puesto': puesto,
                            'Estado': '✅ Radar' if not match.empty else '🔥 Nuevo'
                        })
                except:
                    continue
            
            barara_progreso.progress((idx + 1) / 6)
            time.sleep(0.5) # Respetamos el tiempo de espera de tu script

        df_final = pd.DataFrame(resultados_jornada)
        return df_final.sort_values(by='Nota', ascending=False)

    except Exception as e:
        st.error(f"Error técnico: {e}")
        return pd.DataFrame()

# --- INTERFAZ STREAMLIT ---
st.title("🛡️ Sistema de Scouting Manel")

df_ex = cargar_excel_real()

if st.button("🔍 EJECUTAR SCRAPER (Tu Lógica)"):
    if df_ex.empty:
        st.warning("No se pudo cargar el Excel. Revisa el archivo.")
    else:
        resultado = scrapear_jornada_manel(df_ex)
        
        if not resultado.empty:
            st.subheader("🔝 Top 11 de la Jornada")
            st.table(resultado.head(11))
            
            st.subheader("📋 Datos Completos")
            st.dataframe(resultado)
        else:
            st.error("No se extrajeron datos. Revisa si la URL de BeSoccer ha cambiado.")
