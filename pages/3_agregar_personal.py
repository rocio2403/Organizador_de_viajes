# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from src.geolocalizacion import geocodificar_direccion 
from src.asignaciones import haversine  

st.set_page_config(page_title="Gestión de Personal", layout="wide", page_icon="➕")

URL_SB = st.secrets["SUPABASE_URL"]
KEY_SB = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL_SB, KEY_SB)

st.title("➕ Agregar Nuevo Personal")
st.write("Completa los datos para registrar un nuevo integrante en el sistema.")

try:
    res_config = supabase.table("configuracion").select("*").eq("id", 1).execute()
    if res_config.data:
        lat_planta = res_config.data[0].get("lat")
        lon_planta = res_config.data[0].get("lon")
    else:
        lat_planta, lon_planta = None, None
except Exception:
    lat_planta, lon_planta = None, None

tipo = st.radio("Tipo de personal", ["Empleado", "Chofer"])

with st.form("form_alta", clear_on_submit=True):
    nombre = st.text_input("Nombre Completo")
    direccion = st.text_input("Dirección (Ej: Av. Corrientes 1234)")
    localidad = st.text_input("Localidad")
    
    capacidad = 4
    disponible = True 
    
    if tipo == "Chofer":
        col1, col2 = st.columns(2)
        with col1:
            capacidad = st.number_input("Capacidad de pasajeros (Plazas)", min_value=1, max_value=50, value=4)
        with col2:
            opcion_disp = st.selectbox("Estado Inicial", ["Disponible", "No Disponible"])
            disponible = True if opcion_disp == "Disponible" else False
    
    enviado = st.form_submit_button("💾 Guardar en el Sistema", type="primary")

if enviado:
    if nombre and direccion and localidad:
        # Validación de seguridad: necesitamos la planta para el algoritmo
        if lat_planta is None or lon_planta is None:
            st.error("❌ Error: La ubicación de la Planta no está configurada. Ve a 'Configuración Sistema' primero.")
            st.stop()

        try:
            with st.spinner(f"Calculando ubicación y registrando {tipo.lower()}..."):
                lat, lon = geocodificar_direccion(direccion, localidad)
                
                if lat is None or lon is None:
                    st.error("⚠️ No se pudieron obtener las coordenadas. Revisa que la dirección sea correcta.")
                    st.stop()
                
                dist_p = haversine(lat, lon, lat_planta, lon_planta)
                
                tabla = "empleados" if tipo == "Empleado" else "choferes"
                id_col = "id_empleado" if tipo == "Empleado" else "id_chofer"
                
                res_id = supabase.table(tabla).select(id_col).order(id_col, desc=True).limit(1).execute()
                nuevo_id = (res_id.data[0][id_col] + 1) if res_id.data else 1

                nueva_data = {
                    id_col: nuevo_id,
                    "nombre": nombre,
                    "direccion": direccion,
                    "localidad": localidad,
                    "lat": lat, 
                    "lon": lon, 
                    "distancia_planta": round(dist_p, 2),
                    "observaciones": "Agregado individualmente desde la App"
                }
                
                if tipo == "Chofer":
                    nueva_data["plazas"] = capacidad
                    nueva_data["disponible"] = disponible

                supabase.table(tabla).insert(nueva_data).execute()
                
                st.cache_data.clear() # Limpiar caché para ver los cambios en las otras páginas
                st.success(f"✅ ¡{tipo} registrado con éxito! (Ubicado a {round(dist_p, 2)} km de la planta)")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Error al guardar en el sistema: {e}")
    else:
        st.error("⚠️ Por favor, completa nombre, dirección y localidad.")

st.info("💡 Al guardar desde aquí, los datos quedan protegidos en el sistema y se calcula automáticamente su distancia para optimizar las rutas.")
