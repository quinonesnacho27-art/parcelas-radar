"""
Prefiltro barato: decide si un aviso merece gastar tokens de la API.

La logica aqui es deliberadamente conservadora: ante la duda DEJA PASAR el aviso
al evaluador (Claude), porque un falso negativo aqui es una oportunidad perdida
y un falso positivo solo cuesta unos centavos.
"""

import re
import unicodedata

from config import (
    PRECIO_TOLERABLE_MAX,
    UF_FALLBACK,
    ZONAS,
    ZONAS_TRAMPA,
)


def normalizar(texto: str) -> str:
    """Minusculas, sin tildes, espacios colapsados."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    return re.sub(r"\s+", " ", texto).strip()


# ---------------------------------------------------------------------------
# Precio
# ---------------------------------------------------------------------------

_RE_UF = re.compile(r"(?:uf|u\.f\.)\s*\.?\s*([\d.,]+)|([\d.,]+)\s*(?:uf|u\.f\.)", re.I)
_RE_CLP = re.compile(r"\$\s*([\d.]{4,})")
_RE_MILLONES = re.compile(r"([\d.,]+)\s*millones", re.I)


def _a_numero(s: str) -> float | None:
    """Convierte '13.000.000' o '1.600' o '13,5' a float, formato chileno."""
    if not s:
        return None
    s = s.strip()
    # Si tiene coma y punto, el punto es separador de miles
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # coma decimal chilena
        s = s.replace(",", ".")
    elif s.count(".") >= 1:
        partes = s.split(".")
        # '1.600' -> miles ; '13.5' -> decimal. Heuristica: si el ultimo bloque
        # tiene 3 digitos, son miles.
        if all(len(p) == 3 for p in partes[1:]):
            s = s.replace(".", "")
        else:
            s = s.replace(".", "", len(partes) - 2) if len(partes) > 2 else s
    try:
        return float(s)
    except ValueError:
        return None


def extraer_precio_clp(texto: str, uf_valor: float = UF_FALLBACK) -> tuple[int | None, str]:
    """
    Devuelve (precio_en_clp, nota). nota explica de donde salio el numero.
    Devuelve (None, motivo) si no se pudo determinar.
    """
    if not texto:
        return None, "sin texto"

    # 1) UF explicita (frecuente en avisos de Instagram: 'Parcelas desde 1.600 UF')
    m = _RE_UF.search(texto)
    if m:
        crudo = m.group(1) or m.group(2)
        val = _a_numero(crudo)
        if val and 10 <= val < 100_000:
            clp = int(val * uf_valor)
            return clp, f"{val:,.0f} UF x ${uf_valor:,.0f} = ${clp:,.0f} CLP (conversion automatica)"

    # 2) 'X millones'
    m = _RE_MILLONES.search(texto)
    if m:
        val = _a_numero(m.group(1))
        if val and 1 <= val < 1000:
            return int(val * 1_000_000), f"{val} millones interpretado como ${val * 1_000_000:,.0f} CLP"

    # 3) $ pesos. Tomamos el MENOR valor plausible (los avisos suelen decir "desde $X").
    candidatos = []
    for m in _RE_CLP.finditer(texto):
        val = _a_numero(m.group(1))
        if val and 1_000_000 <= val <= 500_000_000:
            candidatos.append(int(val))
    if candidatos:
        unicos = sorted(set(candidatos))
        menor = unicos[0]
        nota = f"${menor:,.0f} CLP"
        if len(unicos) > 1:
            nota += f" (el aviso menciona un rango: ${unicos[0]:,.0f} - ${unicos[-1]:,.0f})"
        return menor, nota

    return None, "el aviso no publica precio de forma legible"


# ---------------------------------------------------------------------------
# Zona
# ---------------------------------------------------------------------------

def detectar_zona(texto: str) -> tuple[str | None, str]:
    """
    Devuelve (nombre_zona, explicacion).
    nombre_zona es None si el aviso no esta claramente en una zona valida.
    """
    t = normalizar(texto)

    # Primero las trampas: lugares del sur que NO califican.
    # Solo descartan si ademas no hay una keyword valida en el texto.
    #
    # Se elige la que aparece ANTES en el texto, no la primera del diccionario.
    # Los avisos listan tiempos de viaje ("a 35 min de Puerto Varas") y con el
    # orden del diccionario un aviso de Los Muermos terminaba explicado como
    # "Puerto Varas": el descarte era correcto pero el motivo mentia.
    encontradas = [(t.index(clave), clave, motivo)
                   for clave, motivo in ZONAS_TRAMPA.items() if clave in t]
    trampa_encontrada = None
    if encontradas:
        _, clave, motivo = min(encontradas)
        trampa_encontrada = (clave, motivo)

    for zona, cfg in ZONAS.items():
        for kw in cfg["keywords"]:
            if kw in t:
                # 'castro' es ambiguo (hay Castro en varias partes); exigimos
                # refuerzo de contexto para las keywords cortas y genericas.
                if kw in ("castro", "pinto", "recinto") and "chiloe" not in t and "nuble" not in t:
                    contexto = any(
                        otra in t for otra in cfg["keywords"] if otra != kw
                    )
                    if not contexto:
                        continue
                return zona, f"coincide con '{kw}' -> {zona}"

    if trampa_encontrada:
        return None, f"FUERA DE ZONA: {trampa_encontrada[1]}"

    return None, "no se pudo identificar la comuna dentro de las dos zonas objetivo"


# ---------------------------------------------------------------------------
# Prefiltro combinado
# ---------------------------------------------------------------------------

def prefiltrar(aviso: dict, uf_valor: float = UF_FALLBACK) -> dict:
    """
    aviso: {'titulo','descripcion','precio_texto','url','fuente','fecha'}
    Devuelve el aviso enriquecido con: zona_detectada, precio_clp, pasa_prefiltro,
    motivo_prefiltro.
    """
    texto = " ".join(
        str(aviso.get(k, "")) for k in ("titulo", "descripcion", "precio_texto", "ubicacion")
    )

    # Un aviso que es solo un link no esta "fuera de zona": es un aviso que
    # todavia no se ha leido. La diferencia importa, porque uno se descarta
    # para siempre y el otro hay que ir a buscarlo. Antes se confundian y por
    # eso los 16 reenvios del 5 de agosto de 2026 desaparecieron sin dejar
    # rastro en el informe.
    sin_urls = re.sub(r"https?://\S+", " ", texto)
    if len(normalizar(sin_urls)) < 40:
        aviso["zona_detectada"] = None
        aviso["explicacion_zona"] = "el aviso llego sin texto: solo el enlace"
        aviso["precio_clp"] = None
        aviso["nota_precio"] = "sin texto"
        aviso["sin_contenido"] = True
        aviso["pasa_prefiltro"] = False
        aviso["motivo_prefiltro"] = (
            "pendiente de leer: el correo trae solo el enlace, sin texto del aviso"
        )
        return aviso

    aviso["sin_contenido"] = False
    zona, explic_zona = detectar_zona(texto)
    precio, nota_precio = extraer_precio_clp(texto, uf_valor)

    aviso["zona_detectada"] = zona
    aviso["explicacion_zona"] = explic_zona
    aviso["precio_clp"] = precio
    aviso["nota_precio"] = nota_precio

    if zona is None:
        aviso["pasa_prefiltro"] = False
        aviso["motivo_prefiltro"] = explic_zona
        return aviso

    # Margen de 20% sobre el techo: dejamos pasar avisos algo caros para que el
    # evaluador decida si son la "excepcion justificada" que permite el criterio.
    if precio is not None and precio > PRECIO_TOLERABLE_MAX * 1.2:
        aviso["pasa_prefiltro"] = False
        aviso["motivo_prefiltro"] = (
            f"precio ${precio:,.0f} CLP supera con holgura el techo de "
            f"${PRECIO_TOLERABLE_MAX:,.0f} CLP"
        )
        return aviso

    aviso["pasa_prefiltro"] = True
    aviso["motivo_prefiltro"] = "zona valida y precio dentro del rango evaluable"
    return aviso
