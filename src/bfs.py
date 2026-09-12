from collections import deque


def busqueda_anchura(grafo, inicio, objetivo):
    cola = deque([[inicio]])
    visitados = set()
    orden_visita = []

    while cola:
        ruta = cola.popleft()
        nodo_actual = ruta[-1]

        if nodo_actual not in visitados:
            visitados.add(nodo_actual)
            orden_visita.append(nodo_actual)

            if nodo_actual == objetivo:
                return ruta, orden_visita

            for vecino in grafo.get(nodo_actual, []):
                if vecino not in visitados:
                    nueva_ruta = ruta + [vecino]
                    cola.append(nueva_ruta)

    return None, orden_visita

def construir_grafo(conexiones):
    grafo = {}

    for origen, destino, distancia in conexiones:
        if origen not in grafo:
            grafo[origen] = []

        if destino not in grafo:
            grafo[destino] = []

        grafo[origen].append(destino)
        grafo[destino].append(origen)

    return grafo