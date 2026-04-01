import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata

# --- 1. TU LÓGICA DE LIMPIEZA DE ACENTOS (De tus .txt) ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    # Quitar acentos y pasar a minúsculas
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Columna: Nombre) ---
def cargar_excel_real():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        
        if 'Nombre' in df.columns:
            # Creamos la versión limpia para el cruce
            df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        else:
            st.error(f"⚠️ No encuentro la columna 'Nombre'. Columnas en Excel: {list(df.columns)}")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        st.error(f"❌ Error al leer Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER DE PRUEBA (Jornada 1 - Resultado: Jugador) ---
def test_jornada_1(df_excel):
    scraper = cloudscraper.create_scraper()
    url = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("📡 Escaneando BeSoccer... Buscando columna 'Jugador' para cruzar con 'Nombre'")
    
    try:
        r = scraper.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_web = []
        for link in links[:6]: # Analizamos los primeros partidos
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            filas = soup_p.select('.player-row, .lineup-player')
            for fila in filas:
                name_tag = fila.find('span', class_='name')
                nota_tag = fila.find('div', class_='rating')
                
                if name_tag:
                    nombre_raw = name_tag.get_text(strip=True)
                    datos_web.append({
                        'Jugador': nombre_raw, # Columna resultante del scrapeo
                        'web_clean': limpiar_nombre_manel(nombre_raw),
                        'Nota': nota_tag.get_text(strip=True) if nota_tag else "5.0"
                    })
        
        df_web = pd.DataFrame(datos_web).drop_duplicates('web_clean')

        # --- EL CRUCE (Merge de 'Nombre' con 'Jugador') ---
        resultados = []
        for _, row_e in df_excel.iterrows():
            nom_clean_e = row_e['nombre_clean_excel']
            
            # Buscamos si el nombre del excel está contenido en el de la web
            match = df_web[df_web['web_clean'].str.contains(nom_clean_e, na=False)]
            
            if not match.empty:
                for _, row_w in match.iterrows():
                    resultados.append({
                        'Nombre (Excel)': row_e['Nombre'],
                        'Jugador (Web)': row_w['Jugador'],
                        'Nota J1': row_w['Nota'],
                        'Contrato': row_e.get('Contrato_Hasta', 'N/A'),
                        'Puesto': row_e.get('Posición específica', 'N/A')
                    })
        
        return pd.DataFrame(resultados)

    except Exception as e:
        st.error(f"Fallo Scraper: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Cruce Final: Nombre (Excel) vs Jugador (Web)")

df_ex = cargar_excel_real()

if not df_ex.empty:
    if st.button("🚀 EJECUTAR CRUCE JORNADA 1"):
        res = test_jornada_1(df_ex)
        
        if not res.empty:
            st.success(f"✅ ¡Cruce realizado! {len(res)} jugadores encontrados.")
            st.dataframe(res, use_container_width=True)
            
            # Tarjeta de scouting del primer acierto
            j = res.iloc[0]
            st.markdown(f"""
            <div style="background-color:#1a1a1a; padding:20px; border-radius:10px; border-left:8px solid #8b0000; margin-top:20px;">
                <h3 style="color:#8b0000; margin:0;">{j['Nombre (Excel)']}</h3>
                <p style="font-size:1.1em; margin:10px 0;">📅 Contrato: <b style="color:#ffd700;">{j['Contrato']}</b></p>
                <p>📊 Nota J1: <b>{j['Nota J1']}</b> | 📍 {j['Puesto']}</p>
                <p style="font-size:0.8em; color:gray;">Match en BeSoccer: {j['Jugador (Web)']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No hubo coincidencias. Asegúrate de que los jugadores del Excel de 1ª RFEF jugaran en los primeros partidos de la Jornada 1.")
