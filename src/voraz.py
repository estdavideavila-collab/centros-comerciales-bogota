"""Búsqueda voraz primero el mejor: expande el nodo que parece más cerca del destino.

Heurística: h(n) = distancia en línea recta (Haversine) de n al destino.
f(n) = h(n): solo mira lo que falta e ignora lo recorrido; por eso suele expandir muchos
menos nodos que UCS, pero no garantiza la ruta más corta.

Uso:
    from voraz import busqueda_voraz
    ruta, costo, orden, historial = busqueda_voraz(grafo, "Bima", "Centro Mayor")
"""

import heapq
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from data.centros import NODOS  # noqa: E402

RADIO_TIERRA_KM = 6371.0


# ==============================================================================
#  HEURÍSTICA   h(n) = distancia en línea recta (Haversine) de n al destino, en km
#  Es admisible: ninguna ruta por calles es más corta que la línea recta.
# ==============================================================================
def distancia_recta(origen, destino):
    """Distancia en línea recta en km (Haversine) entre dos centros de data/centros.py."""
    lat1, lon1 = NODOS[origen][:2]
    lat2, lon2 = NODOS[destino][:2]

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(a))


# ==============================================================================
#  BÚSQUEDA VORAZ   f(n) = h(n)
# ==============================================================================
def busqueda_voraz(grafo, inicio, objetivo, heuristica=distancia_recta):
    """Expande siempre el nodo con la menor h(n), sin mirar el costo acumulado.

    Devuelve lo mismo que busqueda_costo_uniforme(): costo es la distancia real de la
    ruta y el historial guarda (h, nodo) en vez de (costo, nodo).
    """
    # Entradas (h, contador, ruta): el contador desempata por orden de llegada y evita comparar listas.
    contador = 0
    frontera = [(heuristica(inicio, objetivo), contador, [inicio])]

    # Cada nodo entra una sola vez a la frontera, porque su h no depende del camino (como en AIMA).
    en_frontera = {inicio}

    # Sin este conjunto la voraz cicla; por ejemplo, entre Titán Plaza y Diverplaza rumbo a Nuestro Bogotá.
    expandidos = set()

    orden_visita = []
    historial_frontera = []

    while frontera:
        historial_frontera.append(
            [(round(h, 1), ruta[-1]) for h, _, ruta in sorted(frontera)]
        )

        _, _, ruta = heapq.heappop(frontera)
        nodo_actual = ruta[-1]
        en_frontera.remove(nodo_actual)

        expandidos.add(nodo_actual)
        orden_visita.append(nodo_actual)

        # Devuelve la primera ruta que encuentra, no necesariamente la más corta.
        if nodo_actual == objetivo:
            return ruta, costo_ruta(grafo, ruta), orden_visita, historial_frontera

        # f(n) = h(n): aquí entra la HEURÍSTICA; cada vecino entra con su h, no con la suma del camino.
        for vecino in grafo.get(nodo_actual, {}):
            if vecino not in expandidos and vecino not in en_frontera:
                contador += 1
                en_frontera.add(vecino)
                heapq.heappush(frontera, (heuristica(vecino, objetivo), contador, ruta + [vecino]))

    return None, float("inf"), orden_visita, historial_frontera


def costo_ruta(grafo, ruta):
    """Distancia real de la ruta en km (copia de costo_ruta() de ucs.py, para no depender de él)."""
    return round(sum(grafo[a][b] for a, b in zip(ruta, ruta[1:])), 1)


def tabla_heuristica(grafo, objetivo, heuristica=distancia_recta):
    """Lista de (nodo, h en km), de menor a mayor distancia al objetivo."""
    return sorted(((nodo, round(heuristica(nodo, objetivo), 1)) for nodo in grafo), key=lambda par: par[1])
