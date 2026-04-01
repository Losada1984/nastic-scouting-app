import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata

# --- 1. TU LÓGICA DE LIMPIEZA DE ACENTOS ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    # Quitar acentos (como en tus archivos .txt)
    texto = unicodedata.normalize('NFD', str(texto))
    texto = "".join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL (Usando las columnas reales que detecta tu App) ---
def cargar_excel_real():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        
        # COLUMNAS DETECTADAS SEGÚN TU ERROR:
        # Nombre del jugador: 'Nombre'
        # Vencimiento: 'Contrato_Hasta'
        # Posición: 'Posición específica'
        
        if 'Nombre' in df.columns:
            df['nombre_clean'] = df['Nombre'].apply(limpiar_nombre_manel)
        else:
            st.error(f"⚠️ Sigo sin encontrar 'Nombre'. Columnas que veo: {list(df.columns)}")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        st.error(f"❌ Error al leer Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER DE PRUEBA (Jornada 1 - Grupo 1) ---
def test_jornada_1(df_excel):
    scraper = cloudscraper.create_scraper()
    url = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("📡 Escaneando alineaciones de BeSoccer (Jornada 1)...")
    
    try:
        r = scraper.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_web = []
        # Analizamos los primeros 6 partidos
        for link in links[:6]:
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            filas = soup_p.select('.player-row, .lineup-player')
            for fila in filas:
                name_tag = fila.find('span', class_='name')
                nota_tag = fila.find('div', class_='rating')
                
                if name_tag:
                    nombre_web = name_tag.get_text(strip=True)
                    datos_web.append({
                        'web_original': nombre_web,
                        'web_clean': limpiar_nombre_manel(nombre_web),
                        'nota': nota_tag.get_text(strip=True) if nota_tag else "5.0"
                    })
        
        df_web = pd.DataFrame(datos_web).drop_duplicates('web_clean')

        # --- CRUCE CON TU LÓGICA ---
        resultados = []
        for _, row_e in df_excel.iterrows():
            nom_e = row_e['nombre_clean']
            # Buscamos coincidencia (el del excel dentro del de la web)
            match = df_web[df_web['web_clean'].str.contains(nom_e, na=False)]
            
            if not match.empty:
                for _, row_w in match.iterrows():
                    resultados.append({
                        'Jugador': row_e['Nombre'],
                        'Nota J1': row_w['nota'],
                        'Vencimiento': row_e.get('Contrato_Hasta', 'N/A'),
                        'Puesto': row_e.get('Posición específica', 'N/A')
                    })
        
        return pd.DataFrame(resultados)

    except Exception as e:
        st.error(f"Fallo Scraper: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Test Cruce: Jornada 1 (Columnas Reales)")

df_ex = cargar_excel_real()

if not df_ex.empty:
    if st.button("🚀 EJECUTAR PRUEBA DE CRUCE"):
        res = test_jornada_1(df_ex)
        
        if not res.empty:
            st.success(f"✅ ¡Conseguido! {len(res)} jugadores cruzados.")
            st.dataframe(res, use_container_width=True)
            
            # Tarjeta del primer jugador
            j = res.iloc[0]
            st.markdown(f"""
            <div style="background-color:#1a1a1a; padding:20px; border-radius:10px; border-left:8px solid #8b0000; margin-top:20px;">
                <h3 style="color:#8b0000; margin:0;">{j['Jugador']}</h3>
                <p style="font-size:1.2em; margin:10px 0;">📅 Contrato hasta: <b style="color:#ffd700;">{j['Vencimiento']}</b></p>
                <p>📊 Nota BeSoccer: <b>{j['Nota J1']}</b> | 📍 {j['Puesto']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No hubo coincidencias. Prueba a revisar si los jugadores de tu lista jugaron la J1.")
