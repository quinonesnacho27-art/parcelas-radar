"""
Fuentes de avisos.

Cada fuente expone una funcion buscar(query) -> list[dict] con el formato comun:
    {id, fuente, url, titulo, descripcion, precio_texto, ubicacion, fecha}

Principio de diseno: si una fuente se cae o cambia su HTML, se registra el error
y la corrida continua con las demas. Nunca se pierde el informe diario completo
por culpa de un solo portal.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("fuentes")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9",
}

TIMEOUT = 25


def _id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _limpiar(texto: str | None) -> str:
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto).strip()


def _get(url: str, params: dict | None = None) -> requests.Response | None:
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            log.warning("%s devolvio HTTP %s", url, r.status_code)
            return None
        return r
    except requests.RequestException as e:
        log.warning("Error de red en %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Valor de la UF (para convertir avisos publicados en UF)
# ---------------------------------------------------------------------------

def valor_uf() -> tuple[float, bool]:
    """Devuelve (valor, es_real). es_real=False significa que se uso el respaldo."""
    from config import UF_FALLBACK

    r = _get("https://mindicador.cl/api/uf")
    if r:
        try:
            serie = r.json().get("serie", [])
            if serie:
                return float(serie[0]["valor"]), True
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudo leer mindicador.cl: %s", e)
    log.warning("Usando valor UF de respaldo: %s", UF_FALLBACK)
    return float(UF_FALLBACK), False


# ---------------------------------------------------------------------------
# Portalinmobiliario / MercadoLibre Chile
# ---------------------------------------------------------------------------

def buscar_portalinmobiliario(query: str, max_resultados: int = 30) -> list[dict]:
    """
    Portalinmobiliario corre sobre la infraestructura de MercadoLibre.
    Se raspa la pagina de resultados publica.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    url = f"https://www.portalinmobiliario.com/venta/parcela/{slug}"
    r = _get(url)
    if r is None:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    avisos: list[dict] = []

    # Los resultados vienen como <li class="ui-search-layout__item">
    items = soup.select("li.ui-search-layout__item") or soup.select("div.ui-search-result__wrapper")
    for item in items[:max_resultados]:
        enlace = item.select_one("a.ui-search-link, a.poly-component__title, h2 a, a[href*='MLC']")
        if not enlace or not enlace.get("href"):
            continue
        href = enlace["href"].split("#")[0]

        titulo = _limpiar(
            enlace.get_text() or (item.select_one("h2").get_text() if item.select_one("h2") else "")
        )
        precio_el = item.select_one(
            ".andes-money-amount, .price-tag-fraction, .poly-price__current"
        )
        precio_texto = _limpiar(precio_el.get_text(" ") if precio_el else "")
        ubic_el = item.select_one(
            ".ui-search-item__location, .poly-component__location, .ui-search-item__group__element--location"
        )
        ubicacion = _limpiar(ubic_el.get_text() if ubic_el else "")
        attrs_el = item.select_one(".poly-attributes-list, .ui-search-card-attributes")
        descripcion = _limpiar(attrs_el.get_text(" | ") if attrs_el else "")

        avisos.append({
            "id": _id(href),
            "fuente": "Portalinmobiliario",
            "url": href,
            "titulo": titulo,
            "descripcion": f"{descripcion} {titulo}".strip(),
            "precio_texto": precio_texto,
            "ubicacion": ubicacion,
            "fecha": date.today().isoformat(),
        })

    log.info("Portalinmobiliario '%s': %d avisos", query, len(avisos))
    return avisos


def detalle_portalinmobiliario(url: str) -> str:
    """Baja la descripcion completa de un aviso. Vale la pena solo para los que pasan el prefiltro."""
    r = _get(url)
    if r is None:
        return ""
    soup = BeautifulSoup(r.text, "lxml")
    partes = []
    desc = soup.select_one(".ui-pdp-description__content, [data-testid='content']")
    if desc:
        partes.append(_limpiar(desc.get_text(" ")))
    for fila in soup.select(".andes-table__row, .ui-pdp-specs__table tr"):
        partes.append(_limpiar(fila.get_text(": ")))
    return " | ".join(p for p in partes if p)[:6000]


# ---------------------------------------------------------------------------
# Yapo.cl
# ---------------------------------------------------------------------------

def buscar_yapo(query: str, max_resultados: int = 30) -> list[dict]:
    r = _get("https://www.yapo.cl/chile/inmuebles", params={"q": query, "ca": "15_s"})
    if r is None:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    avisos: list[dict] = []
    for item in soup.select("a[href*='/inmuebles/']")[: max_resultados * 3]:
        href = item.get("href", "")
        if not href or "/inmuebles/" not in href:
            continue
        if href.startswith("/"):
            href = "https://www.yapo.cl" + href
        titulo = _limpiar(item.get_text(" "))
        if len(titulo) < 15:
            continue
        avisos.append({
            "id": _id(href),
            "fuente": "Yapo",
            "url": href,
            "titulo": titulo[:200],
            "descripcion": titulo,
            "precio_texto": "",
            "ubicacion": "",
            "fecha": date.today().isoformat(),
        })
        if len(avisos) >= max_resultados:
            break

    log.info("Yapo '%s': %d avisos", query, len(avisos))
    return avisos


# ---------------------------------------------------------------------------
# Ingesta por correo: Instagram, Facebook Marketplace y reenvios del papa
# ---------------------------------------------------------------------------

def buscar_correo(carpeta: str, usuario: str, password: str, dias: int = 3) -> list[dict]:
    """
    Lee los correos reenviados a una etiqueta de Gmail y los convierte en avisos.

    Esta es la via oficial para Instagram y Facebook Marketplace: Meta no ofrece
    API publica de avisos y el scraping viola sus terminos, asi que el aviso entra
    por reenvio humano y el sistema lo evalua igual que cualquier otro.
    """
    import email
    import imaplib
    from email.header import decode_header, make_header

    avisos: list[dict] = []
    try:
        M = imaplib.IMAP4_SSL("imap.gmail.com")
        M.login(usuario, password)
        estado, _ = M.select(f'"{carpeta}"', readonly=True)
        if estado != "OK":
            log.warning("No existe la carpeta/etiqueta IMAP '%s'", carpeta)
            M.logout()
            return []

        desde = (datetime.now().date().toordinal() - dias)
        fecha_imap = date.fromordinal(desde).strftime("%d-%b-%Y")
        estado, datos = M.search(None, f'(SINCE "{fecha_imap}")')
        ids = datos[0].split() if estado == "OK" else []

        for num in ids[-50:]:
            estado, datos = M.fetch(num, "(RFC822)")
            if estado != "OK":
                continue
            msg = email.message_from_bytes(datos[0][1])
            asunto = str(make_header(decode_header(msg.get("Subject", ""))))
            remitente = str(make_header(decode_header(msg.get("From", ""))))
            fecha = msg.get("Date", "")

            cuerpo = ""
            if msg.is_multipart():
                for parte in msg.walk():
                    if parte.get_content_type() == "text/plain":
                        try:
                            cuerpo += parte.get_payload(decode=True).decode(
                                parte.get_content_charset() or "utf-8", "replace"
                            )
                        except Exception:  # noqa: BLE001
                            pass
            else:
                try:
                    cuerpo = msg.get_payload(decode=True).decode(
                        msg.get_content_charset() or "utf-8", "replace"
                    )
                except Exception:  # noqa: BLE001
                    cuerpo = str(msg.get_payload())

            urls = re.findall(r"https?://[^\s<>\"')]+", cuerpo)
            url_principal = next(
                (u for u in urls if any(d in u for d in
                 ("instagram.com", "facebook.com", "portalinmobiliario", "yapo.cl", "mercadolibre"))),
                urls[0] if urls else "",
            )
            origen = "Instagram" if "instagram.com" in url_principal else (
                "Facebook Marketplace" if "facebook.com" in url_principal else "Reenvio por correo"
            )

            avisos.append({
                "id": _id(url_principal or (asunto + fecha)),
                "fuente": origen,
                "url": url_principal,
                "titulo": _limpiar(asunto)[:200],
                "descripcion": _limpiar(cuerpo)[:6000],
                "precio_texto": "",
                "ubicacion": "",
                "fecha": fecha[:31],
                "remitente": remitente,
            })

        M.close()
        M.logout()
    except Exception as e:  # noqa: BLE001
        log.warning("Ingesta por correo fallo: %s: %s", type(e).__name__, e)

    log.info("Correo '%s': %d avisos", carpeta, len(avisos))
    return avisos


# ---------------------------------------------------------------------------
# Despachador
# ---------------------------------------------------------------------------

BUSCADORES = {
    "portalinmobiliario": buscar_portalinmobiliario,
    "yapo": buscar_yapo,
}


def recolectar(busquedas: list[dict], pausa: float = 1.5) -> tuple[list[dict], list[str]]:
    """Corre todas las busquedas configuradas. Devuelve (avisos, errores)."""
    todos: list[dict] = []
    vistos: set[str] = set()
    errores: list[str] = []

    for b in busquedas:
        fn = BUSCADORES.get(b["fuente"])
        if fn is None:
            errores.append(f"Fuente desconocida: {b['fuente']}")
            continue
        try:
            for aviso in fn(b["query"]):
                if aviso["id"] not in vistos:
                    vistos.add(aviso["id"])
                    aviso["query_origen"] = b["query"]
                    todos.append(aviso)
        except Exception as e:  # noqa: BLE001
            errores.append(f"{b['fuente']} / '{b['query']}': {type(e).__name__}: {e}")
        time.sleep(pausa)

    return todos, errores
