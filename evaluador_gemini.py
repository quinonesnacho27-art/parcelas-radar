"""
Motor opcional: capa gratuita de Google AI Studio (Gemini).

1.500 consultas al dia sin tarjeta de credito, mas que suficiente para el tope
de 25 evaluaciones por corrida de este proyecto.

Usa la API REST directamente con requests, sin SDK, para no sumar dependencias.

La clave se lee de la variable de entorno GEMINI_API_KEY. Si no esta, este modulo
falla limpio y motor.py cae al evaluador de reglas.

Aviso importante: Google indica que los prompts de la capa gratuita pueden usarse
para mejorar sus productos. Aca solo se le envia el texto de avisos publicos de
parcelas, asi que el riesgo es bajo, pero es un dato que hay que tener.
"""

import json
import os
import re

import requests

import evaluador_reglas
import prioridad
from evaluador import ESQUEMA, SYSTEM_PROMPT, _contexto_historico

MODELO = os.environ.get("GEMINI_MODELO", "gemini-2.5-flash")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
TIMEOUT = 60


def _extraer_json(texto: str) -> dict:
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip(), flags=re.M).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", texto, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def evaluar(aviso: dict, historico=None, uf_valor=None) -> dict:
    clave = os.environ.get("GEMINI_API_KEY")
    if not clave:
        return {"_error": "Falta GEMINI_API_KEY"}

    historico = historico or []
    zona = aviso.get("zona_detectada")

    # El motor de reglas hace primero la extraccion. Al modelo se le pide que
    # revise y redacte, no que adivine: asi los datos duros siguen siendo
    # deterministas y solo la narrativa depende del modelo.
    base = evaluador_reglas.evaluar(dict(aviso), historico, uf_valor)

    prompt = "\n".join([
        "AVISO A EVALUAR",
        "=" * 60,
        f"Fuente: {aviso.get('fuente', 'desconocida')}",
        f"URL: {aviso.get('url', 'sin url')}",
        f"Titulo: {aviso.get('titulo', '')}",
        f"Ubicacion segun el aviso: {aviso.get('ubicacion', 'dato faltante')}",
        f"Precio segun el aviso: {aviso.get('precio_texto', 'dato faltante')}",
        "",
        "Descripcion completa:",
        aviso.get("descripcion", "(sin descripcion)"),
        "",
        "=" * 60,
        "EXTRACCION AUTOMATICA YA REALIZADA (corrigela solo si el aviso dice otra cosa):",
        json.dumps({k: base.get(k) for k in
                    ("superficie", "precio_clp", "forma_pago", "estado_rol", "agua", "luz")},
                   ensure_ascii=False, indent=1),
        "",
        _contexto_historico(historico, zona),
        "",
        "Responde con este esquema JSON exacto:",
        ESQUEMA,
    ])

    try:
        r = requests.post(
            URL.format(MODELO),
            params={"key": clave},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048,
                                     "responseMimeType": "application/json"},
            },
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return {"_error": f"Gemini HTTP {r.status_code}: {r.text[:200]}"}

        texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        ficha = _extraer_json(texto)
    except Exception as e:  # noqa: BLE001
        return {"_error": f"{type(e).__name__}: {e}"}

    # Los datos de trazabilidad no los pone el modelo
    ficha.update({
        "url": aviso.get("url", ""),
        "fuente": aviso.get("fuente", ficha.get("fuente", "")),
        "titulo": aviso.get("titulo", ""),
        "id": aviso.get("id", ""),
        "_error": None,
        "_motor": f"gemini ({MODELO})",
    })
    ficha.setdefault("agua_ok", base.get("agua_ok"))
    ficha.setdefault("luz_ok", base.get("luz_ok"))
    ficha.setdefault("cumple_contado", base.get("cumple_contado"))
    return prioridad.calcular(ficha)
