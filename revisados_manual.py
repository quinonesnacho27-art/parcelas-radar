"""
Catalogo de avisos cuyo contenido se leyo fuera del pipeline.

POR QUE EXISTE
--------------
Instagram y Facebook no se raspan (ver README). Cuando el papa reenvia solo el
link, el correo que llega no trae ni una palabra del aviso: el prefiltro no
encuentra comuna y el aviso se descarta en silencio. Ese fue el bug del 5 de
agosto de 2026: 16 avisos reenviados, 0 en el informe.

La solucion es separar DOS cosas que antes estaban pegadas:

  1. LEER el contenido del post  -> pasa fuera de GitHub Actions, en el
     navegador de Nacho, donde la sesion de Instagram ya esta iniciada.
     Eso lo hace la tarea diaria de Cowork y escribe aqui.
  2. EVALUAR el aviso            -> sigue pasando en el pipeline de siempre,
     con los mismos criterios, el mismo puntaje y la misma ficha.

Asi el papa no cambia nada de lo que hace: manda el link y listo.

FORMATO
-------
La clave es la parte estable de la URL (el shortcode de Instagram, o el dominio
para sitios propios). `buscar(url)` normaliza antes de comparar, asi que da lo
mismo si el link viene con ?igsh=... o sin el.

    "DbGRJeYsD_p": {
        "titulo": "...",
        "descripcion": "el texto del aviso, tal como se leyo",
        "url_proyecto": "https://...",   # opcional, sitio propio del proyecto
    }

Lo que va en `descripcion` es TEXTO DEL AVISO, no interpretacion. El evaluador
de reglas extrae de ahi superficie, precio, rol, agua y luz. Si el aviso no dice
algo, no se inventa: queda en "falta preguntar", que es exactamente lo que
tiene que pasar.
"""

import re

# ---------------------------------------------------------------------------
# Avisos leidos el 5 de agosto de 2026 (los 16 que reenvio Marcelo el 4 y 5/08)
# ---------------------------------------------------------------------------

REVISADOS = {
    # --- Isla de Chiloe -----------------------------------------------------
    "DbGRJeYsD_p": {
        "titulo": "Choroihue - Parcelas agricolas en Ancud, Chiloe",
        "url_proyecto": "https://www.choroihue.cl/",
        "descripcion": (
            "Choroihue. Parcelas agricolas en la comuna de Ancud, Chiloe, Region de Los Lagos. "
            "Entorno de bosque nativo, praderas y orilla de rio. Desde $9.990.000. "
            "Credito directo 0% interes, hasta 48 cuotas sin pie. 10% de descuento al contado. "
            "Proyecto de 6 etapas con una reserva natural de 30 hectareas y 1,2 km de extension. "
            "A 27 km de Ancud y 33 km del futuro puente de Chacao. "
            "Algunas parcelas cuentan con arroyo propio y otras con acceso directo a la orilla del rio. "
            "Bosques de coigue, arrayan y tepu. Caminos internos habilitados para acceder a las parcelas. "
            "El aviso no menciona el rol de la propiedad ni la superficie de cada parcela. "
            "El aviso no menciona derecho de aprovechamiento de aguas ni pozo. "
            "El aviso no menciona factibilidad de luz electrica. "
            "Contacto +56 9 9080 5042, info@choroihue.cl."
        ),
    },
    "DbmL9T_s67U": {
        "titulo": "Coipomo, Chiloe - parcelas desde $9.990.000 con rol propio",
        "descripcion": (
            "Invierte desde $9.990.000. Dos proyectos: Cherquenco (Region de La Araucania) y "
            "Coipomo, Chiloe (sector de la comuna de Ancud). Valor referencial llevado a UF. "
            "Cada parcela incluye rol propio, escrituracion inmediata y red de luz y agua. "
            "Credito directo disponible. Promocion por tiempo limitado y sujeta a disponibilidad. "
            "El aviso no publica la superficie de las parcelas. "
            "El aviso no aclara si el precio de $9.990.000 corresponde a Coipomo o a Cherquenco. "
            "El aviso no indica si hay descuento por pago al contado."
        ),
    },
    "DaEL8QeM_gb": {
        "titulo": "Aires de Tarahuin, Chonchi - primeras 10 unidades",
        "descripcion": (
            "Aires de Tarahuin, comuna de Chonchi, Isla de Chiloe. "
            "Las primeras 10 unidades incluyen frente cercado, porton de acceso y "
            "terrenos planos y limpios. A 6 minutos del Lago Tarahuin. "
            "Vendedor: Grupo Sur Nativo. "
            "El aviso no publica precio ni forma de pago. "
            "El aviso no publica la superficie de las parcelas. "
            "El aviso no menciona el rol de la propiedad. "
            "El aviso no menciona factibilidad de agua ni de luz electrica."
        ),
    },
    "Da5py7iMBcS": {
        "titulo": "Azul Canelo - parcelas en Pureo, Queilen, Chiloe",
        "descripcion": (
            "Proyecto Azul Canelo. Parcelas en Pureo, comuna de Queilen, Isla de Chiloe. "
            "Vista al mar, bosque nativo y caminos internos propios. "
            "Cuenta secundaria de @latitudesaustrales. "
            "El aviso no publica precio ni forma de pago. "
            "El aviso no publica la superficie de las parcelas. "
            "El aviso no menciona el rol de la propiedad. "
            "El aviso no menciona factibilidad de agua ni de luz electrica."
        ),
    },

    # --- Fuera de zona ------------------------------------------------------
    "DbYKkoUsa-i": {
        "titulo": "Remate Bosques de Frutillar - Frutillar, Los Lagos",
        "descripcion": (
            "Remate proyecto Bosques de Frutillar, comuna de Frutillar, Region de Los Lagos. "
            "Parcelas desde 5.000 m2 y macrolotes de 13.000 m2. "
            "Valores desde $14.990.000 al contado. Solo venta al contado. "
            "Rol propio. Documentacion al dia: SII, SAG y CBR. Porton principal de acceso. "
            "Caminos estabilizados hacia cada parcela. "
            "A 15 min de la Ruta 5 Sur, 17 min del centro de Frutillar, 21 min del Lago Llanquihue, "
            "35 min de Puerto Varas, 48 min de Puerto Montt, 50 min de Osorno."
        ),
    },
    "DbCyiL7MwZ7": {
        "titulo": "El Avellano - Los Muermos, Los Lagos",
        "descripcion": (
            "Nuevo lanzamiento en Los Muermos, Region de Los Lagos. Proyecto El Avellano. "
            "Desde $12.900.000. A 10 minutos del centro de Los Muermos, 20 minutos del "
            "aeropuerto El Tepual y 45 minutos de Puerto Varas. "
            "Credito directo a 11, 24 y 36 meses. Asesoria legal gratuita. "
            "El aviso promete plusvalia sobre el 70% en 2 anos. "
            "El aviso no menciona el rol de la propiedad ni factibilidad de agua o luz."
        ),
    },
    "DaWlmw-AnFS": {
        "titulo": "Reserva Porma - Teodoro Schmidt, La Araucania",
        "descripcion": (
            "Proyecto en Teodoro Schmidt, Region de La Araucania. Terrenos desde 5.000 m2, "
            "junto al mar. Rol propio, porton de acceso, terreno con suave lomaje, "
            "postacion con luminaria solar, financiamiento directo. "
            "Desde $11.990.000. Financia en cuotas directas. "
            "El aviso no menciona factibilidad de agua."
        ),
    },
    "DXUbEj0DKKK": {
        "titulo": "Reserva Quilaco - a 15 km de Pucon, La Araucania",
        "descripcion": (
            "Reserva Quilaco. Parcelas a 15 km de Pucon, Region de La Araucania. "
            "Rio Trancura, bosque centenario. Parcelas listas para construir. "
            "Un comentario del propio aviso indica valores a partir de 65 millones. "
            "El aviso no publica precio oficial, superficie, rol ni factibilidad de agua."
        ),
    },
    "DWB1O65gIDj": {
        "titulo": "Parque Cantabria - Puerto Varas",
        "descripcion": (
            "Parque Cantabria, Puerto Varas, Region de Los Lagos. "
            "Financiamiento de hasta 60 cuotas en UF, sin intereses, con ayuda para financiar el pie. "
            "El aviso no publica precio, superficie, rol ni factibilidad de agua o luz."
        ),
    },
    "DbBehb5sRGA": {
        "titulo": "Parcelas a minutos de Frutillar - rol propio, SAG",
        "descripcion": (
            "Parcelas a minutos de Frutillar, Region de Los Lagos. Rol propio. "
            "Aprobadas por el SAG. "
            "El aviso no publica precio, forma de pago, superficie ni factibilidad de agua o luz."
        ),
    },
    "DbmcG91AHIL": {
        "titulo": "Fundo Rio Los Ostiones - 25 min del aeropuerto de Puerto Montt",
        "descripcion": (
            "Parcelas a 25 minutos del aeropuerto de Puerto Montt, Region de Los Lagos. "
            "El aviso no publica precio, superficie, rol ni factibilidad de agua o luz."
        ),
    },
    "DYS8c6wjK1H": {
        "titulo": "Estancia Braunau - sector de Purranque, Osorno",
        "descripcion": (
            "Estancia Braunau, sector de Purranque, provincia de Osorno, Region de Los Lagos. "
            "Invita a agendar visita. "
            "El aviso no publica precio, superficie, rol ni factibilidad de agua o luz. "
            "En los comentarios se pregunta el valor repetidamente y se responde por privado."
        ),
    },
    "DTQ7geVDP_E": {
        "titulo": "Pampas del Sur - Region de Los Rios",
        "descripcion": (
            "Parcelas en oferta en la Region de Los Rios, 7 parcelaciones distintas. "
            "Publicacion del 8 de enero de 2026. "
            "El aviso no publica precio, ubicacion exacta, superficie, rol ni factibilidad de agua o luz."
        ),
    },
    "DYppLOCANdv": {
        "titulo": "Desarrollo Las Praderas - ubicacion no indicada",
        "descripcion": (
            "Construye en tu propio terreno con solo el 10% de pie. Oferta por tiempo limitado. "
            "El aviso no indica en que comuna ni region estan los terrenos. "
            "El aviso no publica precio, superficie, rol ni factibilidad de agua o luz. "
            "En los comentarios preguntan el valor repetidamente sin respuesta publica."
        ),
    },
    "Dagb54BgHeR": {
        "titulo": "@mercadodeparcelas - publicacion sin texto",
        "descripcion": (
            "La publicacion no tiene texto, solo imagen. "
            "El aviso no indica ubicacion, precio, superficie, rol ni factibilidad de agua o luz."
        ),
    },

    # --- Sitio propio (no es Instagram) -------------------------------------
    "aguasdelquetro.cl": {
        "titulo": "Aguas del Quetro - Valle Lagunas, Region de Aysen",
        "url_proyecto": "https://www.aguasdelquetro.cl/",
        "descripcion": (
            "Aguas del Quetro. 15 terrenos rurales en Valle Lagunas, Region de Aysen, "
            "a aproximadamente 50 km de Coyhaique, en la Carretera Austral. "
            "Superficies entre 5,5 y 8 hectareas aprox. por predio. "
            "Cada terreno con cerca de 100 metros de frente al rio Quetro. "
            "Bosque nativo y praderas. Cada terreno contara con rol propio. "
            "Proceso de subdivision aprobado y planimetria definida para los 15 terrenos. "
            "Acceso desarrollado y caminos interiores. "
            "Precio base UF 3.200 por terreno. Primeras 5 unidades con 20% de descuento: UF 2.550. "
            "Vendedor: Agricola Aguas del Quetro SpA. "
            "El aviso no menciona factibilidad de luz electrica."
        ),
    },
}


# ---------------------------------------------------------------------------
# Busqueda
# ---------------------------------------------------------------------------

_RE_SHORTCODE = re.compile(r"(?:instagram\.com|facebook\.com)/(?:p|reel|share)/([A-Za-z0-9_-]+)", re.I)
_RE_DOMINIO = re.compile(r"https?://(?:www\.)?([^/?#]+)", re.I)


def clave(url: str) -> str:
    """
    Reduce una URL a la clave estable con la que se guarda en REVISADOS.

    Para Instagram/Facebook es el shortcode del post: sobrevive a ?igsh=,
    ?fbclid= y demas basura de tracking que Meta agrega al compartir.
    Para cualquier otro sitio es el dominio, porque un proyecto suele tener
    un solo sitio y varias URLs con parametros de campana.
    """
    if not url:
        return ""
    m = _RE_SHORTCODE.search(url)
    if m:
        return m.group(1)
    m = _RE_DOMINIO.match(url.strip())
    if m:
        return m.group(1).lower()
    return ""


def buscar(url: str) -> dict | None:
    """Devuelve la ficha leida a mano para esa URL, o None si no esta."""
    k = clave(url)
    return REVISADOS.get(k) if k else None


def aplicar(aviso: dict) -> bool:
    """
    Inyecta el texto leido en el aviso, si existe.

    Devuelve True si se aplico. El texto NO reemplaza lo que ya trae el aviso:
    se concatena, para no perder nada de lo que el papa haya escrito en el correo.
    """
    ficha = buscar(aviso.get("url", ""))
    if not ficha:
        return False

    if ficha.get("titulo"):
        aviso["titulo"] = ficha["titulo"]

    previo = (aviso.get("descripcion") or "").strip()
    nuevo = ficha.get("descripcion", "")
    # El texto previo suele ser la URL pelada; no aporta y ensucia la ficha.
    if previo and not previo.startswith("http"):
        aviso["descripcion"] = f"{previo} | {nuevo}"[:8000]
    else:
        aviso["descripcion"] = nuevo[:8000]

    if ficha.get("url_proyecto"):
        aviso["url_proyecto"] = ficha["url_proyecto"]

    aviso["contenido_leido"] = True
    return True
