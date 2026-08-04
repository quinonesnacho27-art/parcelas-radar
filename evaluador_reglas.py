"""
Evaluador por reglas: genera la ficha completa SIN llamar a ninguna API.

Es el motor por defecto del sistema, y existe por una razon concreta: que Parcelas
Radar funcione sin claves, sin tarjeta y sin costo. Un aviso de parcela publica
siempre los mismos seis datos —superficie, precio, forma de pago, rol, agua, luz—
o los omite, y eso se puede leer con reglas.

Lo que un modelo de lenguaje agrega por sobre esto es redaccion, no criterio.
El criterio ya esta en config.py y prioridad.py.

Que hace y que no:
  SI  extrae los seis datos del texto y detecta las senales de riesgo tipicas
      del rubro (urgencia fabricada, credito directo disfrazado, precio anomalo).
  NO  entiende un aviso escrito de forma rara ni infiere lo que no esta escrito.
      Cuando no encuentra algo lo dice, que es exactamente lo que corresponde.
"""

import re

import filtro
import prioridad
from config import PRECIO_IDEAL_MAX, PRECIO_TOLERABLE_MAX

N = filtro.normalizar


# ---------------------------------------------------------------------------
# Extraccion de los seis datos
# ---------------------------------------------------------------------------

def _comuna(t: str, aviso: dict) -> str:
    """
    Encuentra la comuna o sector dentro del texto.

    Importa sobre todo para los avisos que llegan por correo: ahi el campo
    'ubicacion' viene vacio y sin esto se terminaria usando el asunto del correo
    ('Mira esta parcela'), que no dice nada.
    """
    ubic = N(aviso.get("ubicacion", ""))
    encontradas = [nombre for nombre in prioridad.LOCALIDADES if nombre in t]

    if encontradas:
        # La mas especifica gana: 'coquiao' antes que 'ancud'
        principal = max(encontradas, key=len).title()
        otras = [n.title() for n in encontradas if n != max(encontradas, key=len)]
        return f"{principal}, {otras[0]}" if otras else principal

    if ubic:
        return aviso["ubicacion"][:70]
    return (aviso.get("titulo", "") or "sin ubicacion")[:70]


def _superficie(t: str) -> str:
    # Hectareas primero: "2 a 4,1 hectareas", "3 hectareas"
    m = re.search(r"(?:desde\s+)?([\d.,]+)\s*(?:a|hasta)\s*([\d.,]+)\s*(?:hect|ha\b)", t)
    if m:
        return f"De {m.group(1)} a {m.group(2)} hectareas"
    m = re.search(r"([\d.,]+)\s*(?:hect|ha\b)", t)
    if m:
        return f"{m.group(1)} hectareas"
    # Metros cuadrados: "5.000 m2", "5000 m²", "desde 5.000 mts2"
    m = re.search(r"([\d][\d.,]{2,})\s*(?:m2|m²|mts2|mts²|metros cuadrados|mt2)", t)
    if m:
        return f"{m.group(1)} m2"
    return "dato faltante - pedir al vendedor"


_CONTADO = ("al contado", "pago contado", "precio contado", "pagando al contado",
            "exclusivo para pago contado", "precio de contado")
_FINANCIADO = ("credito directo", "financiamiento directo", "financia en cuotas",
               "cuotas mensuales", "credito hipotecario", "pie inicial", "de pie",
               "cuota fija", "financiamiento")


def _pago(t: str) -> tuple[str, bool | None]:
    hay_contado = any(k in t for k in _CONTADO)
    hay_credito = any(k in t for k in _FINANCIADO)

    if hay_contado and hay_credito:
        return ("Ofrece precio al contado y tambien credito directo; "
                "hay que pedir el precio de contado por escrito"), True
    if hay_contado:
        return "Al contado", True
    if hay_credito:
        return ("El aviso solo promociona credito o financiamiento directo; "
                "no publica precio al contado"), False
    return "dato faltante - pedir al vendedor", None


def _rol(t: str) -> str:
    if re.search(r"\bsin rol\b|no tiene rol|rol matriz|rol comun", t):
        return "El aviso indica que no hay rol propio"
    sag = "sag" in t or "aprobacion sag" in t
    if re.search(r"rol propio|rol individual|roles individuales|rol listo|con rol\b", t):
        base = "Rol propio declarado en el aviso"
        if "listo para escriturar" in t or "escritura inmediata" in t:
            base += ", listo para escriturar"
        if sag:
            base += ", con aprobacion SAG declarada"
        return base + " - falta verificarlo en el SII"
    if sag:
        return "Menciona aprobacion SAG pero no dice nada del rol - falta verificarlo en el SII"
    return "dato faltante - pedir al vendedor"


def _agua(t: str) -> tuple[str, bool | None]:
    if re.search(r"sin agua|no hay agua|sin factibilidad de agua", t):
        return "El aviso indica que no hay factibilidad de agua", False
    if re.search(r"derecho[s]? de (?:agua|aprovechamiento)|inscrito en la dga|"
                 r"agua potable rural|\bapr\b|red de agua", t):
        return "Derecho de agua constituido o conexion a red, segun el aviso", True
    if re.search(r"agua de pozo|con pozo|pozo profundo|pozo construido|puntera", t):
        return "Agua de pozo declarada por el vendedor", True
    if re.search(r"vertiente|factibilidad hidrica|factibilidad de agua|napa|estero", t):
        return ("Menciona vertiente o factibilidad hidrica, pero no un derecho de "
                "aprovechamiento constituido en la DGA"), None
    return "dato faltante - pedir al vendedor", None


def _luz(t: str) -> tuple[str, bool | None]:
    if re.search(r"panel(?:es)? solar|luminaria solar|energia solar", t):
        return "Solo energia solar; no menciona conexion a la red electrica", None
    if re.search(r"empalme (?:instalado|ejecutado|listo)|luz instalada|electricidad instalada", t):
        return "Empalme electrico ejecutado, segun el aviso", True
    if re.search(r"factibilidad electrica|factibilidad de luz|luz electrica|"
                 r"postacion|electrificacion", t):
        return ("Factibilidad electrica declarada; factibilidad no es lo mismo que "
                "empalme ejecutado"), True
    return "dato faltante - pedir al vendedor", None


# ---------------------------------------------------------------------------
# Senales de riesgo del rubro
# ---------------------------------------------------------------------------

_URGENCIA = ("ultimas", "ultimos lotes", "solo quedan", "cupos limitados",
             "hasta agotar stock", "liquidacion", "no dejes pasar", "remate",
             "promocion valida", "ultima oportunidad", "unidades limitadas")

_AGREGADORES = ("portalterreno", "boton cotizar", "haz click en el boton",
                "comenta info", "dejanos tus datos", "cotiza aqui")

_RIESGO_ZONA = {
    "ensenada": "Zona de influencia del volcan Calbuco, que hizo erupcion en 2015.",
    "las trancas": "Sector de alta afluencia turistica: verifica el riesgo de incendio forestal en verano.",
    "recinto": "Sector cordillerano: pregunta por el estado del camino en invierno.",
    "pemuco": "Sector cordillerano: pregunta por riesgo de incendio forestal y estado del camino en invierno.",
    "danicalqui": "Sector cordillerano: pregunta por riesgo de incendio forestal y estado del camino en invierno.",
}


def _riesgos(t: str, aviso: dict, precio, zona, mediana_zona, datos=None) -> list[str]:
    r = []
    datos = datos or {}

    if datos.get("cumple_contado") is False:
        r.append(
            "El aviso promociona credito o financiamiento directo, no venta al contado. "
            "El criterio del proyecto es contado: hay que negociar el precio de contado, "
            "que deberia ser bastante menor al publicado."
        )

    if datos.get("agua_ok") is None and ("vertiente" in t or "factibilidad hidrica" in t):
        r.append(
            "El agua se menciona como vertiente o 'factibilidad hidrica': eso no es un "
            "derecho de aprovechamiento constituido en la DGA. Sin ese derecho inscrito el "
            "suministro no esta garantizado juridicamente y el costo de un pozo queda en tu "
            "cancha."
        )

    if precio and mediana_zona and precio < mediana_zona * 0.6:
        pc = int(round((1 - precio / mediana_zona) * 100))
        r.append(
            f"PRECIO ANOMALO: esta {pc}% bajo la mediana de la zona y el aviso no explica "
            "por que. Las causas habituales son terreno sin acceso vehicular, sin "
            "factibilidad de agua, anegadizo, o subdivision no regularizada. Averigua cual "
            "es antes de entusiasmarte con el precio."
        )

    if any(k in t for k in _URGENCIA):
        r.append(
            "El aviso usa lenguaje de urgencia ('ultimas unidades', 'cupos limitados', "
            "'liquidacion'). Es tecnica de venta estandar en este rubro: no apures la "
            "decision por eso."
        )

    if "remate" in t and "martillero" not in t and "tribunal" not in t:
        r.append(
            "Usa la palabra 'remate' como gancho comercial, sin identificar tribunal ni "
            "martillero. Legalmente no significa nada."
        )

    if any(k in t for k in _AGREGADORES):
        r.append(
            "Vendedor no identificable: el aviso es de un portal agregador que pide "
            "'cotizar' para entregar datos. No se puede hacer estudio de titulos sobre un "
            "anuncio. Ademas, al dejar tus datos entras a una base comercial."
        )

    m = re.search(r"(\d+)\s*cuotas?\s*(?:mensuales?\s*)?de\s*(?:solo\s*)?\$?\s*([\d.]+)", t)
    if m and precio:
        try:
            total = int(m.group(1)) * int(m.group(2).replace(".", ""))
            if total > precio:
                sobre = int(round((total / precio - 1) * 100))
                r.append(
                    f"El financiamiento en cuotas suma ${total:,.0f} frente a ${precio:,.0f} "
                    f"al contado: un {sobre}% mas caro. Es una tasa alta disfrazada de "
                    "facilidad de pago.".replace(",", ".")
                )
        except ValueError:
            pass

    if "escritura inmediata" in t and any(k in t for k in ("credito directo", "financiamiento directo")):
        r.append(
            "'Escritura inmediata' junto con 'financiamiento directo' es una combinacion que "
            "hay que aclarar: escriturar antes de terminar de pagar es poco habitual y cambia "
            "el riesgo de la operacion. Pregunta si queda hipoteca a favor del vendedor."
        )

    ubic = N(aviso.get("ubicacion") or aviso.get("titulo") or "")
    for clave, motivo in _RIESGO_ZONA.items():
        if clave in ubic or clave in t:
            r.append(motivo)
            break

    if zona and not re.search(r"ancud|castro|quellon|dalcahue|quemchi|chonchi|curaco|puqueldon|"
                              r"san fabian|coihueco|pinto|trancas|recinto", ubic):
        r.append(
            "El aviso no identifica la comuna con precision. Sin comuna exacta no se puede "
            "confirmar que caiga dentro de las comunas objetivo."
        )

    return r


# ---------------------------------------------------------------------------
# Preguntas al vendedor
# ---------------------------------------------------------------------------

def _preguntas(datos: dict) -> list[str]:
    q = []
    falta = lambda v: "dato faltante" in str(v).lower()

    if datos["precio_clp"] is None:
        q.append("PRECIO: es el dato que decide todo y el aviso no lo publica")
    if datos["cumple_contado"] is not True:
        q.append("Cual es el precio al contado y que descuento hay respecto del credito directo")
    if falta(datos["estado_rol"]) or "falta verificarlo" in datos["estado_rol"]:
        q.append("Numero de rol de una parcela concreta, para verificarlo en el SII")
    if datos["agua_ok"] is not True:
        q.append("Factibilidad de agua: hay pozo construido con prueba de caudal, o derecho "
                 "de aprovechamiento inscrito en la DGA")
    if datos["luz_ok"] is not True:
        q.append("Factibilidad electrica: hay poste en el deslinde o hay que costear la extension")
    if falta(datos["superficie"]):
        q.append("Superficie exacta de la parcela")
    q.append("Copia del plano de subdivision aprobado y del certificado del SAG")
    q.append("Nombre y RUT del vendedor, para el estudio de titulos")
    q.append("Estado del camino de acceso en invierno y si es publico o servidumbre")
    return q


# ---------------------------------------------------------------------------
# Redaccion de la justificacion
# ---------------------------------------------------------------------------

def _justificar(datos, pr, zona, mediana_zona) -> str:
    p = pr["precio"]["nivel"]
    r = pr["rol"]["nivel"]
    a = pr["agua"]["nivel"]
    resp = pr["respondidos"]
    partes = []

    if resp == 3:
        partes.append("Responde los tres criterios duros, que es poco frecuente en este rubro.")
    elif resp == 2:
        falta = ("el precio" if p == "falta" else "el rol" if r == "falta" else "el agua")
        partes.append(f"Responde dos de los tres criterios; lo que falta es {falta}.")
    elif resp == 1:
        tiene = ("el precio" if p in ("ok", "limite") else "el rol" if r in ("verificado", "declarado") else "el agua")
        partes.append(f"El aviso solo responde {tiene}; el resto hay que preguntarlo.")
    else:
        partes.append("El aviso no responde ninguno de los tres criterios: no hay nada que evaluar todavia.")

    if p == "ok":
        partes.append(f"El precio esta dentro del objetivo de ${PRECIO_IDEAL_MAX:,.0f}.".replace(",", "."))
    elif p == "limite":
        partes.append(f"El precio esta sobre el objetivo pero bajo el techo de ${PRECIO_TOLERABLE_MAX:,.0f}.".replace(",", "."))
    elif p == "caro":
        partes.append("El precio supera el techo del proyecto.")

    if a == "vaga":
        partes.append("El agua se menciona pero sin derecho constituido, que es la diferencia "
                      "entre tener agua y tener derecho a usarla.")
    elif a == "falta":
        partes.append("El agua es el criterio excluyente y el aviso no dice nada: sin esa "
                      "respuesta no avanza.")

    if mediana_zona and datos["precio_clp"]:
        d = datos["precio_clp"] / mediana_zona - 1
        if abs(d) > 0.1:
            partes.append(f"Esta un {abs(int(d*100))}% {'sobre' if d > 0 else 'bajo'} "
                          f"la mediana de {zona}.")

    return " ".join(partes)


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------

def evaluar(aviso: dict, historico=None, uf_valor=None) -> dict:
    """Misma firma y mismo esquema de salida que evaluador.evaluar()."""
    historico = historico or []
    texto = " ".join(str(aviso.get(k, "")) for k in
                     ("titulo", "descripcion", "precio_texto", "ubicacion"))
    t = N(texto)

    zona = aviso.get("zona_detectada")
    precio = aviso.get("precio_clp")

    # Mediana de la zona, para comparar y detectar precios anomalos
    previos = [x["precio_clp"] for x in historico
               if x.get("zona") == zona and isinstance(x.get("precio_clp"), (int, float))]
    mediana = sorted(previos)[len(previos) // 2] if previos else None

    pago, contado = _pago(t)
    agua_txt, agua_ok = _agua(t)
    luz_txt, luz_ok = _luz(t)

    datos = {
        "ubicacion_comuna": _comuna(t, aviso),
        "zona": zona or "Fuera de zona",
        "superficie": _superficie(t),
        "precio_clp": precio,
        "precio_texto": aviso.get("precio_texto") or aviso.get("nota_precio", ""),
        "forma_pago": pago,
        "cumple_contado": contado,
        "estado_rol": _rol(t),
        "agua": agua_txt,
        "agua_ok": agua_ok,
        "luz": luz_txt,
        "luz_ok": luz_ok,
        "fecha_publicacion": aviso.get("fecha", "dato faltante"),
        "fuente": aviso.get("fuente", ""),
        "url": aviso.get("url", ""),
        "titulo": aviso.get("titulo", ""),
        "id": aviso.get("id", ""),
        "_error": None,
        "_motor": "reglas",
    }

    if zona is None:
        datos.update({
            "veredicto": "No cumple",
            "puntaje": 1,
            "justificacion_puntaje": aviso.get("explicacion_zona") or
                "No se pudo confirmar que este en una de las dos zonas objetivo.",
            "riesgos": [],
            "datos_faltantes": [],
            "comparacion_zona": "No aplica: fuera de las zonas objetivo.",
        })
        return prioridad.calcular(datos)

    # Prioridad primero: la justificacion se apoya en ella
    prioridad.calcular(datos)
    pr = datos["prioridad"]

    datos["riesgos"] = _riesgos(t, aviso, precio, zona, mediana, datos)
    datos["datos_faltantes"] = _preguntas(datos)
    datos["justificacion_puntaje"] = _justificar(datos, pr, zona, mediana)

    # Veredicto y puntaje 1-5 derivados del indice, para mantener compatibilidad.
    # "Cumple" a secas exige ademas venta al contado: es criterio del proyecto y no
    # entra en el indice, pero no corresponde dar el visto bueno pleno sin eso.
    idx = pr["indice"]
    if pr["cumple_tres"] and idx >= 75 and datos["cumple_contado"] is True:
        datos["veredicto"], datos["puntaje"] = "Cumple", 5
    elif pr["cumple_tres"] and idx >= 75:
        datos["veredicto"], datos["puntaje"] = "Cumple con reservas", 4
    elif pr["cumple_tres"]:
        datos["veredicto"], datos["puntaje"] = "Cumple con reservas", 4
    elif idx >= 55:
        datos["veredicto"], datos["puntaje"] = "Cumple con reservas", 3
    elif idx >= 35:
        datos["veredicto"], datos["puntaje"] = "Cumple con reservas", 2
    else:
        datos["veredicto"], datos["puntaje"] = "No cumple", 1

    if mediana:
        datos["comparacion_zona"] = (
            f"Mediana de {zona}: ${mediana:,.0f} sobre {len(previos)} aviso(s) con precio."
        ).replace(",", ".")
    else:
        datos["comparacion_zona"] = f"Primer aviso con precio registrado en {zona}."

    return datos
