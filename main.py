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
import prioridad
from evaluador import evaluar

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
    p.add_argument("--sin-api", action="store_true", help="no llama a la API de Claude")
    p.add_argument("--demo", action="store_true", help="usa avisos de ejemplo")
    args = p.parse_args()

    inicio = datetime.now()
    errores: list[str] = []

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

        # Ingesta por correo (Instagram / Facebook Marketplace / reenvios)
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_pass = os.environ.get("GMAIL_APP_PASSWORD")
        if gmail_user and gmail_pass:
            crudos += fuentes.buscar_correo(
                config.IMAP_CARPETA_INGESTA, gmail_user, gmail_pass
            )
        else:
            log.info("Sin credenciales de correo: se omite la ingesta por reenvio.")

    log.info("Recolectados %d avisos en bruto", len(crudos))

    # --- 3. Prefiltro --------------------------------------------------------
    datos = almacen.cargar()
    conocidos = almacen.ids_conocidos(datos)

    candidatos = []
    for a in crudos:
        if a["id"] in conocidos:
            continue
        a = filtro.prefiltrar(a, uf)
        if a["pasa_prefiltro"]:
            candidatos.append(a)

    log.info(
        "%d avisos nuevos pasaron el prefiltro (de %d sin ver antes)",
        len(candidatos),
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

    # --- 5. Evaluacion -------------------------------------------------------
    fichas = []
    for i, a in enumerate(candidatos, 1):
        log.info("Evaluando %d/%d: %s", i, len(candidatos), a.get("titulo", "")[:70])
        if args.sin_api:
            fichas.append({
                "id": a["id"], "url": a.get("url", ""), "fuente": a.get("fuente", ""),
                "titulo": a.get("titulo", ""),
                "ubicacion_comuna": a.get("ubicacion") or a.get("titulo", "")[:60],
                "zona": a.get("zona_detectada") or "Fuera de zona",
                "superficie": "dato faltante", "precio_clp": a.get("precio_clp"),
                "precio_texto": a.get("nota_precio", ""),
                "forma_pago": "dato faltante", "estado_rol": "dato faltante",
                "agua": "dato faltante", "luz": "dato faltante",
                "veredicto": "Cumple con reservas", "puntaje": 3,
                "justificacion_puntaje": "Ficha simulada (--sin-api).",
                "riesgos": [], "datos_faltantes": ["Evaluacion real pendiente"],
                "comparacion_zona": "sin evaluar", "_error": None,
            })
        else:
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
        "errores": errores,
        "uf_valor": uf,
        "uf_estimada": not uf_real,
        "duracion_s": round((datetime.now() - inicio).total_seconds(), 1),
    }
    almacen.registrar_corrida(datos, resumen)
    almacen.guardar(datos)
    log.info("Historico guardado: %d avisos en total", len(datos["avisos"]))

    # --- 7. Correo -----------------------------------------------------------
    html = correo.construir_html(nuevas, resumen, URL_WEB)
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
