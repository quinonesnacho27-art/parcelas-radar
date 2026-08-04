"""
Evaluador: llama a la API de Claude con exactamente los criterios del Proyecto
y devuelve la ficha estructurada.

Regla de oro: el modelo NO puede inventar datos. Todo lo que no este en el aviso
se marca como 'dato faltante'.
"""

import json
import os
import re

from anthropic import Anthropic

from config import (
    CRITERIOS,
    MODELO,
    PRECIO_IDEAL_MAX,
    PRECIO_TOLERABLE_MAX,
    ZONAS,
)

SYSTEM_PROMPT = f"""Eres un agente evaluador de oportunidades inmobiliarias de inversion,
especializado en dos zonas exclusivas del sur de Chile. Analizas avisos de parcelas y
determinas si cumplen los criterios de inversion definidos.

ZONAS VALIDAS (sin excepcion - descarta cualquier otra zona):
- Cordillera de Nuble: San Fabian, Coihueco, Pinto, Las Trancas, Recinto y sectores
  cordilleranos aledanos de la Region de Nuble.
- Isla de Chiloe: Ancud, Castro, Quellon, Dalcahue, Quemchi, Chonchi, Curaco de Velez,
  Puqueldon.

Si el aviso no esta claramente en una de estas dos zonas, indicalo y DETEN el analisis
ahi: veredicto "No cumple", puntaje 1, y no evalues el resto de criterios.

CRITERIOS DE FILTRADO:
- Uso: {CRITERIOS['uso']}
- Precio: {CRITERIOS['precio']}
- Forma de pago: {CRITERIOS['forma_pago']}
- Rol propio (SII): {CRITERIOS['rol']}
- Factibilidad de agua: {CRITERIOS['agua']}
- Factibilidad de luz: {CRITERIOS['luz']}

COMPORTAMIENTO:
- NO inventes datos que no esten en el aviso. Si algo no se puede verificar desde el
  material entregado, dilo explicitamente como "dato faltante - pedir al vendedor".
- Se directo sobre si algo es mala senal. La utilidad de este sistema depende de que
  las advertencias sean honestas, no complacientes.
- Senales de riesgo a reportar APARTE del puntaje (no las escondas dentro del puntaje):
  subdivision no regularizada, loteo irregular, sin acceso o servidumbre de paso poco
  clara, zona de riesgo volcanico o de incendio, vendedor no verificable, precio muy por
  debajo del resto de la zona sin explicacion, discrepancias entre lo publicado y lo
  verificable.
- El puntaje 1-5 considera: precio vs. lo visto antes en esa misma zona, riesgos
  evidentes, y potencial de plusvalia (cercania a polos turisticos, rutas, proyectos de
  conectividad conocidos).

Respondes SIEMPRE con un unico objeto JSON valido, sin texto antes ni despues,
sin bloques de codigo markdown."""

ESQUEMA = """{
  "ubicacion_comuna": "string - comuna y sector tal como aparece en el aviso",
  "zona": "Cordillera de Nuble" | "Isla de Chiloe" | "Fuera de zona",
  "superficie": "string - ej '5.000 m2' o 'dato faltante'",
  "precio_clp": number | null,
  "precio_texto": "string - como lo publica el aviso, incl. UF si aplica",
  "forma_pago": "string - 'al contado' | 'credito directo' | 'dato faltante - pedir al vendedor'",
  "cumple_contado": true | false | null,
  "estado_rol": "string - 'rol propio confirmado' | 'sin rol' | 'dato faltante - pedir al vendedor'",
  "agua": "string - descripcion de la factibilidad o 'dato faltante - pedir al vendedor'",
  "agua_ok": true | false | null,
  "luz": "string - descripcion o 'dato faltante - pedir al vendedor'",
  "luz_ok": true | false | null,
  "fuente": "string",
  "fecha_publicacion": "string o 'dato faltante'",
  "veredicto": "Cumple" | "Cumple con reservas" | "No cumple",
  "puntaje": 1 | 2 | 3 | 4 | 5,
  "justificacion_puntaje": "string - 2 a 4 frases, concretas",
  "riesgos": ["string", ...],
  "datos_faltantes": ["string - preguntas concretas que hay que hacerle al vendedor", ...],
  "comparacion_zona": "string - comparacion con avisos previos de la misma zona, o 'sin avisos previos en esta zona' si no hay historico"
}"""


def _cliente() -> Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta la variable de entorno ANTHROPIC_API_KEY. "
            "En GitHub la configuras en Settings > Secrets and variables > Actions."
        )
    return Anthropic(api_key=key)


def _contexto_historico(historico: list[dict], zona: str | None, limite: int = 8) -> str:
    """Resume avisos previos de la misma zona para que el modelo pueda comparar."""
    if not zona or not historico:
        return "No hay avisos previos registrados en esta zona."
    previos = [
        a for a in historico
        if a.get("zona") == zona and a.get("precio_clp")
    ]
    if not previos:
        return f"No hay avisos previos con precio registrado en {zona}."
    previos = sorted(previos, key=lambda a: a.get("primera_vez", ""), reverse=True)[:limite]
    lineas = [
        f"- {a.get('ubicacion_comuna', '?')}: ${a['precio_clp']:,.0f} CLP, "
        f"{a.get('superficie', '?')}, puntaje {a.get('puntaje', '?')}/5 "
        f"({a.get('primera_vez', '')[:10]})"
        for a in previos
    ]
    precios = [a["precio_clp"] for a in previos]
    mediana = sorted(precios)[len(precios) // 2]
    return (
        f"Avisos previos en {zona} (mediana ${mediana:,.0f} CLP):\n" + "\n".join(lineas)
    )


def _extraer_json(texto: str) -> dict:
    """Tolerante a que el modelo envuelva el JSON en markdown."""
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.M).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", texto, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def evaluar(aviso: dict, historico: list[dict] | None = None, uf_valor: float | None = None) -> dict:
    """
    Evalua un aviso. Devuelve la ficha estructurada mas metadatos de trazabilidad.
    Si la llamada falla, devuelve una ficha de error en vez de reventar la corrida.
    """
    historico = historico or []
    zona_hint = aviso.get("zona_detectada")

    partes = [
        "AVISO A EVALUAR",
        "=" * 60,
        f"Fuente: {aviso.get('fuente', 'desconocida')}",
        f"URL: {aviso.get('url', 'sin url')}",
        f"Fecha de publicacion/captura: {aviso.get('fecha', 'dato faltante')}",
        f"Titulo: {aviso.get('titulo', '')}",
        f"Ubicacion segun el aviso: {aviso.get('ubicacion', 'dato faltante')}",
        f"Precio segun el aviso: {aviso.get('precio_texto', 'dato faltante')}",
        "",
        "Descripcion completa:",
        aviso.get("descripcion", "(sin descripcion)"),
        "",
        "=" * 60,
        "CONTEXTO AUTOMATICO (no es parte del aviso, es del sistema):",
        f"- Zona detectada por el prefiltro: {zona_hint or 'ninguna'}",
        f"- Precio normalizado por el prefiltro: {aviso.get('nota_precio', 'n/a')}",
    ]
    if uf_valor:
        partes.append(f"- Valor UF usado para conversiones: ${uf_valor:,.0f} CLP")
    partes += [
        "",
        _contexto_historico(historico, zona_hint),
        "",
        "=" * 60,
        f"Techo de precio ideal: ${PRECIO_IDEAL_MAX:,.0f} CLP. "
        f"Techo tolerable: ${PRECIO_TOLERABLE_MAX:,.0f} CLP.",
        "",
        "Responde con este esquema JSON exacto:",
        ESQUEMA,
    ]

    try:
        resp = _cliente().messages.create(
            model=MODELO,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n".join(partes)}],
        )
        ficha = _extraer_json(resp.content[0].text)
        ficha["_error"] = None
    except Exception as e:  # noqa: BLE001 - queremos que nada rompa la corrida diaria
        ficha = {
            "ubicacion_comuna": aviso.get("ubicacion", "?"),
            "zona": zona_hint or "Fuera de zona",
            "superficie": "dato faltante",
            "precio_clp": aviso.get("precio_clp"),
            "precio_texto": aviso.get("precio_texto", ""),
            "forma_pago": "dato faltante",
            "estado_rol": "dato faltante",
            "agua": "dato faltante",
            "luz": "dato faltante",
            "veredicto": "Cumple con reservas",
            "puntaje": 2,
            "justificacion_puntaje": "No se pudo evaluar automaticamente.",
            "riesgos": ["El aviso no pudo ser evaluado por el modelo; revisar a mano."],
            "datos_faltantes": ["Evaluacion manual pendiente"],
            "comparacion_zona": "sin evaluar",
            "_error": f"{type(e).__name__}: {e}",
        }

    # Trazabilidad: siempre sabemos de donde vino la ficha
    ficha["url"] = aviso.get("url", "")
    ficha["fuente"] = aviso.get("fuente", ficha.get("fuente", ""))
    ficha["titulo"] = aviso.get("titulo", "")
    ficha["id"] = aviso.get("id", "")
    return ficha
