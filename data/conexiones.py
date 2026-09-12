"""Conexiones entre centros comerciales — aristas del grafo.

Archivo COMPARTIDO: cualquier cambio aquí se avisa al grupo antes de hacerlo,
porque BFS y UCS deben correr sobre exactamente el mismo grafo.

Grafo no dirigido y ponderado. El peso de cada arista es la distancia aproximada
por vía, en kilómetros. Los pesos actuales son ESTIMACIONES (distancia en línea
recta entre coordenadas x 1.30), no consultadas en Google Maps. Para corregir una
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
    ("Bima", "Santafé", 4.4),
    ("Bima", "Cedritos 151", 9.1),
    ("Santafé", "Parque La Colina", 4.6),
    ("Santafé", "Cedritos 151", 4.8),
    ("Santafé", "Plaza Imperial", 7.0),
    ("Plaza Imperial", "Centro Suba", 1.5),
    ("Plaza Imperial", "Portal 80", 6.1),
    ("Centro Suba", "Parque La Colina", 3.1),
    ("Centro Suba", "Bulevar Niza", 4.5),
    ("Parque La Colina", "Bulevar Niza", 2.9),
    ("Parque La Colina", "Cedritos 151", 3.3),
    ("Cedritos 151", "Palatino", 1.5),
    ("Cedritos 151", "Unicentro", 4.0),
    ("Palatino", "Hacienda Santa Bárbara", 3.7),
    ("Bulevar Niza", "Unicentro", 3.8),
    ("Bulevar Niza", "Titán Plaza", 5.5),
    ("Unicentro", "Santa Ana", 2.3),
    ("Santa Ana", "Hacienda Santa Bárbara", 0.9),
    ("Unicentro", "Andino", 5.2),
    ("Santa Ana", "Andino", 4.3),
    ("Andino", "El Retiro", 0.3),
    ("El Retiro", "Atlantis Plaza", 0.4),
    ("Andino", "Atlantis Plaza", 0.6),
    ("Atlantis Plaza", "Avenida Chile", 1.2),
    ("Avenida Chile", "Galerías", 2.8),
    ("Atlantis Plaza", "Metrópolis", 3.9),
    ("Galerías", "Mallplaza NQS", 3.8),
    ("Galerías", "Terraza Pasteur", 4.7),
    ("Galerías", "Metrópolis", 5.4),
    ("Terraza Pasteur", "Gran San Victorino", 2.5),
    ("Mallplaza NQS", "Gran San Victorino", 3.1),
    ("Mallplaza NQS", "Gran Estación", 2.9),
    ("Gran San Victorino", "Centro Mayor", 6.0),
    ("Unicentro de Occidente", "Portal 80", 1.8),
    ("Unicentro de Occidente", "Nuestro Bogotá", 4.6),
    ("Portal 80", "Diverplaza", 1.6),
    ("Portal 80", "Nuestro Bogotá", 4.5),
    ("Diverplaza", "Titán Plaza", 1.8),
    ("Titán Plaza", "Metrópolis", 3.4),
    ("Titán Plaza", "Gran Estación", 7.8),
    ("Metrópolis", "Gran Estación", 6.7),
    ("Nuestro Bogotá", "Viva Fontibón", 3.0),
    ("Nuestro Bogotá", "Hayuelos", 3.4),
    ("Nuestro Bogotá", "Gran Estación", 7.8),
    ("Viva Fontibón", "Hayuelos", 1.8),
    ("Hayuelos", "Salitre Plaza", 4.3),
    ("Hayuelos", "Multiplaza La Felicidad", 2.8),
    ("Hayuelos", "Tintal Plaza", 6.2),
    ("Salitre Plaza", "Gran Estación", 1.9),
    ("Salitre Plaza", "Multiplaza La Felicidad", 2.5),
    ("Multiplaza La Felicidad", "El Edén", 2.1),
    ("Multiplaza La Felicidad", "Plaza Central", 3.2),
    ("Gran Estación", "Plaza Central", 3.0),
    ("Plaza Central", "El Edén", 2.2),
    ("Plaza Central", "Mallplaza NQS", 4.0),
    ("Plaza Central", "Plaza de las Américas", 3.5),
    ("El Edén", "Plaza de las Américas", 1.4),
    ("Plaza de las Américas", "Tintal Plaza", 4.4),
    ("Plaza de las Américas", "Centro Mayor", 5.2),
    ("Tintal Plaza", "Milenio Plaza", 3.9),
    ("Milenio Plaza", "Gran Plaza Bosa", 2.9),
    ("Milenio Plaza", "Paseo Villa del Río", 4.4),
    ("Gran Plaza Bosa", "Paseo Villa del Río", 7.2),
    ("Mallplaza NQS", "Centro Mayor", 6.9),
    ("Paseo Villa del Río", "Centro Mayor", 3.1),
    ("Paseo Villa del Río", "Ciudad Tunal", 3.2),
    ("Paseo Villa del Río", "Gran Plaza El Ensueño", 1.9),
    ("Gran Plaza El Ensueño", "Ciudad Tunal", 3.4),
    ("Ciudad Tunal", "Centro Mayor", 3.0),
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
