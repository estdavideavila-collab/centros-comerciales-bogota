import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.conexiones import construir_adyacencia
from bfs import busqueda_anchura

grafo = construir_adyacencia()

print("\nCentros disponibles:")
for centro in grafo:
    print("-", centro)

inicio = input("\nEscribe el centro de inicio: ")
objetivo = input("Escribe el centro de destino: ")

ruta, orden = busqueda_anchura(grafo, inicio, objetivo)

if ruta is None:
    print("\nNo se encontró una ruta entre los centros seleccionados.")
else:
    print("\n--- RESULTADO BFS ---")
    print("Inicio:", inicio)
    print("Destino:", objetivo)

    print("\nOrden de visita:")
    print(" -> ".join(orden))

    print("\nRuta encontrada:")
    print(" -> ".join(ruta))

    print("\nNúmero de conexiones:", len(ruta) - 1)
