"""Búsqueda en anchura (BFS): la ruta con menos conexiones.

Heurística: ninguna (búsqueda no informada). Usa una cola FIFO: expande los nodos
en orden de llegada, nivel por nivel.
"""

from collections import deque


def busqueda_anchura(grafo, inicio, objetivo):
    """Devuelve (ruta, orden_visita, historial_cola); ruta es None si no hay camino."""
    # Un nodo se marca visitado al entrar a la cola: después no aparece un camino con menos conexiones.
    cola = deque([[inicio]])
    visitados = {inicio}
    orden_visita = []
    historial_cola = []

    while cola:
        historial_cola.append([camino[-1] for camino in cola])

        ruta = cola.popleft()
        nodo_actual = ruta[-1]

        orden_visita.append(nodo_actual)

        if nodo_actual == objetivo:
            return ruta, orden_visita, historial_cola

        for vecino in grafo.get(nodo_actual, {}):
            if vecino not in visitados:
                visitados.add(vecino)
                nueva_ruta = ruta + [vecino]
                # Sin prioridad: el vecino va al final de la cola (FIFO).
                cola.append(nueva_ruta)

    return None, orden_visita, historial_cola
