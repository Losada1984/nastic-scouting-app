import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata

# --- 1. FUNCIÓN DE LIMPIEZA DE NOMBRES ---
def normalizar_nombre(texto):
    if not texto or pd.isna(texto): return ""
    # Quitar tildes, caracteres raros y pasar a minúsculas
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Usando 'nom_complet') ---
def cargar_excel_manel():
    try:
        # Cargamos la pestaña de Primera RFEF
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        
        # Mapeamos tus columnas reales
        if 'nom_complet' in df.columns:
            df.rename(columns={'nom_complet': 'Jugador_Excel'}, inplace=True)
        
        # Mapeamos vencimiento si existe
        if 'vencimiento_contrato' in df.columns:
            df.rename(columns={'vencimiento_contrato': 'Contrato'}, inplace=True)
            
        return df
    except Exception as e:
        st.error(f"Error cargando el Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER DE PRUEBA (Jornada 1) ---
def ejecutar_prueba_j1(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL de la Jornada 1 del Grupo 1
    url_j1 = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🛰️ Conectando con BeSoccer: Jornada 1 - Grupo 1...")
    
    try:
        r = scraper.get(url_j1)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Buscamos los links de los partidos
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_web = []
        # Analizamos los primeros 5 partidos para encontrar coincidencias
        for link in links[:5]:
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            # Buscamos jugadores en las filas de alineación
            filas = soup_p.select('.player-row, .lineup-player')
            for fila in filas:
                name_tag = fila.find('span', class_='name')
                nota_tag = fila.find('div', class_='rating')
                
                if name_tag:
                    datos_web.append({
                        'Nombre_Web': name_tag.get_text(strip=True),
                        'Nota': nota_tag.get_text(strip=True) if nota_tag else "5.0"
                    })
        
        df_web = pd.DataFrame(datos_web).drop_duplicates()
        
        # --- EL CRUCE (MERGE) ---
        df_excel['name_clean'] = df_excel['Jugador_Excel'].apply(normalizar_nombre)
        df_web['name_clean'] = df_web['Nombre_Web'].apply(normalizar_nombre)
        
        resultados = []
        for _, row_e in df_excel.iterrows():
            # Buscamos si el nombre del Excel está en la Web o viceversa
            match = df_web[df_web['name_clean'].str.contains(row_e['name_clean'], na=False) | 
                           df_web['name_clean'].apply(lambda x: row_e['name_clean'] in x)]
            
            if not match.empty:
                for _, row_w in match.iterrows():
                    resultados.append({
                        'Jugador': row_e['Jugador_Excel'],
                        'Nota J1': row_w['Nota'],
                        'Vencimiento': row_e.get('Contrato', 'Sin fecha'),
                        'Posición': row_e.get('posicion_especifica', 'N/A')
                    })
        
        return pd.DataFrame(resultados).drop_duplicates()

    except Exception as e:
        st.error(f"Fallo en el Scraper: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🧪 Prueba de Cruce: BeSoccer ⚔️ Excel")

df_ex = cargar_excel_manel()

if st.button("🚀 LANZAR PRUEBA JORNADA 1"):
    if df_ex.empty:
        st.error("No se pudo leer el Excel. Revisa el nombre del archivo y la pestaña.")
    else:
        final = ejecutar_prueba_j1(df_ex)
        
        if not final.empty:
            st.success(f"✅ ¡Éxito! Se han cruzado {len(final)} jugadores de tu lista.")
            
            # Tabla estilizada
            st.dataframe(final, use_container_width=True)
            
            # Ejemplo visual de ficha
            st.subheader("🎴 Vista previa de Scouting")
            for _, r in final.head(3).iterrows():
                st.markdown(f"""
                <div style="background-color:#1a1a1a; padding:20px; border-radius:10px; border-left:8px solid #8b0000; margin-bottom:10px;">
                    <h3 style="margin:0; color:#8b0000;">{r['Jugador']}</h3>
                    <p style="font-size:1.2em; margin:5px 0;">📅 Contrato hasta: <b style="color:#ffd700;">{r['Vencimiento']}</b></p>
                    <p style="margin:0;">📊 Rendimiento J1: <b>{r['Nota J1']}</b> | 📍 Posición: {r['Posición']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Scrapeo realizado pero 0 coincidencias. Revisa si los nombres en 'nom_complet' son muy distintos a los de BeSoccer.")
