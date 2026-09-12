"""Mapa interactivo (HTML) del grafo de centros comerciales, hecho con Folium.

Complementa a mapa.py: la imagen estática con las localidades de fondo es la que
va en las diapositivas; este HTML permite hacer zoom sobre un mapa real de Bogotá,
prender y apagar capas y ver los datos de cada centro comercial con un clic.

Uso desde main.py:
    from mapa_interactivo import generar_mapa_interactivo
    generar_mapa_interactivo(rutas={"BFS": ruta_bfs, "UCS": ruta_ucs})

Ejecución directa (sin rutas):
    python src/mapa_interactivo.py      -> docs/mapa_interactivo.html
"""

import html
import sys
from pathlib import Path

import folium

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from data.conexiones import validar_grafo  # noqa: E402
from mapa import (  # noqa: E402
    CARPETA_SALIDA, COLOR_ARISTA, COLOR_NODO, COLOR_RUTA, _km, _validar_ruta, cargar_localidades,
)


def _ficha(grafo, nodo):
    """HTML del recuadro que aparece al hacer clic en un centro comercial."""
    datos = grafo.nodes[nodo]
    vecinos = "".join(
        f"<li>{html.escape(vecino)}: {_km(grafo[nodo][vecino]['peso'])}</li>" for vecino in grafo[nodo]
    )
    return (
        f"<b>{html.escape(nodo)}</b><br>"
        f"Localidad: {html.escape(datos['localidad'])}<br>"
        f"Dirección: {html.escape(datos['direccion'])}<br>"
        f"Conexiones ({grafo.degree(nodo)}):<ul style='margin:4px 0 0 16px;padding:0'>{vecinos}</ul>"
    )


def generar_mapa_interactivo(grafo=None, rutas=None, carpeta=CARPETA_SALIDA):
    """Guarda docs/mapa_interactivo.html y devuelve su ruta.

    rutas: diccionario opcional {"BFS": [...], "UCS": [...]} con listas de nombres,
    del inicio al objetivo. Cada ruta queda como una capa que se puede prender y apagar.
    """
    grafo = validar_grafo() if grafo is None else grafo
    rutas = rutas or {}
    latitudes = [d["lat"] for _, d in grafo.nodes(data=True)]
    longitudes = [d["lon"] for _, d in grafo.nodes(data=True)]

    mapa = folium.Map(location=[sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)],
                      zoom_start=12, tiles="OpenStreetMap")

    localidades = cargar_localidades()[["nombre", "color", "geometry"]]
    folium.GeoJson(
        localidades, name="Localidades",
        style_function=lambda f: {"fillColor": f["properties"]["color"], "color": "#3C3C3C",
                                  "weight": 1, "fillOpacity": 0.35},
        tooltip=folium.GeoJsonTooltip(fields=["nombre"], aliases=["Localidad:"]),
    ).add_to(mapa)

    capa_conexiones = folium.FeatureGroup(name="Conexiones")
    for a, b, datos in grafo.edges(data=True):
        folium.PolyLine(
            [(grafo.nodes[a]["lat"], grafo.nodes[a]["lon"]), (grafo.nodes[b]["lat"], grafo.nodes[b]["lon"])],
            color=COLOR_ARISTA, weight=2, opacity=0.8, tooltip=f"{a} – {b}: {_km(datos['peso'])}",
        ).add_to(capa_conexiones)
    capa_conexiones.add_to(mapa)

    for algoritmo, ruta in rutas.items():
        distancia = _validar_ruta(grafo, ruta)
        capa_ruta = folium.FeatureGroup(name=f"Ruta {algoritmo}")
        folium.PolyLine(
            [(grafo.nodes[n]["lat"], grafo.nodes[n]["lon"]) for n in ruta],
            color=COLOR_RUTA[algoritmo], weight=7, opacity=0.9,
            tooltip=f"{algoritmo}: {len(ruta) - 1} conexiones · {_km(distancia)}",
        ).add_to(capa_ruta)
        capa_ruta.add_to(mapa)

    capa_centros = folium.FeatureGroup(name="Centros comerciales")
    for nodo, datos in grafo.nodes(data=True):
        folium.CircleMarker(
            [datos["lat"], datos["lon"]], radius=4 + grafo.degree(nodo),
            color="white", weight=1.5, fill=True, fill_color=COLOR_NODO, fill_opacity=1,
            tooltip=nodo, popup=folium.Popup(_ficha(grafo, nodo), max_width=320),
        ).add_to(capa_centros)
    capa_centros.add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.fit_bounds([[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]])

    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / "mapa_interactivo.html"
    mapa.save(archivo)
    return archivo


if __name__ == "__main__":
    print(f"Guardado: {generar_mapa_interactivo().relative_to(RAIZ)}")
