"""
Configuracion central de Parcelas Radar.
Todos los criterios del Proyecto viven aqui: si cambian los criterios,
se cambian en este archivo y NO en el resto del codigo.
"""

# ---------------------------------------------------------------------------
# ZONAS VALIDAS (sin excepcion)
# ---------------------------------------------------------------------------
# Cada zona define: comunas/localidades aceptadas y palabras clave que
# permiten reconocerla en el texto libre de un aviso.

ZONAS = {
    "Cordillera de Nuble": {
        "region": "Nuble",
        "comunas": [
            "San Fabian", "San Fabian de Alico",
            "Coihueco", "Pinto", "Las Trancas", "Recinto",
            "Chillan Viejo",  # solo sectores cordilleranos; el evaluador lo matiza
        ],
        # keywords normalizadas (sin tilde, minusculas) para el prefiltro barato
        "keywords": [
            "san fabian", "alico", "coihueco", "pinto", "las trancas",
            "recinto", "shangri", "valle hermoso", "atacalco", "los lleuques",
            "cordillera de nuble", "nevados de chillan",
        ],
    },
    "Isla de Chiloe": {
        "region": "Los Lagos",
        # Las 10 comunas de la provincia de Chiloe. Queilen y Quinchao se
        # agregaron el 5 de agosto de 2026: estan en el archipielago igual que
        # el resto, y dejarlas fuera hacia que avisos legitimos (Pureo, Achao)
        # se descartaran por una omision de la lista, no por un criterio.
        "comunas": [
            "Ancud", "Castro", "Quellon", "Dalcahue", "Quemchi",
            "Chonchi", "Curaco de Velez", "Puqueldon", "Queilen", "Quinchao",
        ],
        "keywords": [
            "ancud", "castro", "quellon", "dalcahue", "quemchi", "chonchi",
            "curaco de velez", "puqueldon", "queilen", "quinchao",
            "chiloe", "coquiao", "linao", "quicavi", "tenaun", "achao",
            # sectores y loteos que aparecen en avisos sin nombrar la comuna
            "coipomo", "tarahuin", "pureo", "choroihue", "isla lemuy",
            "rilan", "nercon", "cucao", "huillinco", "quinched", "terao",
            "compu", "yaldad", "chadmo", "detif", "aldachildo",
        ],
    },
}

# Localidades que SUENAN a sur de Chile pero NO son zona valida.
# Sirven para descartar rapido y para explicarle el porque al usuario.
ZONAS_TRAMPA = {
    "ensenada": "Ensenada pertenece a la comuna de Puerto Varas (Los Lagos), no es Chiloe ni cordillera de Nuble.",
    "puerto varas": "Puerto Varas (Los Lagos) no esta en las zonas objetivo.",
    "puerto montt": "Puerto Montt (Los Lagos) no esta en las zonas objetivo.",
    "frutillar": "Frutillar (Los Lagos) no esta en las zonas objetivo.",
    "llanquihue": "Llanquihue (Los Lagos) no esta en las zonas objetivo.",
    "san juan de la costa": "San Juan de la Costa pertenece a la provincia de Osorno, no es Chiloe.",
    "osorno": "Osorno (Los Lagos) no esta en las zonas objetivo.",
    "pucon": "Pucon (La Araucania) no esta en las zonas objetivo.",
    "villarrica": "Villarrica (La Araucania) no esta en las zonas objetivo.",
    "panguipulli": "Panguipulli (Los Rios) no esta en las zonas objetivo.",
    "valdivia": "Valdivia (Los Rios) no esta en las zonas objetivo.",
    "hualqui": "Hualqui (Biobio) no esta en la cordillera de Nuble.",
    "antuco": "Antuco (Biobio) no esta en la cordillera de Nuble.",
    "chiloe continental": "El sector continental no cuenta como Isla de Chiloe.",
    # Agregadas el 5 de agosto de 2026 a partir de los 16 reenvios del papa:
    # todas aparecieron en avisos reales y ninguna estaba cubierta.
    "los muermos": "Los Muermos (Los Lagos) es continente, no es Isla de Chiloe.",
    "fresia": "Fresia (Los Lagos) es continente, no es Isla de Chiloe.",
    "purranque": "Purranque (Los Lagos) pertenece a la provincia de Osorno, no es Chiloe.",
    "teodoro schmidt": "Teodoro Schmidt (La Araucania) no esta en las zonas objetivo.",
    "cherquenco": "Cherquenco (La Araucania) no esta en las zonas objetivo.",
    "aysen": "La Region de Aysen no esta en las zonas objetivo.",
    "coyhaique": "Coyhaique (Aysen) no esta en las zonas objetivo.",
    "carretera austral": "La Carretera Austral queda fuera de las dos zonas objetivo.",
    "patagonia": "La Patagonia (Aysen o Magallanes) no esta en las zonas objetivo.",
    "region de los rios": "La Region de Los Rios no esta en las zonas objetivo.",
    "calbuco": "Calbuco (Los Lagos) es continente, no es Isla de Chiloe.",
    "maullin": "Maullin (Los Lagos) es continente, no es Isla de Chiloe.",
    "el tepual": "El aeropuerto El Tepual esta en Puerto Montt, fuera de las zonas objetivo.",
}

# ---------------------------------------------------------------------------
# CRITERIOS ECONOMICOS
# ---------------------------------------------------------------------------
PRECIO_IDEAL_MAX = 10_000_000     # CLP - objetivo
PRECIO_TOLERABLE_MAX = 14_000_000  # CLP - techo duro salvo excepcion justificada

# Valor UF referencial de respaldo. El script intenta obtener el real de mindicador.cl
# y solo usa este numero si la API no responde. Si se usa el respaldo, queda marcado
# en la ficha como dato estimado.
UF_FALLBACK = 40_500

# Superficie: no es criterio de descarte, pero se usa para el precio por m2
SUPERFICIE_MIN_M2_ESPERADA = 5000  # la parcela tipica de 5.000 m2

# ---------------------------------------------------------------------------
# CRITERIOS DE FILTRADO (usados por el evaluador y por la web)
# ---------------------------------------------------------------------------
CRITERIOS = {
    "uso": "Parcela de inversion. NO vivienda principal ni proyecto habitacional.",
    "precio": (
        f"Idealmente <= ${PRECIO_IDEAL_MAX:,.0f} CLP; tolerable hasta "
        f"${PRECIO_TOLERABLE_MAX:,.0f} CLP. Sobre eso se descarta salvo que el resto "
        "de los indicadores sea excepcional, y en ese caso hay que justificarlo explicitamente."
    ),
    "forma_pago": "Al contado. Credito directo del vendedor NO cumple el criterio.",
    "rol": (
        "Rol propio SII obligatorio. Si el aviso no lo menciona: marcar como "
        "'dato faltante - pedir al vendedor', NO descartar de inmediato, pero bajar el puntaje."
    ),
    "agua": (
        "Factibilidad de agua obligatoria (pozo, vertiente, derecho de agua constituido o red). "
        "Sin esto se descarta."
    ),
    "luz": "Factibilidad electrica deseable, no excluyente. Si falta, senalar como costo/riesgo adicional.",
}

# ---------------------------------------------------------------------------
# FUENTES A MONITOREAR
# ---------------------------------------------------------------------------
# Cada entrada genera una busqueda. Se mantienen acotadas a las zonas objetivo
# para no gastar tokens evaluando avisos de todo Chile.
# 'lugar' es el slug de ubicacion de Portalinmobiliario, verificado uno por uno
# contra el sitio real. 'comuna' es el nombre que debe aparecer en el titulo de la
# pagina: si no aparece, los resultados se descartan.
#
# Ojo con esto: cuando un slug no existe, el sitio NO devuelve 404, devuelve el
# listado nacional de parcelas con HTTP 200. Por eso la verificacion del titulo es
# obligatoria y no un lujo.
#
# Las comunas sin slug propio (Castro, Curaco de Velez, San Fabian, Pinto) se
# buscan con "_q_", que es la busqueda de texto libre del portal.
BUSQUEDAS = [
    # --- Isla de Chiloe ---
    {"fuente": "portalinmobiliario", "lugar": "ancud-los-lagos", "comuna": "Ancud", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "lugar": "quellon-los-lagos", "comuna": "Quellon", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "lugar": "dalcahue-los-lagos", "comuna": "Dalcahue", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "lugar": "quemchi-los-lagos", "comuna": "Quemchi", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "lugar": "chonchi-los-lagos", "comuna": "Chonchi", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "lugar": "puqueldon-los-lagos", "comuna": "Puqueldon", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "lugar": "_q_parcela-castro-chiloe", "comuna": "castro", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "lugar": "_q_parcela-curaco-de-velez", "comuna": "curaco", "zona_hint": "Isla de Chiloe"},
    # --- Cordillera de Nuble ---
    {"fuente": "portalinmobiliario", "lugar": "coihueco-nuble", "comuna": "Coihueco", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "lugar": "chillan-nuble", "comuna": "Chillan", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "lugar": "_q_parcela-san-fabian-nuble", "comuna": "san-fabian", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "lugar": "_q_parcela-pinto-nuble", "comuna": "pinto", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "lugar": "_q_parcela-las-trancas", "comuna": "trancas", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "lugar": "_q_parcela-recinto-nuble", "comuna": "recinto", "zona_hint": "Cordillera de Nuble"},
    # --- Yapo ---
    {"fuente": "yapo", "query": "parcela chiloe", "zona_hint": "Isla de Chiloe"},
    {"fuente": "yapo", "query": "parcela nuble cordillera", "zona_hint": "Cordillera de Nuble"},
]

# ---------------------------------------------------------------------------
# ENTREGA
# ---------------------------------------------------------------------------
DESTINATARIOS = ["jmqs2007@gmail.com"]
REMITENTE_NOMBRE = "Parcelas Radar"
ASUNTO_BASE = "Parcelas Radar"

# ---------------------------------------------------------------------------
# CASILLA PARA LOS AVISOS QUE MANDA EL PAPA
# ---------------------------------------------------------------------------
# Se usa el alias con "+" de Gmail: todo lo que llegue a
# quinonesnacho27+parcelas@gmail.com aterriza igual en la bandeja normal, pero el
# sistema lo reconoce por el destinatario. No hace falta crear filtros ni etiquetas:
# funciona desde el primer correo.
CORREO_INGESTA = "quinonesnacho27+parcelas@gmail.com"

# Cuantos dias hacia atras se revisan los correos en cada corrida. Con 3 dias hay
# margen de sobra si el job no corre un dia.
DIAS_INGESTA_CORREO = 3

# Etiqueta opcional, solo como pista. El codigo ya no depende de este nombre:
# `fuentes._buzones_a_revisar()` lista los buzones de la cuenta, usa el que trae
# el atributo \All (el nombre cambia con el idioma de Gmail) y reconoce sola
# cualquier etiqueta que mencione "parcela". Antes decia "ParcelasRadar", la
# etiqueta real se llama "Parcelas", y eso bastaba para que no se leyera nada.
IMAP_CARPETA_INGESTA = "Parcelas"

# ---------------------------------------------------------------------------
# MOTOR DE EVALUACION
# ---------------------------------------------------------------------------
#   "reglas"     sin API, sin clave, sin costo, sin limite. Es el que viene puesto.
#   "gemini"     capa gratuita de Google AI Studio (necesita GEMINI_API_KEY).
#   "anthropic"  API de pago de Claude (necesita ANTHROPIC_API_KEY).
# Si el motor elegido falla, el sistema cae solo a "reglas" y sigue funcionando.
MOTOR_EVALUACION = "reglas"

# Cuantos avisos como maximo se evaluan por corrida. Con el motor de reglas no
# hay costo, pero el tope evita informes interminables.
MAX_EVALUACIONES_POR_CORRIDA = 25

# Modelo de Claude, si se usa el motor "anthropic"
MODELO = "claude-sonnet-5"
