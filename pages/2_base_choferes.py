# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
from supabase import create_client
from src.geolocalizacion import geocodificar_direccion 
st.set_page_config(page_title="Base de Datos Choferes", layout="wide", page_icon="🚐")

URL_SB = st.secrets["SUPABASE_URL"]
KEY_SB = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL_SB, KEY_SB)

st.title("🗂️ Base de Datos de Choferes")
st.write("Gestiona la información de los choferes y su disponibilidad directamente en el sistema.")

@st.cache_data(ttl=600)
def get_data_choferes():
    try:
        res = supabase.table("choferes").select("*").execute()
        df = pd.DataFrame(res.data)
        
        if df.empty:
            cols = ["id_chofer", "nombre", "direccion", "localidad", "disponible", "plazas", "observaciones", "lat", "lon"]
            df = pd.DataFrame(columns=cols)
        else:
            for col in ['lat', 'lon', 'plazas']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()
df_choferes = get_data_choferes()

st.info("💡 Si cambias la dirección, borra la Latitud/Longitud para que el sistema las recalcule al guardar.")

df_editado = st.data_editor(
    df_choferes, 
    num_rows="dynamic", 
    use_container_width=True,
    key="editor_choferes",
    column_config={
        "id_chofer": st.column_config.Column("ID"),
        "nombre": st.column_config.TextColumn("Nombre Chofer"),
        "disponible": st.column_config.CheckboxColumn("¿Está Disponible?"),
        "plazas": st.column_config.NumberColumn("Capacidad (Asientos)", min_value=1, max_value=50),
        "direccion": st.column_config.TextColumn("Dirección Base"),
        "lat": st.column_config.NumberColumn("Latitud", format="%.4f"),
        "lon": st.column_config.NumberColumn("Longitud", format="%.4f"),
    }
)

if st.button("💾 Guardar y Recalcular Coordenadas Faltantes", type="primary"):
    try:
        with st.spinner("Sincronizando y buscando coordenadas faltantes..."):
            df_para_db = df_editado.copy()
            
            status_placeholder = st.empty()
            
            for index, row in df_para_db.iterrows():
                if pd.isna(row.get('lat')) or pd.isna(row.get('lon')):
                    if row.get('direccion') and row.get('localidad'):
                        status_placeholder.info(f"🌍 Buscando ubicación para el chofer: **{row['nombre']}**")
                        
                        lat, lon = geocodificar_direccion(row['direccion'], row['localidad'])
                        
                        df_para_db.at[index, 'lat'] = lat
                        df_para_db.at[index, 'lon'] = lon
                        
                        time.sleep(1.5)
            
            status_placeholder.empty()
            if 'disponible' in df_para_db.columns:
                df_para_db['disponible'] = df_para_db['disponible'].fillna(False).astype(bool)

            if 'id_chofer' in df_para_db.columns:
                df_para_db['id_chofer'] = pd.to_numeric(df_para_db['id_chofer'], errors='coerce').fillna(0).astype(int)

            df_para_db = df_para_db.replace({pd.NA: None, float('nan'): None})
            
            text_cols = ["nombre", "direccion", "localidad", "observaciones"]
            for col in text_cols:
                if col in df_para_db.columns:
                    df_para_db[col] = df_para_db[col].fillna("")
            
            datos_dict = df_para_db.to_dict(orient='records')

            supabase.table("choferes").delete().neq("nombre", "VALOR_QUE_NUNCA_EXISTIRA").execute()
            
            if datos_dict:
                supabase.table("choferes").insert(datos_dict).execute()

            st.cache_data.clear()
            st.success("✅ ¡Base de datos de Choferes actualizada con coordenadas!")
            st.rerun()

    except Exception as e:
        st.error(f"Ocurrió un error al guardar: {e}")

if not df_choferes.empty:
    st.download_button(
        label="📥 Descargar lista de choferes (CSV)",
        data=df_choferes.to_csv(index=False).encode('utf-8'),
        file_name='choferes_sistema.csv',
        mime='text/csv'
    )