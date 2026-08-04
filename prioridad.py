"""
Prioridad de una parcela.

Regla del proyecto: lo que manda es PRECIO, ROL y AGUA. La localidad es el
segundo criterio, no el primero.

Este modulo convierte el texto libre de cada ficha en tres clasificaciones
explicitas y un indice de 0 a 100. La idea es que el orden del listado se pueda
explicar: si una parcela aparece arriba, se puede senalar exactamente por que.

Los tres criterios duros suman 100:
    precio  40 puntos
    rol     30 puntos
    agua    30 puntos

Un dato faltante suma casi cero. Es a proposito: un aviso con buen precio pero que
no dice nada del rol ni del agua no es mejor que uno con rol y agua resueltos, y el
puntaje tiene que reflejarlo. La informacion que falta es trabajo pendiente, no un
punto neutro.

La localidad NO suma al indice. Se calcula aparte y solo se usa para desempatar
entre parcelas que cumplen lo mismo.
"""

import re
import unicodedata

from config import PRECIO_IDEAL_MAX, PRECIO_TOLERABLE_MAX


def _norm(t) -> str:
    t = unicodedata.normalize("NFKD", str(t or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.lower()).strip()


# Marcadores de negacion. Importan mucho: varias fichas dicen cosas como
# "no menciona derecho de aprovechamiento constituido en la DGA", y buscar la
# frase suelta daria un falso positivo justo al reves de lo que dice el aviso.
_NEGACIONES = (
    "no menciona", "no especifica", "no aclara", "no indica", "no dice",
    "no declara", "no publica", "no tiene", "no hay", "no cuenta con",
    "sin ", "falta ", "faltante", "no se ", "ni ",
)


def _menciona(texto: str, claves) -> bool:
    """
    True si alguna clave aparece SIN una negacion inmediatamente antes.
    Se mira una ventana de 45 caracteres previos, que en la practica cubre
    'no menciona X', 'sin X constituido', 'falta confirmar X'.
    """
    for clave in claves:
        for m in re.finditer(re.escape(clave), texto):
            ventana = texto[max(0, m.start() - 45):m.start()]
            if not any(neg in ventana for neg in _NEGACIONES):
                return True
    return False


# ---------------------------------------------------------------------------
# PRECIO - 40 puntos
# ---------------------------------------------------------------------------

def evaluar_precio(precio) -> tuple[int, str, str]:
    """Devuelve (puntos, nivel, explicacion). nivel: ok | limite | caro | falta."""
    if not isinstance(precio, (int, float)) or precio <= 0:
        return 4, "falta", "El aviso no publica precio"

    if precio <= PRECIO_IDEAL_MAX:
        return 40, "ok", f"${precio:,.0f} esta dentro del objetivo de ${PRECIO_IDEAL_MAX:,.0f}".replace(",", ".")

    if precio <= PRECIO_TOLERABLE_MAX:
        # Decae linealmente de 40 a 20 entre el ideal y el techo tolerable
        tramo = (precio - PRECIO_IDEAL_MAX) / (PRECIO_TOLERABLE_MAX - PRECIO_IDEAL_MAX)
        puntos = int(round(40 - tramo * 20))
        return puntos, "limite", f"${precio:,.0f} esta sobre el objetivo pero bajo el techo tolerable".replace(",", ".")

    return 0, "caro", f"${precio:,.0f} supera el techo de ${PRECIO_TOLERABLE_MAX:,.0f}".replace(",", ".")


# ---------------------------------------------------------------------------
# ROL - 30 puntos
# ---------------------------------------------------------------------------

_ROL_VERIFICADO = ("verificado en el sii", "rol verificado", "rol inscrito")
_ROL_DECLARADO = ("rol propio", "rol individual", "roles individuales",
                  "rol listo", "listo para escriturar", "con rol")
_SIN_ROL = ("sin rol", "no tiene rol", "rol comun", "rol matriz", "en tramite")


def evaluar_rol(texto) -> tuple[int, str, str]:
    """nivel: verificado | declarado | falta | sin_rol."""
    t = _norm(texto)

    if not t or "no evaluado" in t:
        return 3, "falta", "Dato faltante: hay que pedirlo al vendedor"

    if _menciona(t, _SIN_ROL) or any(k in t for k in _SIN_ROL):
        return 0, "sin_rol", "El aviso indica que no hay rol propio"

    if _menciona(t, _ROL_VERIFICADO):
        return 30, "verificado", "Rol verificado en el SII"

    if _menciona(t, _ROL_DECLARADO):
        # Declarado por el vendedor pero sin verificar todavia
        if "falta verificar" in t or "sin verificar" in t or "segun el aviso" in t:
            return 22, "declarado", "Rol propio declarado por el vendedor, falta verificarlo en el SII"
        return 24, "declarado", "Rol propio declarado en el aviso"

    if "dato faltante" in t:
        return 3, "falta", "Dato faltante: hay que pedirlo al vendedor"

    return 3, "falta", "El aviso no aclara el estado del rol"


# ---------------------------------------------------------------------------
# AGUA - 30 puntos
# ---------------------------------------------------------------------------

_AGUA_FIRME = ("derecho de aprovechamiento", "derecho constituido", "derechos de agua constituidos",
               "inscrito en la dga", "red de agua", "apr", "agua potable rural")
_AGUA_OBRA = ("agua de pozo", "pozo construido", "pozo profundo", "con pozo", "puntera")
_AGUA_VAGA = ("vertiente", "factibilidad hidrica", "factibilidad de agua", "napa",
              "agua disponible", "estero", "vertientes subterraneas")
_SIN_AGUA = ("sin agua", "no hay agua", "sin factibilidad de agua")


def evaluar_agua(texto) -> tuple[int, str, str]:
    """nivel: firme | obra | vaga | falta | sin_agua."""
    t = _norm(texto)

    if not t or "no evaluado" in t:
        return 2, "falta", "Dato faltante: es el criterio excluyente, hay que preguntarlo"

    if any(k in t for k in _SIN_AGUA):
        return 0, "sin_agua", "El aviso indica que no hay factibilidad de agua"

    if _menciona(t, _AGUA_FIRME):
        return 30, "firme", "Derecho de agua constituido o conexion a red"

    if _menciona(t, _AGUA_OBRA):
        return 26, "obra", "Pozo declarado por el vendedor"

    if _menciona(t, _AGUA_VAGA):
        return 18, "vaga", "Menciona agua, pero sin derecho constituido en la DGA"

    if "dato faltante" in t:
        return 2, "falta", "Dato faltante: es el criterio excluyente, hay que preguntarlo"

    return 2, "falta", "El aviso no aclara la factibilidad de agua"


# ---------------------------------------------------------------------------
# LOCALIDAD - segundo criterio, no suma al indice
# ---------------------------------------------------------------------------
# Se ordena por conectividad y servicios, que es lo que sostiene la plusvalia.
# Es un juicio explicito y editable, no un dato objetivo.

LOCALIDADES = {
    # Isla de Chiloe
    "ancud": (3, "Capital provincial, acceso directo por la ruta 5 y el canal de Chacao"),
    "castro": (3, "Capital provincial, el mayor centro de servicios de la isla"),
    "dalcahue": (2, "A 20 min de Castro, con servicios y conexion a las islas"),
    "chonchi": (2, "A 25 min de Castro, con servicios basicos"),
    "quellon": (2, "Puerto y terminal sur de la ruta 5"),
    "molulco": (2, "Sector de Chonchi, a 25 min de Castro"),
    "coquiao": (2, "Sector de Ancud, a 17 min del centro"),
    "tarahuin": (2, "Sector de Chonchi, cerca del lago"),
    "quemchi": (1, "Costa oriental, mas aislada y con menos servicios"),
    "curaco de velez": (1, "Isla Quinchao, requiere transbordador"),
    "puqueldon": (1, "Isla Lemuy, requiere transbordador"),
    # Cordillera de Nuble
    "las trancas": (3, "Corazon del polo turistico de Nevados de Chillan"),
    "recinto": (3, "Acceso al polo turistico, con servicios todo el ano"),
    "pinto": (3, "Comuna que conecta Chillan con el sector cordillerano"),
    "san fabian": (2, "Portal del valle del Nuble, turismo en crecimiento"),
    "coihueco": (2, "Cerca del embalse, buena conectividad con Chillan"),
    "danicalqui": (1, "Sector cordillerano de Pemuco, mas alejado de Chillan"),
    "pemuco": (1, "Sector cordillerano, mas alejado de los polos turisticos"),
}


def evaluar_localidad(ubicacion, zona=None) -> tuple[int, str]:
    """Devuelve (nivel 0-3, explicacion). 0 = fuera de zona o no reconocida."""
    if zona == "Fuera de zona":
        return 0, "Fuera de las zonas objetivo"

    t = _norm(ubicacion)
    mejor = (0, "Localidad dentro de la zona, sin referencia de conectividad")
    for clave, (nivel, motivo) in LOCALIDADES.items():
        if clave in t and nivel > mejor[0]:
            mejor = (nivel, motivo)
    return mejor


# ---------------------------------------------------------------------------
# Calculo completo
# ---------------------------------------------------------------------------

def calcular(ficha: dict) -> dict:
    """
    Agrega a la ficha los campos de prioridad. Modifica y devuelve la ficha.
    """
    p_pts, p_niv, p_exp = evaluar_precio(ficha.get("precio_clp"))
    r_pts, r_niv, r_exp = evaluar_rol(ficha.get("estado_rol"))
    a_pts, a_niv, a_exp = evaluar_agua(ficha.get("agua"))

    fuera = ficha.get("zona") == "Fuera de zona"
    indice = 0 if fuera else p_pts + r_pts + a_pts

    l_niv, l_exp = evaluar_localidad(ficha.get("ubicacion_comuna"), ficha.get("zona"))

    # Cuantos de los tres criterios estan efectivamente respondidos por el aviso.
    # Sirve para agrupar el listado de forma que se entienda sin mirar el puntaje.
    ok_precio = p_niv in ("ok", "limite")
    ok_rol = r_niv in ("verificado", "declarado")
    ok_agua = a_niv in ("firme", "obra", "vaga")
    respondidos = sum((ok_precio, ok_rol, ok_agua))

    cumple_tres = not fuera and respondidos == 3

    ficha["prioridad"] = {
        "indice": indice,
        "cumple_tres": cumple_tres,
        "respondidos": 0 if fuera else respondidos,
        "precio": {"puntos": p_pts, "nivel": p_niv, "explicacion": p_exp},
        "rol": {"puntos": r_pts, "nivel": r_niv, "explicacion": r_exp},
        "agua": {"puntos": a_pts, "nivel": a_niv, "explicacion": a_exp},
        "localidad": {"nivel": l_niv, "explicacion": l_exp},
    }
    return ficha


def clave_orden(ficha: dict):
    """
    Clave de ordenamiento del proyecto:
      1. Cumplir los tres criterios duros
      2. Indice de cumplimiento (precio + rol + agua)
      3. Localidad
      4. Precio mas bajo
    """
    pr = ficha.get("prioridad") or {}
    return (
        0 if pr.get("cumple_tres") else 1,
        -(pr.get("indice") or 0),
        -((pr.get("localidad") or {}).get("nivel") or 0),
        ficha.get("precio_clp") or 10**12,
    )
