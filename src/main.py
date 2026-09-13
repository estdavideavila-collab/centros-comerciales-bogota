import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.conexiones import construir_adyacencia
from bfs import busqueda_anchura
from ucs import busqueda_costo_uniforme, costo_ruta, desglose_ruta
from mapa import generar_ruta, generar_comparacion
from mapa_interactivo import generar_mapa_interactivo


def mostrar_desglose(grafo, ruta):
    """Imprime cada tramo de la ruta con su distancia y el costo acumulado."""
    print(f"  {'Tramo':<50} {'km':>6} {'Acumulado':>10}")
    print(f"  {ruta[0]:<50} {'':>6} {0.0:>10.1f}")
    for origen, destino, km, acumulado in desglose_ruta(grafo, ruta):
        print(f"  {origen + ' -> ' + destino:<50} {km:>6.1f} {acumulado:>10.1f}")


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

# ---------------------------------------------------------------- BFS
ruta_bfs, orden_bfs, historial_cola = busqueda_anchura(grafo, inicio, objetivo)

if ruta_bfs is None:
    print("\nNo se encontró una ruta entre los centros seleccionados.")
    sys.exit()

costo_bfs = costo_ruta(grafo, ruta_bfs)

print("\n" + "=" * 70)
print("BÚSQUEDA EN ANCHURA (BFS) - minimiza el NÚMERO DE CONEXIONES")
print("=" * 70)
print("Inicio:", inicio)
print("Destino:", objetivo)

print("\nOrden de visita (nodos expandidos):")
print(" -> ".join(orden_bfs))

print("\nRuta encontrada:")
print(" -> ".join(ruta_bfs))
print("\nNúmero de conexiones:", len(ruta_bfs) - 1)
print(f"Distancia total: {costo_bfs} km")

print("\nCosto acumulado tramo a tramo:")
mostrar_desglose(grafo, ruta_bfs)

print("\nEvolución de la cola FIFO:")
for paso, estado_cola in enumerate(historial_cola, start=1):
    if len(estado_cola) > 6:
        print(f"Paso {paso}: {estado_cola[:6]} ...")
    else:
        print(f"Paso {paso}: {estado_cola}")

# ---------------------------------------------------------------- UCS
ruta_ucs, costo_ucs, orden_ucs, historial_frontera = busqueda_costo_uniforme(grafo, inicio, objetivo)

print("\n" + "=" * 70)
print("BÚSQUEDA DE COSTO UNIFORME (UCS) - minimiza la DISTANCIA TOTAL")
print("=" * 70)
print("Inicio:", inicio)
print("Destino:", objetivo)

print("\nOrden de visita (nodos expandidos):")
print(" -> ".join(orden_ucs))

print("\nRuta encontrada:")
print(" -> ".join(ruta_ucs))
print("\nNúmero de conexiones:", len(ruta_ucs) - 1)
print(f"Distancia total: {costo_ucs} km")

print("\nCosto acumulado tramo a tramo:")
mostrar_desglose(grafo, ruta_ucs)

print("\nEvolución de la cola de prioridad (costo acumulado, nodo), de menor a mayor:")
for paso, estado in enumerate(historial_frontera, start=1):
    if len(estado) > 5:
        print(f"Paso {paso}: {estado[:5]} ...")
    else:
        print(f"Paso {paso}: {estado}")

# ---------------------------------------------------------------- Comparación
print("\n" + "=" * 70)
print("COMPARACIÓN BFS vs UCS")
print("=" * 70)
print(f"  {'':<22} {'BFS':>12} {'UCS':>12}")
print(f"  {'Conexiones':<22} {len(ruta_bfs) - 1:>12} {len(ruta_ucs) - 1:>12}")
print(f"  {'Distancia total (km)':<22} {costo_bfs:>12.1f} {costo_ucs:>12.1f}")
print(f"  {'Nodos expandidos':<22} {len(orden_bfs):>12} {len(orden_ucs):>12}")

if ruta_bfs == ruta_ucs:
    print("\nAmbos algoritmos encontraron LA MISMA ruta: la de menos conexiones")
    print("también es la de menor distancia.")
else:
    diferencia = round(costo_bfs - costo_ucs, 1)
    print(f"\nLas rutas son DISTINTAS. UCS ahorra {diferencia} km frente a BFS.")
    print("BFS escogió la ruta con menos conexiones sin mirar las distancias;")
    print("UCS aceptó más conexiones a cambio de recorrer menos kilómetros.")

print("\nRuta con menor distancia total (UCS):")
print(" -> ".join(ruta_ucs), f"= {costo_ucs} km")

# ---------------------------------------------------------------- Imágenes
print("\nGenerando imágenes en docs/ ...")
for archivo in generar_ruta(ruta_bfs, "BFS"):
    print("Guardado:", archivo)
for archivo in generar_ruta(ruta_ucs, "UCS"):
    print("Guardado:", archivo)
for archivo in generar_comparacion(ruta_bfs, ruta_ucs):
    print("Guardado:", archivo)
print("Guardado:", generar_mapa_interactivo(rutas={"BFS": ruta_bfs, "UCS": ruta_ucs}))
