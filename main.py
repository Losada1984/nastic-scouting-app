import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

def cargar_excel_real():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        if 'Nombre' in df.columns:
            df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

def obtener_datos_partido(link, scraper):
    try:
        r_p = scraper.get(link)
        soup_p = BeautifulSoup(r_p.text, 'html.parser')
        jugadores_partido = []
        
        # BUSCAMOS TODAS LAS FILAS QUE PUEDAN CONTENER UN JUGADOR
        # Tu script usa selectores muy amplios, vamos a asegurar:
        filas = soup_p.find_all(['tr', 'div'], class_=lambda x: x and ('player' in x or 'item-player' in x))
        
        for fila in filas:
            name_tag = fila.find(['span', 'div'], class_='name')
            # BUSQUEDA MULTICLASE DE NOTA (Aquí estaba el fallo)
            nota_tag = (fila.find('div', class_='rating') or 
                        fila.find('span', class_='num') or 
                        fila.find('div', class_='rating-box') or
                        fila.find('p', class_='rating'))

            if name_tag:
                nombre = name_tag.get_text(strip=True)
                nota_texto = "0.0"
                if nota_tag:
                    # Limpiamos el texto de la nota como haces en tu script
                    nota_texto = nota_tag.get_text(strip=True).replace(',', '.')
                
                try:
                    nota_final = float(nota_texto)
                except:
                    nota_final = 0.0
                
                if nombre:
                    jugadores_partido.append({'Jugador_Web': nombre, 'Nota': nota_final})
        
        return jugadores_partido
    except:
        return []

def ejecutar_scouting(df_excel):
    scraper = cloudscraper.create_scraper()
    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🛰️ Iniciando barrido profundo de partidos...")
    
    try:
        r = scraper.get(url_base)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        total_jugadores = []
        progreso = st.progress(0)
        
        # Analizamos los partidos de 1 en 1
        for idx, link in enumerate(links[:8]): # Analizamos 8 partidos para asegurar datos
            datos = obtener_datos_partido(link, scraper)
            total_jugadores.extend(datos)
            progreso.progress((idx + 1) / 8)
            time.sleep(0.2)
            
        df_web = pd.DataFrame(total_jugadores).drop_duplicates()
        
        if df_web.empty:
            return pd.DataFrame()

        # CRUCE CON TU EXCEL
        resultados = []
        df_web['nombre_clean_web'] = df_web['Jugador_Web'].apply(limpiar_nombre_manel)
        
        for _, row_w in df_web.iterrows():
            # Buscamos si el de la web está en tu excel
            match = df_excel[df_excel['nombre_clean_excel'] == row_w['nombre_clean_web']]
            
            resultados.append({
                'Jugador': row_w['Jugador_Web'],
                'Nota': row_w['Nota'],
                'Contrato': match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO",
                'Puesto': match.iloc[0]['Posición específica'] if not match.empty else "Desconocido",
                'Origen': '✅ Excel' if not match.empty else '🕵️ Descubrimiento'
            })
            
        return pd.DataFrame(resultados).sort_values(by='Nota', ascending=False)

    except Exception as e:
        st.error(f"Fallo crítico: {e}")
        return pd.DataFrame()

# --- APP ---
st.title("🛡️ Radar Manel: 11 Ideal + Contratos")

df_ex = cargar_excel_real()

if st.button("🔍 ESCANEAR JORNADA 1"):
    res = ejecutar_scouting(df_ex)
    if not res.empty:
        st.subheader("🌟 Top 11 de la Jornada")
        st.table(res.head(11))
        
        st.subheader("📋 Lista Completa")
        st.dataframe(res)
    else:
        st.error("No se han podido leer las notas. Es posible que BeSoccer haya cambiado la estructura hoy mismo.")
