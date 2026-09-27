"""Búsqueda A* (A estrella) sobre el grafo de centros comerciales.

UCS ordena su cola de prioridad por g(n): los km ya recorridos. A* la ordena
por f(n) = g(n) + h(n), donde h(n) es una estimación de lo que falta desde n
hasta el objetivo. Así deja de expandir en todas las direcciones por igual y
se orienta hacia el destino.

La heurística que se usa aquí es la DISTANCIA EN LÍNEA RECTA (fórmula de
haversine sobre las coordenadas lat/lon de data/centros.py). Es admisible
porque los pesos del grafo son distancias POR VÍA, y una vía nunca puede ser
más corta que la línea recta entre dos puntos: h(n) jamás sobreestima. Y es
consistente porque cumple la desigualdad triangular. Con una heurística
admisible y consistente, A* devuelve la MISMA ruta óptima que UCS, pero
expandiendo menos nodos.

Casos extremos:
  - Si h(n) = 0 para todo n, A* se comporta exactamente como UCS.
  - Si h(n) sobreestima, A* es más rápido pero puede devolver una ruta peor.

Uso:
    from astar import busqueda_a_estrella
    ruta, costo, orden, historial = busqueda_a_estrella(grafo, "Bima", "Centro Mayor")
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


def distancia_linea_recta(nodo_a, nodo_b):
    """Distancia en línea recta (km) entre dos centros, por la fórmula de haversine.

    Haversine da la distancia sobre la superficie de la esfera (el "arco" que
    une los dos puntos), que es lo más corto que se puede ir entre ellos.
    Cualquier ruta por calles mide igual o más, nunca menos.
    """
    lat_a, lon_a = NODOS[nodo_a][0], NODOS[nodo_a][1]
    lat_b, lon_b = NODOS[nodo_b][0], NODOS[nodo_b][1]

    lat_a, lon_a, lat_b, lon_b = map(radians, (lat_a, lon_a, lat_b, lon_b))
    d_lat = lat_b - lat_a
    d_lon = lon_b - lon_a

    a = sin(d_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(d_lon / 2) ** 2
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


def busqueda_a_estrella(grafo, inicio, objetivo, heuristica=distancia_linea_recta):
    """Ruta de menor distancia total, guiada por la heurística.

    grafo: diccionario {nodo: {vecino: km}} (lo devuelve construir_adyacencia()).
    heuristica: función h(nodo, objetivo) -> km estimados que faltan.

    Devuelve (ruta, costo, orden_visita, historial_frontera):
      ruta:               lista de nodos del inicio al objetivo (None si no hay camino)
      costo:              distancia REAL de la ruta en km, o sea g, no f
                          (float('inf') si no hay camino)
      orden_visita:       nodos en el orden en que fueron expandidos
      historial_frontera: estado de la cola antes de cada expansión, como lista
                          de (f, g, h, nodo) ordenada por f de menor a mayor
    """
    # Cola de prioridad. Cada entrada es (f, contador, g, ruta).
    # heapq saca la tupla más pequeña, así que el primer campo (f) manda.
    # A diferencia de UCS, aquí hay que guardar g aparte: f sirve para ordenar,
    # pero el costo real de la ruta es g.
    contador = 0
    h_inicio = heuristica(inicio, objetivo)
    frontera = [(h_inicio, contador, 0.0, [inicio])]

    # Igual que en UCS: un nodo se cierra cuando SALE de la cola, no cuando entra.
    expandidos = set()

    orden_visita = []
    historial_frontera = []

    while frontera:
        # Foto de la frontera antes de expandir, con las tres cifras a la vista.
        historial_frontera.append([
            (round(f, 1), round(g, 1), round(f - g, 1), ruta[-1])
            for f, _, g, ruta in sorted(frontera)
        ])

        # Sacar el camino con menor f = g + h (el más prometedor).
        f, _, g, ruta = heapq.heappop(frontera)
        nodo_actual = ruta[-1]

        if nodo_actual in expandidos:
            continue

        expandidos.add(nodo_actual)
        orden_visita.append(nodo_actual)

        # Prueba de objetivo al expandir. Con h admisible, en este punto ningún
        # camino pendiente puede llegar al objetivo con menos de g.
        if nodo_actual == objetivo:
            return ruta, round(g, 1), orden_visita, historial_frontera

        # Generar sucesores: g crece con los km del tramo; h se recalcula desde
        # el vecino hasta el objetivo.
        for vecino, km in grafo.get(nodo_actual, {}).items():
            if vecino not in expandidos:
                contador += 1
                nuevo_g = g + km
                nuevo_f = nuevo_g + heuristica(vecino, objetivo)
                heapq.heappush(frontera, (nuevo_f, contador, nuevo_g, ruta + [vecino]))

    return None, float("inf"), orden_visita, historial_frontera


def es_admisible(grafo, heuristica=distancia_linea_recta):
    """Nodos donde la heurística sobreestima el costo real, para todo par (n, objetivo).

    Devuelve la lista de (nodo, objetivo, h, costo_real) que violan h <= costo real.
    Si la lista sale vacía, la heurística es admisible en este grafo y A* es óptimo.
    Requiere el costo real mínimo, que se obtiene con UCS.
    """
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
    """Aristas donde se rompe la desigualdad triangular h(n) <= coste(n,m) + h(m).

    Devuelve la lista de (n, m, objetivo, h_n, coste + h_m) que la violan.
    Si sale vacía, la heurística es consistente: A* nunca necesita reabrir un
    nodo ya cerrado.
    """
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
