import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata

# --- 1. TU LÓGICA DE LIMPIEZA (Exacta a tus archivos .txt) ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    # Normalizar para quitar acentos (NFD separa la letra del acento)
    texto = unicodedata.normalize('NFD', str(texto))
    texto = "".join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL ---
def cargar_excel():
    try:
        # Cargamos Primera RFEF
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        
        # Verificamos si existe 'nom_complet'
        if 'nom_complet' in df.columns:
            # Creamos la versión limpia para el cruce
            df['nombre_clean'] = df['nom_complet'].apply(limpiar_nombre_manel)
        else:
            st.error(f"No encuentro 'nom_complet'. Columnas: {list(df.columns)}")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER DE PRUEBA JORNADA 1 ---
def probar_cruce_j1(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL Grupo 1 - Jornada 1
    url = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🔄 Aplicando tu lógica de limpieza de acentos y cruce...")
    
    try:
        r = scraper.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        datos_web = []
        # Escaneamos los primeros partidos para validar
        for link in links[:5]:
            r_p = scraper.get(link)
            soup_p = BeautifulSoup(r_p.text, 'html.parser')
            
            # Buscamos jugadores en las filas (titulares/suplentes)
            filas = soup_p.find_all('tr', class_=lambda x: x and 'player' in x)
            for fila in filas:
                name_tag = fila.find('span', class_='name')
                nota_tag = fila.find('div', class_='rating')
                
                if name_tag:
                    nombre_raw = name_tag.get_text(strip=True)
                    datos_web.append({
                        'nombre_original_web': nombre_raw,
                        'nombre_clean_web': limpiar_nombre_manel(nombre_raw),
                        'nota': nota_tag.get_text(strip=True) if nota_tag else "5.0"
                    })
        
        df_web = pd.DataFrame(datos_web).drop_duplicates('nombre_clean_web')

        # --- EL CRUCE (Igual que en tus notebooks) ---
        resultados = []
        for _, row_e in df_excel.iterrows():
            nombre_e = row_e['nombre_clean']
            
            # Buscamos si el nombre limpio del excel está contenido en el de la web
            # Ejemplo: 'aitor bunuel' contenido en 'aitor bunuel redrado'
            match = df_web[df_web['nombre_clean_web'].str.contains(nombre_e, na=False)]
            
            if not match.empty:
                for _, row_w in match.iterrows():
                    resultados.append({
                        'Jugador Excel': row_e['nom_complet'],
                        'Jugador Web': row_w['nombre_original_web'],
                        'Nota J1': row_w['nota'],
                        'Contrato': row_e.get('vencimiento_contrato', 'N/A'),
                        'Puesto': row_e.get('posicion_especifica', 'N/A')
                    })
        
        return pd.DataFrame(resultados)

    except Exception as e:
        st.error(f"Fallo Scraper: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Test Cruce Manel (Limpieza de Acentos)")

df_ex = cargar_excel()

if not df_ex.empty:
    if st.button("🚀 LANZAR PRUEBA J1"):
        res = probar_cruce_j1(df_ex)
        
        if not res.empty:
            st.success(f"✅ ¡Cruce conseguido! {len(res)} jugadores detectados.")
            st.dataframe(res)
            
            # Ficha de ejemplo
            j = res.iloc[0]
            st.markdown(f"""
            <div style="background-color:#1a1a1a; padding:20px; border-radius:10px; border-left:8px solid #8b0000;">
                <h3 style="color:#8b0000; margin:0;">{j['Jugador Excel']}</h3>
                <p>📍 {j['Puesto']} | ⭐ Nota J1: <b>{j['Nota J1']}</b></p>
                <p style="font-size:1.2em;">📅 Contrato: <b style="color:#ffd700;">{j['Contrato']}</b></p>
                <p style="font-size:0.8em; color:gray;">Detectado en web como: {j['Jugador Web']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No hay coincidencias. Puede que los jugadores de tu lista de Primera RFEF no jugaran en los primeros partidos de la J1.")
