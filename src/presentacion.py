"""Programa para la exposición: BFS, UCS y búsqueda voraz entre dos centros, en consola y en el mapa.

Es el que se empaqueta como ejecutable (ver crear_ejecutable.py). Corre los mismos
algoritmos que main.py (src/bfs.py, src/ucs.py y src/voraz.py) sobre el mismo grafo, pero:
  - los centros se eligen por número o por nombre, sin importar tildes ni mayúsculas;
  - abre el mapa interactivo con las tres rutas dibujadas, y funciona sin internet;
  - se pueden probar varias rutas sin volver a abrir el programa;
  - no genera las imágenes de docs/, así el ejecutable no necesita GeoPandas ni Matplotlib.

Uso sin empaquetar:
    python src/presentacion.py
"""

import json
import re
import shutil
import sys
import tempfile
import traceback
import unicodedata
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from data.conexiones import construir_adyacencia  # noqa: E402
from bfs import busqueda_anchura  # noqa: E402
from ucs import busqueda_costo_uniforme, costo_ruta, desglose_ruta  # noqa: E402
from voraz import busqueda_voraz, distancia_recta  # noqa: E402

LINEA = "=" * 70

# Dentro del ejecutable, PyInstaller deja los archivos agregados en sys._MEIPASS.
MAPA = (Path(sys._MEIPASS) if getattr(sys, "frozen", False) else RAIZ / "docs") / "mapa_interactivo.html"
# El panel del mapa abre con el inicio y el destino que traen estos dos campos (ver mapa_interactivo.py).
CAMPOS_RUTA = re.compile(r'"inicio": (?:null|"[^"]*"), "objetivo": (?:null|"[^"]*")')


def _numero(valor):
    return f"{valor:.1f}".replace(".", ",")


def _km(valor):
    return f"{_numero(valor)} km"


def _clave(texto):
    """Texto para comparar nombres sin tildes ni mayúsculas: 'Titán  plaza' -> 'titan plaza'."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.casefold().split())


def _ancho_consola():
    return min(shutil.get_terminal_size((100, 30)).columns, 110) - 1


def _cadena(nodos):
    """Nodos unidos por flechas y partidos en renglones sin cortar ningún nombre."""
    renglones = [nodos[0]]
    for nodo in nodos[1:]:
        pieza = f" -> {nodo}"
        if len(renglones[-1]) + len(pieza) > _ancho_consola() - 2:
            renglones.append(pieza.strip())
        else:
            renglones[-1] += pieza
    return "\n".join("  " + renglon for renglon in renglones)


def mostrar_centros(centros):
    """Lista numerada de los centros, en columnas."""
    ancho = max(len(centro) for centro in centros) + 7
    columnas = max(1, min(3, _ancho_consola() // ancho))
    filas = -(-len(centros) // columnas)
    for fila in range(filas):
        print("".join(f"{i + 1:>4}. {centros[i]:<{ancho - 6}}" for i in range(fila, len(centros), filas)).rstrip())


def elegir_centro(mensaje, centros):
    """Pide un centro por número o por nombre y repite hasta que la respuesta sea válida."""
    por_clave = {_clave(centro): centro for centro in centros}
    while True:
        respuesta = input(mensaje).strip()
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(centros):
            return centros[int(respuesta) - 1]
        clave = _clave(respuesta)
        if clave in por_clave:
            return por_clave[clave]
        parecidos = [centro for texto, centro in por_clave.items() if clave and clave in texto]
        if len(parecidos) == 1:
            return parecidos[0]
        if parecidos:
            print(f"  Coinciden varios: {', '.join(parecidos)}. Escribe el número.")
        else:
            print(f"  No lo encontré. Escribe un número del 1 al {len(centros)} o el nombre del centro.")


def mostrar_desglose(grafo, ruta):
    """Cada tramo de la ruta con su distancia y el costo acumulado."""
    print(f"  {'Tramo':<50} {'km':>6} {'Acumulado':>10}")
    print(f"  {ruta[0]:<50} {'':>6} {_numero(0):>10}")
    for origen, destino, km, acumulado in desglose_ruta(grafo, ruta):
        print(f"  {origen + ' -> ' + destino:<50} {_numero(km):>6} {_numero(acumulado):>10}")


def mostrar_busqueda(grafo, titulo, ruta, costo, orden, historial, titulo_cola, formato_paso):
    """Lo que imprime main.py para un algoritmo: orden de visita, ruta, cifras, tramos y cola."""
    print("\n" + LINEA)
    print(titulo)
    print(LINEA)
    print("Orden de visita (nodos expandidos):")
    print(_cadena(orden))
    print("\nRuta encontrada:")
    print(_cadena(ruta))
    print(f"\nConexiones: {len(ruta) - 1}  |  Distancia total: {_km(costo)}  |  Nodos expandidos: {len(orden)}")
    print("\nCosto acumulado tramo a tramo:")
    mostrar_desglose(grafo, ruta)
    print(f"\n{titulo_cola}:")
    for paso, estado in enumerate(historial, start=1):
        elementos = [formato_paso(elemento) for elemento in estado]
        resto = f", ... (+{len(elementos) - 6})" if len(elementos) > 6 else ""
        print(f"  Paso {paso:>2}: {', '.join(elementos[:6])}{resto}")


def mostrar_comparacion(bfs, ucs, voraz):
    """Tabla BFS vs UCS vs Voraz y las conclusiones. Cada argumento es (ruta, costo, orden)."""
    (ruta_bfs, costo_bfs, orden_bfs), (ruta_ucs, costo_ucs, orden_ucs) = bfs, ucs
    ruta_voraz, costo_voraz, orden_voraz = voraz
    print("\n" + LINEA)
    print("COMPARACIÓN BFS vs UCS vs VORAZ")
    print(LINEA)
    print(f"  {'':<22} {'BFS':>12} {'UCS':>12} {'Voraz':>12}")
    print(f"  {'Conexiones':<22} {len(ruta_bfs) - 1:>12} {len(ruta_ucs) - 1:>12}"
          f" {len(ruta_voraz) - 1:>12}")
    print(f"  {'Distancia total':<22} {_km(costo_bfs):>12} {_km(costo_ucs):>12}"
          f" {_km(costo_voraz):>12}")
    print(f"  {'Nodos expandidos':<22} {len(orden_bfs):>12} {len(orden_ucs):>12}"
          f" {len(orden_voraz):>12}")
    print()
    _conclusion_bfs_ucs(bfs, ucs)
    print()
    _conclusion_voraz(ucs, voraz)


def _conclusion_bfs_ucs(bfs, ucs):
    """Qué separa la ruta de BFS de la de UCS."""
    (ruta_bfs, costo_bfs, _), (ruta_ucs, costo_ucs, _) = bfs, ucs
    if ruta_bfs == ruta_ucs:
        print("BFS y UCS encontraron LA MISMA ruta: la de menos conexiones")
        print("también es la de menor distancia.")
        return
    diferencia = round(costo_bfs - costo_ucs, 1)
    if diferencia == 0:
        print("Las rutas son DISTINTAS pero miden lo mismo: hay un empate en distancia.")
        return
    print(f"Las rutas de BFS y UCS son DISTINTAS. UCS ahorra {_km(diferencia)} frente a BFS.")
    extra = len(ruta_ucs) - len(ruta_bfs)
    if extra > 0:
        print("BFS escogió la ruta con menos conexiones sin mirar las distancias;")
        print(f"UCS aceptó {extra} {'conexión' if extra == 1 else 'conexiones'} más a cambio de recorrer menos kilómetros.")
    else:
        print("Con el mismo número de conexiones, UCS escogió el camino más corto")
        print("y BFS se quedó con el primero que encontró.")


def _conclusion_voraz(ucs, voraz):
    """Qué ganó y qué perdió la voraz frente a UCS, que es la óptima."""
    (ruta_ucs, costo_ucs, orden_ucs), (ruta_voraz, costo_voraz, orden_voraz) = ucs, voraz
    menos = len(orden_ucs) - len(orden_voraz)
    expansiones = "1 nodo menos" if menos == 1 else f"{menos} nodos menos"
    if ruta_voraz == ruta_ucs:
        print(f"La voraz llegó a la MISMA ruta óptima que UCS expandiendo {expansiones}:")
        print("la heurística la llevó derecho al destino, sin explorar en todas las direcciones.")
        return
    de_mas = round(costo_voraz - costo_ucs, 1)
    if de_mas <= 0:
        print("La voraz encontró otra ruta que mide lo mismo que la de UCS: hay un empate.")
        return
    print(f"La voraz expandió {expansiones} que UCS, pero su ruta cuesta {_km(de_mas)} MÁS.")
    print("Ese es su precio: mira solo lo que falta (h) e ignora lo ya recorrido (g),")
    print("así que no garantiza la ruta más corta.")


def mostrar_resultados(grafo, inicio, objetivo):
    """Corre los tres algoritmos e imprime todo. Devuelve False si no hay camino entre los centros."""
    ruta_bfs, orden_bfs, cola_bfs = busqueda_anchura(grafo, inicio, objetivo)
    if ruta_bfs is None:
        print("\nNo se encontró una ruta entre los centros seleccionados.")
        return False
    costo_bfs = costo_ruta(grafo, ruta_bfs)
    mostrar_busqueda(grafo, "BÚSQUEDA EN ANCHURA (BFS) - minimiza el NÚMERO DE CONEXIONES",
                     ruta_bfs, costo_bfs, orden_bfs, cola_bfs, "Evolución de la cola FIFO", str)

    ruta_ucs, costo_ucs, orden_ucs, frontera_ucs = busqueda_costo_uniforme(grafo, inicio, objetivo)
    mostrar_busqueda(grafo, "BÚSQUEDA DE COSTO UNIFORME (UCS) - minimiza la DISTANCIA TOTAL",
                     ruta_ucs, costo_ucs, orden_ucs, frontera_ucs,
                     "Evolución de la cola de prioridad, de menor a mayor costo acumulado (km)",
                     lambda entrada: f"{entrada[1]} ({_numero(entrada[0])})")

    ruta_voraz, costo_voraz, orden_voraz, frontera_voraz = busqueda_voraz(grafo, inicio, objetivo)
    mostrar_busqueda(grafo, "BÚSQUEDA VORAZ PRIMERO EL MEJOR - se guía por la DISTANCIA EN LÍNEA RECTA",
                     ruta_voraz, costo_voraz, orden_voraz, frontera_voraz,
                     "Evolución de la cola de prioridad, de menor a mayor distancia estimada que FALTA (km)",
                     lambda entrada: f"{entrada[1]} ({_numero(entrada[0])})")
    print(f"\nh({inicio}) = {_km(distancia_recta(inicio, objetivo))} en línea recta hasta {objetivo}: "
          "eso es todo lo que la voraz mira para decidir.")

    mostrar_comparacion((ruta_bfs, costo_bfs, orden_bfs), (ruta_ucs, costo_ucs, orden_ucs),
                        (ruta_voraz, costo_voraz, orden_voraz))
    return True


def abrir_mapa(inicio, objetivo):
    """Abre en el navegador el mapa interactivo con las tres rutas entre inicio y objetivo."""
    if not MAPA.exists():
        print(f"\nNo encontré el mapa interactivo ({MAPA}). Se genera con: python src/mapa_interactivo.py")
        return
    campos = f'"inicio": {json.dumps(inicio, ensure_ascii=False)}, "objetivo": {json.dumps(objetivo, ensure_ascii=False)}'
    html = CAMPOS_RUTA.sub(lambda _: campos, MAPA.read_text(encoding="utf-8"), count=1)
    archivo = Path(tempfile.gettempdir()) / "centros_comerciales_bogota_mapa.html"
    archivo.write_text(html, encoding="utf-8")
    if webbrowser.open(archivo.as_uri()):
        print("\nSe abrió el mapa en el navegador con las tres rutas.")
    else:
        print(f"\nNo se pudo abrir el navegador. Abre este archivo a mano: {archivo}")


def main():
    grafo = construir_adyacencia()
    centros = sorted(grafo, key=_clave)
    conexiones = sum(len(vecinos) for vecinos in grafo.values()) // 2
    print(LINEA)
    print("CENTROS COMERCIALES DE BOGOTÁ - búsquedas en grafos: BFS vs UCS vs Voraz")
    print(LINEA)
    print(f"{len(grafo)} centros comerciales y {conexiones} conexiones. El peso de cada conexión")
    print("es la distancia por vía en carro, en kilómetros.")

    while True:
        print("\nCentros comerciales:")
        mostrar_centros(centros)
        print("\nEscribe el número o el nombre del centro (las tildes y mayúsculas dan igual).")
        inicio = elegir_centro("Punto A (inicio): ", centros)
        objetivo = elegir_centro("Punto B (destino): ", centros)
        if inicio == objetivo:
            print("\nEl punto A y el punto B son el mismo centro comercial. Elige otro destino.")
            continue

        if mostrar_resultados(grafo, inicio, objetivo):
            abrir_mapa(inicio, objetivo)

        while True:
            opcion = input("\n[Enter] otra ruta   [M] abrir otra vez el mapa   [S] salir: ").strip().casefold()
            if opcion != "m":
                break
            abrir_mapa(inicio, objetivo)
        if opcion == "s":
            return


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
    except Exception:
        # En el ejecutable, que la ventana muestre el error en vez de cerrarse de golpe.
        traceback.print_exc()
        input("\nPresiona Enter para cerrar.")
        sys.exit(1)
