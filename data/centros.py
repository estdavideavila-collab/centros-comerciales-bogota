"""Centros comerciales de Bogotá D.C. — nodos del grafo.

Archivo COMPARTIDO: cualquier cambio aquí se avisa al grupo antes de hacerlo,
porque BFS y UCS deben correr sobre exactamente el mismo grafo.

Las coordenadas son aproximadas (derivadas de la dirección, con precisión de unas
pocas cuadras). Sirven para ubicar cada nodo en su localidad, no son GPS exactas.
Las de Nuestro Bogotá, Multiplaza La Felicidad, Mallplaza NQS y Gran San Victorino
se tomaron de OpenStreetMap porque las anteriores caían en la localidad vecina.
"""

# nombre: (latitud, longitud, localidad, direccion)
# Ordenados de norte a sur.
NODOS = {
    "Bima": (4.792, -74.043, "Suba", "Autopista Norte # 232-35"),
    "Santafé": (4.7619, -74.0464, "Suba", "Autopista Norte con Calle 183"),
    "Plaza Imperial": (4.748, -74.093, "Suba", "Carrera 104 con Calle 148"),
    "Centro Suba": (4.743, -74.084, "Suba", "Av. Calle 145 # 91-59"),
    "Parque La Colina": (4.7355, -74.064, "Suba", "Carrera 58D # 146-51"),
    "Cedritos 151": (4.729, -74.042, "Usaquén", "Diagonal 151 # 32-19"),
    "Palatino": (4.7215, -74.0345, "Usaquén", "Carrera 7 con Calle 140"),
    "Bulevar Niza": (4.716, -74.069, "Suba", "Av. Carrera 58 # 127-59"),
    "Unicentro de Occidente": (4.7145, -74.1235, "Engativá", "Carrera 111C # 86-05 (Ciudadela Colsubsidio)"),
    "Portal 80": (4.71, -74.112, "Engativá", "Calle 80 con Av. Ciudad de Cali"),
    "Diverplaza": (4.704, -74.103, "Engativá", "Calle 80 con Carrera 96 (Álamos)"),
    "Unicentro": (4.7017, -74.0466, "Usaquén", "Av. Carrera 15 # 124-30"),
    "Hacienda Santa Bárbara": (4.696, -74.032, "Usaquén", "Carrera 7 # 115-72"),
    "Titán Plaza": (4.692, -74.099, "Engativá", "Av. Boyacá # 80-94"),
    "Santa Ana": (4.6905, -74.0355, "Usaquén", "Calle 110 con Carrera 9"),
    "Nuestro Bogotá": (4.6835, -74.1162, "Engativá", "Av. Ciudad de Cali con Calle 63"),
    "Metrópolis": (4.68, -74.079, "Barrios Unidos", "Av. Carrera 68 # 75A-50"),
    "Viva Fontibón": (4.67, -74.144, "Fontibón", "Calle 22D con Carrera 100"),
    "El Retiro": (4.6672, -74.0548, "Chapinero", "Calle 82 # 11-75"),
    "Andino": (4.6665, -74.053, "Chapinero", "Carrera 11 # 82-71"),
    "Atlantis Plaza": (4.665, -74.0566, "Chapinero", "Calle 81 # 13-05"),
    "Hayuelos": (4.6605, -74.1355, "Fontibón", "Calle 20 con Av. Ciudad de Cali"),
    "Avenida Chile": (4.6565, -74.057, "Chapinero", "Calle 72 # 10-34"),
    "Multiplaza La Felicidad": (4.6531, -74.1244, "Fontibón", "Av. Boyacá con Calle 19A (La Felicidad)"),
    "Salitre Plaza": (4.645, -74.11, "Teusaquillo", "Carrera 68B # 24-39 (Ciudad Salitre)"),
    "Galerías": (4.6435, -74.0715, "Teusaquillo", "Carrera 24 # 53-25"),
    "Gran Estación": (4.638, -74.0985, "Teusaquillo", "Av. Calle 26 # 62-47"),
    "Tintal Plaza": (4.632, -74.168, "Kennedy", "Av. Ciudad de Cali con Calle 6"),
    "El Edén": (4.628, -74.129, "Kennedy", "Av. Boyacá con Calle 13"),
    "Plaza de las Américas": (4.625, -74.138, "Kennedy", "Carrera 71D # 6-94"),
    "Plaza Central": (4.6245, -74.114, "Puente Aranda", "Carrera 65 # 11-50"),
    "Mallplaza NQS": (4.6182, -74.0857, "Los Mártires", "Av. NQS (Cra 30) con Calle 19"),
    "Gran Plaza Bosa": (4.612, -74.188, "Bosa", "Calle 65 Sur con Carrera 80"),
    "Terraza Pasteur": (4.611, -74.07, "Santa Fe", "Carrera 7 # 24-52"),
    "Milenio Plaza": (4.605, -74.169, "Kennedy", "Av. Ciudad de Cali # 42B-51 Sur"),
    "Gran San Victorino": (4.5991, -74.0793, "Santa Fe", "Carrera 10 con Calle 10"),
    "Centro Mayor": (4.5917, -74.1239, "Antonio Nariño", "Autopista Sur con Calle 38A Sur"),
    "Paseo Villa del Río": (4.5865, -74.145, "Bosa / Tunjuelito", "Autopista Sur con Carrera 64B"),
    "Gran Plaza El Ensueño": (4.575, -74.152, "Ciudad Bolívar", "Av. Boyacá con Calle 59 Sur"),
    "Ciudad Tunal": (4.5715, -74.129, "Tunjuelito", "Calle 47B Sur # 24B-33"),
}
