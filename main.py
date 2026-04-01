import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

# --- 1. TU FUNCIÓN DE LIMPIEZA (Fiel a tu script) ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Columnas: Nombre, Contrato_Hasta) ---
def cargar_excel():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error cargando tu Excel: {e}")
        return pd.DataFrame()

# --- 3. TU ESCRAPEO (Copiado de las celdas de tu .txt) ---
def ejecutar_tu_script(df_excel):
    scraper = cloudscraper.create_scraper()
    # Usamos la URL de resultados que usa tu script
    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🚀 Ejecutando TU ESCRAPEO al pie de la letra...")
    
    try:
        r = scraper.get(url_base)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Localizamos los links de partidos (match-link) como haces tú
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_jugadores = []
        barra = st.progress(0)

        for i, link in enumerate(links[:6]): # Test con 6 partidos
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # --- SELECTORES EXACTOS DE TU ARCHIVO .TXT ---
            # Tu script busca los bloques de información del jugador en la alineación
            jugadores_html = soup_p.find_all('div', class_='player-info')
            
            for j in jugadores_html:
                try:
                    # Buscamos 'name' y 'rating'/'num' como en tu celda de código
                    name_tag = j.find(class_='name')
                    # Buscamos la nota en las clases que tú definiste
                    nota_tag = j.find(class_='rating') or j.find(class_='num') or j.find(class_='rating-box')
                    
                    if name_tag and nota_tag:
                        nombre_web = name_tag.get_text(strip=True)
                        # Tu limpieza de nota (coma por punto)
                        nota_web = nota_tag.get_text(strip=True).replace(',', '.')
                        
                        # CRUCE CON TU EXCEL
                        n_clean_w = limpiar_nombre_manel(nombre_web)
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean_w]
                        
                        # Extraemos los datos del Excel si hay match
                        vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                        puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        
                        datos_jugadores.append({
                            'Jugador': nombre_web,
                            'Nota': float(nota_web) if nota_web else 0.0,
                            'Contrato': vencimiento,
                            'Puesto': puesto,
                            'Origen': '✅ Excel' if not match.empty else '🕵️ Descubrimiento'
                        })
                except:
                    continue
            
            barra.progress((i + 1) / 6)
            time.sleep(0.5)

        return pd.DataFrame(datos_jugadores)

    except Exception as e:
        st.error(f"Fallo siguiendo tu lógica: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Sistema Scouting (Lógica Manel)")

df_ex = cargar_excel()

if st.button("🔍 LANZAR SCRAPEO"):
    if not df_ex.empty:
        res = ejecutar_tu_script(df_ex)
        if not res.empty:
            # Eliminamos duplicados y ordenamos por la nota (tus mejores 11)
            res = res.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            
            st.subheader("🌟 Tu 11 Ideal (Basado en Notas de BeSoccer)")
            st.table(res.head(11))
            
            st.subheader("📋 Informe Completo")
            st.dataframe(res)
        else:
            st.error("No se extrajeron datos. Revisa que las notas estén visibles en las cajas 'player-info' de BeSoccer.")
