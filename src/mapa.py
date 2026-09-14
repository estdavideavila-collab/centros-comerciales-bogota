"""Mapa estático del grafo de centros comerciales sobre las localidades de Bogotá.

Genera imágenes PNG y SVG en docs/. El orden de capas (zorder), de abajo hacia
arriba, es fijo: el mapa de localidades SIEMPRE queda debajo del grafo.

    0  relleno de las localidades
    1  bordes de las localidades
    2  nombres de las localidades
    3  aristas del grafo
    4  distancias sobre las aristas
    5  nodos (centros comerciales)
    6  nombres de los centros comerciales

Uso desde main.py:
    from mapa import generar_grafo_completo, generar_ruta, generar_comparacion
    generar_ruta(ruta_bfs, "BFS")      # ruta = lista de nombres, del inicio al objetivo
    generar_ruta(ruta_ucs, "UCS")
    generar_comparacion(ruta_bfs, ruta_ucs)

Ejecución directa (comprueba localidades y genera mapa base y grafo completo):
    python src/mapa.py
"""

import itertools
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import shapely
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as Trazo
from shapely.geometry import LineString, Point, box

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from data.conexiones import validar_grafo  # noqa: E402

ARCHIVO_LOCALIDADES = RAIZ / "data" / "localidades.geojson"
CARPETA_SALIDA = RAIZ / "docs"

FUENTE = (
    "Límites de localidades: Secretaría Distrital de Planeación — Datos Abiertos Bogotá (CC BY 4.0). "
    "Coordenadas aproximadas. Distancias por vía: OSRM, © colaboradores de OpenStreetMap."
)

# El GeoJSON trae los nombres en mayúsculas y sin tildes; se reemplazan por código.
NOMBRES_LOCALIDADES = {
    "01": "Usaquén",
    "02": "Chapinero",
    "03": "Santa Fe",
    "04": "San Cristóbal",
    "05": "Usme",
    "06": "Tunjuelito",
    "07": "Bosa",
    "08": "Kennedy",
    "09": "Fontibón",
    "10": "Engativá",
    "11": "Suba",
    "12": "Barrios Unidos",
    "13": "Teusaquillo",
    "14": "Los Mártires",
    "15": "Antonio Nariño",
    "16": "Puente Aranda",
    "17": "La Candelaria",
    "18": "Rafael Uribe Uribe",
    "19": "Ciudad Bolívar",
    "20": "Sumapaz",
}

# Encuadre (lon_min, lat_min, lon_max, lat_max): zona urbana. Sumapaz se descarta,
# porque si se deja los 40 nodos quedan comprimidos en una esquina.
ENCUADRE = (-74.215, 4.545, -74.005, 4.830)
ANCHO_FIGURA = 17  # pulgadas; el alto se calcula para que el mapa llene la hoja
MARGENES = dict(left=0.01, right=0.99, bottom=0.025, top=0.955)
# Cuántos grados del mapa mide un punto tipográfico (para calcular dónde caben los textos).
PUNTOS_A_GRADOS = (ENCUADRE[2] - ENCUADRE[0]) / (ANCHO_FIGURA * (MARGENES["right"] - MARGENES["left"]) * 72)

# En la Zona Rosa, El Retiro, Andino y Atlantis Plaza están a 300-600 m entre sí
# y en el mapa general se tapan. Se dibujan también en un recuadro ampliado.
ZONA_AMPLIADA = (-74.0600, 4.6625, -74.0495, 4.6695)
UBICACION_AMPLIACION = (0.66, 0.005, 0.33, 0.16)  # fracción de los ejes: abajo a la derecha

Z_RELLENO, Z_BORDES, Z_NOMBRES_LOCALIDAD, Z_ARISTAS, Z_DISTANCIAS, Z_NODOS, Z_NOMBRES_NODO = range(7)

ALPHA_MAPA = 0.45
PALETA_LOCALIDADES = ["#F2D7A7", "#BFD8B8", "#C9D6EA", "#EBC6C4", "#D9CCE8", "#F0E3B2"]
COLOR_BORDE_LOCALIDAD = "#3C3C3C"
COLOR_ARISTA = "#4A4A4A"
COLOR_ARISTA_FONDO = "#8C8C8C"
COLOR_NODO = "#1B2A41"
COLOR_NODO_FONDO = "#7A7A7A"
COLOR_RUTA = {"BFS": "#E69F00", "UCS": "#0072B2"}
COLOR_INICIO = "#009E73"
COLOR_OBJETIVO = "#D55E00"
DESCRIPCION_ALGORITMO = {
    "BFS": "Búsqueda primero en anchura: menor número de conexiones",
    "UCS": "Búsqueda de costo uniforme: menor distancia total",
}

# Desplazamiento de la etiqueta (en puntos) y alineación. Elegidos para que cada
# nombre caiga en un hueco entre sus aristas y no tape distancias de otras.
POSICION_ETIQUETA_DEFECTO = ((0, 9), "center", "bottom")
POSICION_ETIQUETA = {
    "Santafé": ((-8, 5), "right", "bottom"),
    "Plaza Imperial": ((-9, 3), "right", "bottom"),
    "Centro Suba": ((9, 3), "left", "bottom"),
    "Cedritos 151": ((10, 2), "left", "bottom"),
    "Palatino": ((10, 0), "left", "center"),
    "Bulevar Niza": ((10, 2), "left", "bottom"),
    "Unicentro de Occidente": ((-9, 3), "right", "bottom"),
    "Portal 80": ((10, 0), "left", "center"),
    "Diverplaza": ((10, -2), "left", "top"),
    "Titán Plaza": ((-11, 0), "right", "center"),
    "Unicentro": ((10, 0), "left", "center"),
    "Hacienda Santa Bárbara": ((10, 2), "left", "bottom"),
    "Santa Ana": ((10, -3), "left", "top"),
    "Nuestro Bogotá": ((11, 0), "left", "center"),
    "El Retiro": ((-7, 7), "right", "bottom"),
    "Andino": ((9, 2), "left", "bottom"),
    "Atlantis Plaza": ((-8, -6), "right", "top"),
    "Hayuelos": ((-11, 0), "right", "center"),
    "Avenida Chile": ((9, -4), "left", "top"),
    "Galerías": ((-11, 0), "right", "center"),
    "Multiplaza La Felicidad": ((-10, -4), "right", "top"),
    "Gran Estación": ((12, 0), "left", "center"),
    "El Edén": ((9, 3), "left", "bottom"),
    "Plaza de las Américas": ((-9, -4), "right", "top"),
    "Plaza Central": ((0, -10), "center", "top"),
    "Mallplaza NQS": ((11, 0), "left", "center"),
    "Milenio Plaza": ((11, 0), "left", "center"),
    "Gran San Victorino": ((11, -2), "left", "top"),
    "Centro Mayor": ((10, -6), "left", "top"),
    "Paseo Villa del Río": ((-12, 0), "right", "center"),
    "Gran Plaza El Ensueño": ((-9, -4), "right", "top"),
    "Ciudad Tunal": ((9, -4), "left", "top"),
}

# Aristas que se dibujan curvas porque su recta pasaría encima de otro nodo y
# parecería que lo atraviesa. Valor: curvatura (arc3 de Matplotlib) en el sentido de la tupla.
ARISTAS_CURVAS = {
    # Multiplaza La Felicidad queda casi sobre la recta; la curva la esquiva por el norte.
    ("Hayuelos", "Salitre Plaza"): -0.3,
}


# ---------------------------------------------------------------------------
# Datos del mapa
# ---------------------------------------------------------------------------

def cargar_localidades():
    """Lee las localidades en EPSG:4326, sin Sumapaz, con columnas 'nombre' y 'color'."""
    # Las coordenadas del grafo están en grados; el mapa tiene que estar en el mismo sistema.
    localidades = gpd.read_file(ARCHIVO_LOCALIDADES).to_crs(epsg=4326)
    localidades["nombre"] = localidades["LOCCODIGO"].map(NOMBRES_LOCALIDADES)
    localidades = localidades[localidades["nombre"] != "Sumapaz"].reset_index(drop=True)
    localidades["color"] = _colores_localidades(localidades)
    return localidades


def verificar_localidades(grafo, localidades):
    """Devuelve los nodos que NO caen dentro de la localidad que dice su atributo.

    Cada elemento es (nodo, localidad_esperada, localidad_encontrada).
    Si aparece alguno, la coordenada del nodo está mal, no el código.
    """
    discrepancias = []
    for nodo, datos in grafo.nodes(data=True):
        punto = Point(datos["lon"], datos["lat"])
        encontrada = next(
            (fila.nombre for fila in localidades.itertuples() if punto.within(fila.geometry)),
            "fuera del mapa",
        )
        # "Bosa / Tunjuelito" acepta cualquiera de las dos.
        esperadas = [nombre.strip() for nombre in datos["localidad"].split("/")]
        if encontrada not in esperadas:
            discrepancias.append((nodo, datos["localidad"], encontrada))
    return discrepancias


def _colores_localidades(localidades):
    """Asigna colores suaves de modo que dos localidades vecinas nunca compartan color."""
    # El buffer cubre las rendijas que deja la simplificación de los bordes.
    contornos = [geometria.buffer(0.0005) for geometria in localidades.geometry]
    vecindad = nx.Graph()
    vecindad.add_nodes_from(localidades.index)
    for i, j in itertools.combinations(localidades.index, 2):
        if contornos[i].intersects(contornos[j]):
            vecindad.add_edge(i, j)
    colores = nx.greedy_color(vecindad, strategy="largest_first")
    return [PALETA_LOCALIDADES[colores[i] % len(PALETA_LOCALIDADES)] for i in localidades.index]


# ---------------------------------------------------------------------------
# Geometría auxiliar
# ---------------------------------------------------------------------------

def formato_km(valor):
    """Distancia con coma decimal, como se escribe en español: 43,6 km."""
    return f"{valor:.1f} km".replace(".", ",")


def _posiciones(grafo):
    # Longitud en X y latitud en Y. Al revés, el mapa queda acostado.
    return {nodo: (datos["lon"], datos["lat"]) for nodo, datos in grafo.nodes(data=True)}


def _en_zona_ampliada(punto):
    lon_min, lat_min, lon_max, lat_max = ZONA_AMPLIADA
    return lon_min <= punto[0] <= lon_max and lat_min <= punto[1] <= lat_max


def _caja_ampliacion():
    """El recuadro de la ampliación, en coordenadas del mapa."""
    lon_min, lat_min, lon_max, lat_max = ENCUADRE
    x, y, ancho, alto = UBICACION_AMPLIACION
    return box(
        lon_min + x * (lon_max - lon_min), lat_min + y * (lat_max - lat_min),
        lon_min + (x + ancho) * (lon_max - lon_min), lat_min + (y + alto) * (lat_max - lat_min),
    )


def _medidas_texto(texto, tamano):
    """Ancho y alto aproximados (en grados) que ocupa un texto de ese tamaño."""
    return (len(texto) * 0.7 * tamano + 6) * PUNTOS_A_GRADOS, (tamano * 1.4 + 4) * PUNTOS_A_GRADOS


def _caja_etiqueta(nodo, punto, tamano):
    """Rectángulo aproximado que ocupa el nombre de un nodo, según POSICION_ETIQUETA."""
    (dx, dy), ha, va = POSICION_ETIQUETA.get(nodo, POSICION_ETIQUETA_DEFECTO)
    ancho, alto = _medidas_texto(nodo, tamano)
    x0 = punto[0] + dx * PUNTOS_A_GRADOS - {"left": 0, "center": ancho / 2, "right": ancho}[ha]
    y0 = punto[1] + dy * PUNTOS_A_GRADOS - {"bottom": 0, "center": alto / 2, "top": alto}[va]
    return box(x0, y0, x0 + ancho, y0 + alto)


def _obstaculos(grafo, pos, con_ampliacion, tamano_nombres=9):
    """Todo lo que un nombre de localidad no debe tapar: nodos, aristas, sus etiquetas y la ampliación.

    Van como piezas sueltas en un árbol espacial (STRtree): medir la distancia a la pieza
    más cercana da lo mismo que medirla contra la unión de todas, pero es mucho más
    rápido, porque la unión es un solo polígono con miles de vértices.
    """
    geometrias = [Point(p).buffer(8 * PUNTOS_A_GRADOS) for p in pos.values()]
    geometrias += [LineString([pos[a], pos[b]]).buffer(3 * PUNTOS_A_GRADOS) for a, b in grafo.edges]
    geometrias += [_caja_etiqueta(nodo, p, tamano_nombres) for nodo, p in pos.items()]
    if con_ampliacion:
        geometrias.append(_caja_ampliacion())
    return shapely.STRtree(geometrias)


def _punto_para_nombre(visible, texto, tamano, obstaculos):
    """Centro para el nombre de una localidad y si el nombre cabe entero en ella.

    Se prueban posiciones en una rejilla: el rectángulo del nombre debe caber dentro
    de la localidad y quedar lo más lejos posible del grafo y de los bordes. Si
    ninguna posición queda libre, se elige la que menos tapa.
    """
    mayor = max(getattr(visible, "geoms", [visible]), key=lambda parte: parte.area)
    shapely.prepare(mayor)  # acelera las pruebas de contención, que se hacen miles de veces
    xmin, ymin, xmax, ymax = mayor.bounds
    xs, ys = np.meshgrid(np.arange(xmin, xmax, 0.0012), np.arange(ymin, ymax, 0.0012))
    xs, ys = xs.ravel(), ys.ravel()
    dentro = shapely.contains_xy(mayor, xs, ys)
    if not dentro.any():
        return mayor.representative_point(), False
    xs, ys = xs[dentro], ys[dentro]

    ancho, alto = _medidas_texto(texto, tamano)
    cajas = shapely.box(xs - ancho / 2, ys - alto / 2, xs + ancho / 2, ys + alto / 2)
    holgura = shapely.distance(cajas, mayor.boundary)
    if obstaculos is not None:
        (indices, _), distancias = obstaculos.query_nearest(cajas, return_distance=True, all_matches=False)
        holgura[indices] = np.minimum(holgura[indices], distancias)
        if not holgura.any():
            # Ninguna posición queda libre: gana la que menos área tapa. Si hay alguna libre
            # no hace falta calcularlo, porque una libre siempre le gana a una tapada.
            holgura = -shapely.area(shapely.intersection(cajas, shapely.union_all(obstaculos.geometries)))
    # Caber entero en la localidad pesa más que cualquier holgura.
    caben = shapely.contains(mayor, cajas)
    mejor = int(np.argmax(holgura + np.where(caben, 1.0, 0.0)))
    return Point(xs[mejor], ys[mejor]), bool(caben[mejor])


# ---------------------------------------------------------------------------
# Capas de dibujo
# ---------------------------------------------------------------------------

def _dibujar_localidades(ax, localidades):
    """Capas 0 y 1: relleno y bordes de las localidades.

    Arma las mismas colecciones de Matplotlib que localidades.plot() y
    localidades.boundary.plot(), pero sin el redibujado de la figura entera que
    GeoPandas hace al final de cada .plot(): eran cuatro por imagen, y los del
    recuadro ampliado repintaban todo el mapa ya dibujado.
    """
    parches, colores, bordes = [], [], []
    # Normalizadas como las deja GeoPandas antes de dibujar (orden y sentido de los
    # anillos); si no, el suavizado de los bordes cambia en algunos píxeles.
    for relleno, borde, color in zip(localidades.geometry.normalize(), localidades.boundary.normalize(),
                                     localidades["color"]):
        for poligono in getattr(relleno, "geoms", [relleno]):
            anillos = [np.asarray(anillo.coords)[:, :2] for anillo in (poligono.exterior, *poligono.interiors)]
            parches.append(PathPatch(Trazo.make_compound_path(*(Trazo(a, closed=True) for a in anillos))))
            colores.append(color)
        bordes += [np.asarray(linea.coords)[:, :2] for linea in getattr(borde, "geoms", [borde])]
    ax.add_collection(PatchCollection(parches, facecolor=colores, alpha=ALPHA_MAPA, linewidth=0, zorder=Z_RELLENO))
    ax.add_collection(LineCollection(bordes, color=COLOR_BORDE_LOCALIDAD, linewidth=0.8, zorder=Z_BORDES))


def dibujar_mapa_base(ax, localidades, obstaculos=None, con_nombres=True):
    """Capas 0 a 2: relleno, bordes y nombres de las localidades."""
    _dibujar_localidades(ax, localidades)
    if not con_nombres:
        return

    marco = box(*ENCUADRE)
    for fila in localidades.itertuples():
        # El nombre va en la parte visible de la localidad (Usme o Ciudad Bolívar
        # tienen gran parte fuera del encuadre), en el hueco más libre del grafo.
        visible = fila.geometry.intersection(marco)
        if visible.is_empty:
            continue
        texto = fila.nombre.upper()
        tamano = 9 if visible.area < 0.0006 else 12
        punto, cabe = _punto_para_nombre(visible, texto, tamano, obstaculos)
        if not cabe and visible.area < 0.1 * fila.geometry.area:
            continue  # apenas asoma en el borde (Usme): el nombre quedaría cortado
        ax.text(
            punto.x, punto.y, texto, ha="center", va="center", fontsize=tamano,
            fontweight="bold", color="#505050", alpha=0.7, zorder=Z_NOMBRES_LOCALIDAD,
        )


def _curvatura(a, b):
    """(origen, destino, curvatura) si la arista se dibuja curva; None si va recta."""
    if (a, b) in ARISTAS_CURVAS:
        return a, b, ARISTAS_CURVAS[(a, b)]
    if (b, a) in ARISTAS_CURVAS:
        return b, a, ARISTAS_CURVAS[(b, a)]
    return None


def _dibujar_aristas(ax, grafo, pos, aristas, color, ancho, alpha):
    rectas = [arista for arista in aristas if _curvatura(*arista) is None]
    if rectas:
        coleccion = nx.draw_networkx_edges(
            grafo, pos, edgelist=rectas, ax=ax, edge_color=color, width=ancho, alpha=alpha
        )
        coleccion.set_zorder(Z_ARISTAS)
    for curva in filter(None, (_curvatura(*arista) for arista in aristas)):
        origen, destino, rad = curva
        flechas = nx.draw_networkx_edges(
            grafo, pos, edgelist=[(origen, destino)], ax=ax, edge_color=color, width=ancho,
            alpha=alpha, arrows=True, arrowstyle="-", connectionstyle=f"arc3,rad={rad}",
        )
        for flecha in flechas:
            flecha.set_zorder(Z_ARISTAS)


def _dibujar_distancias(ax, grafo, pos, aristas, tamano):
    # Las etiquetas de las aristas curvas se ubican sobre la curva, no sobre la recta.
    por_estilo = {"arc3": {}}
    for a, b in aristas:
        curva = _curvatura(a, b)
        if curva is None:
            por_estilo["arc3"][(a, b)] = formato_km(grafo[a][b]["peso"])
        else:
            origen, destino, rad = curva
            por_estilo.setdefault(f"arc3,rad={rad}", {})[(origen, destino)] = formato_km(grafo[a][b]["peso"])

    for estilo, etiquetas in por_estilo.items():
        if not etiquetas:
            continue
        textos = nx.draw_networkx_edge_labels(
            grafo, pos, edge_labels=etiquetas, ax=ax, font_size=tamano, rotate=False,
            connectionstyle=estilo,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.8),
        )
        for texto in textos.values():
            texto.set_zorder(Z_DISTANCIAS)


def _dibujar_nodos(ax, grafo, pos, nodos, color, tamanos, forma="o"):
    coleccion = nx.draw_networkx_nodes(
        grafo, pos, nodelist=nodos, ax=ax, node_color=color, node_size=tamanos,
        node_shape=forma, edgecolors="white", linewidths=1.5,
    )
    coleccion.set_zorder(Z_NODOS)


def _dibujar_nombres(ax, pos, nodos, tamano, destacados=()):
    for nodo in nodos:
        (dx, dy), ha, va = POSICION_ETIQUETA.get(nodo, POSICION_ETIQUETA_DEFECTO)
        destacado = nodo in destacados
        ax.annotate(
            nodo, pos[nodo], xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
            fontsize=tamano + 2 if destacado else tamano,
            fontweight="bold" if destacado else "normal",
            color="#111111" if destacado or not destacados else "#555555",
            zorder=Z_NOMBRES_NODO,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#999999",
                      linewidth=0.5, alpha=0.85),
        )


def _tamanos_por_grado(grafo, nodos, base=70, por_conexion=45):
    return [base + por_conexion * grafo.degree(nodo) for nodo in nodos]


def _fuera_de_zona(pos, aristas):
    """Aristas cuya distancia se escribe en el mapa general (las de la Zona Rosa van en la ampliación)."""
    return [(a, b) for a, b in aristas if not (_en_zona_ampliada(pos[a]) and _en_zona_ampliada(pos[b]))]


def _capas_grafo_completo(ax, grafo, pos, es_ampliacion=False):
    """Capas 3 a 6 del grafo completo."""
    aristas = list(grafo.edges)
    _dibujar_aristas(ax, grafo, pos, aristas, COLOR_ARISTA, 1.6, 0.85)
    con_distancia = aristas if es_ampliacion else _fuera_de_zona(pos, aristas)
    _dibujar_distancias(ax, grafo, pos, con_distancia, tamano=11 if es_ampliacion else 8)
    _dibujar_nodos(ax, grafo, pos, list(grafo), COLOR_NODO, _tamanos_por_grado(grafo, grafo))
    _dibujar_nombres(ax, pos, list(grafo), tamano=11 if es_ampliacion else 9)


def _capas_rutas(ax, grafo, pos, rutas, omitir_zona=False):
    """Capas 3 a 6 con el grafo en gris de fondo y cada ruta resaltada encima.

    rutas: lista de (nodos, color, ancho, etiqueta_leyenda), en orden de dibujo.
    """
    _dibujar_aristas(ax, grafo, pos, list(grafo.edges), COLOR_ARISTA_FONDO, 1.2, 0.6)

    resaltadas = []
    for nodos, color, ancho, _ in rutas:
        aristas = list(zip(nodos, nodos[1:]))
        _dibujar_aristas(ax, grafo, pos, aristas, color, ancho, 0.95)
        resaltadas += [a for a in aristas if a not in resaltadas]
    _dibujar_distancias(ax, grafo, pos, _fuera_de_zona(pos, resaltadas) if omitir_zona else resaltadas, 11)

    en_ruta = list(dict.fromkeys(nodo for nodos, *_ in rutas for nodo in nodos))
    fuera = [nodo for nodo in grafo if nodo not in en_ruta]
    _dibujar_nodos(ax, grafo, pos, fuera, COLOR_NODO_FONDO, 90)
    _dibujar_nodos(ax, grafo, pos, en_ruta, COLOR_NODO, 260)

    inicio, objetivo = rutas[0][0][0], rutas[0][0][-1]
    _dibujar_nodos(ax, grafo, pos, [inicio], COLOR_INICIO, 650, forma="s")
    _dibujar_nodos(ax, grafo, pos, [objetivo], COLOR_OBJETIVO, 900, forma="*")
    _dibujar_nombres(ax, pos, list(grafo), tamano=8, destacados=set(en_ruta))


def _dibujar_ampliacion(ax, localidades, dibujar_capas):
    """Recuadro con la Zona Rosa ampliada. dibujar_capas(eje) pinta el grafo en ese eje."""
    detalle = ax.inset_axes(UBICACION_AMPLIACION, zorder=10)
    dibujar_mapa_base(detalle, localidades, con_nombres=False)
    dibujar_capas(detalle)

    lon_min, lat_min, lon_max, lat_max = ZONA_AMPLIADA
    detalle.set_xlim(lon_min, lon_max)
    detalle.set_ylim(lat_min, lat_max)
    detalle.set_aspect("equal")
    detalle.set_xticks([])
    detalle.set_yticks([])
    detalle.set_title("Ampliación: Zona Rosa (Chapinero)", fontsize=13, fontweight="bold")
    for borde in detalle.spines.values():
        borde.set_linewidth(1.5)

    # Marca en el mapa general de qué zona es la ampliación.
    ax.add_patch(Rectangle(
        (lon_min, lat_min), lon_max - lon_min, lat_max - lat_min,
        fill=False, edgecolor="#222222", linewidth=1.3, linestyle="--", zorder=Z_DISTANCIAS,
    ))


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

def _nueva_figura(titulo, subtitulo, localidades, obstaculos=None):
    lon_min, lat_min, lon_max, lat_max = ENCUADRE
    proporcion = (lat_max - lat_min) / (lon_max - lon_min)
    ancho_util = MARGENES["right"] - MARGENES["left"]
    alto_util = MARGENES["top"] - MARGENES["bottom"]
    fig, ax = plt.subplots(figsize=(ANCHO_FIGURA, ANCHO_FIGURA * ancho_util * proporcion / alto_util))
    fig.subplots_adjust(**MARGENES)
    fig.suptitle(titulo, fontsize=24, fontweight="bold", y=0.997)
    fig.text(0.5, 0.967, subtitulo, ha="center", fontsize=14, color="#333333")
    fig.text(0.5, 0.008, FUENTE, ha="center", fontsize=10, color="#555555")
    dibujar_mapa_base(ax, localidades, obstaculos)
    return fig, ax


def _guardar(fig, ax, nombre, carpeta):
    # El encuadre se fija al final porque NetworkX reajusta los ejes al dibujar.
    ax.set_xlim(ENCUADRE[0], ENCUADRE[2])
    ax.set_ylim(ENCUADRE[1], ENCUADRE[3])
    ax.set_aspect("equal")
    ax.axis("off")

    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivos = []
    for extension in ("png", "svg"):
        archivo = carpeta / f"{nombre}.{extension}"
        fig.savefig(archivo, dpi=150, bbox_inches="tight", facecolor="white")
        archivos.append(archivo)
    plt.close(fig)
    return archivos


def validar_ruta(grafo, ruta):
    """Revisa que la ruta sea un camino real del grafo y devuelve su distancia total."""
    if not ruta:
        raise ValueError("La ruta está vacía")
    desconocidos = [nodo for nodo in ruta if nodo not in grafo]
    if desconocidos:
        raise ValueError(f"La ruta tiene nodos que no existen en el grafo: {desconocidos}")
    for a, b in zip(ruta, ruta[1:]):
        if not grafo.has_edge(a, b):
            raise ValueError(f"La ruta salta de {a} a {b}, pero no hay arista entre ellos")
    return sum(grafo[a][b]["peso"] for a, b in zip(ruta, ruta[1:]))


def _figura_rutas(grafo, localidades, titulo, subtitulo, rutas, nombre, carpeta):
    pos = _posiciones(grafo)
    con_ampliacion = any(_en_zona_ampliada(pos[nodo]) for nodos, *_ in rutas for nodo in nodos)
    fig, ax = _nueva_figura(titulo, subtitulo, localidades, _obstaculos(grafo, pos, con_ampliacion))
    _capas_rutas(ax, grafo, pos, rutas, omitir_zona=con_ampliacion)
    if con_ampliacion:
        _dibujar_ampliacion(ax, localidades, lambda eje: _capas_rutas(eje, grafo, pos, rutas))

    inicio, objetivo = rutas[0][0][0], rutas[0][0][-1]
    leyenda = [Line2D([], [], color=color, linewidth=ancho, label=etiqueta) for _, color, ancho, etiqueta in rutas]
    leyenda += [
        Line2D([], [], marker="s", linestyle="", markersize=14, color=COLOR_INICIO, label=f"Inicio: {inicio}"),
        Line2D([], [], marker="*", linestyle="", markersize=20, color=COLOR_OBJETIVO, label=f"Objetivo: {objetivo}"),
    ]
    ax.legend(handles=leyenda, loc="upper left", fontsize=14, framealpha=0.95, borderpad=1)
    return _guardar(fig, ax, nombre, carpeta)


def generar_mapa_base(localidades=None, carpeta=CARPETA_SALIDA):
    """Solo el mapa de localidades, sin grafo. Sirve para comprobar que se reconoce Bogotá."""
    localidades = cargar_localidades() if localidades is None else localidades
    fig, ax = _nueva_figura(
        "Localidades de Bogotá D.C.", "Zona urbana (sin Sumapaz) — mapa base del proyecto", localidades
    )
    return _guardar(fig, ax, "mapa_base", carpeta)


def generar_grafo_completo(grafo=None, localidades=None, carpeta=CARPETA_SALIDA):
    """Grafo completo sobre el mapa, con todas las distancias. Guarda docs/grafo_completo."""
    grafo = validar_grafo() if grafo is None else grafo
    localidades = cargar_localidades() if localidades is None else localidades
    pos = _posiciones(grafo)
    fig, ax = _nueva_figura(
        "Centros comerciales de Bogotá D.C. — grafo no dirigido ponderado",
        f"{grafo.number_of_nodes()} centros comerciales · {grafo.number_of_edges()} conexiones · "
        "peso = distancia por vía en carro (km) · tamaño del nodo = número de conexiones",
        localidades,
        _obstaculos(grafo, pos, con_ampliacion=True),
    )
    _capas_grafo_completo(ax, grafo, pos)
    _dibujar_ampliacion(ax, localidades, lambda eje: _capas_grafo_completo(eje, grafo, pos, es_ampliacion=True))
    return _guardar(fig, ax, "grafo_completo", carpeta)


def generar_ruta(ruta, algoritmo, grafo=None, localidades=None, carpeta=CARPETA_SALIDA):
    """Dibuja una ruta resaltada sobre el grafo y la guarda como docs/ruta_<algoritmo>.

    ruta: lista de nombres de nodo, del inicio al objetivo (lo que devuelve BFS o UCS).
    algoritmo: "BFS" o "UCS"; define el color, el título y el nombre del archivo.
    """
    grafo = validar_grafo() if grafo is None else grafo
    localidades = cargar_localidades() if localidades is None else localidades
    distancia = validar_ruta(grafo, ruta)
    conexiones = len(ruta) - 1
    return _figura_rutas(
        grafo, localidades,
        f"Ruta {algoritmo}: {ruta[0]} → {ruta[-1]}",
        f"{DESCRIPCION_ALGORITMO[algoritmo]} · {conexiones} conexiones · {formato_km(distancia)}",
        [(ruta, COLOR_RUTA[algoritmo], 7, f"{algoritmo}: {conexiones} conexiones · {formato_km(distancia)}")],
        f"ruta_{algoritmo.lower()}", carpeta,
    )


def generar_comparacion(ruta_bfs, ruta_ucs, grafo=None, localidades=None, carpeta=CARPETA_SALIDA):
    """Las rutas de BFS y UCS superpuestas en la misma imagen. Guarda docs/comparacion_rutas."""
    grafo = validar_grafo() if grafo is None else grafo
    localidades = cargar_localidades() if localidades is None else localidades
    if (ruta_bfs[0], ruta_bfs[-1]) != (ruta_ucs[0], ruta_ucs[-1]):
        raise ValueError("BFS y UCS deben tener el mismo inicio y el mismo objetivo para compararse")
    km_bfs, km_ucs = validar_ruta(grafo, ruta_bfs), validar_ruta(grafo, ruta_ucs)
    resumen_bfs = f"BFS: {len(ruta_bfs) - 1} conexiones · {formato_km(km_bfs)}"
    resumen_ucs = f"UCS: {len(ruta_ucs) - 1} conexiones · {formato_km(km_ucs)}"
    # BFS va debajo y más ancha, así los tramos compartidos se ven de los dos colores.
    return _figura_rutas(
        grafo, localidades,
        f"BFS vs UCS: {ruta_bfs[0]} → {ruta_bfs[-1]}",
        f"{resumen_bfs}   |   {resumen_ucs}",
        [(ruta_bfs, COLOR_RUTA["BFS"], 12, resumen_bfs), (ruta_ucs, COLOR_RUTA["UCS"], 5, resumen_ucs)],
        "comparacion_rutas", carpeta,
    )


if __name__ == "__main__":
    grafo = validar_grafo()
    localidades = cargar_localidades()

    discrepancias = verificar_localidades(grafo, localidades)
    if discrepancias:
        print("Nodos que NO caen en su localidad (revisar la coordenada):")
        for nodo, esperada, encontrada in discrepancias:
            print(f"  {nodo}: dice {esperada}, cae en {encontrada}")
    else:
        print(f"Los {grafo.number_of_nodes()} nodos caen dentro de su localidad.")

    for archivo in generar_mapa_base(localidades) + generar_grafo_completo(grafo, localidades):
        print(f"Guardado: {archivo.relative_to(RAIZ)}")
