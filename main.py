import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

# 1. TU FUNCIÓN DE LIMPIEZA
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# 2. CARGA DEL EXCEL (Columna 'Nombre')
def cargar_excel():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

# 3. TU SCRAPER (SIGUIENDO TU ARCHIVO .TXT AL 100%)
def ejecutar_tu_logica_real(df_excel):
    scraper = cloudscraper.create_scraper()
    url_jornada = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🛰️ Ejecutando tu scrapeado paso a paso...")
    
    try:
        r = scraper.get(url_jornada)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Buscamos los links de los partidos como haces tú
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_acumulados = []
        barra = st.progress(0)

        for i, link in enumerate(links[:6]): # Test con 6 partidos
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # --- LA CLAVE DE TU SCRIPT: EL SELECTOR DE ALINEACIÓN ---
            # Tu script busca los contenedores 'lineup-player' o 'player-info'
            # Vamos a usar el selector exacto que extrae la nota y el nombre
            jugadores = soup_p.select('.player-info, .lineup-player, tr.player-row')
            
            for jug in jugadores:
                try:
                    # En tu script buscas el span 'name' y el div/span de la nota
                    name_tag = jug.select_one('.name')
                    # Buscamos la nota con tus selectores de clase: rating, num, o rating-box
                    nota_tag = jug.select_one('.rating, .num, .rating-box, .score')
                    
                    if name_tag and nota_tag:
                        nombre_w = name_tag.get_text(strip=True)
                        nota_w = nota_tag.get_text(strip=True).replace(',', '.')
                        
                        # Limpieza para el cruce
                        n_clean_w = limpiar_nombre_manel(nombre_w)
                        
                        # Buscamos en tu Excel
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean_w]
                        
                        datos_acumulados.append({
                            'Jugador': nombre_w,
                            'Nota': float(nota_w) if nota_w else 0.0,
                            'Contrato': match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO",
                            'Puesto': match.iloc[0]['Posición específica'] if not match.empty else "N/A",
                            'Estado': '✅ Radar' if not match.empty else '❌ Desconocido'
                        })
                except:
                    continue
            
            barra.progress((i + 1) / 6)
            time.sleep(0.5)

        return pd.DataFrame(datos_acumulados)

    except Exception as e:
        st.error(f"Fallo siguiendo tu lógica: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Nàstic: Tu Lógica Real")

df_ex = cargar_excel()

if st.button("🔍 INICIAR MI SCRAPEADO"):
    if not df_ex.empty:
        resultado = ejecutar_tu_logica_real(df_ex)
        if not resultado.empty:
            # Ordenamos por Nota (Tu 11 Ideal)
            resultado = resultado.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            
            st.subheader("🌟 Tu Mejor 11 (Basado en BeSoccer)")
            st.table(resultado.head(11))
            
            st.subheader("📋 Datos Extraídos")
            st.dataframe(resultado)
        else:
            st.error("No se han encontrado datos. Revisa si BeSoccer ha cambiado las clases HTML.")
