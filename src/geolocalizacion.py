# -*- coding: utf-8 -*-

from geopy.geocoders import Nominatim

from time import sleep

geolocator = Nominatim(user_agent="organizador_viajes")

def normalizar_direccion(direccion, localidad):
    """
    Limpia y estandariza una dirección antes de geocodificarla.
    """
    out = f"{direccion}, {localidad}"

    out = out.strip()
    if "argentina" not in out.lower():
        out = f"{out}, Buenos Aires, Argentina"

    return out

contador_progreso = 0 
def geocodificar_direccion(direccion, localidad):
    """
    Convierte una dirección en coordenadas (latitud, longitud).
    """
    global contador_progreso
    contador_progreso += 1

    try:
        sleep(1.5)
        print(f" Geocodificando: {direccion}...", end=" ", flush=True)

        sleep(1.5)

        direccion_norm = normalizar_direccion(direccion, localidad)

        location = geolocator.geocode(direccion_norm, timeout=10)

        if location:
            print("✅") 
            return location.latitude, location.longitude
        else:
            print("⚠️ No encontrado")

    except Exception as e:
        print(f"❌ Error: {e}")

    return None, None

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

