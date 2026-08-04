"""
Generacion y envio del informe diario por correo.

HTML pensado para leerse en el celular: una tarjeta por parcela, sin tablas
anidadas, sin CSS externo, fuentes grandes.
"""

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from config import ASUNTO_BASE, DESTINATARIOS, REMITENTE_NOMBRE

COLOR = {
    "Cumple": ("#0f7b3d", "#e8f6ee"),
    "Cumple con reservas": ("#9a6700", "#fff6e0"),
    "No cumple": ("#8b1a1a", "#fdeaea"),
}

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _clp(v) -> str:
    if not isinstance(v, (int, float)):
        return "dato faltante"
    return "$" + f"{int(v):,}".replace(",", ".")


def _fecha_larga(d: datetime) -> str:
    return f"{d.day} de {MESES[d.month]} de {d.year}"


def _fila(etiqueta: str, valor: str) -> str:
    return (
        f'<tr><td style="padding:4px 10px 4px 0;color:#666;font-size:13px;'
        f'white-space:nowrap;vertical-align:top">{etiqueta}</td>'
        f'<td style="padding:4px 0;font-size:14px;color:#1a1a1a">{valor or "dato faltante"}</td></tr>'
    )


def _tarjeta(f: dict, url_web: str) -> str:
    borde, fondo = COLOR.get(f.get("veredicto", ""), ("#555", "#f2f2f2"))
    puntaje = f.get("puntaje", 0) or 0
    estrellas = "&#9733;" * int(puntaje) + "&#9734;" * (5 - int(puntaje))

    riesgos = f.get("riesgos") or []
    bloque_riesgos = ""
    if riesgos:
        items = "".join(f"<li style='margin:3px 0'>{r}</li>" for r in riesgos)
        bloque_riesgos = (
            '<div style="margin-top:10px;padding:10px 12px;background:#fdeaea;'
            'border-left:3px solid #c0392b;border-radius:4px">'
            '<div style="font-weight:600;color:#8b1a1a;font-size:13px;margin-bottom:4px">'
            'Advertencias</div>'
            f'<ul style="margin:0;padding-left:18px;font-size:13px;color:#5a2020">{items}</ul></div>'
        )

    faltantes = f.get("datos_faltantes") or []
    bloque_faltantes = ""
    if faltantes:
        items = "".join(f"<li style='margin:3px 0'>{d}</li>" for d in faltantes)
        bloque_faltantes = (
            '<div style="margin-top:10px;padding:10px 12px;background:#eef4fb;'
            'border-left:3px solid #2c6fb5;border-radius:4px">'
            '<div style="font-weight:600;color:#1c4d80;font-size:13px;margin-bottom:4px">'
            'Preguntar al vendedor</div>'
            f'<ul style="margin:0;padding-left:18px;font-size:13px;color:#24405c">{items}</ul></div>'
        )

    enlace = ""
    if f.get("url"):
        enlace = (
            f'<a href="{f["url"]}" style="display:inline-block;margin-top:12px;'
            'padding:9px 16px;background:#1a1a1a;color:#fff;text-decoration:none;'
            'border-radius:6px;font-size:14px;font-weight:600">Ver el aviso</a>'
        )

    return f"""
<div style="border:1px solid #e0e0e0;border-left:4px solid {borde};border-radius:8px;
            padding:16px;margin-bottom:18px;background:#fff">
  <div style="display:block;margin-bottom:10px">
    <span style="background:{fondo};color:{borde};padding:4px 10px;border-radius:20px;
                 font-size:12px;font-weight:700;letter-spacing:.3px">
      {f.get('veredicto', 'sin veredicto').upper()}</span>
    <span style="color:#c8901a;font-size:16px;margin-left:8px">{estrellas}</span>
    <span style="color:#888;font-size:12px">{puntaje}/5</span>
  </div>
  <div style="font-size:17px;font-weight:700;color:#111;margin-bottom:2px;line-height:1.3">
    {f.get('ubicacion_comuna', 'Ubicacion no especificada')}</div>
  <div style="font-size:13px;color:#777;margin-bottom:12px">
    {f.get('zona', '')} &middot; {f.get('fuente', '')}</div>

  <table style="width:100%;border-collapse:collapse">
    {_fila('Superficie', f.get('superficie'))}
    {_fila('Precio', f"<b>{_clp(f.get('precio_clp'))}</b> &nbsp;<span style='color:#888;font-size:12px'>{f.get('precio_texto','')}</span>")}
    {_fila('Forma de pago', f.get('forma_pago'))}
    {_fila('Rol SII', f.get('estado_rol'))}
    {_fila('Agua', f.get('agua'))}
    {_fila('Luz', f.get('luz'))}
    {_fila('Publicado', f.get('fecha_publicacion'))}
  </table>

  <div style="margin-top:12px;padding:10px 12px;background:#fafafa;border-radius:4px;
              font-size:13px;color:#333;line-height:1.5">
    {f.get('justificacion_puntaje', '')}
  </div>
  <div style="margin-top:8px;font-size:12px;color:#777;font-style:italic">
    Comparacion en zona: {f.get('comparacion_zona', 'sin datos previos')}
  </div>
  {bloque_riesgos}
  {bloque_faltantes}
  {enlace}
</div>"""


def construir_html(nuevas: list[dict], resumen: dict, url_web: str) -> str:
    hoy = _fecha_larga(datetime.now())

    cumplen = [f for f in nuevas if f.get("veredicto") == "Cumple"]
    reservas = [f for f in nuevas if f.get("veredicto") == "Cumple con reservas"]
    descartadas = [f for f in nuevas if f.get("veredicto") == "No cumple"]

    if not nuevas:
        cuerpo = (
            '<div style="padding:28px;text-align:center;background:#fafafa;border-radius:8px;'
            'border:1px dashed #ddd">'
            '<div style="font-size:16px;color:#555;font-weight:600">Sin avisos nuevos hoy</div>'
            '<div style="font-size:13px;color:#888;margin-top:6px">'
            f'Se revisaron {resumen.get("revisados", 0)} publicaciones en '
            f'{resumen.get("fuentes", 0)} fuentes. Ninguna nueva en las zonas objetivo.</div></div>'
        )
    else:
        cuerpo = ""
        for titulo, grupo, color in [
            ("Cumplen los criterios", cumplen, "#0f7b3d"),
            ("Cumplen con reservas", reservas, "#9a6700"),
            ("Revisadas y descartadas", descartadas, "#8b1a1a"),
        ]:
            if not grupo:
                continue
            cuerpo += (
                f'<div style="font-size:14px;font-weight:700;color:{color};'
                'text-transform:uppercase;letter-spacing:.5px;margin:24px 0 12px">'
                f'{titulo} ({len(grupo)})</div>'
            )
            cuerpo += "".join(
                _tarjeta(f, url_web)
                for f in sorted(grupo, key=lambda x: x.get("puntaje", 0), reverse=True)
            )

    avisos_errores = ""
    if resumen.get("errores"):
        items = "".join(f"<li>{e}</li>" for e in resumen["errores"][:6])
        avisos_errores = (
            '<div style="margin-top:20px;padding:12px;background:#fff8e6;border-radius:6px;'
            'font-size:12px;color:#7a5c00">'
            f'<b>Fuentes con problemas en esta corrida:</b><ul style="margin:6px 0 0;padding-left:18px">{items}</ul></div>'
        )

    nota_uf = ""
    if resumen.get("uf_estimada"):
        nota_uf = (
            '<div style="margin-top:12px;padding:10px;background:#fff8e6;border-radius:6px;'
            f'font-size:12px;color:#7a5c00">Aviso: no se pudo consultar el valor real de la UF; '
            f'las conversiones usan un valor estimado de {_clp(resumen.get("uf_valor"))}.</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ASUNTO_BASE}</title></head>
<body style="margin:0;padding:0;background:#f4f4f2;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif">
<div style="max-width:640px;margin:0 auto;padding:20px 14px">

  <div style="background:#1a3a2a;border-radius:10px;padding:22px;margin-bottom:20px">
    <div style="color:#8fd6a8;font-size:12px;font-weight:700;letter-spacing:1.5px;
                text-transform:uppercase">Parcelas Radar</div>
    <div style="color:#fff;font-size:24px;font-weight:700;margin-top:6px">Informe del {hoy}</div>
    <div style="color:#a8c4b4;font-size:14px;margin-top:8px">
      {len(nuevas)} aviso{'s' if len(nuevas) != 1 else ''} nuevo{'s' if len(nuevas) != 1 else ''}
      &middot; {resumen.get('revisados', 0)} publicaciones revisadas
      &middot; Cordillera de Nuble e Isla de Chiloe
    </div>
  </div>

  {cuerpo}
  {avisos_errores}
  {nota_uf}

  <div style="margin-top:24px;text-align:center">
    <a href="{url_web}" style="display:inline-block;padding:13px 26px;background:#1a3a2a;
       color:#fff;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600">
       Abrir el buscador y la calculadora</a>
  </div>

  <div style="margin-top:24px;padding-top:16px;border-top:1px solid #ddd;
              font-size:11px;color:#999;line-height:1.6;text-align:center">
    Este informe lo genera un sistema automatico que revisa portales publicos y los
    avisos que ustedes reenvian por correo. Los datos vienen de los avisos: pueden
    estar incompletos o ser inexactos. Nada aqui reemplaza verificar el rol en el SII,
    revisar el plano de subdivision y visitar el terreno antes de comprometer dinero.
  </div>
</div></body></html>"""


def enviar(html: str, asunto: str, texto_plano: str = "") -> None:
    usuario = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not usuario or not password:
        raise RuntimeError(
            "Faltan GMAIL_USER y/o GMAIL_APP_PASSWORD en las variables de entorno."
        )

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = f"{REMITENTE_NOMBRE} <{usuario}>"
    msg["To"] = ", ".join(DESTINATARIOS)
    msg.set_content(texto_plano or "Abre este correo en un cliente que soporte HTML.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(usuario, password)
        s.send_message(msg)
