# -*- coding: utf-8 -*-

import pandas as pd

def viajes_a_dataframe(viajes, tipo):
    """
    Convierte la lista de viajes en un DataFrame plano.
    tipo: 'ingreso' o 'egreso'
    """
    filas = []

    for viaje in viajes:
        for emp in viaje["empleados"]:
            filas.append({
                "tipo": tipo,
                "horario": emp["horario_ingreso"] if tipo == "ingreso" else emp["horario_egreso"],
                "id_chofer": viaje["id_chofer"],
                "chofer": viaje["chofer"],
                "id_empleado": emp["id_empleado"],
                "empleado": emp["nombre"]
            })

    df = pd.DataFrame(filas)

    return df.sort_values(["horario", "chofer"])
