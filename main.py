import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

# --- 1. TU LÓGICA DE LIMPIEZA ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL ---
def cargar_excel_real():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        if 'Nombre' in df.columns:
            df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER BASADO EN TU CELDA DE CÓDIGO ---
def scrapear_jornada_manel(df_excel):
    scraper = cloudscraper.create_scraper()
    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🔍 Extrayendo datos según tu script original...")
    
    try:
        response = scraper.get(url_base)
        soup = BeautifulSoup(response.text, 'html.parser')
        match_links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_jugadores = []
        progreso = st.progress(0)

        # Recorremos los partidos como hace tu script
        for idx, link in enumerate(match_links[:6]): # Ajustado a 6 para la prueba
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            # Buscamos las filas de jugadores usando tu selector
            # Tu script busca 'tr' con clases de jugadores
            rows = soup_p.find_all('tr', class_=lambda x: x and 'player' in x)
            
            for row in rows:
                try:
                    name_tag = row.find('span', class_='name')
                    # Tu lógica de nota: busca 'rating' o 'num'
                    nota_tag = row.find('div', class_='rating') or row.find('span', class_='num') or row.find('div', class_='rating-box')
                    
                    if name_tag:
                        nombre_raw = name_tag.get_text(strip=True)
                        
                        # Extracción de nota idéntica a tu .txt
                        if nota_tag:
                            val_nota = nota_tag.get_text(strip=True).replace(',', '.')
                            try:
                                nota_final = float(val_nota)
                            except:
                                nota_final = 0.0
                        else:
                            nota_final = 0.0
                            
                        # CRUCE CON EXCEL
                        n_clean = limpiar_nombre_manel(nombre_raw)
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean]
                        
                        vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                        puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        
                        # Guardamos con los nombres de columna que tú usas al final
                        datos_jugadores.append({
                            'Jugador': nombre_raw,
                            'Nota': nota_final, # Aquí forzamos que se llame 'Nota'
                            'Vencimiento': vencimiento,
                            'Puesto': puesto,
                            'Radar': '✅' if not match.empty else '❌'
                        })
                except:
                    continue
            
            progreso.progress((idx + 1) / 6)
            time.sleep(0.3)

        return pd.DataFrame(datos_jugadores)

    except Exception as e:
        st.error(f"Error técnico en el bucle: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Nàstic (Lógica de tu Script)")

df_ex = cargar_excel_real()

if st.button("🚀 INICIAR ESCANEO"):
    if df_ex.empty:
        st.error("No hay datos en el Excel")
    else:
        resultado = scrapear_jornada_manel(df_ex)
        
        if not resultado.empty:
            # Ordenamos por Nota para ver el "Once Ideal"
            resultado = resultado.sort_values(by='Nota', ascending=False).reset_index(drop=True)
            
            st.subheader("🔝 Top Jugadores (Tu 11 Ideal)")
            st.table(resultado.head(11))
            
            st.subheader("📋 Todos los datos extraídos")
            st.dataframe(resultado)
        else:
            st.warning("No se encontraron jugadores con nota en estos partidos.")
