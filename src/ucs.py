"""Búsqueda de costo uniforme (UCS): la ruta de menor distancia total.

Heurística: ninguna (búsqueda no informada). f(n) = g(n), los km recorridos desde el inicio.

Uso:
    from ucs import busqueda_costo_uniforme
    ruta, costo, orden, historial = busqueda_costo_uniforme(grafo, "Bima", "Centro Mayor")
"""

import heapq


def busqueda_costo_uniforme(grafo, inicio, objetivo):
    """Expande siempre el camino de menor costo acumulado g(n).

    grafo: {nodo: {vecino: km}}, el que devuelve construir_adyacencia().
    Devuelve (ruta, costo, orden_visita, historial_frontera); si no hay camino, ruta es
    None y costo float('inf'). El historial guarda la cola como (costo, nodo) antes de
    cada expansión.
    """
    # Entradas (costo, contador, ruta): el contador desempata por orden de llegada y evita comparar listas.
    contador = 0
    frontera = [(0.0, contador, [inicio])]

    # Un nodo se cierra al SALIR de la cola: solo entonces se sabe que se llegó por el camino más barato.
    expandidos = set()

    orden_visita = []
    historial_frontera = []

    while frontera:
        historial_frontera.append(
            [(round(costo, 1), ruta[-1]) for costo, _, ruta in sorted(frontera)]
        )

        costo, _, ruta = heapq.heappop(frontera)
        nodo_actual = ruta[-1]

        # Entrada repetida de un nodo que ya se cerró por un camino más barato.
        if nodo_actual in expandidos:
            continue

        expandidos.add(nodo_actual)
        orden_visita.append(nodo_actual)

        # Prueba de objetivo al expandir, no al generar: así la ruta es la óptima.
        if nodo_actual == objetivo:
            return ruta, round(costo, 1), orden_visita, historial_frontera

        for vecino, km in grafo.get(nodo_actual, {}).items():
            if vecino not in expandidos:
                contador += 1
                # f(n) = g(n): km acumulados más los del tramo.
                heapq.heappush(frontera, (costo + km, contador, ruta + [vecino]))

    return None, float("inf"), orden_visita, historial_frontera


def costo_ruta(grafo, ruta):
    """Distancia total de una ruta en km (sirve para la de BFS, que no la calcula)."""
    return round(sum(grafo[a][b] for a, b in zip(ruta, ruta[1:])), 1)


def desglose_ruta(grafo, ruta):
    """Lista de (origen, destino, km del tramo, km acumulados)."""
    desglose = []
    acumulado = 0.0
    for a, b in zip(ruta, ruta[1:]):
        acumulado += grafo[a][b]
        desglose.append((a, b, grafo[a][b], round(acumulado, 1)))
    return desglose
