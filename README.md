# Organizador de Viajes de Empleados

Sistema para automatizar la asignación de viajes de empleados a choferes de una empresa, teniendo en cuenta ubicación geográfica, horarios de ingreso, capacidad de los vehículos y preferencias de los pasajeros.

Este proyecto está pensado como una solución simple y escalable para tareas administrativas relacionadas con traslados de personal.

---

## Objetivos

Facilitar la organización de viajes diarios de empleados:

- Agrupando empleados que ingresan en el mismo horario
- Optimizando la cercanía geográfica entre puntos
- Asignando choferes disponibles con un máximo de 4 plazas
- Respetando preferencias de los pasajeros cuando sea posible

---

## Funcionalidades

- [ ] Carga de empleados desde archivo Excel
- [ ] Carga de choferes desde archivo Excel
- [ ] Geocodificación de direcciones
- [ ] Visualización de puntos en un mapa
- [ ] Cálculo de distancias entre empleados
- [ ] Asignación automática de choferes
- [ ] Interfaz gráfica simple para uso administrativo
- [ ] Exportación de resultados

---

## Herramientas utilizadas

- Python
- Pandas
- APIs de mapas (Google Maps / OpenStreetMap)
- Streamlit (interfaz de usuario)
- Folium / Mapas interactivos
- Git & GitHub


**Nota**La distancia se calcula inicialmente usando distancia geodésica (línea recta sobre la superficie terrestre) como aproximación. En una etapa posterior, el modelo puede extenderse para utilizar rutas reales mediante APIs de mapas














