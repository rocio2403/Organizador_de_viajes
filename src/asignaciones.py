# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from math import radians, sin, cos, sqrt, atan2


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos
    """
    R = 6371.0
    
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    
    a = np.sin(dphi / 2)**2 + \
        np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2)**2
    
    c = 2 * np.arcsin(np.sqrt(a))
    distancia = R * c
    return distancia



def asignar_empleados_a_choferes(df_empleados, df_choferes, tipo_horario, radio_max_km=6):
    """
    tipo_horario: 'horario_ingreso' o 'horario_egreso'
    radio_max_km: Distancia máxima que un chofer se desviaría para buscar a un 'aislado'
    """
    asignaciones = []
    empleados_libres = df_empleados.copy()
    
    choferes_ordenados = df_choferes[df_choferes['disponible'] == True].sort_values(by='distancia_planta', ascending=False)

    for _, chofer in choferes_ordenados.iterrows():
        capacidad = int(chofer['plazas'])
        if empleados_libres.empty: break
            
        horarios_posibles = empleados_libres[tipo_horario].mode()
        if horarios_posibles.empty: continue
        
        for hora_viaje in horarios_posibles:
            if capacidad <= 0: break
                
            candidatos = empleados_libres[empleados_libres[tipo_horario] == hora_viaje].copy()
            
            if candidatos.empty: continue

            viaje_empleados = []
            candidatos['dist_al_chofer'] = candidatos.apply(
                lambda x: haversine(chofer['lat'], chofer['lon'], x['lat'], x['lon']), axis=1
            )
            
            candidatos = candidatos[candidatos['dist_al_chofer'] <= radio_max_km].sort_values('dist_al_chofer')
            
            for _, emp in candidatos.iterrows():
                if capacidad > 0:
                    viaje_empleados.append(emp.to_dict())
                    empleados_libres = empleados_libres.drop(emp.name)
                    capacidad -= 1
            
            if viaje_empleados:
                asignaciones.append({
                    'id_chofer': chofer['id_chofer'],
                    'chofer': chofer['nombre'],
                    'horario': hora_viaje,
                    'empleados': viaje_empleados
                })
                 

    return asignaciones


def realizar_asignacion(df_empleados, df_choferes, columna_horario):
    """
    Ejecuta la Pasada 1 (7km) y la Pasada 2 (Rescate 20km) 
    y devuelve la lista de viajes final.
    """
    viajes = asignar_empleados_a_choferes(
        df_empleados, 
        df_choferes.copy(), 
        tipo_horario=columna_horario, 
        radio_max_km=7
    )

    ids_con_viaje = [emp['id_empleado'] for v in viajes for emp in v['empleados']]
    empleados_restantes = df_empleados[~df_empleados['id_empleado'].isin(ids_con_viaje)].copy()

    choferes_con_hueco = df_choferes.copy()
    for viaje in viajes:
        idx = choferes_con_hueco[choferes_con_hueco['id_chofer'] == viaje['id_chofer']].index
        choferes_con_hueco.loc[idx, 'plazas'] -= len(viaje['empleados'])

    choferes_con_hueco = choferes_con_hueco[choferes_con_hueco['plazas'] > 0]

    if not empleados_restantes.empty and not choferes_con_hueco.empty:
        viajes_rescate = asignar_empleados_a_choferes(
            empleados_restantes, 
            choferes_con_hueco, 
            tipo_horario=columna_horario, 
            radio_max_km=20
        )
        
        for v_rescate in viajes_rescate:
            encontrado = False
            for v_original in viajes:
                if v_original['id_chofer'] == v_rescate['id_chofer']:
                    v_original['empleados'].extend(v_rescate['empleados'])
                    encontrado = True
                    break
            if not encontrado:
                viajes.append(v_rescate)
                
    return viajes

def clusterizar_empleados(
    df,
    eps_metros=3000, 
    min_samples=3
):
    """
    Aplica DBSCAN sobre empleados usando lat/lon.
    
    - eps_metros: distancia máxima entre empleados (en metros)
    - min_samples: mínimo de empleados para formar un cluster
    
    Devuelve el DataFrame con una columna 'cluster'
    """
    RADIO_TIERRA = 6371000

    eps_radianes = eps_metros / RADIO_TIERRA

    coords = np.radians(
        df[["lat", "lon"]].values
    )

    db = DBSCAN(
        eps=eps_radianes,
        min_samples=min_samples,
        metric="haversine"
    )

    clusters = db.fit_predict(coords)

    df = df.copy()
    df["cluster"] = clusters

    return df



def distancia_metros(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en metros entre dos puntos geográficos
    usando la fórmula de Haversine (distancia en línea recta sobre la Tierra).
    """
    R = 6371000

    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
