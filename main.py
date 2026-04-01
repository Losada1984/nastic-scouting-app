import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata

# --- FUNCIÓN DE LIMPIEZA IDENTICA A TUS TXT ---
def normalizar_nombre(texto):
    if not texto: return ""
    # Quitar tildes y poner en minúsculas
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

def cargar_excel_manel():
    try:
        # Cargamos el Excel que tienes en GitHub
        # Intentamos leer la pestaña de Primera RFEF
        df = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
        
        # Mapeamos tus columnas a lo que espera el scraper
        # Si en tu Excel la columna se llama 'nom_esportiu', la pasamos a 'Jugador'
        if 'nom_esportiu' in df.columns:
            df.rename(columns={'nom_esportiu': 'Jugador'}, inplace=True)
        elif 'Nombre' in df.columns:
            df.rename(columns={'Nombre': 'Jugador'}, inplace=True)
            
        # Aseguramos que existe la columna de contrato
        if 'vencimiento_contrato' in df.columns:
            df.rename(columns={'vencimiento_contrato': 'Contrato'}, inplace=True)
            
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return pd.DataFrame()

# --- SCRAPER DE PRUEBA ---
def test_jornada_1_real(df_excel):
    scraper = cloudscraper.create_scraper()
    # URL real de la Jornada 1 que aparece en tus TXT
    url = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info(f"🛰️ Conectando con BeSoccer: Jornada 1...")
    
    try:
        r = scraper.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Buscamos todos los partidos de la jornada
        partidos = soup.find_all('a', class_='match-link')
        links = [p['href'] for p in partidos]
        
        datos_encontrados = []
        
        # Analizamos los 2 primeros partidos para la prueba
        for link in links[:2]:
            st.write(f"📖 Leyendo acta del partido: {link.split('/')[-1]}")
            res_p = scraper.get(link)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # Buscamos los jugadores en la tabla de alineaciones (clase player-row en BeSoccer)
            filas = soup_p.find_all('tr', class_='player-row')
            for fila in filas:
                # Extraer nombre y nota
                name_tag = fila.find('span', class_='name')
                nota_tag = fila.find('div', class_='rating')
                
                if name_tag:
                    nombre_web = name_tag.get_text(strip=True)
                    nota_web = nota_tag.get_text(strip=True) if nota_tag else "5.0"
                    
                    datos_encontrados.append({
                        'Jugador': nombre_web,
                        'Nota': nota_web
                    })
        
        df_web = pd.DataFrame(datos_encontrados)
        
        # --- EL CRUCE MÁGICO ---
        # Creamos una columna temporal "join_name" normalizada en ambos lados
        df_excel['join_name'] = df_excel['Jugador'].apply(normalizar_nombre)
        df_web['join_name'] = df_web['Jugador'].apply(normalizar_nombre)
        
        # Intentamos el cruce (si el nombre de la web contiene el nombre de tu Excel o viceversa)
        resultados = []
        for _, row_w in df_web.iterrows():
            for _, row_e in df_excel.iterrows():
                # Si el nombre del excel está dentro del nombre largo de la web (o al revés)
                if row_e['join_name'] in row_w['join_name'] or row_w['join_name'] in row_e['join_name']:
                    resultados.append({
                        'Jugador': row_w['Jugador'],
                        'Nota': row_w['Nota'],
                        'Contrato': row_e.get('Contrato', 'Sin datos'),
                        'Puesto': row_e.get('posicion_especifica', 'N/A')
                    })
        
        return pd.DataFrame(resultados).drop_duplicates()

    except Exception as e:
        st.error(f"Error en proceso: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🧪 Prueba de Cruce BeSoccer + Contratos")

df_contratos = cargar_excel_manel()

if st.button("🚀 PROBAR CRUCE JORNADA 1"):
    if df_contratos.empty:
        st.error("El Excel no se ha cargado correctamente.")
    else:
        final_df = test_jornada_1_real(df_contratos)
        
        if not final_df.empty:
            st.success(f"¡Cruce exitoso! Encontrados {len(final_df)} jugadores.")
            st.dataframe(final_df, use_container_width=True)
            
            # Ejemplo de la primera ficha
            j = final_df.iloc[0]
            st.markdown(f"""
            <div style="background-color:#1a1a1a; padding:20px; border-radius:15px; border:2px solid #8b0000;">
                <h3 style="color:#8b0000; margin-top:0;">{j['Jugador']}</h3>
                <p>⭐ Nota Jornada: <b>{j['Nota']}</b></p>
                <p>📝 Vencimiento Contrato: <b style="color:#ffd700;">{j['Contrato']}</b></p>
                <p>📍 Posición: {j['Puesto']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No hay coincidencias. Revisa si en la pestaña 'PRIMERA RFEF' del Excel hay jugadores que jugaran la Jornada 1.")
