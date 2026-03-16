# -*- coding: utf-8 -*-
import os
import pandas as pd
from src.geolocalizacion import *



def agregar_coordenadas(df):
    """
    Agrega columnas de latitud y longitud al DataFrame de empleados
    usando la columna 'direccion'.
    """
    lats = []
    lons = []
    for direccion, localidad in zip(df["direccion"], df["localidad"]):
        lat, lon = geocodificar_direccion(direccion,localidad)

        lats.append(lat)
        lons.append(lon)

    df["lat"] = lats
    df["lon"] = lons
    return df

