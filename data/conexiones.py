"""Conexiones entre centros comerciales — aristas del grafo.

Archivo COMPARTIDO: cualquier cambio aquí se avisa al grupo antes de hacerlo,
porque BFS y UCS deben correr sobre exactamente el mismo grafo.

Grafo no dirigido y ponderado. El peso de cada arista es la distancia por vía,
en kilómetros, calculada con OSRM (rutas en carro sobre OpenStreetMap) el
2026-09-12: promedio de ida y vuelta, redondeado a 0.1 km. Para corregir una
distancia basta con cambiar el número en ARISTAS; el resto del proyecto la toma
de aquí.

Uso desde src/:
    from data.conexiones import conexiones        # lista de (origen, destino, km)
    from data.conexiones import construir_grafo, construir_adyacencia

Validación de los datos:
    python data/conexiones.py
"""

import networkx as nx

try:
    from data.centros import NODOS
except ModuleNotFoundError:  # al ejecutarlo directamente: python data/conexiones.py
    from centros import NODOS

NODOS_ESPERADOS = 40
ARISTAS_ESPERADAS = 69

# (origen, destino, distancia_km)
ARISTAS = [
    ("Bima", "Santafé", 6.2),
    ("Bima", "Cedritos 151", 9.5),
    ("Santafé", "Parque La Colina", 6.7),
    ("Santafé", "Cedritos 151", 6.2),
    ("Santafé", "Plaza Imperial", 8.3),
    ("Plaza Imperial", "Centro Suba", 1.3),
    ("Plaza Imperial", "Portal 80", 8.8),
    ("Centro Suba", "Parque La Colina", 4.9),
    ("Centro Suba", "Bulevar Niza", 5.1),
    ("Parque La Colina", "Bulevar Niza", 3.0),
    ("Parque La Colina", "Cedritos 151", 5.2),
    ("Cedritos 151", "Palatino", 1.8),
    ("Cedritos 151", "Unicentro", 5.2),
    ("Palatino", "Hacienda Santa Bárbara", 3.7),
    ("Bulevar Niza", "Unicentro", 3.8),
    ("Bulevar Niza", "Titán Plaza", 6.2),
    ("Unicentro", "Santa Ana", 3.4),
    ("Santa Ana", "Hacienda Santa Bárbara", 1.3),
    ("Unicentro", "Andino", 5.4),
    ("Santa Ana", "Andino", 4.7),
    ("Andino", "El Retiro", 0.6),
    ("El Retiro", "Atlantis Plaza", 1.2),
    ("Andino", "Atlantis Plaza", 1.4),
    ("Atlantis Plaza", "Avenida Chile", 1.7),
    ("Avenida Chile", "Galerías", 3.6),
    ("Atlantis Plaza", "Metrópolis", 4.8),
    ("Galerías", "Mallplaza NQS", 5.3),
    ("Galerías", "Terraza Pasteur", 5.1),
    ("Galerías", "Metrópolis", 4.9),
    ("Terraza Pasteur", "Gran San Victorino", 3.0),
    ("Mallplaza NQS", "Gran San Victorino", 4.5),
    ("Mallplaza NQS", "Gran Estación", 4.7),
    ("Gran San Victorino", "Centro Mayor", 6.9),
    ("Unicentro de Occidente", "Portal 80", 3.0),
    ("Unicentro de Occidente", "Nuestro Bogotá", 5.7),
    ("Portal 80", "Diverplaza", 2.7),
    ("Portal 80", "Nuestro Bogotá", 4.5),
    ("Diverplaza", "Titán Plaza", 2.7),
    ("Titán Plaza", "Metrópolis", 3.8),
    ("Titán Plaza", "Gran Estación", 8.7),
    ("Metrópolis", "Gran Estación", 6.9),
    ("Nuestro Bogotá", "Viva Fontibón", 5.9),
    ("Nuestro Bogotá", "Hayuelos", 5.9),
    ("Nuestro Bogotá", "Gran Estación", 7.9),
    ("Viva Fontibón", "Hayuelos", 3.5),
    ("Hayuelos", "Salitre Plaza", 7.3),
    ("Hayuelos", "Multiplaza La Felicidad", 2.9),
    ("Hayuelos", "Tintal Plaza", 5.9),
    ("Salitre Plaza", "Gran Estación", 3.5),
    ("Salitre Plaza", "Multiplaza La Felicidad", 5.0),
    ("Multiplaza La Felicidad", "El Edén", 5.4),
    ("Multiplaza La Felicidad", "Plaza Central", 5.7),
    ("Gran Estación", "Plaza Central", 4.3),
    ("Plaza Central", "El Edén", 3.9),
    ("Plaza Central", "Mallplaza NQS", 5.1),
    ("Plaza Central", "Plaza de las Américas", 5.4),
    ("El Edén", "Plaza de las Américas", 1.7),
    ("Plaza de las Américas", "Tintal Plaza", 6.4),
    ("Plaza de las Américas", "Centro Mayor", 7.5),
    ("Tintal Plaza", "Milenio Plaza", 4.1),
    ("Milenio Plaza", "Gran Plaza Bosa", 3.5),
    ("Milenio Plaza", "Paseo Villa del Río", 5.3),
    ("Gran Plaza Bosa", "Paseo Villa del Río", 7.2),
    ("Mallplaza NQS", "Centro Mayor", 6.3),
    ("Paseo Villa del Río", "Centro Mayor", 4.5),
    ("Paseo Villa del Río", "Ciudad Tunal", 4.5),
    ("Paseo Villa del Río", "Gran Plaza El Ensueño", 3.5),
    ("Gran Plaza El Ensueño", "Ciudad Tunal", 3.7),
    ("Ciudad Tunal", "Centro Mayor", 3.7),
]

# La misma lista con el nombre que usa el grupo: from data.conexiones import conexiones
conexiones = ARISTAS


def construir_grafo():
    """Devuelve el grafo como nx.Graph.

    Cada nodo trae los atributos lat, lon, localidad y direccion; cada arista,
    el atributo peso (km). Los vecinos de cada nodo salen en orden alfabético,
    así el desempate de BFS y UCS es el mismo en cualquier computador.
    """
    grafo = nx.Graph()
    for nombre, (lat, lon, localidad, direccion) in NODOS.items():
        grafo.add_node(nombre, lat=lat, lon=lon, localidad=localidad, direccion=direccion)
    # Insertar las aristas ordenadas por (menor, mayor) deja los vecinos de cada nodo en orden alfabético.
    for origen, destino, km in sorted((min(a, b), max(a, b), km) for a, b, km in ARISTAS):
        grafo.add_edge(origen, destino, peso=km)
    return grafo


def construir_adyacencia():
    """Devuelve el grafo como diccionario simple {nodo: {vecino: km}}.

    Pensado para BFS y UCS escritos a mano, sin depender de NetworkX.
    Mismo contenido y mismo orden de vecinos que construir_grafo().
    """
    grafo = construir_grafo()
    return {nodo: {vecino: grafo[nodo][vecino]["peso"] for vecino in grafo[nodo]} for nodo in grafo}


def validar_grafo():
    """Revisa que los datos estén bien transcritos y devuelve el grafo.

    Lanza ValueError con la lista de problemas si algo no cuadra.
    """
    errores = []

    # Un nombre mal escrito crearía un nodo fantasma sin coordenadas.
    fantasmas = {n for a, b, _ in ARISTAS for n in (a, b)} - NODOS.keys()
    if fantasmas:
        errores.append(f"Nombres en ARISTAS que no existen en NODOS: {sorted(fantasmas)}")

    pares = [frozenset((a, b)) for a, b, _ in ARISTAS]
    repetidas = sorted({tuple(sorted(p)) for p in pares if pares.count(p) > 1})
    if repetidas:
        errores.append(f"Aristas repetidas: {repetidas}")

    lazos = [a for a, b, _ in ARISTAS if a == b]
    if lazos:
        errores.append(f"Aristas de un nodo consigo mismo: {lazos}")

    no_positivas = [(a, b, km) for a, b, km in ARISTAS if km <= 0]
    if no_positivas:
        errores.append(f"Distancias no positivas: {no_positivas}")

    grafo = construir_grafo()
    if grafo.number_of_nodes() != NODOS_ESPERADOS:
        errores.append(f"Se esperaban {NODOS_ESPERADOS} nodos y hay {grafo.number_of_nodes()}")
    if grafo.number_of_edges() != ARISTAS_ESPERADAS:
        errores.append(f"Se esperaban {ARISTAS_ESPERADAS} aristas y hay {grafo.number_of_edges()}")

    aislados = list(nx.isolates(grafo))
    if aislados:
        errores.append(f"Nodos sin conexiones: {aislados}")
    elif not nx.is_connected(grafo):
        errores.append("El grafo no es conexo: hay grupos de nodos sin camino entre sí")

    if errores:
        raise ValueError("Los datos del grafo tienen problemas:\n- " + "\n- ".join(errores))
    return grafo


if __name__ == "__main__":
    grafo = validar_grafo()
    grados = [g for _, g in grafo.degree()]
    print("Datos del grafo OK")
    print(f"  Nodos:   {grafo.number_of_nodes()}")
    print(f"  Aristas: {grafo.number_of_edges()}")
    print("  Conexo:  sí")
    print(f"  Grados:  entre {min(grados)} y {max(grados)}")
    print(f"  Distancia total de todas las aristas: {grafo.size(weight='peso'):.1f} km")
