# Centros Comerciales de Bogotá - Búsquedas en Grafos

Proyecto académico para representar centros comerciales de Bogotá mediante un grafo y aplicar algoritmos de búsqueda.

## Objetivo

Modelar centros comerciales de Bogotá como nodos de un grafo y comparar diferentes algoritmos de búsqueda.

## Algoritmos

- Búsqueda en anchura (BFS): encuentra la ruta con menos conexiones.
- Búsqueda de costo uniforme (UCS): encuentra la ruta con menor distancia total.

## El grafo

- 40 centros comerciales (nodos) y 69 conexiones (aristas). Es no dirigido y ponderado.
- El peso de cada arista es la distancia por vía en carro, en kilómetros.
- Las coordenadas son aproximadas: sirven para ubicar cada centro en su localidad.

## Instalación

Probado con Python 3.11.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (en macOS o Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Cómo ejecutarlo

Desde la raíz del proyecto:

| Comando | Qué hace |
|---|---|
| `python src/main.py` | Pide el centro de inicio y el de destino, corre BFS y UCS, imprime la comparación y genera en `docs/` las imágenes de las rutas y el mapa interactivo |
| `python src/presentacion.py` | Lo mismo en consola, eligiendo los centros por número o por nombre, y abre el mapa con las dos rutas. No genera imágenes: es lo que corre el ejecutable |
| `python src/mapa.py` | Comprueba que cada centro caiga en su localidad y genera `mapa_base` y `grafo_completo` |
| `python src/mapa_interactivo.py` | Genera solo `docs/mapa_interactivo.html` |
| `python data/conexiones.py` | Valida los datos del grafo: 40 nodos, 69 aristas y conexo |

`main.py` sobrescribe las imágenes de `docs/` con la ruta que se elija.

`docs/mapa_interactivo.html` se abre en el navegador y funciona sin internet. En el panel «Buscar ruta» se elige el punto A y el punto B, o se hace clic en un centro comercial, y el mapa muestra las rutas de BFS y UCS con su comparación.

## Ejecutable para la exposición

`CentrosComercialesBogota.exe` corre BFS y UCS en consola y abre el mapa interactivo con las dos rutas. Funciona en Windows 10 u 11 sin instalar Python y sin internet.

Para crearlo, con el entorno del proyecto activo:

```bash
pip install pyinstaller
python crear_ejecutable.py
```

Queda en `dist/CentrosComercialesBogota.exe`. No se sube al repositorio: se copia a una USB o a la nube y en el otro computador se abre con doble clic. Si Windows muestra «Windows protegió su PC», se elige «Más información» y luego «Ejecutar de todas formas»; el aviso sale porque el ejecutable no está firmado.

## Estructura del proyecto

```text
centros-comerciales-bogota/
├── data/
│   ├── centros.py            # nodos: coordenadas, localidad y dirección de cada centro
│   ├── conexiones.py         # aristas con su distancia en km y validación del grafo
│   └── localidades.geojson   # límites de las localidades (mapa de fondo)
├── docs/                     # imágenes y mapa interactivo generados, diagrama del grafo
├── src/
│   ├── bfs.py                # búsqueda en anchura
│   ├── ucs.py                # búsqueda de costo uniforme
│   ├── mapa.py               # imágenes PNG y SVG del grafo y de las rutas sobre las localidades
│   ├── mapa_interactivo.py   # mapa HTML con buscador de rutas
│   ├── main.py               # punto de entrada
│   ├── presentacion.py       # programa del ejecutable: BFS y UCS en consola y en el mapa
│   └── web/                  # Leaflet y jQuery, para que el mapa funcione sin internet
├── crear_ejecutable.py       # arma dist/CentrosComercialesBogota.exe
├── .gitignore
├── README.md
└── requirements.txt
```

`data/centros.py` y `data/conexiones.py` son compartidos: BFS y UCS deben correr sobre el mismo grafo, así que cualquier cambio ahí se avisa al grupo antes de hacerlo.

## Fuentes de datos

- Límites de localidades: Secretaría Distrital de Planeación — Datos Abiertos Bogotá (CC BY 4.0).
- Distancias por vía: OSRM, © colaboradores de OpenStreetMap.

## Librerías incluidas

- Leaflet 1.9.3 (BSD 2-Clause) y jQuery 3.7.1 (MIT), en `src/web/` con sus licencias.
