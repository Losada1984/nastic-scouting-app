import streamlit as st
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
import unicodedata
import time
import random

# 1. TU FUNCIÓN DE LIMPIEZA (TAL CUAL EN TU TXT)
def limpiar_nombre_manel(texto):
    if not texto or pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# 2. TU LÓGICA DE EXTRACCIÓN (ADAPTACIÓN DIRECTA)
def ejecutar_scouting_manel(df_excel):
    # Usamos un scraper que simula ser un navegador real para evitar el "bloqueo"
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # Cabeceras para que BeSoccer crea que somos un humano
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    url_base = "https://es.besoccer.com/competicion/resultados/primera_rfef/2026/grupo1/jornada1"
    
    st.info("🚀 Ejecutando tu lógica de escrapeo...")
    
    try:
        # Petición principal
        r = scraper.get(url_base, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', class_='match-link')]
        
        if not links:
            st.error("❌ BeSoccer no devuelve la lista de partidos (Bloqueo de IP).")
            return pd.DataFrame()

        datos_finales = []
        barra = st.progress(0)

        # Recorremos partidos como en tu script
        for i, link in enumerate(links[:8]): # Analizamos los primeros 8 para asegurar el 11
            time.sleep(random.uniform(1.0, 2.5)) # Pausa aleatoria "humana"
            
            res_p = scraper.get(link, headers=headers, timeout=20)
            soup_p = BeautifulSoup(res_p.text, 'html.parser')
            
            # --- TUS SELECTORES EXACTOS DEL TXT ---
            # Buscamos en 'player-info', que es donde tu script localiza la nota
            jugadores_html = soup_p.select('.player-info, .lineup-player')
            
            for j in jugadores_html:
                try:
                    # Buscamos nombre y nota con tus clases exactas
                    name_tag = j.find(class_='name')
                    # Buscamos la nota en 'rating', 'num' o 'rating-box' (como en tu celda 6)
                    nota_tag = j.find(class_=['rating', 'num', 'rating-box'])
                    
                    if name_tag and nota_tag:
                        nombre_w = name_tag.get_text(strip=True)
                        nota_w = nota_tag.get_text(strip=True).replace(',', '.')
                        
                        # Cruce con tu Excel
                        n_clean_w = limpiar_nombre_manel(nombre_w)
                        match = df_excel[df_excel['nombre_clean_excel'] == n_clean_w]
                        
                        vencimiento = match.iloc[0]['Contrato_Hasta'] if not match.empty else "NUEVO"
                        puesto = match.iloc[0]['Posición específica'] if not match.empty else "N/A"
                        
                        datos_finales.append({
                            'Jugador': nombre_web,
                            'Nota': float(nota_w) if nota_w else 0.0,
                            'Vencimiento': vencimiento,
                            'Puesto': puesto,
                            'Estado': '✅ Radar' if not match.empty else '🕵️ Fichaje'
                        })
                except:
                    continue
            
            barra.progress((i + 1) / 8)

        return pd.DataFrame(datos_finales)

    except Exception as e:
        st.error(f"Error técnico: {e}")
        return pd.DataFrame()

# --- CARGA E INTERFAZ ---
st.title("🛡️ Scouting Nàstic (Tu Script)")

try:
    df_ex = pd.read_excel("-COMPETICIONS.xlsx", sheet_name="PRIMERA RFEF")
    df_ex['nombre_clean_excel'] = df_ex['Nombre'].apply(limpiar_nombre_manel)
except:
    st.error("Fallo al cargar el Excel.")
    df_ex = pd.DataFrame()

if st.button("🔍 LANZAR ESCRAPEO"):
    if not df_ex.empty:
        resultado = ejecutar_scouting_manel(df_ex)
        if not resultado.empty:
            # Quitamos duplicados y ordenamos para el 11 IDEAL
            resultado = resultado.drop_duplicates('Jugador').sort_values(by='Nota', ascending=False)
            
            st.success("¡Éxito! Aquí tienes el Mejor 11 según tus notas:")
            st.table(resultado.head(11))
            st.dataframe(resultado)
        else:
            st.warning("No se han podido leer los datos. BeSoccer está bloqueando la conexión de Streamlit.")
