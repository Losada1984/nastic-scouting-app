import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata

# --- 1. TU LÓGICA DE LIMPIEZA DE ACENTOS ---
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 2. CARGA DEL EXCEL ---
def cargar_excel_real():
    try:
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        if 'Nombre' in df.columns:
            df['nombre_clean_excel'] = df['Nombre'].apply(limpiar_nombre_manel)
        return df
    except Exception as e:
        st.error(f"Error Excel: {e}")
        return pd.DataFrame()

# --- 3. SCRAPER DEL 11 IDEAL (Muestra todo, coincida o no) ---
def obtener_once_ideal_completo(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL del Once Ideal de la Jornada 1
    url = "https://es.besoccer.com/competicion/once_ideal/primera_rfef/2026/jornada1"
    
    st.info("⭐ Extrayendo el ONCE IDEAL de BeSoccer...")
    
    try:
        r = scraper.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        once_data = []
        # Buscamos los bloques de jugadores del 11 ideal
        jugadores_once = soup.find_all('div', class_='name')
        
        for j in jugadores_once:
            nombre_web = j.get_text(strip=True)
            nombre_clean_web = limpiar_nombre_manel(nombre_web)
            
            # Buscamos si este jugador del 11 ideal está en tu Excel
            match_excel = df_excel[df_excel['nombre_clean_excel'] == nombre_clean_web]
            
            if not match_excel.empty:
                # JUGADOR CONOCIDO (Está en tu lista)
                row_e = match_excel.iloc[0]
                once_data.append({
                    'Jugador': nombre_web,
                    'Estado': '✅ EN RADAR',
                    'Contrato': row_e.get('Contrato_Hasta', 'Revisar'),
                    'Puesto': row_e.get('Posición específica', 'N/A'),
                    'Nota': 'ONCE IDEAL'
                })
            else:
                # JUGADOR NUEVO (No está en tu lista, pero es de los mejores)
                once_data.append({
                    'Jugador': nombre_web,
                    'Estado': '🔥 NUEVO TALENTO',
                    'Contrato': 'Desconocido',
                    'Puesto': 'Ver en Web',
                    'Nota': 'ONCE IDEAL'
                })
        
        return pd.DataFrame(once_data)

    except Exception as e:
        st.error(f"Fallo en Once Ideal: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🛡️ Scouting Nàstic: El 11 Ideal de la Jornada")

df_ex = cargar_excel_real()

if st.button("🚀 VER MEJOR 11 Y CRUZAR CONTRATOS"):
    res_once = obtener_once_ideal_completo(df_ex)
    
    if not res_once.empty:
        st.success(f"Encontrados los 11 jugadores top. ¡Cruza de datos completado!")
        
        # Mostramos la tabla total
        st.dataframe(res_once, use_container_width=True)
        
        # Separamos visualmente los nuevos de los conocidos
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📌 En tu Radar")
            conocidos = res_once[res_once['Estado'] == '✅ EN RADAR']
            if not conocidos.empty:
                for _, c in conocidos.iterrows():
                    st.success(f"**{c['Jugador']}** - Contrato: {c['Contrato']}")
            else:
                st.write("Ninguno de este 11 está en tu Excel aún.")

        with col2:
            st.subheader("🕵️‍♂️ No están en tu Excel")
            nuevos = res_once[res_once['Estado'] == '🔥 NUEVO TALENTO']
            for _, n in nuevos.iterrows():
                st.warning(f"**{n['Jugador']}** - ¡Fíchalo en tu Excel!")
    else:
        st.warning("No se pudo obtener el 11 ideal. BeSoccer puede estar actualizando los datos.")
