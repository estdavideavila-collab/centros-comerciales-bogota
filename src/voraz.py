"""Búsqueda voraz primero el mejor (greedy best-first) sobre el grafo de centros comerciales.

Es el primer algoritmo INFORMADO del proyecto. BFS y UCS solo miran el grafo;
la voraz usa además una HEURÍSTICA h(n): una estimación de lo que falta desde
cada nodo hasta el objetivo.

    BFS    ordena la cola por orden de llegada  -> menos conexiones
    UCS    ordena la cola por f(n) = g(n)       -> menos kilómetros (óptima)
    VORAZ  ordena la cola por f(n) = h(n)       -> rápida, pero NO óptima
    (A*    ordenaría por f(n) = g(n) + h(n))

Lo característico de la voraz es que DESCARTA g(n): no le importa cuánto lleva
recorrido, solo se lanza siempre hacia el nodo que parece más cerca del destino.
Por eso suele expandir muchos menos nodos que UCS, pero puede devolver una ruta
más larga en kilómetros: cae en trampas geográficas, centros comerciales que en
línea recta quedan cerquísima del destino pero están mal conectados por vía.

La heurística es la distancia en LÍNEA RECTA (fórmula de Haversine) entre las
coordenadas de data/centros.py. Nunca sobreestima el costo real, porque las
distancias de data/conexiones.py se estimaron como Haversine x 1.30: la línea
recta siempre es menor o igual que la distancia por vía. Multiplicar h por una
constante positiva no cambiaría la ruta, solo los números que se muestran.

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


def distancia_recta(origen, destino):
    """Distancia en línea recta entre dos centros comerciales, en km (Haversine).

    Haversine mide sobre la superficie de la Tierra, no sobre el plano: con
    latitudes y longitudes en grados, restarlas sin más daría un número sin
    sentido físico, porque un grado de longitud no mide lo mismo que uno de
    latitud. Es la distancia "en avión": ninguna ruta por calles puede ser menor.
    """
    lat1, lon1 = NODOS[origen][0], NODOS[origen][1]
    lat2, lon2 = NODOS[destino][0], NODOS[destino][1]

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(a))


def busqueda_voraz(grafo, inicio, objetivo, heuristica=distancia_recta):
    """Ruta hacia el objetivo expandiendo siempre el nodo con la menor h(n).

    grafo:      diccionario {nodo: {vecino: km}} (lo devuelve construir_adyacencia()).
    heuristica: función h(nodo, objetivo) en km. Por defecto, la línea recta.
                Se deja como parámetro para poder probar otras en la exposición.

    Devuelve (ruta, costo, orden_visita, historial_frontera), el mismo formato que
    busqueda_costo_uniforme(), para que main.py y los mapas la traten igual:
      ruta:               lista de nodos del inicio al objetivo (None si no hay camino)
      costo:              distancia REAL de la ruta en km (float('inf') si no hay camino);
                          la voraz no la va acumulando, se suma al final tramo a tramo
      orden_visita:       nodos en el orden en que fueron expandidos
      historial_frontera: estado de la cola de prioridad antes de cada expansión,
                          como lista de (h, nodo) ordenada de menor a mayor. Ojo:
                          en UCS ese número es el costo ya recorrido; aquí es lo
                          que se ESTIMA que falta.
    """
    # Cola de prioridad. Cada entrada es (h_del_ultimo_nodo, contador, ruta).
    # heapq siempre saca la tupla más pequeña, así que el primer campo decide la
    # prioridad: sale el nodo que parece más cerca del objetivo. El contador
    # desempata heurísticas iguales en orden de llegada y evita que Python
    # intente comparar listas.
    contador = 0
    frontera = [(heuristica(inicio, objetivo), contador, [inicio])]

    # Nodos ya expandidos. Sin este conjunto la voraz puede quedarse dando
    # vueltas entre dos nodos vecinos que se apuntan mutuamente al objetivo.
    expandidos = set()

    orden_visita = []
    historial_frontera = []

    while frontera:
        # Foto de la frontera antes de expandir, ordenada por h, para mostrarla.
        historial_frontera.append(
            [(round(h, 1), ruta[-1]) for h, _, ruta in sorted(frontera)]
        )

        # Sacar el camino cuyo último nodo tenga la MENOR distancia estimada al
        # objetivo. El costo acumulado hasta él no se mira: esa es la apuesta.
        _, _, ruta = heapq.heappop(frontera)
        nodo_actual = ruta[-1]

        if nodo_actual in expandidos:
            continue

        expandidos.add(nodo_actual)
        orden_visita.append(nodo_actual)

        # Prueba de objetivo al expandir, igual que UCS. Aquí no garantiza nada:
        # la voraz devuelve la primera ruta que encuentra, no la más corta.
        if nodo_actual == objetivo:
            return ruta, costo_ruta(grafo, ruta), orden_visita, historial_frontera

        # Generar sucesores: cada vecino entra con SU heurística, no con la suma
        # del camino. Por eso la voraz puede "retroceder" en kilómetros sin notarlo.
        for vecino in grafo.get(nodo_actual, {}):
            if vecino not in expandidos:
                contador += 1
                heapq.heappush(frontera, (heuristica(vecino, objetivo), contador, ruta + [vecino]))

    return None, float("inf"), orden_visita, historial_frontera


def costo_ruta(grafo, ruta):
    """Distancia real en km de una ruta, sumando tramo a tramo.

    La voraz nunca suma kilómetros mientras busca, así que el costo de su ruta
    hay que calcularlo al final. Hace lo mismo que costo_ruta() de ucs.py; se
    repite aquí para que este archivo funcione por sí solo.
    """
    return round(sum(grafo[a][b] for a, b in zip(ruta, ruta[1:])), 1)


def tabla_heuristica(grafo, objetivo, heuristica=distancia_recta):
    """Lista de (nodo, h_en_km) ordenada de menor a mayor distancia al objetivo.

    Es la tabla de h(n) que se muestra en la exposición: los datos que la voraz
    conoce de antemano y que BFS y UCS ignoran por completo.
    """
    return sorted(((nodo, round(heuristica(nodo, objetivo), 1)) for nodo in grafo), key=lambda par: par[1])
