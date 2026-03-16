# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import io
import time
from supabase import create_client
from src.geolocalizacion import agregar_coordenadas
from src.geolocalizacion import geocodificar_direccion
from src.asignaciones import haversine  

URL_SB = st.secrets["SUPABASE_URL"]
KEY_SB = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL_SB, KEY_SB)

st.set_page_config(page_title="Configuración Sistema", layout="wide")
st.title("⚙️ Configuración del Sistema")

st.subheader("1. Ubicación de la Empresa")

try:
    res_config = supabase.table("configuracion").select("*").eq("id", 1).execute()
    if res_config.data:
        config_actual = res_config.data[0]
    else:
        config_actual = {"direccion": "", "localidad": "", "lat": None, "lon": None}
except Exception:
    config_actual = {"direccion": "", "localidad": "", "lat": None, "lon": None}
with st.form("form_planta"):
    col1, col2 = st.columns(2)
    with col1:
        nueva_dir = st.text_input(
            "Dirección de la Planta", 
            value=config_actual.get("direccion", ""),
            help="Ejemplo: Av. Corrientes 123"  
        )
    with col2:
        nueva_loc = st.text_input(
            "Localidad", 
            value=config_actual.get("localidad", ""),
            help="Ejemplo: CABA o Moreno"     
        )
    guardar_planta = st.form_submit_button("Actualizar y Validar Ubicación")

if guardar_planta:
    if nueva_dir and nueva_loc:
        with st.spinner("Geocodificando planta..."):
            lat_p, lon_p = geocodificar_direccion(nueva_dir, nueva_loc)
            if lat_p and lon_p:
                supabase.table("configuracion").upsert({
                    "id": 1, 
                    "direccion": nueva_dir, 
                    "localidad": nueva_loc, 
                    "lat": lat_p, 
                    "lon": lon_p
                }).execute()
                st.success(f"✅ Planta guardada")
                st.rerun()
            else:
                st.error("❌ No se encontró la dirección de la planta.")

st.divider()

st.subheader("2. Gestión de Bases de Datos")

def generar_plantilla_excel(columnas):
    output = io.BytesIO()
    df_temp = pd.DataFrame(columns=columnas)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_temp.to_excel(writer, index=False, sheet_name='Plantilla')
    return output.getvalue()

cols_empleados = ["id_empleado", "nombre", "direccion", "localidad", "horario_ingreso", "horario_egreso", "observaciones"]
cols_choferes = ["id_chofer", "nombre", "direccion", "localidad", "disponible", "plazas", "observaciones"]

st.write("📥 **Plantillas para descargar:**")
st.write("Descargue y llene las plantillas con los datos correspondientes.Luego carguelas al sistema.")
col_d1, col_d2 = st.columns(2)
with col_d1:
    st.download_button("📥 Plantilla Empleados", data=generar_plantilla_excel(cols_empleados), file_name="empleados.xlsx")
with col_d2:
    st.download_button("📥 Plantilla Choferes", data=generar_plantilla_excel(cols_choferes), file_name="choferes.xlsx")

st.write("---")
st.write("🚀 **Carga de datos y cálculo de coordenadas**")
col_up1, col_up2 = st.columns(2)
with col_up1:
    emp_file = st.file_uploader("Subir Excel de Empleados", type=["xlsx"])
with col_up2:
    chof_file = st.file_uploader("Subir Excel de Choferes", type=["xlsx"])

if st.button("☁️ Procesar y Sincronizar bases de datos", type="primary"):
    if emp_file and chof_file:
        try:
            if config_actual["lat"] is None or config_actual["lon"] is None:
                st.error("❌ Error: Primero debes validar la ubicación de la Planta en el paso 1.")
                st.stop()
            
            lat_planta = float(config_actual["lat"])
            lon_planta = float(config_actual["lon"])

            df_e = pd.read_excel(emp_file).fillna("")
            df_c = pd.read_excel(chof_file).fillna("")

            lats_e, lons_e, dists_e = [], [], []
            placeholder_e = st.empty()
            for i, row in df_e.iterrows():
                placeholder_e.info(f"🌍 Procesando Empleado: **{row['nombre']}**")
                lat, lon = geocodificar_direccion(row['direccion'], row['localidad'])
                
                d_planta = haversine(lat, lon, lat_planta, lon_planta) if lat and lon else 0.0
                
                lats_e.append(lat)
                lons_e.append(lon)
                dists_e.append(round(d_planta, 2))
                time.sleep(0.4)
            
            df_e['lat'], df_e['lon'], df_e['distancia_planta'] = lats_e, lons_e, dists_e
            placeholder_e.empty()

            lats_c, lons_c, dists_c = [], [], []
            placeholder_c = st.empty()
            for i, row in df_c.iterrows():
                placeholder_c.info(f"🌍 Procesando Chofer: **{row['nombre']}**")
                lat, lon = geocodificar_direccion(row['direccion'], row['localidad'])
                
                d_planta = haversine(lat, lon, lat_planta, lon_planta) if lat and lon else 0.0
                
                lats_c.append(lat)
                lons_c.append(lon)
                dists_c.append(round(d_planta, 2))
                time.sleep(0.4)
            
            df_c['lat'], df_c['lon'], df_c['distancia_planta'] = lats_c, lons_c, dists_c
            placeholder_c.empty()

            if 'disponible' in df_c.columns:
                df_c['disponible'] = df_c['disponible'].apply(
                    lambda x: True if str(x).strip().lower() in ['sí', 'si', 'true', '1'] else False
                )
            
            for df in [df_e, df_c]:
                df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                df['distancia_planta'] = pd.to_numeric(df['distancia_planta'], errors='coerce').fillna(0.0)
                df.replace({pd.NA: None, float('nan'): None}, inplace=True)

            with st.spinner("🚀 Subiendo datos con distancias calculadas..."):
                supabase.table("empleados").delete().neq("nombre", "XYZ_NUNCA_EXISTIRA").execute()
                supabase.table("choferes").delete().neq("nombre", "XYZ_NUNCA_EXISTIRA").execute()
                
                datos_e = df_e.to_dict(orient='records')
                datos_c = df_c.to_dict(orient='records')

                if datos_e:
                    supabase.table("empleados").insert(datos_e).execute()
                if datos_c:
                    supabase.table("choferes").insert(datos_c).execute()

            st.cache_data.clear()
            st.success("✅ ¡Sincronización completa! Se han guardado los datos.")
            
        except Exception as e:
            st.error(f"❌ Error durante la sincronización: {e}")
    else:
        st.error("⚠️ Por favor, carga ambos archivos de Excel para continuar.")