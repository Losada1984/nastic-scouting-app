import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

# --- 1. TU FUNCIÓN DE LIMPIEZA (Literal de tu txt) ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Usando tus nombres de columna) ---
def cargar_excel():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        # Preparamos el cruce con tu columna 'Nombre'
        df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return pd.DataFrame()

# --- 3. TU SCRAPER (Copiado de tus celdas de código) ---
def ejecutar_tu_logica_txt(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL específica que pediste
    url_jornada = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🚀 Ejecutando tu scrapeo exacto...")
    
    try:
        r = scraper.get(url_jornada)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Localizamos los links de partidos igual que en tu script
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_jugadores = []
        barra = st.progress(0)

        for i, link in enumerate(links[:10]): # Procesamos los 10 partidos del grupo
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # --- AQUÍ EMPIEZA TU BLOQUE DE CÓDIGO DEL TXT ---
            # Buscamos en las alineaciones (lineup)
            jugadores_html = soup_p.find_all('div', class_='player-info')
            
            for j in jugadores_html:
                try:
                    # Buscamos el nombre (clase name)
                    name_tag = j.find(class_='name')
                    # Buscamos la nota (clases rating, num o rating-box de tu script)
                    nota_tag = j.find(class_='rating') or j.find(class_='num') or j.find(class_='rating-box')
                    
                    if name_tag and nota_tag:
                        nombre_web = name_tag.get_text(strip=True)
                        # Tu limpieza de nota: replace(',', '.')
                        nota_web = nota_tag.get_text(strip=True).replace(',', '.')
                        
                        # --- CRUCE CON TU EXCEL ---
                        n_clean_w = limpiar_nombre_manel(nombre_web)
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean_w]
                        
                        vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                        puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        
                        datos_jugadores.append({
                            'Jugador': nombre_web,
                            'Nota': float(nota_web) if nota_web else 0.0,
                            'Contrato': vencimiento,
                            'Puesto': puesto,
                            'Estado': '✅ Radar' if not match.empty else '❌ Desconocido'
                        })
                except:
                    continue
            
            barra.progress((i + 1) / 10)
            time.sleep(0.5) # Tu delay de seguridad

        return pd.DataFrame(datos_jugadores)

    except Exception as e:
        st.error(f"Fallo siguiendo tu script: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Nàstic: Tu Script de BeSoccer")

df_ex = cargar_excel()

if st.button("🔍 LANZAR SCRAPEO"):
    if not df_ex.empty:
        res = ejecutar_tu_logica_txt(df_ex)
        if not res.empty:
            # Eliminamos duplicados y ordenamos por Nota
            res = res.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            
            st.subheader("🌟 Top 11 de la Jornada (Tus Datos)")
            st.table(res.head(11))
            
            st.subheader("📋 Informe Completo")
            st.dataframe(res)
        else:
            st.error("No se han extraído datos. Verifica que las notas ya estén publicadas en BeSoccer para esta jornada.")
    else:
        st.error("No se pudo cargar el archivo -COMPETICIONS.xlsx")
