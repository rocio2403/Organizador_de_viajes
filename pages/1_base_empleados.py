# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
from supabase import create_client
from src.geolocalizacion import geocodificar_direccion 
from src.geolocalizacion import agregar_coordenadas

st.set_page_config(page_title="Base de Datos Empleados", layout="wide", page_icon="🗂️")

URL_SB = st.secrets["SUPABASE_URL"]
KEY_SB = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL_SB, KEY_SB)

st.title("🗂️ Base de Datos de Empleados")

@st.cache_data(ttl=600)
def get_data_empleados():
    try:
        res = supabase.table("empleados").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            cols = ["id_empleado", "nombre", "direccion", "localidad", "observaciones", "lat", "lon"]
            df = pd.DataFrame(columns=cols)
        else:
            for col in ['lat', 'lon']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return pd.DataFrame()

df_empleados = get_data_empleados()

st.info("💡 Si cambias la dirección, borra la Latitud/Longitud para que el sistema las recalcule al guardar.")

df_editado = st.data_editor(
    df_empleados, 
    num_rows="dynamic", 
    use_container_width=True,
    key="editor_empleados",
    column_config={
        "lat": st.column_config.NumberColumn("Latitud", format="%.4f"),
        "lon": st.column_config.NumberColumn("Longitud", format="%.4f"),
    }
)

if st.button("💾 Guardar y Recalcular Coordenadas Faltantes", type="primary"):
    try:
        with st.spinner("Procesando y buscando coordenadas faltantes..."):
            df_para_db = df_editado.copy()
            
            status_text = st.empty()
            
            for index, row in df_para_db.iterrows():
                if pd.isna(row['lat']) or pd.isna(row['lon']):
                    if row['direccion'] and row['localidad']:
                        status_text.info(f"🌍 Buscando coordenadas para: {row['nombre']}...")
                        
                        nueva_lat, nueva_lon = geocodificar_direccion(row['direccion'], row['localidad'])
                        
                        df_para_db.at[index, 'lat'] = nueva_lat
                        df_para_db.at[index, 'lon'] = nueva_lon
                        
                        time.sleep(1.5)
            
            status_text.empty()

            df_para_db['lat'] = pd.to_numeric(df_para_db['lat'], errors='coerce')
            df_para_db['lon'] = pd.to_numeric(df_para_db['lon'], errors='coerce')
            
            df_para_db = df_para_db.replace({pd.NA: None, float('nan'): None})
            
            text_cols = ["nombre", "direccion", "localidad", "observaciones"]
            for col in text_cols:
                if col in df_para_db.columns:
                    df_para_db[col] = df_para_db[col].fillna("")

            datos_dict = df_para_db.to_dict(orient='records')
            
            supabase.table("empleados").delete().neq("nombre", "VALOR_INEXISTENTE").execute()
            if datos_dict:
                supabase.table("empleados").insert(datos_dict).execute()

            st.cache_data.clear()
            st.success("✅ ¡Cambios guardados y coordenadas actualizadas!")
            st.rerun()

    except Exception as e:
        st.error(f"Error al guardar: {e}")