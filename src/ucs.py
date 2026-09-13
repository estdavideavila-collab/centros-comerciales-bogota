"""Búsqueda de costo uniforme (UCS) sobre el grafo de centros comerciales.

Mientras BFS usa una cola FIFO y encuentra la ruta con MENOS CONEXIONES,
UCS usa una cola de prioridad ordenada por el costo acumulado g(n) (km
recorridos desde el inicio) y encuentra la ruta con MENOR DISTANCIA TOTAL.

Es el algoritmo de Dijkstra con prueba de objetivo: se detiene apenas el
objetivo sale de la cola de prioridad, porque en ese momento ya no puede
existir un camino más corto hasta él (todos los caminos pendientes cuestan
igual o más).

Uso:
    from ucs import busqueda_costo_uniforme
    ruta, costo, orden, historial = busqueda_costo_uniforme(grafo, "Bima", "Centro Mayor")
"""

import heapq


def busqueda_costo_uniforme(grafo, inicio, objetivo):
    """Ruta de menor distancia total entre inicio y objetivo.

    grafo: diccionario {nodo: {vecino: km}} (lo devuelve construir_adyacencia()).

    Devuelve (ruta, costo, orden_visita, historial_frontera):
      ruta:               lista de nodos del inicio al objetivo (None si no hay camino)
      costo:              distancia total de la ruta en km (float('inf') si no hay camino)
      orden_visita:       nodos en el orden en que fueron expandidos
      historial_frontera: estado de la cola de prioridad antes de cada expansión,
                          como lista de (costo, nodo) ordenada de menor a mayor
    """
    # Cola de prioridad. Cada entrada es (costo_acumulado, contador, ruta).
    # heapq siempre saca la tupla más pequeña, así que el primer campo (costo)
    # decide la prioridad. El contador desempata costos iguales en orden de
    # llegada y evita que Python intente comparar listas.
    contador = 0
    frontera = [(0.0, contador, [inicio])]

    # Nodos ya expandidos. En UCS un nodo se marca "visitado" cuando SALE de la
    # cola (no cuando entra), porque solo en ese momento sabemos que llegamos a
    # él por el camino más barato.
    expandidos = set()

    orden_visita = []
    historial_frontera = []

    while frontera:
        # Foto de la frontera antes de expandir, ordenada por costo, para mostrarla.
        historial_frontera.append(
            [(round(costo, 1), ruta[-1]) for costo, _, ruta in sorted(frontera)]
        )

        # Sacar el camino de MENOR costo acumulado.
        costo, _, ruta = heapq.heappop(frontera)
        nodo_actual = ruta[-1]

        # Puede haber varias entradas para el mismo nodo (llegamos por distintos
        # caminos). La primera que sale es la más barata; las demás se descartan.
        if nodo_actual in expandidos:
            continue

        expandidos.add(nodo_actual)
        orden_visita.append(nodo_actual)

        # Prueba de objetivo AL EXPANDIR, no al generar. Esto garantiza que la
        # ruta devuelta sea la óptima.
        if nodo_actual == objetivo:
            return ruta, round(costo, 1), orden_visita, historial_frontera

        # Generar sucesores: cada vecino entra con el costo acumulado + km del tramo.
        for vecino, km in grafo.get(nodo_actual, {}).items():
            if vecino not in expandidos:
                contador += 1
                heapq.heappush(frontera, (costo + km, contador, ruta + [vecino]))

    return None, float("inf"), orden_visita, historial_frontera


def costo_ruta(grafo, ruta):
    """Distancia total en km de una ruta cualquiera, sumando tramo a tramo.

    Sirve para calcular el costo de la ruta que devuelve BFS (que no lo
    calcula) y así compararla con la de UCS.
    """
    return round(sum(grafo[a][b] for a, b in zip(ruta, ruta[1:])), 1)


def desglose_ruta(grafo, ruta):
    """Lista de (origen, destino, km_tramo, km_acumulado) para mostrar el costo paso a paso."""
    desglose = []
    acumulado = 0.0
    for a, b in zip(ruta, ruta[1:]):
        acumulado += grafo[a][b]
        desglose.append((a, b, grafo[a][b], round(acumulado, 1)))
    return desglose
