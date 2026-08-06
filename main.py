"""
Parcelas Radar - corrida diaria.

Flujo:
  1. Recolecta avisos de portales publicos + los reenviados por correo.
  2. Prefiltra por zona y precio (barato, sin API).
  3. Evalua con Claude solo lo que paso el prefiltro.
  4. Guarda el historico y publica la web.
  5. Envia el informe por correo.

Uso:
  python main.py                 corrida real completa
  python main.py --dry-run       recolecta y evalua, pero NO envia correo
  python main.py --sin-api       usa fichas simuladas, no llama a la API (para probar el formato)
  python main.py --demo          carga los avisos de ejemplo de fixtures.py
"""

import argparse
import logging
import os
import sys
from datetime import datetime

import almacen
import config
import correo
import filtro
import fuentes
import motor
import prioridad
import revisados_manual
from motor import evaluar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

URL_WEB = os.environ.get("URL_WEB", "https://TU-USUARIO.github.io/parcelas-radar/")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="no envia el correo")
    p.add_argument("--sin-api", action="store_true",
                   help="atajo para --motor reglas (ya es el valor por defecto)")
    p.add_argument("--demo", action="store_true", help="usa avisos de ejemplo")
    p.add_argument("--motor", help="reglas | gemini | anthropic (por defecto: config.py)")
    args = p.parse_args()

    if args.motor:
        motor.MOTOR = args.motor.lower()

    inicio = datetime.now()
    errores: list[str] = []
    log.info("Motor de evaluacion: %s", motor._elegido())

    # Diagnostico: que credenciales llegaron. Nunca se imprime el valor, solo si
    # esta o no. Ahorra tener que leer todo el log cuando algo falla.
    for nombre in ("GMAIL_USER", "GMAIL_APP_PASSWORD"):
        log.info("  %s: %s", nombre,
                 "configurado" if os.environ.get(nombre) else "FALTA")

    # --- 1. Valor de la UF ---------------------------------------------------
    uf, uf_real = fuentes.valor_uf()
    if not uf_real:
        errores.append("No se pudo consultar el valor real de la UF (mindicador.cl).")

    # --- 2. Recoleccion ------------------------------------------------------
    if args.demo:
        import fixtures
        crudos = fixtures.AVISOS_EJEMPLO
        log.info("Modo demo: %d avisos de ejemplo", len(crudos))
    else:
        crudos, errs = fuentes.recolectar(config.BUSQUEDAS)
        errores += errs

        # Ingesta por correo (Instagram / Facebook Marketplace / reenvios del papa)
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_pass = os.environ.get("GMAIL_APP_PASSWORD")
        if gmail_user and gmail_pass:
            del_correo, probs_correo = fuentes.buscar_correo(
                usuario=gmail_user,
                password=gmail_pass,
                destino=config.CORREO_INGESTA,
                carpeta=config.IMAP_CARPETA_INGESTA,
                dias=config.DIAS_INGESTA_CORREO,
            )
            crudos += del_correo
            errores += probs_correo
        else:
            errores.append(
                "Faltan las credenciales de Gmail: no se pudieron leer los avisos "
                "reenviados por correo."
            )
            log.info("Sin credenciales de correo: se omite la ingesta por reenvio.")

    log.info("Recolectados %d avisos en bruto", len(crudos))

    # --- 3. Prefiltro --------------------------------------------------------
    datos = almacen.cargar()
    conocidos = almacen.ids_conocidos(datos)

    candidatos = []
    pendientes = []   # llegaron por correo pero sin texto: no se pueden evaluar todavia
    descartados = []  # reenviados por el papa que si se leyeron y quedaron fuera de zona

    for a in crudos:
        if a["id"] in conocidos:
            continue

        # Los avisos que llegan por correo suelen traer solo el link. Antes de
        # filtrarlos se intenta completarlos por dos vias, en este orden:
        #   1. el catalogo de contenido ya leido (revisados_manual.py)
        #   2. el sitio propio del proyecto, si el link no es de Meta
        if "correo" in str(a.get("fuente", "")).lower():
            revisados_manual.aplicar(a)
            if not a.get("contenido_leido"):
                extra = fuentes.detalle_url(a.get("url", ""))
                if extra:
                    a["descripcion"] = (str(a.get("descripcion", "")) + " | " + extra)[:8000]
                    a["contenido_leido"] = True

        a = filtro.prefiltrar(a, uf)
        if a["pasa_prefiltro"]:
            candidatos.append(a)
        elif a.get("sin_contenido"):
            pendientes.append(a)
        elif "correo" in str(a.get("fuente", "")).lower():
            # Lo que reenvia el papa se le responde siempre, aunque sea que no.
            # Los descartes de los portales no: son cientos y no le interesan.
            descartados.append(a)

    log.info(
        "%d avisos nuevos pasaron el prefiltro, %d quedaron pendientes de leer "
        "(de %d sin ver antes)",
        len(candidatos),
        len(pendientes),
        len([a for a in crudos if a["id"] not in conocidos]),
    )

    if len(candidatos) > config.MAX_EVALUACIONES_POR_CORRIDA:
        log.warning(
            "Limitando a %d evaluaciones (habia %d) para controlar el costo",
            config.MAX_EVALUACIONES_POR_CORRIDA, len(candidatos),
        )
        candidatos = candidatos[: config.MAX_EVALUACIONES_POR_CORRIDA]

    # --- 4. Enriquecer con el detalle del aviso ------------------------------
    for a in candidatos:
        if a.get("fuente") == "Portalinmobiliario" and a.get("url"):
            detalle = fuentes.detalle_portalinmobiliario(a["url"])
            if detalle:
                a["descripcion"] = (a.get("descripcion", "") + " | " + detalle)[:8000]
        # Si el catalogo apunta al sitio propio del proyecto, se lee tambien:
        # ahi suele estar la superficie y el detalle del agua que el post omite.
        elif a.get("url_proyecto"):
            detalle = fuentes.detalle_url(a["url_proyecto"])
            if detalle:
                a["descripcion"] = (a.get("descripcion", "") + " | " + detalle)[:8000]

    # --- 5. Evaluacion -------------------------------------------------------
    fichas = []
    for i, a in enumerate(candidatos, 1):
        log.info("Evaluando %d/%d: %s", i, len(candidatos), a.get("titulo", "")[:70])
        ficha = evaluar(a, datos["avisos"], uf)
        if ficha.get("_error"):
            errores.append(f"Evaluacion fallida ({a.get('url','?')[:50]}): {ficha['_error']}")
        fichas.append(ficha)

    # --- 6. Prioridad y guardado ---------------------------------------------
    # El orden lo manda precio/rol/agua; la localidad solo desempata.
    for f in fichas:
        prioridad.calcular(f)

    nuevas = almacen.agregar(datos, fichas)
    for f in datos["avisos"]:
        if "prioridad" not in f:
            prioridad.calcular(f)
    datos["avisos"].sort(key=prioridad.clave_orden)
    resumen = {
        "fecha": inicio.isoformat(timespec="seconds"),
        "revisados": len(crudos),
        "nuevos": len(nuevas),
        "evaluados": len(fichas),
        "fuentes": len({b["fuente"] for b in config.BUSQUEDAS}) + 1,
        "pendientes": len(pendientes),
        "errores": errores,
        "uf_valor": uf,
        "uf_estimada": not uf_real,
        "duracion_s": round((datetime.now() - inicio).total_seconds(), 1),
    }
    almacen.registrar_corrida(datos, resumen)
    almacen.guardar(datos)
    log.info("Historico guardado: %d avisos en total", len(datos["avisos"]))

    # --- 7. Correo -----------------------------------------------------------
    html = correo.construir_html(nuevas, resumen, URL_WEB,
                                 pendientes=pendientes, descartados=descartados)
    salida = os.path.join(os.path.dirname(__file__), "ultimo_informe.html")
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    log.info("Vista previa del correo guardada en %s", salida)

    if args.dry_run:
        log.info("--dry-run: no se envia el correo.")
        return 0

    n = len(nuevas)
    mejores = [f for f in nuevas if (f.get("prioridad") or {}).get("cumple_tres")]
    if mejores:
        asunto = f"{config.ASUNTO_BASE}: {len(mejores)} con precio, rol y agua - {inicio:%d/%m}"
    elif n:
        asunto = f"{config.ASUNTO_BASE}: {n} aviso{'s' if n != 1 else ''} nuevo{'s' if n != 1 else ''} - {inicio:%d/%m}"
    elif pendientes:
        p = len(pendientes)
        asunto = (f"{config.ASUNTO_BASE}: {p} enlace{'s' if p != 1 else ''} "
                  f"por leer - {inicio:%d/%m}")
    else:
        asunto = f"{config.ASUNTO_BASE}: sin novedades - {inicio:%d/%m}"

    try:
        correo.enviar(html, asunto)
        log.info("Correo enviado a %s", ", ".join(config.DESTINATARIOS))
    except Exception as e:  # noqa: BLE001
        log.error("No se pudo enviar el correo: %s", e)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
