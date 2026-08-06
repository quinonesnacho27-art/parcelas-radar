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


def _sin_tildes(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower().strip()


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

def buscar_portalinmobiliario(lugar: str, esperado: str = "",
                              tope_precio: int | None = None,
                              max_resultados: int = 40) -> list[dict]:
    """
    Portalinmobiliario corre sobre la infraestructura de MercadoLibre.

    'lugar' es el slug de ubicacion del sitio ("ancud-los-lagos") o una busqueda
    de texto ("_q_san-fabian-nuble"). 'esperado' es el nombre de la comuna, que se
    usa para comprobar que la pagina devuelta sea la correcta.

    Esa comprobacion no es opcional: si el slug no existe, el sitio NO devuelve un
    404 sino un HTTP 200 con el listado nacional completo de parcelas. Sin este
    chequeo el sistema se llena de avisos de todo Chile, que es exactamente lo que
    pasaba antes.
    """
    # A proposito NO se usa el filtro _PriceRange_ de la URL: rompe las busquedas
    # de texto "_q_" (devuelve el listado nacional) y da 404 cuando una comuna no
    # tiene resultados bajo el tope. El filtro de precio de filtro.py hace lo mismo
    # de forma mas confiable, ya con el valor de la UF resuelto.
    url = f"https://www.portalinmobiliario.com/venta/parcela/{lugar}"
    r = _get(url)
    if r is None:
        return []

    soup = BeautifulSoup(r.text, "lxml")

    # El <h1> es la fuente preferida, pero el sitio empezo a servir paginas sin
    # <h1> a los clientes que no son navegador (6 de agosto de 2026: las 14
    # busquedas devolvieron "(sin titulo)" desde GitHub Actions, mientras la
    # misma URL abierta a mano mostraba 97 resultados). El <title> viene en el
    # HTML crudo con la misma informacion, asi que sirve de respaldo.
    titulo = _limpiar(soup.h1.get_text() if soup.h1 else "")
    if not titulo:
        titulo = _limpiar(soup.title.get_text() if soup.title else "")

    if esperado:
        if not titulo:
            # Ni h1 ni title: no es que el slug este malo, es que no llego la
            # pagina. Decirlo distinto importa, porque el arreglo es otro.
            log.warning(
                "Portalinmobiliario devolvio una pagina sin titulo para '%s'. "
                "Probablemente esta bloqueando al robot o la pagina se arma con "
                "JavaScript; el slug no es el problema.", lugar,
            )
            return []
        if _sin_tildes(esperado) not in _sin_tildes(titulo):
            log.warning(
                "Portalinmobiliario devolvio '%s' para '%s': no corresponde a la comuna "
                "pedida, se descartan los resultados. Revisa el slug en config.BUSQUEDAS.",
                titulo, lugar,
            )
            return []

    avisos: list[dict] = []

    # Los resultados vienen como <li class="ui-search-layout__item">
    items = soup.select("li.ui-search-layout__item") or soup.select("div.ui-search-result__wrapper")
    for item in items[:max_resultados]:
        enlace = item.select_one("a.ui-search-link, a.poly-component__title, h2 a, a[href*='MLC']")
        if not enlace or not enlace.get("href"):
            continue
        href = enlace["href"].split("#")[0]

        titulo_item = _limpiar(
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
            "titulo": titulo_item,
            "descripcion": f"{descripcion} {titulo_item} {ubicacion}".strip(),
            "precio_texto": precio_texto,
            "ubicacion": ubicacion or esperado,
            "fecha": date.today().isoformat(),
        })

    log.info("Portalinmobiliario %s (%s): %d avisos", lugar, titulo, len(avisos))
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
# Sitio propio del proyecto
# ---------------------------------------------------------------------------

# Dominios de Meta: no se leen nunca. No es una limitacion tecnica sino una
# decision del proyecto (ver README). Si alguna vez se agrega otro dominio que
# tampoco se deba tocar, va aqui y el resto del codigo no cambia.
_DOMINIOS_VETADOS = (
    "instagram.com", "facebook.com", "fb.watch", "fb.me", "messenger.com",
    "threads.net", "whatsapp.com", "wa.me",
)


def _vetado(url: str) -> bool:
    u = (url or "").lower()
    return any(d in u for d in _DOMINIOS_VETADOS)


def detalle_url(url: str) -> str:
    """
    Baja el texto de la pagina de un proyecto para completar la ficha.

    Muchos avisos de Instagram llevan a un sitio propio (choroihue.cl,
    aguasdelquetro.cl) que publica precio, comuna, superficie y rol de forma
    perfectamente legible. Ese sitio SI se puede leer: es una pagina publica
    de venta, hecha para que la lean.

    Devuelve "" para dominios vetados y para paginas que no dan texto util
    (las hechas con JavaScript devuelven un cascaron vacio).
    """
    if not url or _vetado(url):
        return ""

    r = _get(url)
    if r is None:
        return ""

    soup = BeautifulSoup(r.text, "lxml")
    for basura in soup(["script", "style", "noscript", "svg", "iframe"]):
        basura.decompose()

    partes = []
    # La meta description suele traer el resumen comercial completo y limpio.
    for sel, attr in (('meta[name="description"]', "content"),
                      ('meta[property="og:description"]', "content"),
                      ('meta[property="og:title"]', "content")):
        tag = soup.select_one(sel)
        if tag and tag.get(attr):
            partes.append(_limpiar(tag[attr]))

    cuerpo = soup.select_one("main") or soup.body
    if cuerpo:
        partes.append(_limpiar(cuerpo.get_text(" ")))

    texto = " | ".join(dict.fromkeys(p for p in partes if p))
    # Menos de 200 caracteres = pagina renderizada con JavaScript, no hay nada.
    return texto[:6000] if len(texto) >= 200 else ""


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

def _cuerpo_texto(msg) -> str:
    """Saca el texto del correo. Prefiere text/plain; si solo hay HTML, lo desarma."""
    plano, html = "", ""
    if msg.is_multipart():
        for parte in msg.walk():
            if parte.get_content_disposition() == "attachment":
                continue
            tipo = parte.get_content_type()
            if tipo not in ("text/plain", "text/html"):
                continue
            try:
                trozo = parte.get_payload(decode=True).decode(
                    parte.get_content_charset() or "utf-8", "replace")
            except Exception:  # noqa: BLE001
                continue
            if tipo == "text/plain":
                plano += trozo
            else:
                html += trozo
    else:
        try:
            crudo = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", "replace")
        except Exception:  # noqa: BLE001
            crudo = str(msg.get_payload())
        (plano := crudo) if msg.get_content_type() == "text/plain" else (html := crudo)

    if plano.strip():
        return plano
    if html.strip():
        # Los links quedan visibles antes de borrar las etiquetas, para no perderlos
        html = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>', r" \1 ", html, flags=re.I)
        return BeautifulSoup(html, "lxml").get_text(" ")
    return ""


_DOMINIOS_AVISO = ("instagram.com", "facebook.com", "fb.watch", "portalinmobiliario",
                   "yapo.cl", "mercadolibre", "toctoc", "parcela", "terreno")


_RE_BUZON = re.compile(r'^\((?P<flags>[^)]*)\)\s+"[^"]*"\s+(?P<nombre>.+)$')


def _buzones_a_revisar(M, carpeta_pista: str | None) -> tuple[list[str], list[str]]:
    """
    Decide en que buzones IMAP buscar, preguntandole al servidor.

    POR QUE NO SE PUEDE USAR "[Gmail]/All Mail" A SECAS
    ---------------------------------------------------
    Gmail traduce el nombre de sus carpetas especiales al idioma de la cuenta.
    En una cuenta en espanol "All Mail" se llama "[Gmail]/Todos", asi que el
    SELECT fallaba, el codigo hacia `continue`, y la busqueda terminaba sin
    revisar nada. Sumado a que los correos del papa los archiva un filtro (no
    quedan en INBOX) y a que la etiqueta se llama "Parcelas" y no
    "ParcelasRadar", los tres buzones que se probaban estaban vacios o no
    existian. Resultado: 0 avisos, todos los dias, sin un solo error en el log.

    La solucion es no adivinar nombres: se listan los buzones y se elige el que
    trae el atributo \\All, que es igual en todos los idiomas. Ademas se
    reconoce cualquier etiqueta que mencione "parcela", asi da lo mismo como la
    haya bautizado el usuario.

    Devuelve (buzones_en_orden, diagnostico).
    """
    diagnostico: list[str] = []
    todas: list[tuple[str, str]] = []

    try:
        estado, lineas = M.list()
    except Exception as e:  # noqa: BLE001
        estado, lineas = "NO", []
        diagnostico.append(f"No se pudo listar los buzones IMAP: {type(e).__name__}: {e}")

    if estado == "OK":
        for linea in lineas or []:
            s = linea.decode("utf-8", "replace") if isinstance(linea, bytes) else str(linea)
            m = _RE_BUZON.match(s.strip())
            if m:
                todas.append((m.group("nombre").strip().strip('"'), m.group("flags")))

    buzones: list[str] = []

    # 1) La carpeta "todos los mensajes", identificada por atributo, no por nombre.
    for nombre, flags in todas:
        if "\\All" in flags and nombre not in buzones:
            buzones.append(nombre)
    if not buzones:
        diagnostico.append(
            "El servidor no expuso la carpeta \\All (todos los mensajes). "
            "Se buscara solo en INBOX y en las etiquetas reconocidas."
        )

    # 2) Cualquier etiqueta que hable de parcelas, se llame como se llame.
    for nombre, _ in todas:
        if "parcela" in _sin_tildes(nombre) and nombre not in buzones:
            buzones.append(nombre)

    # 3) La etiqueta configurada, si de verdad existe.
    if carpeta_pista and carpeta_pista not in buzones:
        if any(n == carpeta_pista for n, _ in todas):
            buzones.append(carpeta_pista)
        elif todas:
            diagnostico.append(
                f"La etiqueta '{carpeta_pista}' de config.IMAP_CARPETA_INGESTA no "
                f"existe en la cuenta. Se ignora."
            )

    # 4) INBOX al final: es donde caen los correos que ningun filtro archiva.
    if "INBOX" not in buzones:
        buzones.append("INBOX")

    return buzones, diagnostico


def buscar_correo(usuario: str, password: str, destino: str,
                  carpeta: str | None = None,
                  dias: int = 3) -> tuple[list[dict], list[str]]:
    """
    Lee los avisos que llegan por correo y los convierte en fichas evaluables.

    Esta es la via para Instagram y Facebook Marketplace: Meta no ofrece API
    publica de avisos y el scraping viola sus terminos, asi que el aviso entra
    por reenvio humano y de ahi en adelante se evalua igual que cualquier otro.

    Devuelve (avisos, problemas). 'problemas' viaja hasta el recuadro amarillo
    del informe: esta parte fallo tres dias seguidos sin que se notara porque
    solo escribia un log que nadie lee.
    """
    import email
    import imaplib
    from email.header import decode_header, make_header
    from email.utils import parseaddr

    avisos: list[dict] = []
    vistos: set[str] = set()
    problemas: list[str] = []

    try:
        M = imaplib.IMAP4_SSL("imap.gmail.com")
        M.login(usuario, password)

        desde = date.fromordinal(datetime.now().date().toordinal() - dias)
        fecha_imap = desde.strftime("%d-%b-%Y")

        buzones, diag = _buzones_a_revisar(M, carpeta)
        problemas += diag
        log.info("Buzones a revisar: %s", ", ".join(buzones))

        # Dos formas de preguntar lo mismo. X-GM-RAW es la busqueda propia de
        # Gmail y entiende "deliveredto:", que resuelve bien el alias con "+";
        # el TO de IMAP estandar a veces no lo hace. Si la primera no devuelve
        # nada se prueba la segunda antes de dar el buzon por vacio.
        criterios = [
            ("X-GM-RAW", f'"deliveredto:{destino} newer_than:{dias}d"'),
            ("TO", f'(SINCE "{fecha_imap}" TO "{destino}")'),
        ]

        encontrados_totales = 0

        for buzon in buzones:
            try:
                estado, _ = M.select(f'"{buzon}"', readonly=True)
            except Exception as e:  # noqa: BLE001
                problemas.append(f"No se pudo abrir el buzon '{buzon}': {type(e).__name__}")
                continue
            if estado != "OK":
                continue

            nums: list[bytes] = []
            for modo, criterio in criterios:
                try:
                    if modo == "X-GM-RAW":
                        estado, datos = M.search(None, "X-GM-RAW", criterio)
                    else:
                        estado, datos = M.search(None, criterio)
                except Exception:  # noqa: BLE001
                    continue
                if estado == "OK" and datos and datos[0]:
                    nums = datos[0].split()
                    log.info("  %s [%s]: %d mensajes", buzon, modo, len(nums))
                    break

            for num in nums[-60:]:
                estado, bruto = M.fetch(num, "(RFC822)")
                if estado != "OK" or not bruto or not bruto[0]:
                    continue
                msg = email.message_from_bytes(bruto[0][1])

                mid = msg.get("Message-ID", "") or str(num)
                if mid in vistos:
                    continue
                vistos.add(mid)

                asunto = str(make_header(decode_header(msg.get("Subject", ""))))
                remitente = parseaddr(str(make_header(decode_header(msg.get("From", "")))))[1]
                fecha = msg.get("Date", "")
                cuerpo = _cuerpo_texto(msg)

                urls = re.findall(r"https?://[^\s<>\"')\]]+", cuerpo)
                url = next((u for u in urls if any(d in u.lower() for d in _DOMINIOS_AVISO)),
                           urls[0] if urls else "")

                # Sin link y sin texto util no hay nada que evaluar
                if not url and len(_limpiar(cuerpo)) < 40:
                    continue

                u = url.lower()
                origen = ("Instagram" if "instagram.com" in u else
                          "Facebook Marketplace" if ("facebook.com" in u or "fb.watch" in u) else
                          "Portalinmobiliario" if "portalinmobiliario" in u else
                          "Yapo" if "yapo.cl" in u else
                          "Reenvio por correo")

                texto = _limpiar(f"{asunto} {cuerpo}")
                avisos.append({
                    "id": _id(url or (asunto + fecha)),
                    "fuente": f"{origen} (enviado por correo)",
                    "url": url,
                    "titulo": _limpiar(asunto)[:200] or texto[:120],
                    "descripcion": texto[:6000],
                    "precio_texto": "",
                    "ubicacion": "",
                    "fecha": fecha[:31] or date.today().isoformat(),
                    "remitente": remitente,
                })
                encontrados_totales += 1
            M.close()

        M.logout()

        if encontrados_totales == 0:
            problemas.append(
                f"No se encontro ningun correo dirigido a {destino} en los ultimos "
                f"{dias} dias. Se revisaron estos buzones: {', '.join(buzones)}."
            )
    except Exception as e:  # noqa: BLE001
        log.warning("Ingesta por correo fallo: %s: %s", type(e).__name__, e)
        problemas.append(
            f"La lectura de la casilla {destino} fallo: {type(e).__name__}: {e}"
        )

    log.info("Correo (%s): %d avisos", destino, len(avisos))
    return avisos, problemas


# ---------------------------------------------------------------------------
# Despachador
# ---------------------------------------------------------------------------

def recolectar(busquedas: list[dict], pausa: float = 1.5) -> tuple[list[dict], list[str]]:
    """Corre todas las busquedas configuradas. Devuelve (avisos, errores)."""
    todos: list[dict] = []
    vistos: set[str] = set()
    errores: list[str] = []
    sin_resultado: list[str] = []

    for b in busquedas:
        origen = b.get("lugar") or b.get("query", "?")
        try:
            if b["fuente"] == "portalinmobiliario":
                encontrados = buscar_portalinmobiliario(b["lugar"], b.get("comuna", ""))
            elif b["fuente"] == "yapo":
                encontrados = buscar_yapo(b.get("query", ""))
            else:
                errores.append(f"Fuente desconocida: {b['fuente']}")
                continue

            if not encontrados:
                sin_resultado.append(origen)

            for aviso in encontrados:
                if aviso["id"] not in vistos:
                    vistos.add(aviso["id"])
                    aviso["query_origen"] = origen
                    aviso["zona_hint"] = b.get("zona_hint")
                    todos.append(aviso)
        except Exception as e:  # noqa: BLE001
            errores.append(f"{b['fuente']} / '{origen}': {type(e).__name__}: {e}")
        time.sleep(pausa)

    # Si TODAS las busquedas de un portal vuelven vacias, el portal cambio algo.
    # Conviene que quede anotado en el informe y no pasar de largo.
    portales = [b for b in busquedas if b["fuente"] == "portalinmobiliario"]
    if portales and len(sin_resultado) >= len(portales):
        errores.append(
            "Ninguna busqueda de Portalinmobiliario devolvio resultados. Si en el log "
            "aparece 'pagina sin titulo', el sitio esta bloqueando al robot y no hay "
            "nada que arreglar en los slugs: hay que esperar o cambiar de fuente. "
            "Los avisos que llegan por correo no dependen de esto y siguen entrando."
        )

    return todos, errores
