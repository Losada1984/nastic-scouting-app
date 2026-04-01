import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

# --- 1. TU LIMPIEZA DE ACENTOS ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Columnas: Nombre, Contrato_Hasta) ---
def cargar_excel():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        df['nombre_clean'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

# --- 3. TU LÓGICA DE EXTRACCIÓN (CELDA 5/6 DEL TXT) ---
def ejecutar_scraper_fiel(df_excel):
    scraper = cloudscraper.create_scraper()
    url_jornada = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🚀 Ejecutando según tu script original...")
    
    try:
        r = scraper.get(url_jornada)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        lista_final = []
        progreso = st.progress(0)

        for i, link in enumerate(links[:6]): # Prueba con 6 partidos
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # --- AQUÍ ESTÁ TU LÓGICA EXACTA ---
            # Buscamos los contenedores de jugadores de la alineación
            jugadores_html = soup_p.find_all('div', class_='player-info') or soup_p.find_all('tr', class_='player-row')
            
            for j_html in jugadores_html:
                try:
                    # Buscamos nombre y nota como haces en tu .txt
                    nombre_tag = j_html.find(class_='name')
                    # Tu script busca específicamente estas clases para la puntuación
                    nota_tag = j_html.find(class_='rating-box') or j_html.find(class_='num') or j_html.find(class_='rating')
                    
                    if nombre_tag and nota_tag:
                        nombre_w = nombre_tag.get_text(strip=True)
                        nota_w = nota_tag.get_text(strip=True).replace(',', '.')
                        
                        # Cruce con Excel
                        n_clean_w = limpiar_nombre_manel(nombre_w)
                        match = df_excel[df_excel['nombre_clean'] == n_clean_w]
                        
                        lista_final.append({
                            'Jugador': nombre_w,
                            'Nota': float(nota_w) if nota_w else 0.0,
                            'Contrato': match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO",
                            'Puesto': match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        })
                except:
                    continue
            
            progreso.progress((i + 1) / 6)
            time.sleep(0.3)

        return pd.DataFrame(lista_final)

    except Exception as e:
        st.error(f"Error siguiendo el script: {e}")
        return pd.DataFrame()

# --- APP ---
st.title("🛡️ Scouting Nàstic (Lógica Original)")

df_ex = cargar_excel()

if st.button("🔍 COMENZAR SCRAPING"):
    if not df_ex.empty:
        res = ejecutar_scraper_fiel(df_ex)
        if not res.empty:
            res = res.sort_values(by='Nota', ascending=False).drop_duplicates('Jugador')
            
            st.subheader("🌟 Top 11 de la Jornada")
            st.table(res.head(11))
            
            st.subheader("📋 Datos Totales")
            st.dataframe(res)
        else:
            st.error("No se han encontrado datos. Revisa si en BeSoccer los jugadores ya tienen nota asignada.")
    else:
        st.error("No se pudo cargar el Excel.")
