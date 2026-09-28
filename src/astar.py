"""Búsqueda A*: la ruta de menor distancia total, guiada por una heurística.

Heurística: h(n) = distancia en línea recta (Haversine) de n al destino. Nunca supera la
distancia por vía (es admisible), así que A* da la ruta óptima expandiendo menos nodos que UCS.
f(n) = g(n) + h(n): lo recorrido más lo que se estima que falta.

Uso:
    from astar import busqueda_a_estrella
    ruta, costo, orden, historial = busqueda_a_estrella(grafo, "Bima", "Centro Mayor")
Comprobar la heurística: python src/astar.py
"""

import heapq
from math import radians, sin, cos, asin, sqrt

try:
    from data.centros import NODOS
except ModuleNotFoundError:  # al ejecutarlo directamente desde src/
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.centros import NODOS

RADIO_TIERRA_KM = 6371.0


# ==============================================================================
#  HEURÍSTICA   h(n) = distancia en línea recta (Haversine) de n al destino, en km
#  Es admisible: ninguna ruta por calles es más corta que la línea recta.
# ==============================================================================
def distancia_linea_recta(nodo_a, nodo_b):
    """Distancia en línea recta en km (Haversine) entre dos centros."""
    lat_a, lon_a = NODOS[nodo_a][0], NODOS[nodo_a][1]
    lat_b, lon_b = NODOS[nodo_b][0], NODOS[nodo_b][1]

    lat_a, lon_a, lat_b, lon_b = map(radians, (lat_a, lon_a, lat_b, lon_b))
    d_lat = lat_b - lat_a
    d_lon = lon_b - lon_a

    a = sin(d_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(d_lon / 2) ** 2
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


# ==============================================================================
#  BÚSQUEDA A*   f(n) = g(n) + h(n)
# ==============================================================================
def busqueda_a_estrella(grafo, inicio, objetivo, heuristica=distancia_linea_recta):
    """Ruta de menor distancia total, guiada por la heurística.

    Devuelve (ruta, costo, orden_visita, historial_frontera) como UCS; costo es g, la
    distancia real, y el historial guarda (f, g, h, nodo) ordenado por f.
    """
    # Entradas (f, contador, g, ruta): f ordena la cola y g guarda el costo real.
    contador = 0
    h_inicio = heuristica(inicio, objetivo)
    frontera = [(h_inicio, contador, 0.0, [inicio])]

    # Como en UCS, un nodo se cierra al salir de la cola, no al entrar.
    expandidos = set()

    orden_visita = []
    historial_frontera = []

    while frontera:
        historial_frontera.append([
            (round(f, 1), round(g, 1), round(f - g, 1), ruta[-1])
            for f, _, g, ruta in sorted(frontera)
        ])

        f, _, g, ruta = heapq.heappop(frontera)
        nodo_actual = ruta[-1]

        if nodo_actual in expandidos:
            continue

        expandidos.add(nodo_actual)
        orden_visita.append(nodo_actual)

        # Prueba de objetivo al expandir: con h admisible, la ruta es la óptima.
        if nodo_actual == objetivo:
            return ruta, round(g, 1), orden_visita, historial_frontera

        for vecino, km in grafo.get(nodo_actual, {}).items():
            if vecino not in expandidos:
                contador += 1
                # f(n) = g(n) + h(n): aquí entra la HEURÍSTICA, sumada a lo recorrido.
                nuevo_g = g + km
                nuevo_f = nuevo_g + heuristica(vecino, objetivo)
                heapq.heappush(frontera, (nuevo_f, contador, nuevo_g, ruta + [vecino]))

    return None, float("inf"), orden_visita, historial_frontera


# ==============================================================================
#  COMPROBACIÓN DE LA HEURÍSTICA   (python src/astar.py)
# ==============================================================================
def es_admisible(grafo, heuristica=distancia_linea_recta):
    """Lista de (nodo, objetivo, h, costo real) donde h supera el costo real; vacía si es admisible."""
    from ucs import busqueda_costo_uniforme

    violaciones = []
    for objetivo in grafo:
        for nodo in grafo:
            if nodo == objetivo:
                continue
            _, real, _, _ = busqueda_costo_uniforme(grafo, nodo, objetivo)
            h = heuristica(nodo, objetivo)
            if h > real + 1e-9:
                violaciones.append((nodo, objetivo, round(h, 2), real))
    return violaciones


def es_consistente(grafo, heuristica=distancia_linea_recta):
    """Lista de (n, m, objetivo, h(n), costo + h(m)) donde h(n) > costo(n, m) + h(m); vacía si es consistente."""
    violaciones = []
    for objetivo in grafo:
        for nodo in grafo:
            for vecino, km in grafo[nodo].items():
                h_n = heuristica(nodo, objetivo)
                cota = km + heuristica(vecino, objetivo)
                if h_n > cota + 1e-9:
                    violaciones.append((nodo, vecino, objetivo, round(h_n, 2), round(cota, 2)))
    return violaciones


if __name__ == "__main__":
    from data.conexiones import construir_adyacencia

    grafo = construir_adyacencia()

    print("Verificando la heurística de línea recta sobre el grafo completo...")
    admisible = es_admisible(grafo)
    consistente = es_consistente(grafo)

    print(f"  Violaciones de admisibilidad: {len(admisible)}")
    print(f"  Violaciones de consistencia:  {len(consistente)}")
    if not admisible and not consistente:
        print("  La heurística es admisible y consistente: A* devuelve la ruta óptima.")
    else:
        for v in (admisible + consistente)[:5]:
            print("   ", v)
