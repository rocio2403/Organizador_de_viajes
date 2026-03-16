# -*- coding: utf-8 -*-

from geopy.distance import geodesic
import pandas as pd
import numpy as np

def distancia_a_planta(lat, lon, planta_lat, planta_lon):
    """
    Devuelve la distancia en metros entre un punto y la planta.
    Valida que las coordenadas sean números válidos.
    """
    if pd.isna(lat) or pd.isna(lon) or pd.isna(planta_lat) or pd.isna(planta_lon):
        return np.nan   
    return geodesic(
        (lat, lon),
        (planta_lat, planta_lon)
    ).meters

def agregar_distancia_planta(df, planta_lat, planta_lon):
    """
    Agrega una columna con la distancia a la planta (en metros).
    """
    df["distancia_planta"] = df.apply(
        lambda fila: distancia_a_planta(
            fila["lat"],
            fila["lon"],
            planta_lat,
            planta_lon
        ),
        axis=1
    )
    return df