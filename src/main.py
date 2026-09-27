import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.conexiones import construir_adyacencia
from bfs import busqueda_anchura
from ucs import busqueda_costo_uniforme, costo_ruta, desglose_ruta
from astar import busqueda_a_estrella, distancia_linea_recta
from mapa import generar_ruta, generar_comparacion
from mapa_interactivo import generar_mapa_interactivo


def mostrar_desglose(grafo, ruta):
    """Imprime cada tramo de la ruta con su distancia y el costo acumulado."""
    print(f"  {'Tramo':<50} {'km':>6} {'Acumulado':>10}")
    print(f"  {ruta[0]:<50} {'':>6} {0.0:>10.1f}")
    for origen, destino, km, acumulado in desglose_ruta(grafo, ruta):
        print(f"  {origen + ' -> ' + destino:<50} {km:>6.1f} {acumulado:>10.1f}")


def mostrar_historial(historial, titulo, maximo=5):
    """Imprime la evolución de la cola, recortando los estados muy largos."""
    print(f"\n{titulo}:")
    for paso, estado in enumerate(historial, start=1):
        if len(estado) > maximo:
            print(f"Paso {paso}: {estado[:maximo]} ...")
        else:
            print(f"Paso {paso}: {estado}")


def mostrar_algoritmo(grafo, nombre, criterio, ruta, costo, orden, historial, titulo_cola, maximo):
    """Imprime el bloque completo de resultados de un algoritmo."""
    print("\n" + "=" * 70)
    print(f"{nombre} - {criterio}")
    print("=" * 70)
    print("Inicio:", ruta[0])
    print("Destino:", ruta[-1])

    print("\nOrden de visita (nodos expandidos):")
    print(" -> ".join(orden))

    print("\nRuta encontrada:")
    print(" -> ".join(ruta))
    print("\nNúmero de conexiones:", len(ruta) - 1)
    print(f"Distancia total: {costo} km")

    print("\nCosto acumulado tramo a tramo:")
    mostrar_desglose(grafo, ruta)

    mostrar_historial(historial, titulo_cola, maximo)


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
mostrar_algoritmo(
    grafo, "BÚSQUEDA EN ANCHURA (BFS)", "minimiza el NÚMERO DE CONEXIONES",
    ruta_bfs, costo_bfs, orden_bfs, historial_cola,
    "Evolución de la cola FIFO", 6,
)

# ---------------------------------------------------------------- UCS
ruta_ucs, costo_ucs, orden_ucs, historial_frontera = busqueda_costo_uniforme(grafo, inicio, objetivo)
mostrar_algoritmo(
    grafo, "BÚSQUEDA DE COSTO UNIFORME (UCS)", "minimiza la DISTANCIA TOTAL",
    ruta_ucs, costo_ucs, orden_ucs, historial_frontera,
    "Evolución de la cola de prioridad (costo acumulado, nodo), de menor a mayor", 5,
)

# ---------------------------------------------------------------- A*
ruta_astar, costo_astar, orden_astar, historial_astar = busqueda_a_estrella(grafo, inicio, objetivo)
mostrar_algoritmo(
    grafo, "BÚSQUEDA A* (A ESTRELLA)", "minimiza la DISTANCIA TOTAL guiado por la heurística",
    ruta_astar, costo_astar, orden_astar, historial_astar,
    "Evolución de la cola de prioridad (f = g + h, g, h, nodo), ordenada por f", 5,
)

print(f"\nHeurística usada: distancia en línea recta al objetivo ({objetivo}).")
print(f"  h({inicio}) = {distancia_linea_recta(inicio, objetivo):.1f} km en línea recta")
print(f"  Distancia real recorrida = {costo_astar} km por vía")
print("  h nunca sobreestima (una vía no puede ser más corta que la línea recta),")
print("  por eso la heurística es admisible y A* devuelve la ruta óptima.")

# ---------------------------------------------------------------- Comparación
print("\n" + "=" * 70)
print("COMPARACIÓN BFS vs UCS vs A*")
print("=" * 70)
print(f"  {'':<22} {'BFS':>12} {'UCS':>12} {'A*':>12}")
print(f"  {'Conexiones':<22} {len(ruta_bfs) - 1:>12} {len(ruta_ucs) - 1:>12} {len(ruta_astar) - 1:>12}")
print(f"  {'Distancia total (km)':<22} {costo_bfs:>12.1f} {costo_ucs:>12.1f} {costo_astar:>12.1f}")
print(f"  {'Nodos expandidos':<22} {len(orden_bfs):>12} {len(orden_ucs):>12} {len(orden_astar):>12}")

print("\n--- BFS frente a las búsquedas por costo ---")
if ruta_bfs == ruta_ucs:
    print("BFS encontró LA MISMA ruta que UCS: la de menos conexiones también es")
    print("la de menor distancia.")
else:
    print(f"Las rutas son DISTINTAS. UCS y A* ahorran {round(costo_bfs - costo_ucs, 1)} km frente a BFS.")
    print("BFS escogió la ruta con menos conexiones sin mirar las distancias;")
    print("UCS y A* aceptaron más conexiones a cambio de recorrer menos kilómetros.")

print("\n--- A* frente a UCS ---")
if costo_astar == costo_ucs:
    print(f"Los dos encontraron el mismo costo óptimo ({costo_ucs} km), como debe ser:")
    print("la heurística es admisible, así que A* no pierde optimalidad.")
    if ruta_astar != ruta_ucs:
        print("Las rutas difieren pero valen lo mismo: hay varios caminos óptimos y")
        print("cada algoritmo desempató por uno distinto.")
else:
    print(f"ATENCIÓN: A* dio {costo_astar} km y UCS {costo_ucs} km. Si la heurística")
    print("fuera admisible esto no debería pasar.")

ahorro_nodos = len(orden_ucs) - len(orden_astar)
if ahorro_nodos > 0:
    print(f"A* expandió {ahorro_nodos} nodos menos que UCS "
          f"({100 * ahorro_nodos / len(orden_ucs):.0f}% menos trabajo) porque la")
    print("heurística lo orientó hacia el objetivo en vez de explorar en todas direcciones.")
elif ahorro_nodos == 0:
    print("A* expandió los mismos nodos que UCS: en este par la heurística no")
    print("alcanzó a descartar ninguna rama.")
else:
    print(f"A* expandió {-ahorro_nodos} nodos más que UCS (puede pasar en trayectos muy cortos).")

print("\nRuta con menor distancia total:")
print(" -> ".join(ruta_astar), f"= {costo_astar} km")

# ---------------------------------------------------------------- Imágenes
print("\nGenerando imágenes en docs/ ...")
for algoritmo, ruta in (("BFS", ruta_bfs), ("UCS", ruta_ucs), ("A*", ruta_astar)):
    for archivo in generar_ruta(ruta, algoritmo):
        print("Guardado:", archivo)
for archivo in generar_comparacion(ruta_bfs, ruta_ucs, ruta_astar):
    print("Guardado:", archivo)
print("Guardado:", generar_mapa_interactivo(
    rutas={"BFS": ruta_bfs, "UCS": ruta_ucs, "A*": ruta_astar}))
