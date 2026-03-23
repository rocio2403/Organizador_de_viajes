# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
import time
from supabase import create_client
from src.asignaciones import realizar_asignacion
from src.resultados import viajes_a_dataframe

st.set_page_config(
    page_title="Organizador de Transporte",
    page_icon="🚐",
    layout="wide",
)

# Conexión a Supabase
URL_SB = st.secrets["SUPABASE_URL"]
KEY_SB = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL_SB, KEY_SB)

@st.cache_data(ttl=300)
def obtener_datos_sistema():
    """Recupera empleados, choferes y planta desde Supabase sin recalcular nada."""
    try:
        # 1. Recuperar Empleados
        res_emp = supabase.table("empleados").select("*").execute()
        df_emp = pd.DataFrame(res_emp.data)
        
        # 2. Recuperar Choferes
        res_cho = supabase.table("choferes").select("*").execute()
        df_cho = pd.DataFrame(res_cho.data)
        
        # 3. Recuperar Configuración de Planta
        res_planta = supabase.table("configuracion").select("*").eq("id", 1).execute()
        
        # Validación de datos existentes
        if df_emp.empty or df_cho.empty or not res_planta.data:
            return None, None, None
            
        planta = res_planta.data[0]
        
        # Asegurar que lat/lon y distancia sean numéricos para el algoritmo
        for df in [df_emp, df_cho]:
            if 'lat' in df.columns:
                df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            if 'lon' in df.columns:
                df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        
        if 'distancia_planta' in df_emp.columns:
            df_emp['distancia_planta'] = pd.to_numeric(df_emp['distancia_planta'], errors='coerce')
        
        return df_emp, df_cho, planta
        
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return None, None, None

st.title("🚐 Gestión de Transporte Diario")

# Carga de datos inicial
df_maestro, df_choferes, config_planta = obtener_datos_sistema()

if df_maestro is not None:
    st.sidebar.success("✅ Sistema Conectado (Cloud)")
    st.sidebar.write(f"📍 Planta: {config_planta['direccion']}")
else:
    st.sidebar.error("⚠️ Configuración incompleta")
    st.warning("Por favor, carga los datos en la página de Configuración o agrega personal.")
    st.stop()

st.subheader("📝 Registro de Horarios Diarios")
st.info("Utiliza este panel para actualizar los horarios según la necesidad del día.")

with st.expander("➕ Cargar Horario Individual", expanded=True):
    col_nom, col_tipo, col_hora = st.columns([2, 1, 1])
    
    with col_nom:
        empleado_sel = st.selectbox(
            "Seleccionar Empleado", 
            options=df_maestro["nombre"].sort_values().tolist()
        )
    
    with col_tipo:
        tipo_horario = st.selectbox(
            "Evento", 
            options=["horario_ingreso", "horario_egreso"],
            format_func=lambda x: "Ingreso" if x == "horario_ingreso" else "Egreso"
        )
    
    with col_hora:
        horas_lista = [i for i in range(24)]
        hora_sel = st.selectbox("Hora (0-23)", options=horas_lista, index=8)

    if st.button("💾 Actualizar en Base de Datos", type="secondary"):
        try:
            supabase.table("empleados")\
                .update({tipo_horario: int(hora_sel)})\
                .eq("nombre", empleado_sel)\
                .execute()
            
            st.success(f"¡Listo! {empleado_sel} actualizado a las {hora_sel}:00hs.")
            st.cache_data.clear() 
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

st.divider()
st.subheader("🚗 Cálculo de Asignaciones")

col_f, col_a = st.columns([1, 2])
with col_f:
    fecha = st.date_input("Fecha de viaje", date.today(), format="DD/MM/YYYY")
with col_a:
    empleados_asisten = st.multiselect(
        "Confirmar personal para hoy:",
        options=df_maestro["nombre"].tolist(),
        default=df_maestro["nombre"].tolist(),
        help="Quita a los empleados que no asisten hoy."
    )

if st.button("CALCULAR ASIGNACIONES DE TRANSPORTE", type="primary"):
    if not empleados_asisten:
        st.error("Debes seleccionar al menos un empleado.")
    else:
        with st.spinner("Ejecutando algoritmo de asignación..."):
            try:
                # Filtrar solo los empleados que asisten hoy
                df_procesar = df_maestro[df_maestro["nombre"].isin(empleados_asisten)].copy()

                # Ejecutar lógica de asignación para Ingreso
                viajes_in = realizar_asignacion(df_procesar, df_choferes.copy(), "horario_ingreso")
                df_res_in = viajes_a_dataframe(viajes_in, "ingreso")

                # Ejecutar lógica de asignación para Egreso
                viajes_out = realizar_asignacion(df_procesar, df_choferes.copy(), "horario_egreso")
                df_res_out = viajes_a_dataframe(viajes_out, "egreso")

                # Unificar resultados
                df_final = pd.concat([df_res_in, df_res_out], ignore_index=True)

                st.success(f"✅ Asignación completa para {len(empleados_asisten)} empleados.")
                
                st.dataframe(df_final, use_container_width=True)

                # Opción de descarga
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Planilla de Viajes (CSV)",
                    data=csv,
                    file_name=f"viajes_{fecha}.csv",
                    mime="text/csv",
                )
            except Exception as e:
                st.error(f"Error durante el cálculo: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("Sistema de Logística v2.1")
