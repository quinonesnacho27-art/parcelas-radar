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
        "comunas": [
            "Ancud", "Castro", "Quellon", "Dalcahue", "Quemchi",
            "Chonchi", "Curaco de Velez", "Puqueldon",
        ],
        "keywords": [
            "ancud", "castro", "quellon", "dalcahue", "quemchi", "chonchi",
            "curaco de velez", "puqueldon", "chiloe", "coquiao", "linao",
            "quicavi", "tenaun", "achao",
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
BUSQUEDAS = [
    # --- Cordillera de Nuble ---
    {"fuente": "portalinmobiliario", "query": "parcela san fabian nuble", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "query": "parcela coihueco", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "query": "parcela pinto nuble", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "query": "parcela recinto nuble", "zona_hint": "Cordillera de Nuble"},
    {"fuente": "portalinmobiliario", "query": "parcela las trancas", "zona_hint": "Cordillera de Nuble"},
    # --- Isla de Chiloe ---
    {"fuente": "portalinmobiliario", "query": "parcela ancud chiloe", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "query": "parcela castro chiloe", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "query": "parcela quellon", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "query": "parcela dalcahue", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "query": "parcela chonchi", "zona_hint": "Isla de Chiloe"},
    {"fuente": "portalinmobiliario", "query": "parcela quemchi", "zona_hint": "Isla de Chiloe"},
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

# Etiqueta opcional. Si existe en Gmail tambien se lee; si no existe no pasa nada.
IMAP_CARPETA_INGESTA = "ParcelasRadar"

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
