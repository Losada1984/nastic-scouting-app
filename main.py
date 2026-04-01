import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time

# --- 1. TU FUNCIÓN DE LIMPIEZA (Literal de tu archivo) ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    # Quitar acentos y normalizar como haces tú
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Mantenemos tus nombres de columna) ---
def cargar_excel():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        # Preparamos el cruce con la columna 'Nombre'
        df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error cargando el Excel: {e}")
        return pd.DataFrame()

# --- 3. TU LÓGICA DE SCRAPEO (Copiada de las celdas de tu .txt) ---
def ejecutar_tu_propio_script(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL de la Jornada 1 del Grupo 1
    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("📡 Iniciando tu proceso de extracción...")
    
    try:
        r = scraper.get(url_base)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Localizamos los links de partidos igual que en tu script
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_jugadores = []
        barra_progreso = st.progress(0)

        # Recorremos los partidos (tu lógica de bucle)
        for i, link in enumerate(links):
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # --- BLOQUE DE EXTRACCIÓN FIEL A TU ARCHIVO ---
            # Buscamos en las alineaciones visuales (donde están las notas)
            jugadores_html = soup_p.find_all('div', class_='player-info')
            
            for j in jugadores_html:
                try:
                    # Buscamos el nombre (clase name)
                    name_tag = j.find(class_='name')
                    # Buscamos la nota (clases rating, num o rating-box de tu script)
                    nota_tag = j.find(class_='rating') or j.find(class_='num') or j.find(class_='rating-box')
                    
                    if name_tag and nota_tag:
                        nombre_web = name_tag.get_text(strip=True)
                        # Tu limpieza de nota: replace(',', '.') para convertir a número
                        nota_web = nota_tag.get_text(strip=True).replace(',', '.')
                        
                        # CRUCE CON TU EXCEL USANDO TU LIMPIEZA
                        n_clean_w = limpiar_nombre_manel(nombre_web)
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean_w]
                        
                        # Extraemos Contrato y Puesto si hay coincidencia
                        vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                        puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        
                        datos_jugadores.append({
                            'Jugador': nombre_web,
                            'Nota': float(nota_web) if nota_web else 0.0,
                            'Vencimiento': vencimiento,
                            'Puesto': puesto,
                            'Estado': '✅ Radar' if not match.empty else '❌ Desconocido'
                        })
                except:
                    continue
            
            barra_progreso.progress((i + 1) / len(links))
            time.sleep(0.5) # Tu delay de seguridad

        return pd.DataFrame(datos_jugadores)

    except Exception as e:
        st.error(f"Fallo siguiendo tu lógica: {e}")
        return pd.DataFrame()

# --- INTERFAZ STREAMLIT ---
st.title("🛡️ Sistema Scouting: Clon de tu Script")

df_ex = cargar_excel()

if st.button("🔍 LANZAR MI SCRAPEO"):
    if not df_ex.empty:
        res = ejecutar_tu_propio_script(df_ex)
        
        if not res.empty:
            # Eliminamos duplicados y ordenamos por Nota (tus mejores 11)
            res = res.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            
            st.subheader("🌟 Tu 11 Ideal de la Jornada")
            st.table(res.head(11))
            
            st.subheader("📋 Informe Completo")
            st.dataframe(res)
        else:
            st.error("No se han extraído datos. Es posible que el servidor de Streamlit esté bloqueado por BeSoccer.")
    else:
        st.error("No se pudo leer el archivo -COMPETICIONS.xlsx")
