"""Mapa interactivo (HTML) del grafo de centros comerciales, hecho con Folium.

Complementa a mapa.py: la imagen estática con las localidades de fondo es la que
va en las diapositivas; este HTML permite hacer zoom, prender y apagar capas y ver
los datos de cada centro comercial con un clic. No lleva mapa de calles de fondo:
las coordenadas son aproximadas y sobre las calles reales los puntos se ven corridos.

Trae además el panel "Buscar ruta": se elige el punto A (inicio) y el punto B
(destino), en las listas o con los botones del recuadro de cada centro, y el
navegador corre BFS y UCS, dibuja las dos rutas y muestra lo mismo que main.py:
ruta, conexiones, km, costo tramo a tramo, orden de visita, evolución de la cola
y la comparación. Los algoritmos están en JavaScript copiados paso a paso de
src/bfs.py y src/ucs.py, sobre el mismo grafo y con el mismo orden de vecinos,
así que dan exactamente las mismas rutas.

Funciona sin internet: Leaflet y jQuery van dentro del HTML (copiados en src/web/),
en vez de enlazarse desde un CDN como hace Folium. El ejecutable de la exposición
(src/presentacion.py) abre este HTML cambiando los campos "inicio" y "objetivo" de
DATOS, así que el formato de esos dos campos no debe cambiar.

Uso desde main.py:
    from mapa_interactivo import generar_mapa_interactivo
    generar_mapa_interactivo(rutas={"BFS": ruta_bfs, "UCS": ruta_ucs})
El HTML abre con el inicio y el destino de esas rutas ya elegidos.

Ejecución directa (sin inicio ni destino elegidos):
    python src/mapa_interactivo.py      -> docs/mapa_interactivo.html
"""

import html
import json
import sys
from pathlib import Path

import folium
from jinja2 import Template

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_WEB = Path(__file__).resolve().parent / "web"
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from data.conexiones import validar_grafo  # noqa: E402
from mapa import (  # noqa: E402
    ALPHA_MAPA, CARPETA_SALIDA, COLOR_ARISTA, COLOR_INICIO, COLOR_NODO, COLOR_OBJETIVO, COLOR_RUTA,
    DESCRIPCION_ALGORITMO, cargar_localidades, formato_km, validar_ruta,
)


def _ficha(grafo, nodo):
    """HTML del recuadro que aparece al hacer clic en un centro comercial."""
    datos = grafo.nodes[nodo]
    centro = html.escape(nodo)
    vecinos = "".join(
        f"<li>{html.escape(vecino)}: {formato_km(grafo[nodo][vecino]['peso'])}</li>" for vecino in grafo[nodo]
    )
    return (
        f"<b>{centro}</b><br>"
        f"Localidad: {html.escape(datos['localidad'])}<br>"
        f"Dirección: {html.escape(datos['direccion'])}<br>"
        f"Conexiones ({grafo.degree(nodo)}):<ul style='margin:4px 0 0 16px;padding:0'>{vecinos}</ul>"
        f"<div class='ficha-botones'>"
        f"<button type='button' data-rol='inicio' data-centro='{centro}'>Desde aquí (A)</button>"
        f"<button type='button' data-rol='destino' data-centro='{centro}'>Hasta aquí (B)</button></div>"
    )


def _extremos(grafo, rutas):
    """Inicio y destino con que abre el panel, sacados de las rutas que manda main.py."""
    for ruta in rutas.values():
        validar_ruta(grafo, ruta)
    pares = {(ruta[0], ruta[-1]) for ruta in rutas.values()}
    if len(pares) > 1:
        raise ValueError(f"Las rutas no van entre los mismos centros: {sorted(pares)}")
    return pares.pop() if pares else (None, None)


_PLANTILLA_PANEL = r"""
{% macro header(this, kwargs) %}
<style>
#rutas-panel {
    position: absolute; top: 10px; left: 10px; z-index: 1000;
    width: min(340px, calc(100% - 20px)); max-height: calc(100% - 20px); overflow-y: auto;
    box-sizing: border-box; background: #fff; color: #1B2A41;
    border-radius: 8px; box-shadow: 0 1px 6px rgba(0, 0, 0, .35);
    font: 13px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
#rutas-panel > summary {
    position: sticky; top: 0; background: #fff; cursor: pointer;
    padding: 10px 12px; font-weight: 600; font-size: 14px;
}
/* Sin Bootstrap, las listas y botones no traen box-sizing: border-box y se saldrían del panel. */
#rutas-panel *, .ficha-botones * { box-sizing: border-box; }
.rutas-cuerpo { padding: 0 12px 12px; }
.rutas-cuerpo label { display: block; margin-bottom: 8px; font-size: 12px; font-weight: 600; }
.rutas-cuerpo select { display: block; width: 100%; margin-top: 3px; padding: 4px; font: inherit; font-weight: 400; }
.rutas-botones, .ficha-botones { display: flex; gap: 6px; }
.ficha-botones { margin-top: 8px; }
.rutas-botones button, .ficha-botones button {
    flex: 1; padding: 5px 8px; font: inherit; font-size: 12px; cursor: pointer;
    background: #f4f5f7; color: #1B2A41; border: 1px solid #c5cad3; border-radius: 5px;
}
.rutas-botones button:hover, .ficha-botones button:hover { background: #e6e9ee; }
.rutas-nota { margin: 10px 0 0; color: #5b6472; font-size: 12px; }
.rutas-algo { margin: 14px 0 0; padding-left: 10px; border-left: 4px solid var(--color); }
.rutas-algo h3, .rutas-comparacion h3 { margin: 0; font-size: 14px; }
.rutas-algo h3 small { display: block; font-weight: 400; font-size: 12px; color: #5b6472; }
.rutas-camino { margin: 6px 0 4px; }
.rutas-cifras { margin: 0 0 4px; }
#rutas-panel details summary { cursor: pointer; }
.rutas-algo details summary { font-size: 12px; color: #5b6472; margin-top: 3px; }
.rutas-algo details p { margin: 4px 0; font-size: 12px; }
#rutas-panel table { width: 100%; border-collapse: collapse; font-size: 12px; font-variant-numeric: tabular-nums; margin: 4px 0; }
#rutas-panel th, #rutas-panel td { padding: 2px 4px; border-bottom: 1px solid #eceef2; text-align: left; }
#rutas-panel .num { text-align: right; white-space: nowrap; }
#rutas-panel ol { margin: 4px 0; padding-left: 24px; font-size: 12px; }
.rutas-comparacion { margin-top: 16px; padding-top: 10px; border-top: 1px solid #dfe3e8; }
.rutas-comparacion p { margin: 6px 0 0; }
.rutas-etiqueta { font-weight: 600; }
</style>
{% endmacro %}

{% macro html(this, kwargs) %}
<details id="rutas-panel" open>
    <summary>Buscar ruta (BFS y UCS)</summary>
    <div class="rutas-cuerpo">
        <label>Punto A · inicio
            <select id="rutas-inicio"><option value="">— Elige un centro comercial —</option></select>
        </label>
        <label>Punto B · destino
            <select id="rutas-destino"><option value="">— Elige un centro comercial —</option></select>
        </label>
        <div class="rutas-botones">
            <button type="button" id="rutas-intercambiar">⇅ Intercambiar A y B</button>
            <button type="button" id="rutas-limpiar">Limpiar</button>
        </div>
        <div id="rutas-resultado"></div>
    </div>
</details>
{% endmacro %}

{% macro script(this, kwargs) %}
(function () {
    var DATOS = {{ this.datos }};
    var grafo = DATOS.grafo;
    var mapa = {{ this._parent.get_name() }};
    var control = {{ this.control }};
    var capaCentros = {{ this.centros }};

    // ---- Mismos algoritmos que src/bfs.py y src/ucs.py ----
    function redondear(x) {
        return Number(x.toFixed(1));
    }

    function busquedaAnchura(grafo, inicio, objetivo) {
        var cola = [[inicio]];
        var visitados = new Set([inicio]);
        var ordenVisita = [];
        var historialCola = [];

        while (cola.length) {
            historialCola.push(cola.map(function (camino) { return camino[camino.length - 1]; }));

            var ruta = cola.shift();
            var nodoActual = ruta[ruta.length - 1];

            ordenVisita.push(nodoActual);

            if (nodoActual === objetivo) {
                return {ruta: ruta, ordenVisita: ordenVisita, historial: historialCola};
            }

            Object.keys(grafo[nodoActual] || {}).forEach(function (vecino) {
                if (!visitados.has(vecino)) {
                    visitados.add(vecino);
                    cola.push(ruta.concat([vecino]));
                }
            });
        }
        return {ruta: null, ordenVisita: ordenVisita, historial: historialCola};
    }

    function busquedaCostoUniforme(grafo, inicio, objetivo) {
        // Cola de prioridad con entradas [costo acumulado, contador, ruta]: sale la de
        // menor costo y, si hay empate, la que llegó primero (igual que heapq en ucs.py).
        var contador = 0;
        var frontera = [[0, contador, [inicio]]];
        var expandidos = new Set();
        var ordenVisita = [];
        var historialFrontera = [];

        while (frontera.length) {
            frontera.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
            historialFrontera.push(frontera.map(function (e) { return [redondear(e[0]), e[2][e[2].length - 1]]; }));

            var entrada = frontera.shift();
            var costo = entrada[0];
            var ruta = entrada[2];
            var nodoActual = ruta[ruta.length - 1];

            if (expandidos.has(nodoActual)) {
                continue;
            }
            expandidos.add(nodoActual);
            ordenVisita.push(nodoActual);

            // Prueba de objetivo al expandir, no al generar: así la ruta es la óptima.
            if (nodoActual === objetivo) {
                return {ruta: ruta, costo: redondear(costo), ordenVisita: ordenVisita, historial: historialFrontera};
            }

            Object.keys(grafo[nodoActual] || {}).forEach(function (vecino) {
                if (!expandidos.has(vecino)) {
                    contador += 1;
                    frontera.push([costo + grafo[nodoActual][vecino], contador, ruta.concat([vecino])]);
                }
            });
        }
        return {ruta: null, costo: Infinity, ordenVisita: ordenVisita, historial: historialFrontera};
    }

    function costoRuta(grafo, ruta) {
        var total = 0;
        for (var i = 1; i < ruta.length; i++) {
            total += grafo[ruta[i - 1]][ruta[i]];
        }
        return redondear(total);
    }

    function desgloseRuta(grafo, ruta) {
        var desglose = [];
        var acumulado = 0;
        for (var i = 1; i < ruta.length; i++) {
            var km = grafo[ruta[i - 1]][ruta[i]];
            acumulado += km;
            desglose.push([ruta[i - 1], ruta[i], km, redondear(acumulado)]);
        }
        return desglose;
    }
    // ---- Interfaz ----

    var panel = document.getElementById("rutas-panel");
    var selInicio = document.getElementById("rutas-inicio");
    var selDestino = document.getElementById("rutas-destino");
    var salida = document.getElementById("rutas-resultado");

    Object.keys(grafo).sort(function (a, b) { return a.localeCompare(b, "es"); }).forEach(function (centro) {
        selInicio.add(new Option(centro, centro));
        selDestino.add(new Option(centro, centro));
    });

    // El panel ocupa la esquina superior izquierda, donde Leaflet pone el zoom.
    if (mapa.zoomControl) {
        mapa.zoomControl.setPosition("bottomright");
    }

    var capas = {BFS: L.layerGroup().addTo(mapa), UCS: L.layerGroup().addTo(mapa)};
    control.addOverlay(capas.BFS, "Ruta BFS");
    control.addOverlay(capas.UCS, "Ruta UCS");
    var capaExtremos = L.layerGroup().addTo(mapa);

    function numero(v) {
        return v.toFixed(1).replace(".", ",");
    }

    function formatoKm(v) {
        return numero(v) + " km";
    }

    function esc(texto) {
        return String(texto).replace(/[&<>"]/g, function (c) {
            return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c];
        });
    }

    function flechas(nodos) {
        return nodos.map(esc).join(" → ");
    }

    function marcarExtremo(nodo, letra, color) {
        var radio = 4 + Object.keys(grafo[nodo]).length + 5;
        L.circleMarker(DATOS.coords[nodo], {radius: radio, color: color, weight: 4, fill: false, interactive: false})
            .bindTooltip(letra + " · " + esc(nodo),
                         {permanent: true, direction: "top", offset: [0, -radio], className: "rutas-etiqueta"})
            .addTo(capaExtremos);
    }

    function dibujar(resultados, inicio, objetivo) {
        capas.BFS.clearLayers();
        capas.UCS.clearLayers();
        capaExtremos.clearLayers();

        if (resultados) {
            // BFS ancha debajo y UCS delgada encima: si coinciden en un tramo, se ven las dos.
            [["BFS", 9, 0.85], ["UCS", 4, 1]].forEach(function (a) {
                var r = resultados[a[0]];
                L.polyline(r.ruta.map(function (n) { return DATOS.coords[n]; }),
                           {color: DATOS.colores[a[0]], weight: a[1], opacity: a[2]})
                    .bindTooltip(a[0] + ": " + (r.ruta.length - 1) + " conexiones · " + formatoKm(r.costo))
                    .addTo(capas[a[0]]);
            });
            // Los centros quedan encima de las rutas para que se les pueda seguir dando clic.
            if (mapa.hasLayer(capaCentros)) {
                capaCentros.bringToFront();
            }
        }
        if (inicio) {
            marcarExtremo(inicio, "A", DATOS.colores.inicio);
        }
        if (objetivo) {
            marcarExtremo(objetivo, "B", DATOS.colores.destino);
        }
    }

    function seccion(algoritmo, r, tituloCola, formatoPaso) {
        var filas = '<tr><th>Tramo</th><th class="num">km</th><th class="num">Acumulado</th></tr>' +
            "<tr><td>" + esc(r.ruta[0]) + '</td><td></td><td class="num">' + numero(0) + "</td></tr>";
        desgloseRuta(grafo, r.ruta).forEach(function (t) {
            filas += "<tr><td>" + esc(t[0]) + " → " + esc(t[1]) + '</td><td class="num">' + numero(t[2]) +
                '</td><td class="num">' + numero(t[3]) + "</td></tr>";
        });
        var pasos = r.historial.map(function (paso) {
            return "<li>" + paso.map(formatoPaso).join(", ") + "</li>";
        }).join("");

        return '<section class="rutas-algo" style="--color:' + DATOS.colores[algoritmo] + '">' +
            "<h3>" + algoritmo + "<small>" + esc(DATOS.descripcion[algoritmo]) + "</small></h3>" +
            '<p class="rutas-camino">' + flechas(r.ruta) + "</p>" +
            '<p class="rutas-cifras"><b>' + (r.ruta.length - 1) + "</b> conexiones · <b>" + formatoKm(r.costo) +
            "</b> · " + r.orden.length + " nodos expandidos</p>" +
            "<details><summary>Costo acumulado tramo a tramo</summary><table>" + filas + "</table></details>" +
            "<details><summary>Orden de visita (nodos expandidos)</summary><p>" + flechas(r.orden) + "</p></details>" +
            "<details><summary>" + tituloCola + "</summary><ol>" + pasos + "</ol></details>" +
            "</section>";
    }

    function conclusion(bfs, ucs) {
        if (JSON.stringify(bfs.ruta) === JSON.stringify(ucs.ruta)) {
            return "Ambos algoritmos encontraron <b>la misma ruta</b>: la de menos conexiones también es la de menor distancia.";
        }
        var diferencia = redondear(bfs.costo - ucs.costo);
        if (diferencia === 0) {
            return "Las rutas son distintas pero miden lo mismo: hay un empate en distancia.";
        }
        var texto = "Las rutas son <b>distintas</b>. UCS ahorra <b>" + formatoKm(diferencia) + "</b> frente a BFS. ";
        var extra = ucs.ruta.length - bfs.ruta.length;
        if (extra > 0) {
            return texto + "BFS escogió la ruta con menos conexiones sin mirar las distancias; UCS aceptó " +
                extra + (extra === 1 ? " conexión más" : " conexiones más") + " a cambio de recorrer menos kilómetros.";
        }
        return texto + "Con el mismo número de conexiones, UCS escogió el camino más corto y BFS se quedó con el primero que encontró.";
    }

    function comparacion(bfs, ucs) {
        function fila(nombre, a, b) {
            return "<tr><td>" + nombre + '</td><td class="num">' + a + '</td><td class="num">' + b + "</td></tr>";
        }
        return '<section class="rutas-comparacion"><h3>Comparación BFS vs UCS</h3><table>' +
            '<tr><th></th><th class="num">BFS</th><th class="num">UCS</th></tr>' +
            fila("Conexiones", bfs.ruta.length - 1, ucs.ruta.length - 1) +
            fila("Distancia total", formatoKm(bfs.costo), formatoKm(ucs.costo)) +
            fila("Nodos expandidos", bfs.orden.length, ucs.orden.length) +
            "</table><p>" + conclusion(bfs, ucs) + "</p></section>";
    }

    function nota(texto) {
        salida.innerHTML = '<p class="rutas-nota">' + texto + "</p>";
    }

    function buscar() {
        var inicio = selInicio.value;
        var objetivo = selDestino.value;

        if (!inicio || !objetivo) {
            dibujar(null, inicio, objetivo);
            nota("Elige el punto A y el punto B. También puedes hacer clic en un centro del mapa y usar " +
                 "«Desde aquí» o «Hasta aquí».");
            return;
        }
        if (inicio === objetivo) {
            dibujar(null, inicio, null);
            nota("El punto A y el punto B son el mismo centro comercial.");
            return;
        }

        var bfs = busquedaAnchura(grafo, inicio, objetivo);
        if (!bfs.ruta) {
            dibujar(null, inicio, objetivo);
            nota("No se encontró una ruta entre los centros seleccionados.");
            return;
        }
        var ucs = busquedaCostoUniforme(grafo, inicio, objetivo);

        var resultados = {
            BFS: {ruta: bfs.ruta, costo: costoRuta(grafo, bfs.ruta), orden: bfs.ordenVisita, historial: bfs.historial},
            UCS: {ruta: ucs.ruta, costo: ucs.costo, orden: ucs.ordenVisita, historial: ucs.historial},
        };
        dibujar(resultados, inicio, objetivo);
        salida.innerHTML =
            seccion("BFS", resultados.BFS, "Evolución de la cola FIFO", esc) +
            seccion("UCS", resultados.UCS, "Evolución de la cola de prioridad (costo acumulado)",
                    function (e) { return esc(e[1]) + " (" + numero(e[0]) + ")"; }) +
            comparacion(resultados.BFS, resultados.UCS);
    }

    selInicio.addEventListener("change", buscar);
    selDestino.addEventListener("change", buscar);
    document.getElementById("rutas-intercambiar").addEventListener("click", function () {
        var inicio = selInicio.value;
        selInicio.value = selDestino.value;
        selDestino.value = inicio;
        buscar();
    });
    document.getElementById("rutas-limpiar").addEventListener("click", function () {
        selInicio.value = "";
        selDestino.value = "";
        buscar();
    });

    // Botones "Desde aquí" / "Hasta aquí" del recuadro de cada centro. Se escucha en la fase
    // de captura porque Leaflet no deja que los clics dentro de un popup lleguen al documento.
    document.addEventListener("click", function (e) {
        var boton = e.target.closest ? e.target.closest("[data-rol]") : null;
        if (!boton) {
            return;
        }
        (boton.dataset.rol === "inicio" ? selInicio : selDestino).value = boton.dataset.centro;
        mapa.closePopup();
        panel.open = true;
        buscar();
    }, true);

    // Encuadrar todos los centros en la parte del mapa que no tapan el panel ni el control de capas.
    var izquierda = 20;
    var derecha = 20;
    if (window.innerWidth >= 900) {
        izquierda = panel.getBoundingClientRect().right + 10;
        var controlCapas = document.querySelector(".leaflet-control-layers");
        if (controlCapas) {
            derecha = controlCapas.getBoundingClientRect().width + 20;
        }
    }
    mapa.fitBounds(L.latLngBounds(Object.values(DATOS.coords)),
                   {paddingTopLeft: [izquierda, 20], paddingBottomRight: [derecha, 20]});

    if (DATOS.inicio) {
        selInicio.value = DATOS.inicio;
        selDestino.value = DATOS.objetivo;
    }
    buscar();
})();
{% endmacro %}
"""


class _PanelRutas(folium.MacroElement):
    """Panel "Buscar ruta": se agrega al mapa después del control de capas, porque lo usa."""

    _template = Template(_PLANTILLA_PANEL)

    def __init__(self, datos, control, capa_centros):
        super().__init__()
        self._name = "PanelRutas"
        self.datos = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
        self.control = control.get_name()
        self.centros = capa_centros.get_name()


def generar_mapa_interactivo(grafo=None, rutas=None, carpeta=CARPETA_SALIDA):
    """Guarda docs/mapa_interactivo.html y devuelve su ruta.

    rutas: diccionario opcional {"BFS": [...], "UCS": [...]} con listas de nombres,
    del inicio al objetivo. El HTML abre con ese inicio y ese destino ya elegidos en
    el panel "Buscar ruta"; desde el navegador se puede elegir cualquier otro par.
    """
    grafo = validar_grafo() if grafo is None else grafo
    inicio, objetivo = _extremos(grafo, rutas or {})
    latitudes = [d["lat"] for _, d in grafo.nodes(data=True)]
    longitudes = [d["lon"] for _, d in grafo.nodes(data=True)]

    # Sin mapa de calles (tiles=None): el fondo son solo las localidades, sobre blanco.
    mapa = folium.Map(location=[sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)],
                      zoom_start=12, tiles=None)
    # Leaflet y jQuery van dentro del HTML para que funcione sin internet (Folium las enlazaría
    # desde un CDN, junto con Bootstrap y Font Awesome, que este mapa no usa). El {% raw %}
    # evita que Jinja, con el que Folium arma el HTML, interprete llaves del código de las librerías.
    mapa.default_js, mapa.default_css = [], []
    cabecera = mapa.get_root().header
    for etiqueta, archivo in (("style", "leaflet.css"), ("script", "leaflet.js"), ("script", "jquery.min.js")):
        codigo = (CARPETA_WEB / archivo).read_text(encoding="utf-8")
        cabecera.add_child(folium.Element(f"{{% raw %}}<{etiqueta}>{codigo}</{etiqueta}>{{% endraw %}}"))
    # Va después de leaflet.css, que pinta el fondo de gris.
    cabecera.add_child(folium.Element("<style>.leaflet-container{background:#ffffff}</style>"))

    localidades = cargar_localidades()[["nombre", "color", "geometry"]]
    folium.GeoJson(
        localidades, name="Localidades",
        style_function=lambda f: {"fillColor": f["properties"]["color"], "color": "#3C3C3C",
                                  "weight": 1, "fillOpacity": ALPHA_MAPA},
        tooltip=folium.GeoJsonTooltip(fields=["nombre"], aliases=["Localidad:"]),
    ).add_to(mapa)

    capa_conexiones = folium.FeatureGroup(name="Conexiones")
    for a, b, datos in grafo.edges(data=True):
        folium.PolyLine(
            [(grafo.nodes[a]["lat"], grafo.nodes[a]["lon"]), (grafo.nodes[b]["lat"], grafo.nodes[b]["lon"])],
            color=COLOR_ARISTA, weight=2, opacity=0.8, tooltip=f"{a} – {b}: {formato_km(datos['peso'])}",
        ).add_to(capa_conexiones)
    capa_conexiones.add_to(mapa)

    capa_centros = folium.FeatureGroup(name="Centros comerciales")
    for nodo, datos in grafo.nodes(data=True):
        folium.CircleMarker(
            [datos["lat"], datos["lon"]], radius=4 + grafo.degree(nodo),
            color="white", weight=1.5, fill=True, fill_color=COLOR_NODO, fill_opacity=1,
            tooltip=nodo, popup=folium.Popup(_ficha(grafo, nodo), max_width=320),
        ).add_to(capa_centros)
    capa_centros.add_to(mapa)

    control = folium.LayerControl(collapsed=False)
    control.add_to(mapa)
    mapa.fit_bounds([[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]])

    # Mismo orden de vecinos que construir_adyacencia(): de él depende el desempate de BFS y UCS.
    datos_panel = {
        "grafo": {nodo: {vecino: grafo[nodo][vecino]["peso"] for vecino in grafo[nodo]} for nodo in grafo},
        "coords": {nodo: [d["lat"], d["lon"]] for nodo, d in grafo.nodes(data=True)},
        "colores": {**COLOR_RUTA, "inicio": COLOR_INICIO, "destino": COLOR_OBJETIVO},
        "descripcion": DESCRIPCION_ALGORITMO,
        "inicio": inicio,
        "objetivo": objetivo,
    }
    _PanelRutas(datos_panel, control, capa_centros).add_to(mapa)

    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / "mapa_interactivo.html"
    mapa.save(archivo)
    return archivo


if __name__ == "__main__":
    print(f"Guardado: {generar_mapa_interactivo().relative_to(RAIZ)}")
