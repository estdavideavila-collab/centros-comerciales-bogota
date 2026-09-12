import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.conexiones import construir_adyacencia
from bfs import busqueda_anchura
from mapa import generar_ruta
from mapa_interactivo import generar_mapa_interactivo


grafo = construir_adyacencia()

print("\nCentros disponibles:")
for centro in grafo:
    print("-", centro)

inicio = input("\nEscribe el centro de inicio: ").strip()
objetivo = input("Escribe el centro de destino: ").strip()

if inicio not in grafo:
    print("\nEl centro de inicio no existe en el grafo.")
    sys.exit()

if objetivo not in grafo:
    print("\nEl centro de destino no existe en el grafo.")
    sys.exit()

ruta, orden, historial_cola = busqueda_anchura(grafo, inicio, objetivo)

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

    print("\nEvolución de la cola FIFO:")

    for paso, estado_cola in enumerate(historial_cola, start=1):
        if len(estado_cola) > 6:
            visibles = estado_cola[:6]
            print(f"Paso {paso}: {visibles} ...")
        else:
            print(f"Paso {paso}: {estado_cola}")

    # Imágenes en docs/. Cuando exista ucs.py se agregan también
    # generar_ruta(ruta_ucs, "UCS") y generar_comparacion(ruta, ruta_ucs) de mapa.py.
    print("\nGenerando imágenes en docs/ ...")
    for archivo in generar_ruta(ruta, "BFS"):
        print("Guardado:", archivo)
    print("Guardado:", generar_mapa_interactivo(rutas={"BFS": ruta}))