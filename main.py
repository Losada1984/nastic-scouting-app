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
        # Usamos 'Nombre' que es la columna que Python detecta en tu Excel
        if 'Nombre' in df.columns:
            df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER CON EXTRACCIÓN DE NOTA SEGURA ---
def obtener_jugadores_jornada(df_excel):
    scraper = cloudscraper.create_scraper()
    url_resultados = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🏟️ Analizando partidos y extrayendo notas...")
    
    try:
        r = scraper.get(url_resultados)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        todos_los_jugadores = []
        progreso = st.progress(0)
        
        for i, link in enumerate(links[:5]): # Probamos con los primeros 5 para validar
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            # Buscamos las filas de jugadores
            filas = soup_p.find_all('tr', class_=lambda x: x and 'player' in x)
            
            for fila in filas:
                name_tag = fila.find('span', class_='name')
                # Buscamos la nota en el div con clase 'rating' o 'num'
                nota_tag = fila.find('div', class_='rating') or fila.find('span', class_='rating')
                
                if name_tag:
                    nombre_web = name_tag.get_text(strip=True)
                    
                    # --- EXTRACCIÓN SEGURA DE LA NOTA ---
                    try:
                        if nota_tag:
                            nota_texto = nota_tag.get_text(strip=True).replace(',', '.')
                            # Si la nota es un guion o está vacía, ponemos 0.0
                            nota_final = float(nota_texto) if nota_texto not in ['', '-', None] else 0.0
                        else:
                            nota_final = 0.0
                    except:
                        nota_final = 0.0
                    
                    # Cruce con tu Excel
                    nombre_clean_web = limpiar_nombre_manel(nombre_web)
                    match = df_excel[df_excel['nombre_clean_excel'] == nombre_clean_web]
                    
                    # Si no hay match exacto, probamos si el nombre está contenido
                    if match.empty:
                        match = df_excel[df_excel['nombre_clean_excel'].str.contains(nombre_clean_web, na=False)]

                    vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                    puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                    
                    todos_los_jugadores.append({
                        'Jugador': nombre_web,
                        'Calificacion': nota_final, # Cambiamos el nombre interno para evitar conflictos
                        'Contrato': vencimiento,
                        'Puesto': puesto,
                        'Estado': '✅ Radar' if not match.empty else '🔥 Nuevo'
                    })
            
            progreso.progress((i + 1) / 5)
            time.sleep(0.1)
            
        df_final = pd.DataFrame(todos_los_jugadores)
        if not df_final.empty:
            # Ordenamos por la nota (Calificacion)
            return df_final.sort_values(by='Calificacion', ascending=False)
        return df_final

    except Exception as e:
        st.error(f"Error en el proceso de notas: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("📊 Scouting Nàstic: Rendimiento J1")

df_ex = cargar_excel_real()

if st.button("🚀 INICIAR ESCANEO DE NOTAS"):
    res = obtener_jugadores_jornada(df_ex)
    
    if not res.empty:
        st.subheader("⭐ Mejores Jugadores Detectados")
        # Mostramos los 11 mejores como tu "Once Ideal" personalizado
        st.table(res.head(11))
        
        st.subheader("📋 Lista Completa de la Jornada")
        st.dataframe(res)
    else:
        st.warning("No se pudieron extraer datos. Comprueba la conexión con BeSoccer.")
