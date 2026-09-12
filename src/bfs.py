from collections import deque


def busqueda_anchura(grafo, inicio, objetivo):
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
                cola.append(nueva_ruta)

    return None, orden_visita, historial_cola