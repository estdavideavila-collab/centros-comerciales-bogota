"""Crea el ejecutable para la exposición: dist/CentrosComercialesBogota.exe (Windows).

El ejecutable corre src/presentacion.py (BFS y UCS en consola) y lleva adentro el mapa
interactivo, que funciona sin internet. En el otro computador no hace falta instalar
Python ni nada más.

Una sola vez, con el entorno del proyecto activo:
    pip install pyinstaller

Luego, cada vez que cambie algo del proyecto:
    python crear_ejecutable.py
"""

import os
import sys
from pathlib import Path

import PyInstaller.__main__

RAIZ = Path(__file__).resolve().parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "src")]

from mapa_interactivo import generar_mapa_interactivo  # noqa: E402

NOMBRE = "CentrosComercialesBogota"
CARPETA_TRABAJO = RAIZ / "build"

# El programa solo necesita NetworkX. Estas librerías están en el entorno para las imágenes
# y el mapa, y NetworkX las menciona como opcionales: si no se excluyen, PyInstaller las mete
# todas y el ejecutable pasa de unos MB a cientos.
EXCLUIDAS = [
    "matplotlib", "numpy", "scipy", "pandas", "geopandas", "shapely", "pyogrio", "pyproj",
    "folium", "branca", "jinja2", "PIL", "tkinter",
]


def crear_ejecutable():
    """Genera el mapa interactivo sin ruta elegida, empaqueta el programa y devuelve la ruta del .exe."""
    mapa = generar_mapa_interactivo(carpeta=CARPETA_TRABAJO)
    PyInstaller.__main__.run([
        str(RAIZ / "src" / "presentacion.py"),
        "--name", NOMBRE,
        "--onefile",
        "--console",
        "--noconfirm",
        "--clean",
        "--paths", str(RAIZ),
        "--paths", str(RAIZ / "src"),
        "--add-data", f"{mapa}{os.pathsep}.",
        "--distpath", str(RAIZ / "dist"),
        "--workpath", str(CARPETA_TRABAJO / "pyinstaller"),
        "--specpath", str(CARPETA_TRABAJO),
        *(f"--exclude-module={modulo}" for modulo in EXCLUIDAS),
    ])
    return RAIZ / "dist" / f"{NOMBRE}.exe"


if __name__ == "__main__":
    print(f"\nListo: {crear_ejecutable().relative_to(RAIZ)}")
