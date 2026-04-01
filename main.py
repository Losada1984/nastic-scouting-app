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
        # Forzamos los nombres que detectamos antes
        if 'Nombre' in df.columns:
            df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER BASADO EN TU DOCUMENTO (Recorre partidos) ---
def obtener_jugadores_jornada(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL de resultados de la jornada (esta nunca falla)
    url_resultados = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🏟️ Recorriendo partidos como en tu script...")
    
    try:
        r = scraper.get(url_resultados)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Buscamos los links de cada partido (match-link)
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        todos_los_jugadores = []
        
        progreso = st.progress(0)
        for i, link in enumerate(links):
            # Entramos en cada partido como hace tu .txt
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            # Buscamos las filas de jugadores (titulares y suplentes)
            filas = soup_p.find_all('tr', class_=lambda x: x and 'player' in x)
            
            for fila in filas:
                name_tag = fila.find('span', class_='name')
                nota_tag = fila.find('div', class_='rating')
                equipo_tag = fila.find_previous('div', class_='team-name') # Intento de pillar equipo
                
                if name_tag and nota_tag:
                    nombre_web = name_tag.get_text(strip=True)
                    nota_web = nota_tag.get_text(strip=True)
                    
                    # Cruce con tu Excel
                    nombre_clean_web = limpiar_nombre_manel(nombre_web)
                    match = df_excel[df_excel['nombre_clean_excel'] == nombre_clean_web]
                    
                    vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                    puesto = match.iloc[0]['Posición específica'] if not match.empty else "Desconocido"
                    
                    todos_los_jugadores.append({
                        'Jugador': nombre_web,
                        'Nota': float(nota_web.replace(',', '.')),
                        'Contrato': vencimiento,
                        'Puesto': puesto,
                        'En_Radar': '✅' if not match.empty else '❌'
                    })
            
            progreso.progress((i + 1) / len(links))
            time.sleep(0.1) # Pausa suave
            
        df_final = pd.DataFrame(todos_los_jugadores)
        # Ordenamos por nota para sacar el "11 Ideal" real
        return df_final.sort_values(by='Nota', ascending=False)

    except Exception as e:
        st.error(f"Error siguiendo tu lógica: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Pro: Análisis de Jornada Completa")

df_ex = cargar_excel_real()

if st.button("🚀 INICIAR BARRIDO DE PARTIDOS (Lógica .txt)"):
    res = obtener_jugadores_jornada(df_ex)
    
    if not res.empty:
        st.subheader("⭐ Top Jugadores de la Jornada (Tu 11 Ideal)")
        # Mostramos los 11 mejores
        top_11 = res.head(11)
        st.table(top_11[['Jugador', 'Nota', 'Contrato', 'En_Radar']])
        
        st.subheader("📋 Todos los jugadores detectados")
        st.dataframe(res)
    else:
        st.warning("No se detectaron datos. Revisa la conexión.")
