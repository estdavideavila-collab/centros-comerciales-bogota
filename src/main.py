import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.conexiones import construir_adyacencia
from bfs import busqueda_anchura
from ucs import busqueda_costo_uniforme, costo_ruta, desglose_ruta
from voraz import busqueda_voraz
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

# ------------------------------------------------ BFS (no informada)
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

# ------------------------------------------------ UCS (no informada)
ruta_ucs, costo_ucs, orden_ucs, historial_frontera = busqueda_costo_uniforme(grafo, inicio, objetivo)
mostrar_algoritmo(
    grafo, "BÚSQUEDA DE COSTO UNIFORME (UCS)", "minimiza la DISTANCIA TOTAL",
    ruta_ucs, costo_ucs, orden_ucs, historial_frontera,
    "Evolución de la cola de prioridad (costo acumulado g, nodo), de menor a mayor", 5,
)

# ------------------------------------------------ Voraz (informada, f = h)
ruta_voraz, costo_voraz, orden_voraz, historial_voraz = busqueda_voraz(grafo, inicio, objetivo)
mostrar_algoritmo(
    grafo, "BÚSQUEDA VORAZ PRIMERO EL MEJOR", "se guía SOLO por la distancia en línea recta (f = h)",
    ruta_voraz, costo_voraz, orden_voraz, historial_voraz,
    "Evolución de la cola de prioridad (distancia estimada que FALTA h, nodo), de menor a mayor", 5,
)

# ------------------------------------------------ A* (informada, f = g + h)
ruta_astar, costo_astar, orden_astar, historial_astar = busqueda_a_estrella(grafo, inicio, objetivo)
mostrar_algoritmo(
    grafo, "BÚSQUEDA A* (A ESTRELLA)",
    "minimiza la DISTANCIA TOTAL guiado por la heurística (f = g + h)",
    ruta_astar, costo_astar, orden_astar, historial_astar,
    "Evolución de la cola de prioridad (f = g + h, g, h, nodo), ordenada por f", 5,
)

print(f"\nLa voraz y A* comparten la misma heurística: la línea recta hasta {objetivo}.")
print(f"  h({inicio}) = {distancia_linea_recta(inicio, objetivo):.1f} km en línea recta")
print(f"  Por vía, la ruta óptima mide {costo_ucs} km.")
print("  h nunca sobreestima (una vía no puede ser más corta que la línea recta).")
print("  A* la suma a lo ya recorrido y conserva la optimalidad; la voraz descarta")
print("  lo recorrido, así que la misma heurística no le alcanza para garantizarla.")

# ------------------------------------------------ Comparación
print("\n" + "=" * 70)
print("COMPARACIÓN BFS vs UCS vs VORAZ vs A*")
print("=" * 70)
print(f"  {'':<22} {'BFS':>11} {'UCS':>11} {'Voraz':>11} {'A*':>11}")
print(f"  {'Conexiones':<22} {len(ruta_bfs) - 1:>11} {len(ruta_ucs) - 1:>11}"
      f" {len(ruta_voraz) - 1:>11} {len(ruta_astar) - 1:>11}")
print(f"  {'Distancia total (km)':<22} {costo_bfs:>11.1f} {costo_ucs:>11.1f}"
      f" {costo_voraz:>11.1f} {costo_astar:>11.1f}")
print(f"  {'Nodos expandidos':<22} {len(orden_bfs):>11} {len(orden_ucs):>11}"
      f" {len(orden_voraz):>11} {len(orden_astar):>11}")

print("\n--- BFS frente a UCS ---")
if ruta_bfs == ruta_ucs:
    print("BFS encontró LA MISMA ruta que UCS: la de menos conexiones también es")
    print("la de menor distancia.")
else:
    diferencia = round(costo_bfs - costo_ucs, 1)
    if diferencia == 0:
        print("Las rutas son DISTINTAS pero miden lo mismo: hay un empate en distancia.")
    else:
        print(f"Las rutas son DISTINTAS. UCS ahorra {diferencia} km frente a BFS.")
        print("BFS escogió la ruta con menos conexiones sin mirar las distancias;")
        print("UCS aceptó más conexiones a cambio de recorrer menos kilómetros.")

print("\n--- La voraz frente a UCS ---")
menos_voraz = len(orden_ucs) - len(orden_voraz)
if ruta_voraz == ruta_ucs:
    print(f"La voraz llegó a la MISMA ruta óptima que UCS expandiendo {menos_voraz} nodos menos:")
    print("la heurística la llevó derecho al destino en vez de explorar en todas direcciones.")
    print("Que acierte aquí no es garantía: en otros pares se equivoca.")
else:
    de_mas = round(costo_voraz - costo_ucs, 1)
    if de_mas <= 0:
        print("La voraz encontró otra ruta que mide lo mismo que la de UCS: hay un empate.")
    else:
        print(f"La voraz expandió {menos_voraz} nodos menos que UCS, pero su ruta cuesta {de_mas} km MÁS.")
        print("Ese es su precio: mira solo lo que falta (h) e ignora lo ya recorrido (g),")
        print("así que no garantiza la ruta más corta.")

print("\n--- A* frente a UCS y a la voraz ---")
if costo_astar == costo_ucs:
    print(f"A* y UCS llegaron al mismo costo óptimo ({costo_ucs} km), como debe ser:")
    print("la heurística es admisible, así que A* no pierde optimalidad.")
    if ruta_astar != ruta_ucs:
        print("Las rutas difieren pero valen lo mismo: hay varios caminos óptimos y")
        print("cada algoritmo desempató por uno distinto.")
else:
    print(f"ATENCIÓN: A* dio {costo_astar} km y UCS {costo_ucs} km. Si la heurística")
    print("fuera admisible esto no debería pasar.")

ahorro_astar = len(orden_ucs) - len(orden_astar)
if ahorro_astar > 0:
    print(f"A* expandió {ahorro_astar} nodos menos que UCS "
          f"({100 * ahorro_astar / len(orden_ucs):.0f}% menos trabajo).")
elif ahorro_astar == 0:
    print("A* expandió los mismos nodos que UCS: la heurística no descartó ninguna rama.")
else:
    print(f"A* expandió {-ahorro_astar} nodos más que UCS (puede pasar en trayectos muy cortos).")

if len(orden_voraz) < len(orden_astar):
    print(f"La voraz expandió aún menos ({len(orden_voraz)} nodos), pero sin garantizar la")
    print("ruta más corta: es la diferencia entre ir rápido e ir rápido y bien.")

print("\nRuta con menor distancia total:")
print(" -> ".join(ruta_astar), f"= {costo_astar} km")

# ------------------------------------------------ Imágenes
print("\nGenerando imágenes en docs/ ...")
for algoritmo, ruta in (("BFS", ruta_bfs), ("UCS", ruta_ucs), ("Voraz", ruta_voraz), ("A*", ruta_astar)):
    for archivo in generar_ruta(ruta, algoritmo):
        print("Guardado:", archivo)
for archivo in generar_comparacion(ruta_bfs, ruta_ucs, ruta_voraz, ruta_astar):
    print("Guardado:", archivo)
print("Guardado:", generar_mapa_interactivo(
    rutas={"BFS": ruta_bfs, "UCS": ruta_ucs, "Voraz": ruta_voraz, "A*": ruta_astar}))
